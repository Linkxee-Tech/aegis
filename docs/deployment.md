# Aegis — Deployment

## Local development (Docker Compose)

```bash
cp .env.example .env
# edit .env with your QWEN_API_KEY and Alibaba Cloud credentials

cd infrastructure
docker compose up -d --build
```

This starts Postgres (with pgvector), Redis, the FastAPI backend on `:8000`,
and the frontend (served by nginx, proxying `/api` and `/ws` to the backend)
on `:3000`.

## Local development (without Docker)

See the root `README.md` quick-start — run Postgres/Redis via
`docker-compose up -d postgres redis`, then run the backend with `python
backend/main.py` and the frontend with `npm run dev` separately, which gives
hot-reload on both sides.

## Alibaba Cloud production deployment

The architectural plan targets:

- **Frontend**: built as static files (`npm run build` in `frontend/`) and
  uploaded to an Alibaba Cloud OSS bucket configured for static website
  hosting, fronted by Alibaba Cloud CDN for global edge caching.
- **Backend**: containerized via `infrastructure/Dockerfile.backend` and run
  on Alibaba Cloud ECS (or ACK if you want orchestration), behind an Nginx or
  SLB layer handling TLS termination and routing `/api` + `/ws` to the
  backend container(s).
- **Database**: Alibaba Cloud RDS for PostgreSQL with the pgvector extension
  enabled, rather than a self-managed Postgres container, for production
  durability and backups.
- **Reports**: incident report PDFs uploaded to OSS via
  `AlibabaCloudService.upload_report`, with the bucket configured for
  appropriate access control (reports may contain incident detail an
  organization doesn't want public).
- **Observability**: Alibaba Cloud Log Service for aggregating backend logs
  across instances/containers, since `backend/main.py` logs through the
  standard `logging` module and can be shipped there with the standard
  Log Service agent.

### Minimal ECS deployment steps

1. Provision an ECS instance (Ubuntu 22.04+, at least 2 vCPU / 4GB for the
   backend; the LLM calls are the heavy lifting, not local compute).
2. Install Docker and Docker Compose on the instance.
3. Clone the repo, set up `.env` with production credentials (use Alibaba
   Cloud's KMS or a secrets manager rather than a plaintext `.env` file for
   anything beyond a hackathon demo).
4. Point an RDS for PostgreSQL instance's connection string at `DATABASE_URL`
   instead of the bundled Postgres container, and enable the `vector`
   extension on it (`CREATE EXTENSION vector;` — RDS supports this on
   supported engine versions).
5. Run `docker compose -f infrastructure/docker-compose.yml up -d backend`
   (omitting the bundled `postgres` service since RDS replaces it).
6. Build the frontend (`npm run build`) and sync `frontend/dist/` to an OSS
   bucket; attach a CDN domain in front of it.
7. Configure DNS / SLB to route your domain's `/api` and `/ws` paths to the
   ECS instance's backend port, and everything else to the OSS+CDN frontend.

### Environment variables that must change in production

- `ENVIRONMENT=production` (disables uvicorn's `--reload`)
- `CORS_ORIGINS` — restrict to your actual frontend domain, not `localhost`
- `DATABASE_URL` — RDS connection string
- `REDIS_URL` — Alibaba Cloud ApsaraDB for Redis connection string, if using
  the managed offering instead of a self-hosted Redis container
- All `ALIBABA_CLOUD_*` and `QWEN_*` credentials — real production keys, kept
  out of version control

## CI/CD

`requirements.txt` and the frontend `package.json` are the two dependency
manifests a GitHub Actions workflow would install before running:

```bash
# backend
pip install -r requirements.txt --break-system-packages
pytest tests/unit tests/integration

# frontend
cd frontend && npm install && npm run build
```

A typical pipeline builds both Docker images on every push to `main`, runs the
test suite, and on success pushes images to a container registry and triggers
a rolling restart on the ECS instance (or redeploys to ACK if using
Kubernetes-style orchestration).
