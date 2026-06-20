# Aegis — Frontend

React + TypeScript + Tailwind CSS interface for Aegis, the autonomous incident-response system.

## Stack

- React 18 + TypeScript
- Vite
- Tailwind CSS (custom design tokens — see `tailwind.config.js`)
- No UI component library — all components are hand-built to match the Aegis instrumentation aesthetic

## Run it

```bash
npm install
npm run dev
```

Opens on `http://localhost:3000`. Requests to `/api` and `/ws` are proxied to `http://localhost:8000` (the FastAPI backend) — see `vite.config.ts`.

Every page fetches from the live API on mount via the hooks in `src/hooks/` and falls back to the demo data in `src/data/mockData.ts` if the backend isn't reachable, so the app is fully explorable standalone. Routing is real client-side routing via `react-router-dom` (`/`, `/incidents`, `/reports`, `/memory`, `/settings`), so refresh and the browser back button both work correctly.

## Structure

```
src/
├── components/      All UI components (Dashboard, AgentStatus, ApprovalModal, etc.)
├── hooks/            useIncidents (live data + approve/reject actions), useLiveData
│                      (agents/health/memory/reports), useWebSocket, useToast
├── services/         api.ts — typed fetch wrapper for the FastAPI backend
├── types/            Shared TypeScript interfaces mirroring backend Pydantic models
├── data/             Mock data used as a fallback when no backend is reachable
└── utils/            Formatting & color-mapping helpers
```

## Connecting to the real backend

Set `VITE_API_BASE_URL` and `VITE_WS_URL` in `.env` (copy from `.env.example`). Once the FastAPI backend is live at those URLs, `useIncidents` and `useWebSocket` will automatically take over from the mock data — no component changes needed.

## Design system

Dark "instrument console" aesthetic rather than a generic dashboard look — built around a graphite background, a warm amber "live system" accent, and a distinct signal color per agent (Detective = blue, Diagnostician = violet, Remediation = green, Reporter = amber). The signature element is the animated signal-trace line inside each active agent card, echoing an oscilloscope readout, and the approval control is a two-step "arm, then confirm" switch rather than a single button, so the human-in-the-loop step feels deliberate rather than incidental.

Full tokens live in `tailwind.config.js` under `theme.extend.colors` (`graphite`, `bone`, `signal`).
