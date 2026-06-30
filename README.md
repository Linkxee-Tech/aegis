# Aegis

An autonomous AI operations team that detects and fixes cloud server problems
automatically — like a self-healing IT department.

Five agents work together: **Detective** monitors logs and metrics for
anomalies, **Diagnostician** finds the root cause, **Remediation** proposes a
fix (and only executes it after a human clicks Approve, or after the Memory
Agent recognizes a high-confidence repeat of a past incident), **Reporter**
writes the incident report, and **Memory** remembers every incident so the
same problem gets fixed faster next time.

## Why this matters

Instead of an engineer waking up at 3 AM to manually debug a server, Aegis
handles the grunt work — cutting downtime from hours to minutes while keeping
a human in control of anything that touches production.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- An Alibaba Cloud account with a Qwen Cloud (DashScope) API key
- PostgreSQL 15+ with pgvector, and Redis 7+ (or just use the bundled Docker
  Compose services for local dev)

## Quick start (30 minutes to first run)

```bash
# 1. Clone repository
git clone https://github.com/Linkxee-Tech/aegis.git
cd aegis

# 2. Set up environment
cp .env.example .env
# Edit .env with your QWEN_API_KEY, Alibaba Cloud credentials, and any auth keys

# 3. Start infrastructure
cd infrastructure
docker compose up -d postgres redis
cd ..

# 4. Backend setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python backend/main.py

# 5. Frontend setup (new terminal)
cd frontend
npm install
npm run dev

# 6. Access at http://localhost:3000
```

The frontend works fully standalone with realistic demo data even before
you've set up the backend, and automatically switches to live data the moment
a backend is reachable — see "Live vs. demo data" below and `frontend/README.md`.

## Live vs. demo data

Every page fetches from the real API on load. If the backend isn't running
(or a specific endpoint fails), each page falls back to realistic demo data
so the UI is always fully explorable — useful for frontend development, demos,
and judging without first standing up Postgres/Redis/Qwen credentials.

The moment a backend becomes reachable, the Dashboard also opens a WebSocket
connection and refreshes incident data live as the agent pipeline progresses,
instead of relying only on the initial page-load fetch. Approve/Reject buttons
call the real `/incidents/{id}/approve` and `/incidents/{id}/reject` endpoints
when live, and fall back to a local optimistic update in demo mode so the
approval flow is still fully clickable in a standalone walkthrough.

If gateway auth is enabled, the frontend reads the token from Settings and
sends it as a Bearer token for REST requests and as `?token=` for WebSocket
connections.

Routing is real client-side routing (`react-router-dom`) — `/`, `/incidents`,
`/reports`, `/memory`, and `/settings` are all directly navigable, refreshable,
and back-button-friendly, not just in-memory tab state.

## Project structure

```
aegis/
├── backend/
│   ├── agents/            Detective, Diagnostician, Remediation, Reporter, Memory
│   ├── orchestrator/       Coordinator, message bus, human approval checkpoint
│   ├── api/                FastAPI routes, Pydantic schemas, WebSocket handler
│   ├── services/           Qwen client, memory store, Redis cache, Alibaba Cloud
│   ├── config/             Settings and agent system prompts
│   └── main.py
├── frontend/
│   └── src/                React + TypeScript + Tailwind dashboard (see frontend/README.md)
├── infrastructure/         docker-compose.yml, Dockerfiles, nginx.conf
├── docs/                    architecture.md, api_reference.md, deployment.md
├── tests/
│   ├── unit/                message bus, human checkpoint policy
│   └── integration/         full agent pipeline with mocked Qwen responses
├── .env.example
└── requirements.txt
```

## Environment variables

| Variable | Description |
|---|---|
| `QWEN_API_KEY` | Qwen Cloud / DashScope API key |
| `QWEN_API_BASE` | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| `QWEN_MODEL_FLASH` / `QWEN_MODEL_PLUS` / `QWEN_MODEL_CODER` | Model names per agent role |
| `DATABASE_URL` | PostgreSQL connection string (pgvector extension required) |
| `REDIS_URL` | Redis connection string |
| `ALIBABA_CLOUD_ACCESS_KEY` / `ALIBABA_CLOUD_SECRET_KEY` | Alibaba Cloud credentials |
| `AUTH_ENABLED` | Turns on gateway auth for live operations |
| `VIEWER_API_KEYS` | Comma-separated API keys allowed to read dashboard data |
| `OPERATOR_API_KEYS` | Comma-separated API keys allowed to approve/reject/simulate |
| `ADMIN_API_KEYS` | Comma-separated API keys allowed to access every endpoint |
| `MEMORY_SIMILARITY_THRESHOLD` | Minimum similarity to consider a memory "matched" (default 0.85) |
| `MEMORY_AUTO_APPLY_THRESHOLD` | Minimum confidence to skip human approval (default 0.92) |
| `REQUIRE_APPROVAL_FOR_HIGH_RISK` | If true, high-risk steps always need a human regardless of memory confidence |

Full list in `.env.example`.

## Key development workflows

1. **Adding a new agent** — extend `BaseAgent` in `backend/agents/base_agent.py`
   and implement `process()`. Register it in `Coordinator.__init__` and wire it
   into the pipeline in `coordinator.py` wherever it should run.
2. **Tuning agent behavior** — edit the relevant prompt in
   `backend/config/prompts.py`. Each agent's system prompt is kept separate
   from its orchestration logic on purpose.
3. **Adjusting memory matching** — `MEMORY_SIMILARITY_THRESHOLD` and
   `MEMORY_AUTO_APPLY_THRESHOLD` in `.env`, or the search logic itself in
   `backend/services/memory_store.py`.
4. **Changing approval policy** — `backend/orchestrator/human_checkpoint.py`'s
   `evaluate()` method is the single source of truth for when a human is
   required.

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests (agent pipeline with mocked Qwen responses — no real API calls)
pytest tests/integration/

# Load testing
locust -f tests/load_test.py --host http://localhost:8000
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system design, agent
  responsibilities, the human-checkpoint policy, and known production gaps
- [`docs/api_reference.md`](docs/api_reference.md) — every REST endpoint and
  the WebSocket event schema
- [`docs/deployment.md`](docs/deployment.md) — Alibaba Cloud deployment steps

## Technology stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| AI/LLM | Qwen Cloud API (Plus / Flash / Coder), OpenAI-compatible SDK |
| Memory | PostgreSQL + pgvector |
| Cache | Redis |
| Frontend | React + TypeScript + Tailwind CSS |
| Real-time | WebSocket |
| Infrastructure | Docker + Alibaba Cloud ECS / OSS / CDN / RDS |

## License

See [LICENSE](LICENSE).
