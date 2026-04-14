"""LLM Client — unified interface for any OpenAI-compatible API.

Adapted from MiroFish's llm_client.py but simplified.
Works with OpenAI, Anthropic (via proxy), Qwen, DeepSeek, local models, etc.
"""

from __future__ import annotations

import json
import re
from typing import Any

from openai import AsyncOpenAI


class LLMClient:
    """Async LLM client wrapping the OpenAI SDK."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
    ):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.7,
    ) -> str:
        """Simple text completion."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    async def chat_json(
        self,
        system: str,
        user: str,
        temperature: float = 0.5,
    ) -> dict[str, Any]:
        """Completion that returns parsed JSON."""
        raw = await self.chat(system, user, temperature=temperature)
        return _extract_json(raw)


def _extract_json(text: str) -> dict[str, Any]:
    """Extract JSON from LLM response, handling markdown fences."""
    # Try direct parse first
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Last resort: find first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return {}
