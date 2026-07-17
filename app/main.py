from __future__ import annotations

import json
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings
from app.memory import ConversationMemory
from app.ollama import OllamaClient, OllamaError
from app.prompts import resolve_language, system_prompt
from app.schemas import ChatRequest, ChatResponse, ModelsResponse, SessionResponse, StoredMessage

ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    ollama = OllamaClient(settings.ollama_base_url, settings.ollama_timeout_seconds)
    app.state.settings = settings
    app.state.memory = ConversationMemory(settings.max_context_messages)
    app.state.ollama = ollama
    yield
    await ollama.close()


app = FastAPI(
    title="Local LLM Chat API",
    version="1.0.0",
    description="A bilingual chat API backed by a local Ollama model.",
    lifespan=lifespan,
)


def _session_id(requested: str | None) -> str:
    return requested or uuid4().hex


def _messages(system: str, history: list[dict[str, str]], latest: str) -> list[dict[str, str]]:
    return [{"role": "system", "content": system}, *history, {"role": "user", "content": latest}]


def _services(request: Request) -> tuple[Settings, ConversationMemory, Any]:
    return request.app.state.settings, request.app.state.memory, request.app.state.ollama


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health/live", tags=["health"])
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def ready(request: Request) -> dict[str, str]:
    _, _, ollama = _services(request)
    try:
        await ollama.models()
        return {"status": "ready"}
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/models", response_model=ModelsResponse, tags=["chat"])
async def models(request: Request) -> ModelsResponse:
    settings, _, ollama = _services(request)
    try:
        installed = await ollama.models()
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ModelsResponse(models=installed, default=settings.ollama_model)


@app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    settings, memory, ollama = _services(request)
    session_id = _session_id(body.session_id)
    model = body.model or settings.ollama_model
    language = resolve_language(body.language, body.message)
    history = await memory.context(session_id)
    prompt = system_prompt(body.language, body.message)

    try:
        answer = await ollama.chat(model, _messages(prompt, history, body.message))
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    await memory.append_exchange(session_id, body.message, answer)
    stored = (await memory.get(session_id))[-1]
    return ChatResponse(session_id=session_id, model=model, language=language, message=stored)


@app.post("/api/chat/stream", tags=["chat"])
async def stream_chat(body: ChatRequest, request: Request) -> StreamingResponse:
    settings, memory, ollama = _services(request)
    session_id = _session_id(body.session_id)
    model = body.model or settings.ollama_model
    language = resolve_language(body.language, body.message)
    history = await memory.context(session_id)
    prompt = system_prompt(body.language, body.message)
    messages = _messages(prompt, history, body.message)

    async def generate():
        collected: list[str] = []
        meta = {"type": "meta", "session_id": session_id, "model": model, "language": language}
        yield json.dumps(meta, ensure_ascii=False) + "\n"
        try:
            async for token in ollama.stream_chat(model, messages):
                collected.append(token)
                yield json.dumps({"type": "token", "content": token}, ensure_ascii=False) + "\n"
        except OllamaError as exc:
            yield json.dumps({"type": "error", "detail": str(exc)}, ensure_ascii=False) + "\n"
            return

        answer = "".join(collected)
        if answer:
            await memory.append_exchange(session_id, body.message, answer)
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@app.get("/api/sessions/{session_id}", response_model=SessionResponse, tags=["sessions"])
async def get_session(session_id: str, request: Request) -> SessionResponse:
    _, memory, _ = _services(request)
    return SessionResponse(session_id=session_id, messages=await memory.get(session_id))


@app.delete("/api/sessions/{session_id}", status_code=204, tags=["sessions"])
async def delete_session(session_id: str, request: Request) -> Response:
    _, memory, _ = _services(request)
    await memory.clear(session_id)
    return Response(status_code=204)


def _markdown_export(session_id: str, messages: list[StoredMessage]) -> str:
    parts = [f"# Conversation {session_id}", ""]
    for message in messages:
        label = "You" if message.role == "user" else "Assistant"
        parts.extend([f"## {label}", "", message.content, ""])
    return "\n".join(parts)


@app.get("/api/sessions/{session_id}/export", tags=["sessions"])
async def export_session(session_id: str, request: Request, format: str = "json") -> Response:
    _, memory, _ = _services(request)
    messages = await memory.get(session_id)
    safe_filename_id = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:100] or "session"
    if format == "json":
        content = json.dumps(
            {"session_id": session_id, "messages": [item.model_dump(mode="json") for item in messages]},
            ensure_ascii=False,
            indent=2,
        )
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="conversation-{safe_filename_id}.json"'},
        )
    if format == "markdown":
        return Response(
            content=_markdown_export(session_id, messages),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="conversation-{safe_filename_id}.md"'},
        )
    raise HTTPException(status_code=400, detail="format must be 'json' or 'markdown'")


app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")
