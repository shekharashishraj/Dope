# IGSHIELD Frontend Demo

This is a static frontend for showcasing the IGSHIELD pipeline at demos/expos.

## Run locally

1. From the repo root, start a simple web server:

```bash
python -m http.server 8080 --directory frontend
```

2. Open `http://localhost:8080` in a browser.

## Backend endpoint

Set the backend endpoint in `frontend/js/config.js`:

```js
export const config = {
  endpoint: "http://localhost:5000",
};
```

The frontend calls the step endpoints in sequence (`/ingest`, `/perturb`, `/inject`, `/evaluate`) and updates the UI from their responses.

## Backend API

This frontend is wired to the FastAPI server in `backend/` and calls:

- `POST /ingest`
- `POST /perturb`
- `POST /inject`
- `POST /evaluate`

Run the backend:

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8001
```
