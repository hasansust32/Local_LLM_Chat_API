from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx


class OllamaError(RuntimeError):
    """A friendly wrapper around connection and protocol failures."""


class OllamaClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout_seconds, connect=10.0),
        )

    @staticmethod
    def _payload(model: str, messages: list[dict[str, str]], stream: bool) -> dict:
        return {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": 0.7},
        }

    async def chat(self, model: str, messages: list[dict[str, str]]) -> str:
        try:
            response = await self._client.post(
                "/api/chat", json=self._payload(model, messages, stream=False)
            )
            response.raise_for_status()
            content = response.json().get("message", {}).get("content", "")
            if not content:
                raise OllamaError("Ollama returned an empty response.")
            return content
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaError(f"Could not get a response from Ollama: {exc}") from exc

    async def stream_chat(
        self, model: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        try:
            async with self._client.stream(
                "POST", "/api/chat", json=self._payload(model, messages, stream=True)
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    payload = json.loads(line)
                    if payload.get("error"):
                        raise OllamaError(str(payload["error"]))
                    token = payload.get("message", {}).get("content", "")
                    if token:
                        yield token
        except OllamaError:
            raise
        except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
            raise OllamaError(f"Could not stream a response from Ollama: {exc}") from exc

    async def models(self) -> list[str]:
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            return [item["name"] for item in response.json().get("models", []) if item.get("name")]
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise OllamaError(f"Could not list Ollama models: {exc}") from exc

    async def close(self) -> None:
        await self._client.aclose()

