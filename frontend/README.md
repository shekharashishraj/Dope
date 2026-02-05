# IGSHIELD Frontend Demo

Static frontend for the IGSHIELD pipeline (upload PDF → extract → perturb → inject → evaluate). Requires the backend to be running.

## Setup

1. **Backend must be running** at the URL configured in `frontend/js/config.js` (default: `http://localhost:8001`). See the main [README](../README.md#backend--frontend-setup-web-demo) for backend setup.

2. **From the repo root**, start a simple web server:

   ```bash
   python -m http.server 8080 --directory frontend
   ```

3. **Open http://localhost:8080** in a browser.

## Backend endpoint

The frontend talks to the backend via `frontend/js/config.js`:

```js
export const config = {
  endpoint: "http://localhost:8001",
};
```

To use a different host/port, change `endpoint` (e.g. `http://localhost:8001` or `http://your-server:8001`).

## API usage

The frontend calls these backend endpoints in sequence:

- `POST /ingest` — upload PDF (and optional answer key)
- `POST /perturb` — generate or load perturbations
- `POST /inject` — run injection methods and compile PDFs
- `POST /evaluate` — run detection pipeline

See [backend/README.md](../backend/README.md) for request/response shapes.
