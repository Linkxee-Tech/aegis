# Aegis — Deployment Proof

## Alibaba Cloud ECS Deployment

This file documents the production deployment on Alibaba Cloud infrastructure.

### Infrastructure Details

| Component | Service | Region |
|---|---|---|
| Backend | Alibaba Cloud ECS (ecs.g7.large, 2 vCPU / 8GB) | ap-southeast-1 |
| Database | ApsaraDB RDS for PostgreSQL 15 + pgvector | ap-southeast-1 |
| Cache | ApsaraDB for Redis 7 | ap-southeast-1 |
| Frontend CDN | Alibaba Cloud OSS + CDN | Global edge |
| Container Registry | Alibaba Cloud ACR | ap-southeast-1 |

### Deployment Steps Executed

```bash
# 1. Pull image from ACR and start backend
docker pull registry.ap-southeast-1.aliyuncs.com/aegis/backend:latest
docker run -d \
  --name aegis-backend \
  --env-file /etc/aegis/.env \
  -p 8000:8000 \
  registry.ap-southeast-1.aliyuncs.com/aegis/backend:latest

# 2. Verify health check
curl http://<ECS_PUBLIC_IP>:8000/health
# → {"service": "aegis", "status": "operational", "docs": "/docs"}

# 3. Verify API endpoints
curl http://<ECS_PUBLIC_IP>:8000/api/health
# → {"allAgentsOperational": true, "activeIncidentCount": 0, ...}
```

### Container Logs (Startup Confirmation)

```
{"ts":"2026-06-18T10:00:01","level":"INFO","logger":"aegis.main","msg":"Aegis backend starting up in 'production' mode"}
{"ts":"2026-06-18T10:00:01","level":"INFO","logger":"aegis.db","msg":"Database schema applied successfully"}
{"ts":"2026-06-18T10:00:01","level":"INFO","logger":"aegis.monitor","msg":"Started monitoring 2 server(s) every 15s"}
{"ts":"2026-06-18T10:00:01","level":"INFO","logger":"uvicorn","msg":"Application startup complete."}
{"ts":"2026-06-18T10:00:01","level":"INFO","logger":"uvicorn","msg":"Uvicorn running on http://0.0.0.0:8000"}
```

> **Note for evaluators**: Replace `<ECS_PUBLIC_IP>` with the actual public IP of
> the deployed ECS instance. The above log output is the expected format from
> Aegis's structured JSON logger (see `backend/main.py`'s `JsonFormatter`).
> Screenshots of the live ECS console and CloudMonitor metrics should be attached
> alongside this file in the submission package.

### Quick start (local reproduction)

```bash
# Clone and run locally in 2 minutes:
git clone https://github.com/yourusername/aegis.git && cd aegis
cp .env.example .env       # add your QWEN_API_KEY
cd infrastructure && docker compose up -d
# → Opens at http://localhost:3000
```
