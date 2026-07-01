"""
Abstract base class that every Aegis agent extends.
Now powered by LangChain!
"""

import logging
import time
import json
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from backend.services.qwen_client import QwenClient, get_qwen_client

logger = logging.getLogger("aegis.agents")

class AgentResult:
    """Wraps an agent's output along with timing and confidence metadata."""
    def __init__(self, data: dict[str, Any], *, duration_ms: float, agent_id: str) -> None:
        self.data = data
        self.duration_ms = duration_ms
        self.agent_id = agent_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "agentId": self.agent_id,
            "durationMs": round(self.duration_ms, 1),
            **self.data,
        }

class BaseAgent(ABC):
    """
    Extend this class to add a new agent to Aegis.
    Now utilizes LangChain for agent orchestration.
    """
    agent_id: str
    model_name: str
    system_prompt: str

    def __init__(self, qwen_client: QwenClient | None = None) -> None:
        self.qwen = qwen_client or get_qwen_client()
        # Initialize the LangChain chat model
        self.llm = self.qwen.get_chat_model(self.model_name)
        
        # Bind tools if agent defines any
        if hasattr(self, "tools") and self.tools:
            self.llm = self.llm.bind_tools(self.tools, strict=True)

        # Apply fallback to qwen-flash if primary model is not qwen-flash
        from backend.config.settings import get_settings
        settings = get_settings()
        if self.model_name != settings.qwen_model_flash:
            fallback_llm = self.qwen.get_chat_model(settings.qwen_model_flash)
            if hasattr(self, "tools") and self.tools:
                fallback_llm = fallback_llm.bind_tools(self.tools, strict=True)
            self.llm = self.llm.with_fallbacks([fallback_llm])
        
        # We define a base chain for JSON responses using LangChain
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            ("user", "{user_prompt}")
        ])
        self.chain = prompt_template | self.llm | JsonOutputParser()

    @abstractmethod
    async def process(self, context: dict[str, Any]) -> AgentResult:
        raise NotImplementedError

    async def _call_model(self, user_prompt: str, *, temperature: float = 0.2) -> dict[str, Any]:
        """Backward compatibility or convenience method to call the chain."""
        start = time.perf_counter()
        
        # If a different temperature is needed, we could bind it or re-instantiate, 
        # but for simplicity we'll just use the chain we built.
        try:
            result = await self.chain.ainvoke({
                "system_prompt": self.system_prompt,
                "user_prompt": user_prompt
            })
        except Exception as e:
            logger.error("LangChain invocation failed for %s: %s", self.agent_id, e)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info("%s call took %.1fms", self.agent_id, elapsed_ms)
            
        return result

    def _timed(self, data: dict[str, Any], started_at: float) -> AgentResult:
        duration_ms = (time.perf_counter() - started_at) * 1000
        return AgentResult(data, duration_ms=duration_ms, agent_id=self.agent_id)
