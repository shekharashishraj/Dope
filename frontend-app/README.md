# IGSHIELD React UI

Professional UI for the IGSHIELD Document Integrity Pipeline.

## Stack

- React 19 + TypeScript
- Vite
- Tailwind CSS v4
- Radix UI primitives (Sheet, Tabs, Switch, etc.)
- Lucide React icons
- Sonner (toasts)

## Setup

```bash
npm install
```

## Development

```bash
npm run dev
```

Runs at `http://localhost:5173` by default. Set `VITE_API_ENDPOINT` (e.g. `http://localhost:8001`) if your backend is elsewhere; see [src/lib/api.ts](src/lib/api.ts).

## Build

```bash
npm run build
```

Output is in `dist/`. To serve the built app from the project root, copy `dist/*` to a folder served by your backend or use `npm run preview`.

## Layout

- **Setup** (left): PDF/answer key upload, attack method cards, compile toggle, Run/Reset.
- **Pipeline Timeline** (center): Six steps with status; click a step for details.
- **Results** (right): Run summary, status feed, evaluation highlights, artifacts by stage.

Logs are hidden by default. Enable **Developer Mode** in the top bar to show the **Developer** button and open the drawer (Logs, Trace JSON).
