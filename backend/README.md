# IGSHIELD Backend API

FastAPI server that exposes the IGSHIELD pipeline as HTTP endpoints for the frontend.

## Setup

1. **From the repository root**, create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env and set OPENAI_API_KEY=your-key-here
   ```

4. **Run the server:**

   ```bash
   uvicorn backend.app:app --host 0.0.0.0 --port 8001
   ```

   API base URL: **http://localhost:8001**. The frontend expects this URL by default (see `frontend/js/config.js`).

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
