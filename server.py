import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from db import (
    init_db as init_kri_db,
    seed_from_json as seed_kri,
    fetch_all_data as fetch_all_kri,
    get_kri,
    add_system as db_add_system,
    upsert_data_point as kri_upsert_data_point,
    update_data_point as kri_update_data_point,
    delete_data_point as kri_delete_data_point,
    delete_system as db_delete_system,
    VALUE_FIELD_MAP as KRI_VALUE_FIELD_MAP,
    APP_BASED_KRIS,
)

from rhi_db import (
    init_db as init_rhi_db,
    seed_from_json as seed_rhi,
    fetch_all_data as fetch_all_rhi,
    get_rhi,
    upsert_data_point as rhi_upsert_data_point,
    update_data_point as rhi_update_data_point,
    delete_data_point as rhi_delete_data_point,
    RHI_VALUE_FIELD_MAP,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KRI_FILE = os.path.join(BASE_DIR, 'kri.html')
RHI_FILE = os.path.join(BASE_DIR, 'rhi.html')


# Pydantic models (KRI)
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


# Pydantic models (RHI)
class RHIAddDataPointRequest(BaseModel):
    rhiId: str
    period: str
    value: float


class RHIUpdateDataPointRequest(BaseModel):
    rhiId: str
    period: str
    value: Optional[float] = None


class RHIDeleteDataPointRequest(BaseModel):
    rhiId: str
    period: str


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
    # Ensure DBs exist and seed from JSON if empty
    init_kri_db(drop=False)
    init_rhi_db(drop=False)

    # Seed when DBs are empty
    kri_data = fetch_all_kri()
    if all((not v.get('data')) and (not v.get('applications')) for v in kri_data.values()):
        seed_kri()

    rhi_data = fetch_all_rhi()
    if all((not v.get('data')) for v in rhi_data.values()):
        seed_rhi()


@app.get('/')
async def root_redirect():
    return RedirectResponse(url='/kri', status_code=307)


@app.get('/kri', response_class=HTMLResponse)
async def get_kri_index():
    if not os.path.exists(KRI_FILE):
        raise HTTPException(status_code=404, detail='kri.html not found')
    with open(KRI_FILE, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get('/rhi', response_class=HTMLResponse)
async def get_rhi_index():
    if not os.path.exists(RHI_FILE):
        raise HTTPException(status_code=404, detail='rhi.html not found')
    with open(RHI_FILE, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get('/api/health')
async def health():
    return {'status': 'ok'}


# ----------- KRI API -----------
@app.get('/api/kri-data')
async def api_get_kri_data():
    return fetch_all_kri()


@app.get('/api/kri/{kri_id}')
async def api_get_single_kri(kri_id: str):
    if kri_id not in KRI_VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    return get_kri(kri_id)


@app.post('/api/add-system')
async def api_add_system(req: AddSystemRequest):
    kri = req.kriId
    if kri not in KRI_VALUE_FIELD_MAP:
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
    if kri not in KRI_VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')

    field = req.valueField or KRI_VALUE_FIELD_MAP[kri]
    if field != KRI_VALUE_FIELD_MAP[kri]:
        raise HTTPException(status_code=400, detail=f'Invalid valueField for {kri}. Expected {KRI_VALUE_FIELD_MAP[kri]}')

    period = req.period.strip()
    if not period:
        raise HTTPException(status_code=400, detail='Period is required')

    value = float(req.value)
    if value < 0:
        raise HTTPException(status_code=400, detail='Value must be non-negative')

    if kri in APP_BASED_KRIS and not req.systemName:
        raise HTTPException(status_code=400, detail='systemName is required for applications-based KRI')

    kri_upsert_data_point(kri, period, value, system_name=req.systemName)
    return {'success': True, 'kriId': kri, 'kri': get_kri(kri)}


@app.put('/api/update-data-point')
async def api_update_data_point(req: UpdateDataPointRequest):
    kri = req.kriId
    if kri not in KRI_VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    if req.valueField and req.valueField != KRI_VALUE_FIELD_MAP[kri]:
        raise HTTPException(status_code=400, detail=f'Invalid valueField for {kri}. Expected {KRI_VALUE_FIELD_MAP[kri]}')

    changed = kri_update_data_point(
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
    if kri not in KRI_VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    deleted = kri_delete_data_point(kri, req.period, req.systemName)
    if deleted == 0:
        raise HTTPException(status_code=404, detail='Data point not found')
    return {'success': True, 'kriId': kri, 'kri': get_kri(kri)}


@app.delete('/api/delete-system')
async def api_delete_system(req: DeleteSystemRequest):
    kri = req.kriId
    if kri not in KRI_VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown KRI id')
    if kri not in APP_BASED_KRIS:
        raise HTTPException(status_code=400, detail='KRI is not applications-based')
    pts, sys = db_delete_system(kri, req.systemName)
    if sys == 0:
        raise HTTPException(status_code=404, detail='System not found')
    return {'success': True, 'deletedPoints': pts, 'deletedSystems': sys, 'kriId': kri, 'kri': get_kri(kri)}


# ----------- RHI API -----------
@app.get('/api/rhi-data')
async def api_get_rhi_data():
    return fetch_all_rhi()


@app.get('/api/rhi/{rhi_id}')
async def api_get_single_rhi(rhi_id: str):
    if rhi_id not in RHI_VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown RHI id')
    return get_rhi(rhi_id)


@app.post('/api/rhi/add-data-point')
async def api_rhi_add_data_point(req: RHIAddDataPointRequest):
    rhi = req.rhiId
    if rhi not in RHI_VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown RHI id')
    period = req.period.strip()
    if not period:
        raise HTTPException(status_code=400, detail='Period is required')
    value = float(req.value)
    if value < 0:
        raise HTTPException(status_code=400, detail='Value must be non-negative')
    rhi_upsert_data_point(rhi, period, value)
    return {'success': True, 'rhiId': rhi, 'rhi': get_rhi(rhi)}


@app.put('/api/rhi/update-data-point')
async def api_rhi_update_data_point(req: RHIUpdateDataPointRequest):
    rhi = req.rhiId
    if rhi not in RHI_VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown RHI id')
    changed = rhi_update_data_point(rhi_id=rhi, period=req.period, value=req.value)
    if changed == 0:
        raise HTTPException(status_code=404, detail='Data point not found or no changes provided')
    return {'success': True, 'rhiId': rhi, 'rhi': get_rhi(rhi)}


@app.delete('/api/rhi/delete-data-point')
async def api_rhi_delete_data_point(req: RHIDeleteDataPointRequest):
    rhi = req.rhiId
    if rhi not in RHI_VALUE_FIELD_MAP:
        raise HTTPException(status_code=400, detail='Unknown RHI id')
    deleted = rhi_delete_data_point(rhi, req.period)
    if deleted == 0:
        raise HTTPException(status_code=404, detail='Data point not found')
    return {'success': True, 'rhiId': rhi, 'rhi': get_rhi(rhi)}

