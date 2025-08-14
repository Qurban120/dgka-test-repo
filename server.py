import os
import json
import threading
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'kri-data.json')
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')

# KRI configuration
APP_BASED_KRIS = {'kri8', 'kri10', 'kri12', 'kri13', 'kri19'}
VALUE_FIELD_MAP: Dict[str, str] = {
	'kri2': 'percentage',
	'kri3': 'percentage',
	'kri4': 'count',
	'kri5': 'percentage',
	'kri6': 'percentage',
	'kri8': 'value',
	'kri9': 'count',
	'kri10': 'incidents',
	'kri12': 'incidents',
	'kri13': 'value',
	'kri15': 'percentage',
	'kri18': 'percentage',
	'kri19': 'value',
	'kri20': 'count',
	'kri21': 'count',
	'kri22': 'percentage',
	'kri27': 'percentage',
	'kri28': 'percentage',
}

_file_lock = threading.Lock()


def _read_json() -> Dict[str, Any]:
	if not os.path.exists(DATA_FILE):
		raise HTTPException(status_code=500, detail='Data file not found')
	with _file_lock:
		with open(DATA_FILE, 'r', encoding='utf-8') as f:
			return json.load(f)


def _atomic_write_json(data: Dict[str, Any]) -> None:
	# Write atomically to avoid corruption
	tmp_path = DATA_FILE + '.tmp'
	with _file_lock:
		with open(tmp_path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		os.replace(tmp_path, DATA_FILE)


def _parse_date_from_period(period: str) -> str:
	"""Return ISO date string (YYYY-MM-DD) from period.
	Supports formats like 'Q1-2025' or '01-2025'. Defaults to first day of period.
	"""
	if '-' not in period:
		raise ValueError('Invalid period format')
	part1, year = period.split('-')
	year_i = int(year)
	if part1.startswith('Q'):
		q = part1.upper()
		month = {'Q1': 1, 'Q2': 4, 'Q3': 7, 'Q4': 10}[q]
		return f"{year_i:04d}-{month:02d}-01"
	else:
		# MM-YYYY
		month_i = int(part1)
		return f"{year_i:04d}-{month_i:02d}-01"


class AddSystemRequest(BaseModel):
	kriId: str
	systemName: str


class AddDataPointRequest(BaseModel):
	kriId: str
	period: str
	value: float
	valueField: Optional[str] = None
	systemName: Optional[str] = None
	date: Optional[str] = None  # ISO YYYY-MM-DD


app = FastAPI()

# CORS (relaxed for simplicity; tighten in prod)
app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)


@app.get('/', response_class=HTMLResponse)
async def get_index():
	if not os.path.exists(INDEX_FILE):
		raise HTTPException(status_code=404, detail='index.html not found')
	with open(INDEX_FILE, 'r', encoding='utf-8') as f:
		return HTMLResponse(content=f.read(), status_code=200)


@app.get('/api/kri-data')
async def get_kri_data():
	return _read_json()


@app.post('/api/add-system')
async def add_system(req: AddSystemRequest):
	kri = req.kriId
	if kri not in VALUE_FIELD_MAP:
		raise HTTPException(status_code=400, detail='Unknown KRI id')
	if kri not in APP_BASED_KRIS:
		raise HTTPException(status_code=400, detail='KRI is not applications-based')
	name = req.systemName.strip()
	if not name:
		raise HTTPException(status_code=400, detail='System name is required')

	data = _read_json()
	data.setdefault(kri, {})
	data[kri].setdefault('applications', {})
	if name not in data[kri]['applications']:
		data[kri]['applications'][name] = []
		_atomic_write_json(data)

	return {
		'success': True,
		'kriId': kri,
		'kri': data[kri]
	}


@app.post('/api/add-data-point')
async def add_data_point(req: AddDataPointRequest):
	kri = req.kriId
	if kri not in VALUE_FIELD_MAP:
		raise HTTPException(status_code=400, detail='Unknown KRI id')

	field = req.valueField or VALUE_FIELD_MAP[kri]
	if field != VALUE_FIELD_MAP[kri]:
		raise HTTPException(status_code=400, detail=f'Invalid valueField for {kri}. Expected {VALUE_FIELD_MAP[kri]}')

	period = req.period.strip()
	if not period:
		raise HTTPException(status_code=400, detail='Period is required')

	try:
		iso_date = req.date or _parse_date_from_period(period)
		# Validate date
		datetime.strptime(iso_date, '%Y-%m-%d')
	except Exception:
		raise HTTPException(status_code=400, detail='Invalid date/period')

	value = float(req.value)
	if value < 0:
		raise HTTPException(status_code=400, detail='Value must be non-negative')

	data = _read_json()
	data.setdefault(kri, {})

	if kri in APP_BASED_KRIS:
		# Applications-based
		if not req.systemName:
			raise HTTPException(status_code=400, detail='systemName is required for applications-based KRI')
		system = req.systemName.strip()
		data[kri].setdefault('applications', {})
		apps = data[kri]['applications']
		apps.setdefault(system, [])
		entries = apps[system]

		# Update or insert by period
		existing = next((idx for idx, e in enumerate(entries) if e.get('period') == period), None)
		new_entry = {'period': period, field: value, 'date': iso_date}
		if existing is not None:
			entries[existing] = new_entry
		else:
			entries.append(new_entry)
		# Sort by date
		entries.sort(key=lambda e: e.get('date'))
	else:
		# Simple data list
		data[kri].setdefault('data', [])
		entries = data[kri]['data']
		existing = next((idx for idx, e in enumerate(entries) if e.get('period') == period), None)
		new_entry = {'period': period, field: value, 'date': iso_date}
		if existing is not None:
			entries[existing] = new_entry
		else:
			entries.append(new_entry)
		entries.sort(key=lambda e: e.get('date'))

	_atomic_write_json(data)
	return {
		'success': True,
		'kriId': kri,
		'kri': data[kri]
	}