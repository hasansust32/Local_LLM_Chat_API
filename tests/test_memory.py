import asyncio

from app.memory import ConversationMemory


def test_memory_stores_and_limits_context() -> None:
    async def scenario() -> None:
        memory = ConversationMemory(max_context_messages=2)
        await memory.append_exchange("demo", "one", "first")
        await memory.append_exchange("demo", "two", "second")

        assert await memory.context("demo") == [
            {"role": "user", "content": "two"},
            {"role": "assistant", "content": "second"},
        ]
        assert len(await memory.get("demo")) == 4
        assert await memory.clear("demo") is True
        assert await memory.get("demo") == []

    asyncio.run(scenario())

