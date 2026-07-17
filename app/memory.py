from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone

from app.schemas import StoredMessage


class ConversationMemory:
    """Small process-local conversation store suitable for a demo."""

    def __init__(self, max_context_messages: int = 20) -> None:
        self.max_context_messages = max_context_messages
        self._sessions: dict[str, list[StoredMessage]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def context(self, session_id: str) -> list[dict[str, str]]:
        async with self._lock:
            messages = self._sessions.get(session_id, [])[-self.max_context_messages :]
            return [{"role": item.role, "content": item.content} for item in messages]

    async def append_exchange(self, session_id: str, user: str, assistant: str) -> None:
        now = datetime.now(timezone.utc)
        async with self._lock:
            self._sessions[session_id].extend(
                [
                    StoredMessage(role="user", content=user, created_at=now),
                    StoredMessage(
                        role="assistant",
                        content=assistant,
                        created_at=datetime.now(timezone.utc),
                    ),
                ]
            )

    async def get(self, session_id: str) -> list[StoredMessage]:
        async with self._lock:
            return [item.model_copy() for item in self._sessions.get(session_id, [])]

    async def clear(self, session_id: str) -> bool:
        async with self._lock:
            return self._sessions.pop(session_id, None) is not None

