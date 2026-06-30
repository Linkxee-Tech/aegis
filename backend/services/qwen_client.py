"""
Thin wrapper around the Qwen Cloud (DashScope) API returning LangChain models.
"""

import logging
from langchain_openai import ChatOpenAI
from backend.config.settings import get_settings

logger = logging.getLogger("aegis.qwen_client")
settings = get_settings()

class QwenServiceUnavailable(RuntimeError):
    pass

class QwenClient:
    """Async client for providing LangChain models and embeddings via DashScope."""
    
    def get_chat_model(self, model: str, temperature: float = 0.2) -> ChatOpenAI:
        """Returns a LangChain ChatOpenAI instance configured for Qwen Cloud."""
        return ChatOpenAI(
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_api_base,
            model=model,
            temperature=temperature,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

    async def embed(self, *, model: str, text: str) -> list[float]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.qwen_api_key, base_url=settings.qwen_api_base)
        try:
            response = await client.embeddings.create(model=model, input=text)
            return response.data[0].embedding
        except Exception as exc:
            logger.exception("Qwen embedding request failed (model=%s)", model)
            raise QwenServiceUnavailable(f"Qwen embedding request failed for model {model}") from exc

_qwen_client: QwenClient | None = None

def get_qwen_client() -> QwenClient:
    global _qwen_client
    if _qwen_client is None:
        _qwen_client = QwenClient()
    return _qwen_client
