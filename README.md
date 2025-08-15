# KRI Dashboards (SQLite, No Dates)

This version removes all date fields from DB, API, seed data, and UI. The only temporal identifier is `period` (e.g., `Q2-2025` or `06-2025`). Update/Delete forms no longer include “New Period” or “New Date”.

## Files
- `index.html` — Front-end (CRUD forms without date fields)
- `server.py` — FastAPI server (no date handling)
- `db.py` — SQLite schema and CRUD (no date columns)
- `kri-data.json` — Seed data without date fields
- `requirements.txt`

## Install
```bash
pip3 install --break-system-packages -r requirements.txt
```

## Run
```bash
~/.local/bin/uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```
Open `http://localhost:8000`.

## API
- GET `/api/kri-data`
- GET `/api/kri/{kriId}`
- POST `/api/add-system` — `{ "kriId":"kri8", "systemName":"BirBank" }`
- POST `/api/add-data-point` —
  - simple: `{ "kriId":"kri2", "period":"Q2-2025", "value":97 }`
  - app: `{ "kriId":"kri10", "systemName":"BirBank", "period":"06-2025", "value":4 }`
- PUT `/api/update-data-point` —
  - simple: `{ "kriId":"kri2", "period":"Q2-2025", "value":98 }`
  - app: `{ "kriId":"kri10", "systemName":"BirBank", "period":"06-2025", "value":5 }`
- DELETE `/api/delete-data-point` — `{ "kriId":"kri2", "period":"Q2-2025" }` or `{ "kriId":"kri10", "systemName":"BirBank", "period":"06-2025" }`
- DELETE `/api/delete-system` — `{ "kriId":"kri10", "systemName":"BirBank" }`

Notes:
- Value must be non-negative
- Period string is used as-is; no server-side date inference
- UI forms accept one `period` and one `value` for add/update; delete uses `period` only