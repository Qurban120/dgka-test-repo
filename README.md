# KRI + RHI Dashboards

- App pages:
  - /kri.html (default route /)
  - /rhi.html
- APIs:
  - KRI: /api/kri-*
  - RHI: /api/rhi-*

Run:

```bash
python3 -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

