# IGSHIELD Backend API

FastAPI server that exposes the IGSHIELD pipeline as HTTP endpoints for the frontend.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8001
```

## Endpoints

- `GET /health` -> simple health check
- `GET /methods` -> returns default injection methods from config
- `POST /ingest` -> upload PDF + optional answer key
- `POST /perturb` -> resolve or generate perturbation JSONs
- `POST /inject` -> run injection + compile + overlay
- `POST /evaluate` -> run detection pipeline
- `GET /runs/{run_id}` -> inspect stored run metadata

### Request shapes

`POST /ingest` (multipart form):
- `pdf` (file, optional)
- `answer_key` (file, optional)
- `doc_name` (string, optional)

`POST /perturb` (JSON):
```json
{
  "run_id": "run_...",
  "mode": "existing",
  "perturbation_json_path": "output_perturbation/.../doc_perturbation.json"
}
```

`POST /inject` (JSON):
```json
{
  "run_id": "run_...",
  "methods": ["dual_layer", "font_attack"],
  "compile_pdf": true
}
```

`POST /evaluate` (JSON):
```json
{
  "run_id": "run_...",
  "model": "gpt-4o",
  "limit": 1
}
```
