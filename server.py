import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

import kri_db
import rhi_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KRI_FILE = os.path.join(BASE_DIR, 'kri.html')
RHI_FILE = os.path.join(BASE_DIR, 'rhi.html')


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
    # Ensure both DBs exist and seed from JSON if empty
    kri_db.init_db(drop=False)
    rhi_db.init_db(drop=False)
    # Optionally seed when DB is empty (first run)
    kri_data = kri_db.fetch_all_data()
    if all((not v.get('data')) and (not v.get('applications')) for v in kri_data.values()):
        kri_db.seed_from_json()
    rhi_data = rhi_db.fetch_all_data()
    if all((not v.get('data')) and (not v.get('applications')) for v in rhi_data.values()):
        rhi_db.seed_from_json()


@app.get('/', response_class=HTMLResponse)
async def get_root():
    if not os.path.exists(KRI_FILE):
        raise HTTPException(status_code=404, detail='kri.html not found')
    return FileResponse(KRI_FILE)


@app.get('/kri.html', response_class=HTMLResponse)
async def get_kri_page():
    if not os.path.exists(KRI_FILE):
        raise HTTPException(status_code=404, detail='kri.html not found')
    return FileResponse(KRI_FILE)


@app.get('/rhi.html', response_class=HTMLResponse)
async def get_rhi_page():
    if not os.path.exists(RHI_FILE):
        raise HTTPException(status_code=404, detail='rhi.html not found')
    return FileResponse(RHI_FILE)


# -------------------- KRI API --------------------
@app.get('/api/kri-data')
async def api_get_kri_data():
    return kri_db.fetch_all_data()


@app.get('/api/kri/{kri_id}')
async def api_get_single_kri(kri_id: str):
    if kri_id not in kri_db.VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    return kri_db.get_kri(kri_id)


@app.post('/api/kri/add-system')
async def api_kri_add_system(req: AddSystemRequest):
    kri = req.kriId
    if kri not in kri_db.VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    if kri not in kri_db.APP_BASED_KRIS:
        raise HTTPException(status_code=400, detail='KRI is not applications-based')
    name = req.systemName.strip()
    if not name:
        raise HTTPException(status_code=400, detail='System name is required')
    kri_db.add_system(kri, name)
    return {'success': True, 'kriId': kri, 'kri': kri_db.get_kri(kri)}


@app.post('/api/kri/add-data-point')
async def api_kri_add_data_point(req: AddDataPointRequest):
    kri = req.kriId
    if kri not in kri_db.VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')

    field = req.valueField or kri_db.VALUE_FIELD_MAP[kri]
    if field != kri_db.VALUE_FIELD_MAP[kri]:
        raise HTTPException(status_code=400, detail=f'Invalid valueField for {kri}. Expected {kri_db.VALUE_FIELD_MAP[kri]}')

    period = req.period.strip()
    if not period:
        raise HTTPException(status_code=400, detail='Period is required')

    value = float(req.value)
    if value < 0:
        raise HTTPException(status_code=400, detail='Value must be non-negative')

    if kri in kri_db.APP_BASED_KRIS and not req.systemName:
        raise HTTPException(status_code=400, detail='systemName is required for applications-based KRI')

    kri_db.upsert_data_point(kri, period, value, system_name=req.systemName)
    return {'success': True, 'kriId': kri, 'kri': kri_db.get_kri(kri)}


@app.put('/api/kri/update-data-point')
async def api_kri_update_data_point(req: UpdateDataPointRequest):
    kri = req.kriId
    if kri not in kri_db.VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    if req.valueField and req.valueField != kri_db.VALUE_FIELD_MAP[kri]:
        raise HTTPException(status_code=400, detail=f'Invalid valueField for {kri}. Expected {kri_db.VALUE_FIELD_MAP[kri]}')

    changed = kri_db.update_data_point(
        kri_id=kri,
        period=req.period,
        value=req.value,
        system_name=req.systemName,
    )
    if changed == 0:
        raise HTTPException(status_code=404, detail='Data point not found or no changes provided')
    return {'success': True, 'kriId': kri, 'kri': kri_db.get_kri(kri)}


