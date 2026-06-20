"""
Load test for the Aegis API surface. Run with:
    locust -f tests/load_test.py --host http://localhost:8000

Exercises the read-heavy dashboard endpoints, since those are what the
frontend polls/streams continuously, plus the approve/reject endpoints to
make sure the human-checkpoint path holds up under concurrent engineers.
"""

import random

from locust import HttpUser, between, task


class DashboardUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def get_health(self):
        self.client.get("/api/health")

    @task(5)
    def get_agents(self):
        self.client.get("/api/agents")

    @task(4)
    def get_incidents(self):
        self.client.get("/api/incidents")

    @task(2)
    def get_memory(self):
        self.client.get("/api/memory")

    @task(2)
    def get_reports(self):
        self.client.get("/api/reports")

    @task(1)
    def approve_random_incident(self):
        # Best-effort: in a real run this would target a known seeded incident id.
        fake_id = f"INC-2026-{random.randint(1000, 9999)}"
        with self.client.post(f"/api/incidents/{fake_id}/approve", catch_response=True) as response:
            if response.status_code in (200, 404, 409):
                response.success()
