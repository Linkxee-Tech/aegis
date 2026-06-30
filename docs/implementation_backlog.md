# Aegis Implementation Backlog

This backlog covers the gaps that are still not fully implemented in the current repo.

Status legend:
- `done` means the repo already has working code for it.
- `in_progress` means the next build step is being worked on now.
- `todo` means it still needs implementation.

## Core Product Gaps

1. `done` Add gateway authentication and role-based access for live operations.
2. `done` Finish incident report export as downloadable PDF and OSS upload.
3. `todo` Add GitHub Actions CI/CD for backend tests, frontend build, and release checks.
4. `todo` Add production deployment wiring for OSS/CDN and ECS publish flow.
5. `todo` Add memory retention / pruning so old resolved patterns can expire or be archived.
6. `todo` Add a visible efficiency dashboard showing auto-resolution savings vs manual response.
7. `todo` Add real Alibaba Cloud live monitoring / remediation integrations in place of the current stubs.
8. `todo` Add MCP-based tool routing if the hackathon submission specifically requires MCP language.

## Already Implemented

- `done` Detective, Diagnostician, Remediation, Reporter, and Memory agents.
- `done` Human approval checkpoint.
- `done` PostgreSQL + pgvector memory store.
- `done` Redis cache layer.
- `done` WebSocket live updates.
- `done` Frontend dashboard, incidents, reports, and memory views.
- `done` Startup health check and Qwen timeout fallback.

## Build Order

1. Report export and delivery.
2. CI/CD workflow.
3. Gateway auth.
4. Memory retention policy.
5. Production deployment wiring.
6. Observability and efficiency metrics.
7. Optional MCP compatibility layer.
