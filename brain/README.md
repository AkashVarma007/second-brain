# Brain (laptop server)

Local FastAPI server: audio in → transcript → AI-processed note or task → SQLite → JSON out.

## Requirements

- Python 3.12
- [Ollama](https://ollama.com) running locally with `llama3.2:3b` pulled
- ~3 GB free disk for the models

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
ollama pull llama3.2:3b
```

## Run

```bash
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Interactive API docs: <http://localhost:8000/docs>

## Test

```bash
.venv/bin/python -m pytest -m "not slow"   # fast unit tests, no models needed
.venv/bin/python -m pytest -m slow         # real whisper + ollama
.venv/bin/python test_pipeline.py          # end-to-end, needs the server running
```

## Endpoints

| Method + path | Body / query | Returns |
|---|---|---|
| `POST /process` | multipart `audio` + `mode=note\|task` | `{ transcript, result }` |
| `POST /process-sample` | `?mode=note\|task` | `{ transcript, result }` |
| `GET /notes` | — | `[ { id, text, created_at } ]` |
| `GET /tasks` | — | `[ { id, title, priority, created_at } ]` |
| `GET /health` | — | `{ status: "ok" }` |

`mode=note` → `result = { text }`. `mode=task` → `result = { title, priority }`.

## Configuration

All settings are environment variables with defaults in `app/config.py`:
`WHISPER_MODEL`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE`, `OLLAMA_HOST`, `OLLAMA_MODEL`,
`OLLAMA_TIMEOUT`, `DB_PATH`, `SAMPLE_WAV`, `CORS_ORIGINS`.
