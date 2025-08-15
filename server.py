import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from db import (
    init_db,
    seed_from_json,
    fetch_all_data,
    get_kri,
    add_system as db_add_system,
    upsert_data_point,
    update_data_point as db_update_data_point,
    delete_data_point as db_delete_data_point,
    delete_system as db_delete_system,
    VALUE_FIELD_MAP,
    APP_BASED_KRIS,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')


# Pydantic models
class AddSystemRequest(BaseModel):
    kriId: str
    systemName: str


class AddDataPointRequest(BaseModel):
    kriId: str
    period: str
    value: float
    valueField: Optional[str] = None
    systemName: Optional[str] = None


class UpdateDataPointRequest(BaseModel):
    kriId: str
    period: str
    systemName: Optional[str] = None
    value: Optional[float] = None
    valueField: Optional[str] = None


class DeleteDataPointRequest(BaseModel):
    kriId: str
    period: str
    systemName: Optional[str] = None


class DeleteSystemRequest(BaseModel):
    kriId: str
    systemName: str


app = FastAPI()

# CORS (relaxed for simplicity; tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def startup_event():
    # Ensure DB exists and seed from JSON if empty
    init_db(drop=False)
    # Optionally seed when DB is empty (first run)
    data = fetch_all_data()
    if all((not v.get('data')) and (not v.get('applications')) for v in data.values()):
        seed_from_json()


@app.get('/', response_class=HTMLResponse)
async def get_index():
    if not os.path.exists(INDEX_FILE):
        raise HTTPException(status_code=404, detail='index.html not found')
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get('/api/kri-data')
async def api_get_kri_data():
    return fetch_all_data()


@app.get('/api/kri/{kri_id}')
async def api_get_single_kri(kri_id: str):
    if kri_id not in VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    return get_kri(kri_id)


@app.post('/api/add-system')
async def api_add_system(req: AddSystemRequest):
    kri = req.kriId
    if kri not in VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    if kri not in APP_BASED_KRIS:
        raise HTTPException(status_code=400, detail='KRI is not applications-based')
    name = req.systemName.strip()
    if not name:
        raise HTTPException(status_code=400, detail='System name is required')
    db_add_system(kri, name)
    return {'success': True, 'kriId': kri, 'kri': get_kri(kri)}


@app.post('/api/add-data-point')
async def api_add_data_point(req: AddDataPointRequest):
    kri = req.kriId
    if kri not in VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')

    field = req.valueField or VALUE_FIELD_MAP[kri]
    if field != VALUE_FIELD_MAP[kri]:
        raise HTTPException(status_code=400, detail=f'Invalid valueField for {kri}. Expected {VALUE_FIELD_MAP[kri]}')

    period = req.period.strip()
    if not period:
        raise HTTPException(status_code=400, detail='Period is required')

    value = float(req.value)
    if value < 0:
        raise HTTPException(status_code=400, detail='Value must be non-negative')

    if kri in APP_BASED_KRIS and not req.systemName:
        raise HTTPException(status_code=400, detail='systemName is required for applications-based KRI')

    upsert_data_point(kri, period, value, system_name=req.systemName)
    return {'success': True, 'kriId': kri, 'kri': get_kri(kri)}


@app.put('/api/update-data-point')
async def api_update_data_point(req: UpdateDataPointRequest):
    kri = req.kriId
    if kri not in VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    if req.valueField and req.valueField != VALUE_FIELD_MAP[kri]:
        raise HTTPException(status_code=400, detail=f'Invalid valueField for {kri}. Expected {VALUE_FIELD_MAP[kri]}')

    changed = db_update_data_point(
        kri_id=kri,
        period=req.period,
        value=req.value,
        system_name=req.systemName,
    )
    if changed == 0:
        raise HTTPException(status_code=404, detail='Data point not found or no changes provided')
    return {'success': True, 'kriId': kri, 'kri': get_kri(kri)}


@app.delete('/api/delete-data-point')
async def api_delete_data_point(req: DeleteDataPointRequest):
    kri = req.kriId
    if kri not in VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    deleted = db_delete_data_point(kri, req.period, req.systemName)
    if deleted == 0:
        raise HTTPException(status_code=404, detail='Data point not found')
    return {'success': True, 'kriId': kri, 'kri': get_kri(kri)}


@app.delete('/api/delete-system')
async def api_delete_system(req: DeleteSystemRequest):
    kri = req.kriId
    if kri not in VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    if kri not in APP_BASED_KRIS:
        raise HTTPException(status_code=400, detail='KRI is not applications-based')
    pts, sys = db_delete_system(kri, req.systemName)
    if sys == 0:
        raise HTTPException(status_code=404, detail='System not found')
    return {'success': True, 'deletedPoints': pts, 'deletedSystems': sys, 'kriId': kri, 'kri': get_kri(kri)}