# KRI Dashboards (SQLite, FastAPI)

This is a FastAPI + SQLite implementation of the KRI dashboards. The front-end is a single `index.html` (vanilla JS + Chart.js). The back-end exposes CRUD APIs and stores all KRI data in SQLite.

Important change: The project no longer uses or stores any `date` fields. All operations are based on `period` (e.g., `Q2-2025` or `06-2025`). The UI no longer asks for "New Period" or "New Date" anywhere.

## Features
- Dashboards and charts for multiple KRIs
- SQLite database (`kri.db`) with schema for both simple KRIs and application-based KRIs
- CRUD endpoints:
  - Add system (applications-based KRIs)
  - Add/Update/Delete data point (value only; no date or period changes via update)
  - Delete system (with cascading point delete)
- First run auto-seeds DB from `kri-data.json`

## Structure
- `index.html` — Front-end UI. Includes forms for Add/Update/Delete
- `server.py` — FastAPI server and REST API
- `db.py` — SQLite schema, seed, and CRUD helpers
- `kri-data.json` — Seed data used on first run (no `date` fields)
- `requirements.txt` — Python deps

## Install
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```
Then open `http://localhost:8000` in a browser.

## API Summary
- `GET /api/kri-data` — Fetch all KRIs in the JSON shape expected by the front-end
- `GET /api/kri/{kriId}` — Fetch single KRI
- `POST /api/add-system` — Add system to an applications-based KRI
  - body: `{ "kriId": "kri8", "systemName": "BirBank" }`
- `POST /api/add-data-point` — Add/Upsert data point
  - simple KRI body example: `{ "kriId": "kri2", "period": "Q2-2025", "value": 97 }`
  - app KRI body example: `{ "kriId": "kri10", "systemName": "BirBank", "period": "06-2025", "value": 4 }`
- `PUT /api/update-data-point` — Update the value of a specific data point
  - simple example: `{ "kriId": "kri2", "period": "Q2-2025", "value": 96 }`
  - app example: `{ "kriId": "kri10", "systemName": "BirBank", "period": "06-2025", "value": 5 }`
- `DELETE /api/delete-data-point` — Delete a specific data point
  - body: `{ "kriId": "kri2", "period": "Q2-2025" }`
  - or `{ "kriId": "kri10", "systemName": "BirBank", "period": "06-2025" }`
- `DELETE /api/delete-system` — Delete a system and all its points
  - body: `{ "kriId": "kri10", "systemName": "BirBank" }`

Notes:
- Period formats
  - Quarter based: `Q1-YYYY`, `Q2-YYYY`, `Q3-YYYY`, `Q4-YYYY`
  - Month based: `MM-YYYY` (e.g. `06-2025`)
- Negative values are rejected
- Ordering is computed by YEAR + QUARTER or YEAR + MONTH; no `date` columns are stored

## Development
- If you want to reset DB and re-seed from JSON, delete `kri.db` and restart the server.
- The front-end uses the same JSON shape as before, minus `date` fields.