KRI Dashboards

Run locally

1. Create venv and install deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Start the server

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

3. Open http://localhost:8000

Export reports

- Open any KRI dashboard and use the Export section to pick HTML, PDF, DOCX, or TXT.
- The backend endpoint /api/export-report generates and streams a file for download.

