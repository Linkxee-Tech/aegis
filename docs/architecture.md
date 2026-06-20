# Aegis — Architecture

## Overview

Aegis is a multi-agent system that detects, diagnoses, remediates, and documents
cloud infrastructure incidents with a human approval checkpoint before any action
runs against live servers, and persistent memory so recurring incidents can
eventually skip that checkpoint entirely.

```
Presentation Layer (React + TS + Tailwind)
        |
API Gateway Layer (FastAPI)
        |
Orchestrator Layer
   Coordinator -- Message Bus -- Human Checkpoint
   Detective -> Diagnostician -> Remediation -> Reporter
                       |
                  Memory Agent
        |
Data Layer (PostgreSQL+pgvector, Redis, Alibaba Cloud, Qwen Cloud)
```

## Why a Coordinator, not a fully decentralized agent swarm

Each agent (`backend/agents/*.py`) is intentionally narrow: it receives a context
dict and returns a structured result. None of them know about each other or about
the message bus. The `Coordinator` (`backend/orchestrator/coordinator.py`) is the
only component that knows the shape of the full workflow — which agent runs after
which, and what gets passed between them.

This tradeoff was deliberate for a hackathon-scoped system: a fully decentralized
negotiation protocol between agents adds real engineering value at larger scale,
but for five agents with a strictly sequential dependency chain (you can't remediate
before you diagnose), an explicit coordinator is easier to reason about, test, and
debug under time pressure — and it's where the "measurable efficiency gain over a
single-agent baseline" claim can actually be measured, since the Coordinator can
log how long each agent took versus a hypothetical single large prompt.

## The five agents

| Agent | Model | Input | Output | Notes |
|---|---|---|---|---|
| Detective | Qwen-Flash | metric snapshot + baseline + logs | anomaly bool, severity, evidence | Runs continuously, needs to be cheap |
| Diagnostician | Qwen-Plus | alert + extended logs + deploys + memory matches | root cause, confidence | Benefits most from a stronger model |
| Remediation | Qwen-Coder | root cause + memory confidence | ordered steps with risk levels | Never executes from `process()` — see below |
| Reporter | Qwen-Flash | full incident record | summary, root cause writeup, actions taken | Summarization, not novel reasoning |
| Memory | Qwen-Plus (+ embeddings) | incident title + root cause | matched record + confidence, or storage confirmation | Backed by pgvector |

## The human checkpoint

`backend/orchestrator/human_checkpoint.py` is the single place that decides whether
a remediation plan may run automatically. The policy, in order:

1. If any step is tagged `high` risk and `REQUIRE_APPROVAL_FOR_HIGH_RISK=true`
   (the default), a human is always required — regardless of memory confidence.
2. Otherwise, if the Memory Agent's matched confidence clears
   `MEMORY_AUTO_APPLY_THRESHOLD` (default 0.92), the plan auto-executes.
3. Anything else waits for an engineer to click Approve or Reject in the UI.

This is what makes the "next time it remembers and applies the fix automatically"
behavior safe: a recurring low-risk incident with a consistently matched fix
graduates out of needing a human, but a first-time high-risk action never does,
no matter how confident any single model call is.

## Memory and auto-resolution

`backend/services/memory_store.py` stores every resolved incident's title + root
cause as a vector embedding (`text-embedding-v3` via the Qwen-compatible endpoint)
alongside the fix that was applied. On each new incident, the Memory Agent embeds
the new root cause and searches for the closest match by cosine similarity.

Two thresholds matter:
- `MEMORY_SIMILARITY_THRESHOLD` (default 0.85) — below this, Aegis doesn't consider
  it a match at all, and the Diagnostician proceeds as if this were a brand-new
  problem.
- `MEMORY_AUTO_APPLY_THRESHOLD` (default 0.92) — above this (and combined with the
  risk-level check above), the orchestrator can skip the human checkpoint.

## Real-time updates

`backend/orchestrator/message_bus.py` is a simple in-process asyncio pub/sub. The
Coordinator publishes to topics like `incident.created`, `agent.status_changed`,
and `incident.timeline_event` as the pipeline progresses; `backend/api/websocket.py`
subscribes to all of them per-connection and forwards each event to the frontend
as a typed JSON envelope. This is why the dashboard updates live as agents work,
without polling.

## Continuous monitoring

`backend/orchestrator/monitor_loop.py` is what makes "constantly monitoring"
literally true rather than aspirational. `MonitorLoop.start()` is called from
`main.py`'s startup event and spins up one asyncio task per server listed in
`MONITORED_SERVERS`. Each task polls `AlibabaCloudService.fetch_instance_metrics`
on a `POLL_INTERVAL_SECONDS` cadence, maintains a simple in-memory rolling
mean/stddev per metric as the baseline the Detective Agent compares against,
and calls `Coordinator.run_detection_cycle` every cycle.

If Alibaba Cloud credentials aren't configured, or `MONITORED_SERVERS` is
empty (both true by default in a fresh local checkout), the loop logs a clear
message and stays idle rather than crashing startup — the rest of the API
still serves demo data normally. This means the same binary runs identically
whether you're demoing it locally with mock data or running it against real
infrastructure; only the environment variables differ.

## Where production hardening is still needed

This reference implementation makes a few simplifications worth knowing about
before a real production deploy:

- Incidents live in the Coordinator's in-memory dict, not in Postgres. A restart
  loses in-flight incidents (resolved incidents are still safely persisted via the
  Memory Agent's store). Moving incident state into the same Postgres instance is
  the natural next step.
- `AlibabaCloudService.fetch_instance_metrics` and `run_remediation_command` are
  integration points with `NotImplementedError` stubs where the actual CloudMonitor
  / SLB / ACK SDK calls go — these are account- and topology-specific and were left
  explicit rather than guessed at. `MonitorLoop` handles this gracefully (see above),
  but real monitoring requires implementing these against your account.
- The Memory Agent's embedding model (`text-embedding-v3`) is called via the same
  Qwen-compatible client as the chat models; verify that specific model name is
  available in your DashScope region before relying on it.
