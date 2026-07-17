# Local LLM Chat API

একটি ছোট কিন্তু complete local AI chat project। FastAPI API, Ollama model, streaming response,
in-memory conversation context, Bangla/English prompt, responsive HTML UI, export এবং Docker setup—সব একসাথে আছে।

## Features

- Ollama-এর যেকোনো installed chat model ব্যবহার করা যায়
- Normal JSON এবং streaming NDJSON—দুই ধরনের API
- প্রতি session-এর basic chat memory (default: শেষ 20টি message context)
- Auto/Bangla/English system prompt
- JSON ও Markdown conversation export
- Responsive, dependency-free HTML/CSS/JavaScript UI
- Swagger docs, health endpoints, Dockerfile ও Docker Compose
- Unit/API tests

## সবচেয়ে সহজে চালান (Docker)

প্রয়োজন: [Docker Desktop](https://www.docker.com/products/docker-desktop/) অথবা Docker Engine + Compose।

```bash
cp .env.example .env
docker compose up --build
```

প্রথমবার `llama3.2:3b` download হওয়ায় কিছু সময় লাগবে। প্রস্তুত হলে খুলুন:

- Chat UI: http://localhost:8000
- API docs: http://localhost:8000/docs
- Ollama API: http://localhost:11434

বন্ধ করতে `Ctrl+C`, তারপর:

```bash
docker compose down
```

Model data রেখে দেওয়া হয়। Model-সহ volume মুছতে চাইলে সচেতনভাবে `docker compose down -v` চালান।

## Docker ছাড়া local run

1. [Ollama](https://ollama.com/) install করে model চালু করুন:

```bash
ollama pull llama3.2:3b
ollama serve
```

2. নতুন terminal-এ app চালান:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
export OLLAMA_BASE_URL=http://localhost:11434
uvicorn app.main:app --reload
```

`config.py` সরাসরি environment variables পড়ে; `.env` file Python নিজে load করে না। Docker Compose `.env` load করে।

## API examples

Normal response:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"বাংলায় FastAPI বুঝিয়ে বলো","language":"auto"}'
```

Streaming response (প্রতি line একটি JSON event):

```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"Write a two-line poem","session_id":"demo","language":"en"}'
```

একই `session_id` পরের request-এ দিলে আগের conversation context হিসেবে যাবে।

| Method | Endpoint | কাজ |
| --- | --- | --- |
| `POST` | `/api/chat` | সম্পূর্ণ JSON response |
| `POST` | `/api/chat/stream` | NDJSON token stream |
| `GET` | `/api/models` | Installed Ollama models |
| `GET` | `/api/sessions/{id}` | Session messages |
| `DELETE` | `/api/sessions/{id}` | Session clear |
| `GET` | `/api/sessions/{id}/export?format=json` | JSON export |
| `GET` | `/api/sessions/{id}/export?format=markdown` | Markdown export |
| `GET` | `/health/live` | App liveness |
| `GET` | `/health/ready` | Ollama readiness |

## Configuration

| Variable | Default | অর্থ |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2:3b` | Default model |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | Request timeout |
| `MAX_CONTEXT_MESSAGES` | `20` | LLM-কে পাঠানো recent message count |
| `APP_NAME` | `Local LLM Chat` | App name setting |

Model বদলাতে:

```bash
OLLAMA_MODEL=qwen2.5:3b docker compose up --build
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests চালাতে Ollama দরকার নেই; fake client ব্যবহার করা হয়েছে।

## Project structure

```text
app/
  main.py       FastAPI routes, streaming ও export
  ollama.py     Ollama HTTP client
  memory.py     Session memory
  prompts.py    Bangla/English prompts
  schemas.py    Request/response validation
static/         Browser UI
tests/          Unit ও API tests
Dockerfile
docker-compose.yml
```

## Important limitation

Conversation memory process-local RAM-এ থাকে। App restart হলে chat history চলে যাবে এবং একাধিক app worker
একই memory share করবে না। Production version-এর জন্য `ConversationMemory`-র বদলে Redis/PostgreSQL adapter ব্যবহার করুন।

## License

MIT License—ব্যক্তিগত, শিক্ষামূলক বা commercial project-এ পরিবর্তন করে ব্যবহার করতে পারেন।
