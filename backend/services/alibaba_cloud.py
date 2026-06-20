"""
Alibaba Cloud integrations used by Aegis.

Three responsibilities live here:
  1. Pulling live metrics from ECS/CloudMonitor for the Detective Agent to watch.
  2. Executing approved remediation commands (SLB pool changes, ECS restarts,
     kubectl rollbacks against an ACK cluster) for the Remediation Agent.
  3. Uploading generated incident report PDFs to OSS for durable storage.

Each method is written defensively — if Alibaba Cloud credentials aren't
configured (e.g. local development), calls raise a clear error rather than
silently no-op-ing, since silently skipping a "restart the server" command
would be dangerous to hide.
"""

import logging
from typing import Any

from backend.config.settings import get_settings

logger = logging.getLogger("aegis.alibaba_cloud")
settings = get_settings()


class AlibabaCloudNotConfiguredError(RuntimeError):
    """Raised when an Alibaba Cloud action is attempted without credentials configured."""


class AlibabaCloudService:
    def __init__(self) -> None:
        self._configured = bool(settings.alibaba_cloud_access_key and settings.alibaba_cloud_secret_key)
        self._client: Any | None = None

    def _require_configured(self) -> None:
        if not self._configured:
            raise AlibabaCloudNotConfiguredError(
                "ALIBABA_CLOUD_ACCESS_KEY / ALIBABA_CLOUD_SECRET_KEY are not set. "
                "Set them in .env before Aegis can act on live infrastructure."
            )

    def _get_client(self) -> Any:
        """
        Lazily constructs the Alibaba Cloud SDK client on first use.

        Uses the `alibabacloud_ecs20140526` and related SDKs. Import is deferred
        into this method so the rest of the app can run (e.g. in demo mode against
        mock data) without the Alibaba Cloud SDK installed.
        """
        if self._client is None:
            from alibabacloud_ecs20140526.client import Client as EcsClient
            from alibabacloud_tea_openapi import models as open_api_models

            config = open_api_models.Config(
                access_key_id=settings.alibaba_cloud_access_key,
                access_key_secret=settings.alibaba_cloud_secret_key,
                region_id=settings.alibaba_cloud_region,
            )
            self._client = EcsClient(config)
        return self._client

    async def fetch_instance_metrics(self, *, instance_id: str) -> dict[str, float]:
        """
        Pull current CPU/memory/network metrics for an ECS instance via
        CloudMonitor. Returns a dict consumed directly by the Detective Agent's
        `current_metrics` context field.
        """
        self._require_configured()
        # CloudMonitor's DescribeMetricLast API call would go here in production;
        # left as an integration point since metric polling is infrastructure-
        # specific to each deployment's instance IDs and project namespaces.
        logger.info("Fetching CloudMonitor metrics for instance %s", instance_id)
        raise NotImplementedError(
            "Wire this method up to CloudMonitor's DescribeMetricLast API for your account."
        )

    async def run_remediation_command(self, *, command: str, description: str) -> dict[str, Any]:
        """
        Execute a single approved remediation step against live infrastructure.

        This is the one method in the entire codebase that touches production.
        It is only ever called from RemediationAgent.execute_steps(), which is
        itself only ever called by the orchestrator after a human approval or
        a qualifying auto-apply decision — see orchestrator/human_checkpoint.py.
        """
        self._require_configured()
        logger.warning("EXECUTING REMEDIATION COMMAND: %s (%s)", command, description)
        # Real implementation dispatches based on command prefix:
        #   "aliyun slb ..."   -> SLB SDK calls to drain/register backend servers
        #   "kubectl ..."      -> calls against the cluster's API server (via ACK)
        #   "aliyun ecs ..."   -> ECS SDK calls (RebootInstance, etc.)
        raise NotImplementedError(
            "Wire this dispatcher up to the SLB / ECS / ACK SDKs for your account before going live."
        )

    async def upload_report(self, *, key: str, content: bytes, content_type: str = "application/pdf") -> str:
        """Upload a generated incident report to OSS and return its public/signed URL."""
        self._require_configured()
        from alibabacloud_oss_v2 import Client as OssClient  # type: ignore[import-not-found]
        from alibabacloud_oss_v2 import config as oss_config  # type: ignore[import-not-found]

        cfg = oss_config.load_default()
        cfg.access_key_id = settings.alibaba_cloud_access_key
        cfg.access_key_secret = settings.alibaba_cloud_secret_key
        cfg.region = settings.alibaba_cloud_region
        client = OssClient(cfg)

        client.put_object(bucket=settings.alibaba_oss_bucket, key=key, body=content, content_type=content_type)
        return f"https://{settings.alibaba_oss_bucket}.oss-{settings.alibaba_cloud_region}.aliyuncs.com/{key}"
