"""
Thin wrapper around the Qwen Cloud (DashScope) API.

Qwen Cloud exposes an OpenAI-compatible endpoint, so we use the official `openai`
SDK pointed at DashScope's base URL rather than maintaining a bespoke HTTP client.
This keeps streaming, tool-calling, and retry semantics consistent with the wider
Python AI ecosystem.
"""

import json
import logging
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from backend.config.settings import get_settings

logger = logging.getLogger("aegis.qwen_client")

settings = get_settings()


class QwenServiceUnavailable(RuntimeError):
    """Raised when the upstream Qwen service cannot complete a request."""


def _is_retryable_timeout(exc: Exception) -> bool:
    name = exc.__class__.__name__.lower()
    message = str(exc).lower()
    return "timeout" in name or "timeout" in message or "connection" in name and "error" in name


class QwenClient:
    """Async client for calling Qwen models through the DashScope compatible-mode API."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_api_base,
        )

    async def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1500,
        json_mode: bool = True,
    ) -> str:
        """
        Send a single-turn completion request and return the raw text response.

        json_mode=True asks the model to return a JSON object directly, which we
        rely on heavily since every agent in Aegis communicates via structured
        output rather than free text.
        """
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.chat.completions.create(**kwargs)
        except Exception as exc:
            if model != settings.qwen_model_flash and _is_retryable_timeout(exc):
                logger.warning(
                    "Qwen timeout on model=%s; retrying once with fallback model=%s",
                    model,
                    settings.qwen_model_flash,
                )
                try:
                    response = await self._client.chat.completions.create(
                        **{**kwargs, "model": settings.qwen_model_flash}
                    )
                except Exception as fallback_exc:
                    logger.exception("Qwen fallback model also failed (primary=%s)", model)
                    raise QwenServiceUnavailable(
                        f"Qwen timed out on {model} and fallback {settings.qwen_model_flash} also failed"
                    ) from fallback_exc
            else:
                logger.exception("Qwen API call failed (model=%s)", model)
                raise QwenServiceUnavailable(f"Qwen request failed for model {model}") from exc

        content = response.choices[0].message.content or "{}"
        return content

    async def complete_json(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> dict[str, Any]:
        """Convenience wrapper that parses the JSON response, with a clear error on malformed output."""
        raw = await self.complete(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Qwen returned non-JSON output despite json_mode: %r", raw[:500])
            raise

    async def embed(self, *, model: str, text: str) -> list[float]:
        """
        Generate an embedding for memory similarity search.

        Note: DashScope's embedding models (e.g. text-embedding-v3) are called
        through the same compatible-mode client but via the embeddings endpoint.
        """
        try:
            response = await self._client.embeddings.create(model=model, input=text)
        except Exception as exc:
            logger.exception("Qwen embedding request failed (model=%s)", model)
            raise QwenServiceUnavailable(f"Qwen embedding request failed for model {model}") from exc
        return response.data[0].embedding


_qwen_client: QwenClient | None = None


def get_qwen_client() -> QwenClient:
    """Module-level singleton accessor so agents share one underlying HTTP connection pool."""
    global _qwen_client
    if _qwen_client is None:
        _qwen_client = QwenClient()
    return _qwen_client