@app.delete('/api/kri/delete-data-point')
async def api_kri_delete_data_point(req: DeleteDataPointRequest):
    kri = req.kriId
    if kri not in kri_db.VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    deleted = kri_db.delete_data_point(kri, req.period, req.systemName)
    if deleted == 0:
        raise HTTPException(status_code=404, detail='Data point not found')
    return {'success': True, 'kriId': kri, 'kri': kri_db.get_kri(kri)}


@app.delete('/api/kri/delete-system')
async def api_kri_delete_system(req: DeleteSystemRequest):
    kri = req.kriId
    if kri not in kri_db.VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    if kri not in kri_db.APP_BASED_KRIS:
        raise HTTPException(status_code=400, detail='KRI is not applications-based')
    pts, sys = kri_db.delete_system(kri, req.systemName)
    if sys == 0:
        raise HTTPException(status_code=404, detail='System not found')
    return {'success': True, 'deletedPoints': pts, 'deletedSystems': sys, 'kriId': kri, 'kri': kri_db.get_kri(kri)}


# -------------------- RHI API --------------------
@app.get('/api/rhi-data')
async def api_get_rhi_data():
    return rhi_db.fetch_all_data()


@app.get('/api/rhi/{rhi_id}')
async def api_get_single_rhi(rhi_id: str):
    if rhi_id not in rhi_db.VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown RHI id')
    return rhi_db.get_kri(rhi_id)


@app.post('/api/rhi/add-data-point')
async def api_rhi_add_data_point(req: AddDataPointRequest):
    rhi = req.kriId
    if rhi not in rhi_db.VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown RHI id')

    field = req.valueField or rhi_db.VALUE_FIELD_MAP[rhi]
    if field != rhi_db.VALUE_FIELD_MAP[rhi]:
        raise HTTPException(status_code=400, detail=f'Invalid valueField for {rhi}. Expected {rhi_db.VALUE_FIELD_MAP[rhi]}')

    period = req.period.strip()
    if not period:
        raise HTTPException(status_code=400, detail='Period is required')

    value = float(req.value)
    if value < 0:
        raise HTTPException(status_code=400, detail='Value must be non-negative')

    rhi_db.upsert_data_point(rhi, period, value)
    return {'success': True, 'kriId': rhi, 'kri': rhi_db.get_kri(rhi)}


@app.put('/api/rhi/update-data-point')
async def api_rhi_update_data_point(req: UpdateDataPointRequest):
    rhi = req.kriId
    if rhi not in rhi_db.VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown RHI id')
    if req.valueField and req.valueField != rhi_db.VALUE_FIELD_MAP[rhi]:
        raise HTTPException(status_code=400, detail=f'Invalid valueField for {rhi}. Expected {rhi_db.VALUE_FIELD_MAP[rhi]}')

    changed = rhi_db.update_data_point(
        kri_id=rhi,
        period=req.period,
        value=req.value,
    )
    if changed == 0:
        raise HTTPException(status_code=404, detail='Data point not found or no changes provided')
    return {'success': True, 'kriId': rhi, 'kri': rhi_db.get_kri(rhi)}


@app.delete('/api/rhi/delete-data-point')
async def api_rhi_delete_data_point(req: DeleteDataPointRequest):
    rhi = req.kriId
    if rhi not in rhi_db.VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown RHI id')
    deleted = rhi_db.delete_data_point(rhi, req.period)
    if deleted == 0:
        raise HTTPException(status_code=404, detail='Data point not found')
    return {'success': True, 'kriId': rhi, 'kri': rhi_db.get_kri(rhi)}


# --------------- Legacy KRI routes for compatibility ---------------
@app.post('/api/add-system')
async def legacy_add_system(req: AddSystemRequest):
    return await api_kri_add_system(req)


@app.post('/api/add-data-point')
async def legacy_add_data_point(req: AddDataPointRequest):
    return await api_kri_add_data_point(req)


@app.put('/api/update-data-point')
async def legacy_update_data_point(req: UpdateDataPointRequest):
    return await api_kri_update_data_point(req)


@app.delete('/api/delete-data-point')
async def legacy_delete_data_point(req: DeleteDataPointRequest):
    return await api_kri_delete_data_point(req)


@app.delete('/api/delete-system')
async def legacy_delete_system(req: DeleteSystemRequest):
    return await api_kri_delete_system(req)

