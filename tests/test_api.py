from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.main import app


class FakeOllama:
    async def chat(self, model: str, messages: list[dict[str, str]]) -> str:
        return f"Echo: {messages[-1]['content']}"

    async def stream_chat(self, model: str, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        yield "হ্যালো"
        yield " বিশ্ব"

    async def models(self) -> list[str]:
        return ["test-model:latest"]

    async def close(self) -> None:
        return None


def test_chat_and_export() -> None:
    with TestClient(app) as client:
        client.app.state.ollama = FakeOllama()
        response = client.post("/api/chat", json={"message": "Hello", "session_id": "test"})
        assert response.status_code == 200
        assert response.json()["message"]["content"] == "Echo: Hello"

        exported = client.get("/api/sessions/test/export?format=markdown")
        assert exported.status_code == 200
        assert "## You" in exported.text
        assert "Echo: Hello" in exported.text


def test_streaming_chat() -> None:
    with TestClient(app) as client:
        client.app.state.ollama = FakeOllama()
        response = client.post("/api/chat/stream", json={"message": "হাই", "language": "auto"})
        assert response.status_code == 200
        assert '"type": "token"' in response.text
        assert "হ্যালো" in response.text
        assert '"language": "bn"' in response.text

