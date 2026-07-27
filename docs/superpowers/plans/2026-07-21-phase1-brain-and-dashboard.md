# Phase 1: Laptop Brain + Monitoring Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local FastAPI server that accepts an audio file, transcribes it with faster-whisper, processes it with Ollama into a cleaned note or a prioritised task, persists it to SQLite, and exposes it through a React dashboard — all running on the laptop with no device hardware.

**Architecture:** Three isolated layers behind a fixed HTTP+JSON protocol. `brain/app/` holds single-responsibility modules (`config`, `models`, `storage`, `transcribe`, `ai`, `main`) so the AI and storage layers can be tested with mocks and swapped independently. `web/` is a separate Vite React app that consumes the same protocol over HTTP — it shares no code with the brain, only the contract.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, faster-whisper (`small.en`), Ollama (`llama3.2:3b`) over HTTP via httpx, SQLite (stdlib `sqlite3`), pytest. Frontend: Vite + React + TypeScript.

## Global Constraints

Copied verbatim from `docs/superpowers/specs/2026-07-21-second-brain-design.md`:

- Transcription model: faster-whisper `small.en`.
- AI model: Ollama `llama3.2:3b`.
- Brain language: **Python (FastAPI)**. Monitoring UI: **React + Vite + TypeScript** (`web/`).
- Protocol contract (§5 of the spec) — these paths and JSON shapes are fixed:
  | Method + path | Body / query | Returns |
  |---|---|---|
  | `POST /process` | multipart `audio` file + `mode=note\|task` | `{ transcript, result }` |
  | `POST /process-sample` | `?mode=note\|task` | `{ transcript, result }` |
  | `GET /notes` | — | `[ { id, text, created_at } ]` |
  | `GET /tasks` | — | `[ { id, title, priority, created_at } ]` |
  | `GET /health` | — | `{ status: "ok" }` |
- `mode=note` → `result = { text: <cleaned note> }`
- `mode=task` → `result = { title: str, priority: "high"|"medium"|"low" }`
- Error boundaries: non-audio/empty upload → 400; Ollama unreachable → 503; whisper failure → 500; invalid `mode` → 400.
- Everything runs locally and free. No cloud services.

## Verified Environment (checked 2026-07-21 on this machine)

- Python 3.12.3, `venv` available, pip3 at `/usr/bin/pip3`
- Node v22.14.0, npm 10.9.2
- Ollama 0.20.5 **running** at `http://localhost:11434`; model `llama3.2:3b` is **NOT yet pulled** (only `gemma4:e4b`)
- NVIDIA GTX 1650 (4096 MiB), driver 580.95.05 → Ollama will offload `llama3.2:3b` to GPU
- 8 CPU cores, 15 GiB RAM (~2.8 GiB free), **disk 97% full — 7.2 GiB free** (needs ~3 GiB; keep an eye on it)
- ffmpeg 6.1.1 installed; 3 audio capture devices present; **no TTS installed** → the sample WAV is recorded from the mic

## File Structure

| Path | Responsibility |
|---|---|
| `brain/requirements.txt` | Python dependencies |
| `brain/pytest.ini` | pytest config: test paths + `slow` marker |
| `brain/app/__init__.py` | Package marker |
| `brain/app/config.py` | All runtime settings, env-overridable. Single source of paths/models |
| `brain/app/models.py` | Pydantic schemas — the protocol contract in Python |
| `brain/app/storage.py` | SQLite persistence for notes + tasks. No HTTP, no AI |
| `brain/app/transcribe.py` | faster-whisper wrapper. Audio path in, text out |
| `brain/app/ai.py` | Ollama calls: `clean_note`, `parse_task`. No HTTP server, no DB |
| `brain/app/main.py` | FastAPI app: endpoints, validation, error mapping, wiring |
| `brain/samples/sample_note.wav` | Recorded test audio |
| `brain/tests/test_storage.py` | Storage unit tests |
| `brain/tests/test_ai.py` | AI layer unit tests (Ollama mocked) |
| `brain/tests/test_transcribe.py` | Segment-joining unit test + slow real-model test |
| `brain/tests/test_api.py` | Endpoint tests (transcribe + ai mocked) |
| `brain/test_pipeline.py` | Standalone script: posts the sample WAV at a running server |
| `web/src/protocol.ts` | The protocol contract in TypeScript |
| `web/src/api.ts` | fetch wrappers for the brain API |
| `web/src/components/NotesList.tsx` | Renders notes |
| `web/src/components/TasksList.tsx` | Renders tasks with priority |
| `web/src/App.tsx` | Dashboard shell: health, actions, lists |

**Testing note:** the brain is unit-tested with pytest (mocks for whisper/Ollama keep tests fast). The `web/` dashboard is thin view code over a fully-tested API, so it is verified by `tsc --noEmit`, `npm run build`, and a live browser check rather than adding a JS test runner. This is a deliberate YAGNI call.

---

### Task 1: Environment + project scaffold

**Files:**
- Create: `brain/requirements.txt`
- Create: `brain/pytest.ini`
- Create: `brain/app/__init__.py`
- Create: `brain/app/config.py`
- Create: `brain/tests/__init__.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: `app.config` module exposing `WHISPER_MODEL: str`, `WHISPER_DEVICE: str`, `WHISPER_COMPUTE_TYPE: str`, `OLLAMA_HOST: str`, `OLLAMA_MODEL: str`, `OLLAMA_TIMEOUT: float`, `DB_PATH: Path`, `SAMPLE_WAV: Path`, `CORS_ORIGINS: list[str]`, `BASE_DIR: Path`

- [ ] **Step 1: Check free disk before downloading ~3 GB**

Run: `df -h /home | tail -1`
Expected: the "Avail" column shows at least 4G. If under 4G, stop and free space before continuing (do not delete anything without asking the user).

- [ ] **Step 2: Create the Python virtual environment**

```bash
cd "/home/nishanth/Desktop/Personal/Akash/Second Brain"
python3 -m venv brain/.venv
```

Run: `brain/.venv/bin/python --version`
Expected: `Python 3.12.3`

- [ ] **Step 3: Write `brain/requirements.txt`**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-multipart==0.0.20
faster-whisper==1.1.1
av==18.0.0  # PyAV: the decoder faster-whisper uses; we catch its decode errors to map undecodable uploads to 400
requests==2.34.2  # undeclared transitive dep: faster_whisper.utils imports it but faster-whisper 1.1.1 omits it from Requires-Dist
httpx==0.28.1
pytest==8.3.4
```

> Note: `av` and `requests` are pulled in transitively by `faster-whisper`, but are declared
> explicitly because the code imports them directly (`av` for the decode-error types) or because
> the upstream package omits them from its metadata (`requests`). Task 5 imports `av`'s decode-error
> classes; Task 3's `import faster_whisper` needs `requests` present.

- [ ] **Step 4: Install dependencies**

```bash
brain/.venv/bin/pip install --upgrade pip
brain/.venv/bin/pip install -r brain/requirements.txt
```

Run: `brain/.venv/bin/python -c "import fastapi, faster_whisper, httpx; print('deps ok')"`
Expected: `deps ok`

- [ ] **Step 5: Pull the Ollama model (~2 GB download)**

```bash
ollama pull llama3.2:3b
```

Run: `ollama list | grep llama3.2`
Expected: a line containing `llama3.2:3b`

- [ ] **Step 6: Verify Ollama answers and uses the GPU**

```bash
ollama run llama3.2:3b "Reply with exactly: ready" --keepalive 60s
ollama ps
```

Expected: the model replies `ready`, and `ollama ps` shows `llama3.2:3b` with a `PROCESSOR` column reading `100% GPU` (or partial GPU). CPU-only still works, just slower — do not block on it.

- [ ] **Step 7: Create the package skeleton**

```bash
mkdir -p brain/app brain/tests brain/samples
touch brain/app/__init__.py brain/tests/__init__.py
```

- [ ] **Step 8: Write `brain/app/config.py`**

```python
"""Runtime configuration. Every value is overridable with an environment variable."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # -> brain/

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small.en")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))

DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "second_brain.sqlite3")))
SAMPLE_WAV = Path(os.getenv("SAMPLE_WAV", str(BASE_DIR / "samples" / "sample_note.wav")))

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
```

- [ ] **Step 9: Write `brain/pytest.ini`**

```ini
[pytest]
testpaths = tests
markers =
    slow: needs the real whisper or Ollama models
```

- [ ] **Step 10: Verify config imports cleanly**

Run: `cd brain && .venv/bin/python -c "from app import config; print(config.OLLAMA_MODEL, config.WHISPER_MODEL)"`
Expected: `llama3.2:3b small.en`

- [ ] **Step 11: Commit**

```bash
git add brain/requirements.txt brain/pytest.ini brain/app/__init__.py brain/app/config.py brain/tests/__init__.py
git commit -m "feat(brain): scaffold Python package, deps and runtime config"
```

---

### Task 2: Protocol models + SQLite storage

**Files:**
- Create: `brain/app/models.py`
- Create: `brain/app/storage.py`
- Test: `brain/tests/test_storage.py`

**Interfaces:**
- Consumes: `app.config` (nothing at import time; tests pass explicit paths)
- Produces:
  - `app.models.Mode = Literal["note", "task"]`
  - `app.models.Priority = Literal["high", "medium", "low"]`
  - `app.models.NoteResult(text: str)`
  - `app.models.TaskResult(title: str, priority: Priority)`
  - `app.models.ProcessResponse(transcript: str, result: NoteResult | TaskResult)`
  - `app.models.NoteOut(id: int, text: str, created_at: str)`
  - `app.models.TaskOut(id: int, title: str, priority: Priority, created_at: str)`
  - `app.storage.init_db(db_path) -> None`
  - `app.storage.save_note(db_path, text: str) -> NoteOut`
  - `app.storage.save_task(db_path, title: str, priority: str) -> TaskOut`
  - `app.storage.list_notes(db_path) -> list[NoteOut]`
  - `app.storage.list_tasks(db_path) -> list[TaskOut]`

- [ ] **Step 1: Write the failing test**

Create `brain/tests/test_storage.py`:

```python
from app import storage


def test_save_note_returns_row_with_id(tmp_path):
    db = tmp_path / "test.sqlite3"
    storage.init_db(db)

    saved = storage.save_note(db, "buy milk")

    assert saved.id == 1
    assert saved.text == "buy milk"
    assert saved.created_at != ""


def test_list_notes_returns_newest_first(tmp_path):
    db = tmp_path / "test.sqlite3"
    storage.init_db(db)
    storage.save_note(db, "first")
    storage.save_note(db, "second")

    notes = storage.list_notes(db)

    assert [note.text for note in notes] == ["second", "first"]


def test_save_task_persists_priority(tmp_path):
    db = tmp_path / "test.sqlite3"
    storage.init_db(db)

    saved = storage.save_task(db, "Call the dentist", "high")
    tasks = storage.list_tasks(db)

    assert saved.id == 1
    assert tasks[0].title == "Call the dentist"
    assert tasks[0].priority == "high"


def test_lists_are_empty_on_fresh_db(tmp_path):
    db = tmp_path / "test.sqlite3"
    storage.init_db(db)

    assert storage.list_notes(db) == []
    assert storage.list_tasks(db) == []


def test_init_db_is_idempotent(tmp_path):
    db = tmp_path / "test.sqlite3"
    storage.init_db(db)
    storage.save_note(db, "kept")
    storage.init_db(db)

    assert [note.text for note in storage.list_notes(db)] == ["kept"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd brain && .venv/bin/python -m pytest tests/test_storage.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.storage'`

- [ ] **Step 3: Write `brain/app/models.py`**

```python
"""Pydantic schemas — the Python side of the HTTP protocol contract."""

from typing import Literal

from pydantic import BaseModel

Mode = Literal["note", "task"]
Priority = Literal["high", "medium", "low"]


class NoteResult(BaseModel):
    text: str


class TaskResult(BaseModel):
    title: str
    priority: Priority


class ProcessResponse(BaseModel):
    transcript: str
    result: NoteResult | TaskResult


class NoteOut(BaseModel):
    id: int
    text: str
    created_at: str


class TaskOut(BaseModel):
    id: int
    title: str
    priority: Priority
    created_at: str
```

- [ ] **Step 4: Write `brain/app/storage.py`**

```python
"""SQLite persistence for notes and tasks. No HTTP and no AI live here."""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from app.models import NoteOut, TaskOut

# Single source of truth for valid priorities: used by the save_task guard and
# to build the SQLite CHECK constraint, so the two cannot drift apart.
VALID_PRIORITIES = ("high", "medium", "low")
_PRIORITY_SQL_LIST = ", ".join(f"'{p}'" for p in VALID_PRIORITIES)

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ({_PRIORITY_SQL_LIST})),
    created_at TEXT NOT NULL
);
"""


def _connect(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(db_path: Path | str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with closing(_connect(db_path)) as conn, conn:
        conn.executescript(SCHEMA)


def save_note(db_path: Path | str, text: str) -> NoteOut:
    created_at = _now()
    with closing(_connect(db_path)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO notes (text, created_at) VALUES (?, ?)", (text, created_at)
        )
    return NoteOut(id=cursor.lastrowid, text=text, created_at=created_at)


def save_task(db_path: Path | str, title: str, priority: str) -> TaskOut:
    # Validate before opening a connection: never commit a row we then reject.
    if priority not in VALID_PRIORITIES:
        raise ValueError(
            f"invalid priority {priority!r}: must be one of {VALID_PRIORITIES}"
        )
    created_at = _now()
    with closing(_connect(db_path)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, priority, created_at) VALUES (?, ?, ?)",
            (title, priority, created_at),
        )
    return TaskOut(id=cursor.lastrowid, title=title, priority=priority, created_at=created_at)


def list_notes(db_path: Path | str) -> list[NoteOut]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT id, text, created_at FROM notes ORDER BY id DESC"
        ).fetchall()
    return [NoteOut(**dict(row)) for row in rows]


def list_tasks(db_path: Path | str) -> list[TaskOut]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT id, title, priority, created_at FROM tasks ORDER BY id DESC"
        ).fetchall()
    return [TaskOut(**dict(row)) for row in rows]
```

- [ ] **Step 5: Run tests to verify they pass**

Also add two tests covering the priority guard: one asserting an invalid priority raises
`ValueError` **and** leaves the table empty (`list_tasks(db) == []` after the raise), and one
asserting all three valid priorities round-trip.

Run: `cd brain && .venv/bin/python -m pytest tests/test_storage.py -v`
Expected: PASS — 7 passed

- [ ] **Step 6: Commit**

```bash
git add brain/app/models.py brain/app/storage.py brain/tests/test_storage.py
git commit -m "feat(brain): add protocol models and SQLite storage"
```

---

### Task 3: Sample audio + transcription

**Files:**
- Create: `brain/app/transcribe.py`
- Create: `brain/samples/sample_note.wav`
- Test: `brain/tests/test_transcribe.py`

**Interfaces:**
- Consumes: `app.config.WHISPER_MODEL`, `app.config.WHISPER_DEVICE`, `app.config.WHISPER_COMPUTE_TYPE`, `app.config.SAMPLE_WAV`
- Produces:
  - `app.transcribe.transcribe_file(audio_path: Path | str) -> str`
  - `app.transcribe._join_segments(segments) -> str` (internal, unit-tested)

- [ ] **Step 1: Record the sample WAV (manual — needs the user to speak)**

```bash
cd "/home/nishanth/Desktop/Personal/Akash/Second Brain"
ffmpeg -y -f alsa -i default -t 6 -ar 16000 -ac 1 brain/samples/sample_note.wav
```

Speak this clearly while it records: **"Remind me to buy milk and call the dentist tomorrow morning, this is urgent."**

If no microphone is available, use this fallback (a public-domain speech sample) instead:

```bash
curl -L -o brain/samples/sample_note.wav \
  https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav
```

Run: `ls -la brain/samples/sample_note.wav && ffprobe -hide_banner brain/samples/sample_note.wav 2>&1 | tail -3`
Expected: file exists, non-zero size, and ffprobe reports an audio stream several seconds long.

- [ ] **Step 2: Write the failing test**

Create `brain/tests/test_transcribe.py`:

```python
import pytest

from app import config, transcribe


class _FakeSegment:
    def __init__(self, text: str) -> None:
        self.text = text


def test_join_segments_trims_and_joins():
    segments = [_FakeSegment("  Remind me to buy milk "), _FakeSegment(" and call the dentist. ")]

    assert transcribe._join_segments(segments) == "Remind me to buy milk and call the dentist."


def test_join_segments_returns_empty_string_for_no_speech():
    assert transcribe._join_segments([]) == ""


@pytest.mark.slow
def test_transcribes_the_sample_wav_to_real_text():
    assert config.SAMPLE_WAV.exists(), "record brain/samples/sample_note.wav first"

    text = transcribe.transcribe_file(config.SAMPLE_WAV)

    assert len(text.split()) >= 3
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd brain && .venv/bin/python -m pytest tests/test_transcribe.py -v -m "not slow"`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.transcribe'`

- [ ] **Step 4: Write `brain/app/transcribe.py`**

```python
"""faster-whisper wrapper: audio file in, transcript text out."""

from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel

from app import config


@lru_cache(maxsize=1)
def _get_model() -> WhisperModel:
    """Load the model once and reuse it. First call downloads the model files."""
    return WhisperModel(
        config.WHISPER_MODEL,
        device=config.WHISPER_DEVICE,
        compute_type=config.WHISPER_COMPUTE_TYPE,
    )


def _join_segments(segments) -> str:
    return " ".join(segment.text.strip() for segment in segments).strip()


def transcribe_file(audio_path: Path | str) -> str:
    """Transcribe an audio file. Returns "" when no speech is detected."""
    segments, _info = _get_model().transcribe(
        str(audio_path), beam_size=5, vad_filter=True
    )
    return _join_segments(segments)
```

- [ ] **Step 5: Run the fast tests to verify they pass**

Run: `cd brain && .venv/bin/python -m pytest tests/test_transcribe.py -v -m "not slow"`
Expected: PASS — 2 passed, 1 deselected

- [ ] **Step 6: Run the slow test — downloads `small.en` (~500 MB) on first run**

Run: `cd brain && .venv/bin/python -m pytest tests/test_transcribe.py -v -m slow`
Expected: PASS — 1 passed. Takes 1–3 minutes the first time (model download), seconds afterwards.

- [ ] **Step 7: Print the transcript to sanity-check quality**

Run: `cd brain && .venv/bin/python -c "from app import config, transcribe; print(repr(transcribe.transcribe_file(config.SAMPLE_WAV)))"`
Expected: readable text close to what was spoken. If it is garbled, re-record with less background noise before continuing.

- [ ] **Step 8: Commit**

```bash
git add brain/app/transcribe.py brain/tests/test_transcribe.py brain/samples/sample_note.wav
git commit -m "feat(brain): add faster-whisper transcription and sample audio"
```

---

### Task 4: AI layer (Ollama)

**Files:**
- Create: `brain/app/ai.py`
- Test: `brain/tests/test_ai.py`

**Interfaces:**
- Consumes: `app.config.OLLAMA_HOST`, `app.config.OLLAMA_MODEL`, `app.config.OLLAMA_TIMEOUT`
- Produces:
  - `app.ai.OllamaUnavailable` (exception class, subclass of `RuntimeError`)
  - `app.ai.clean_note(text: str) -> str`
  - `app.ai.parse_task(text: str) -> dict` with keys `title: str`, `priority: str`
  - `app.ai._generate(prompt: str, *, as_json: bool) -> str` (internal; tests monkeypatch this)

- [ ] **Step 1: Write the failing test**

Create `brain/tests/test_ai.py`:

```python
import httpx
import pytest

from app import ai


def _fake_generate(response: str):
    def _inner(prompt: str, *, as_json: bool) -> str:
        return response

    return _inner


def test_clean_note_returns_model_text(monkeypatch):
    monkeypatch.setattr(ai, "_generate", _fake_generate("Buy milk and call the dentist."))

    assert ai.clean_note("buy milk an call dentist") == "Buy milk and call the dentist."


def test_clean_note_falls_back_to_original_when_model_returns_nothing(monkeypatch):
    monkeypatch.setattr(ai, "_generate", _fake_generate(""))

    assert ai.clean_note("buy milk") == "buy milk"


def test_parse_task_returns_title_and_priority(monkeypatch):
    monkeypatch.setattr(
        ai, "_generate", _fake_generate('{"title": "Call the dentist", "priority": "high"}')
    )

    assert ai.parse_task("call the dentist, urgent") == {
        "title": "Call the dentist",
        "priority": "high",
    }


def test_parse_task_defaults_unknown_priority_to_medium(monkeypatch):
    monkeypatch.setattr(
        ai, "_generate", _fake_generate('{"title": "Call mom", "priority": "urgent"}')
    )

    assert ai.parse_task("call mom") == {"title": "Call mom", "priority": "medium"}


def test_parse_task_normalises_priority_case(monkeypatch):
    monkeypatch.setattr(
        ai, "_generate", _fake_generate('{"title": "Pay rent", "priority": "  HIGH "}')
    )

    assert ai.parse_task("pay rent")["priority"] == "high"


def test_parse_task_falls_back_when_model_returns_invalid_json(monkeypatch):
    monkeypatch.setattr(ai, "_generate", _fake_generate("sorry, I cannot do that"))

    assert ai.parse_task("water the plants") == {
        "title": "water the plants",
        "priority": "medium",
    }


def test_parse_task_falls_back_when_title_missing(monkeypatch):
    monkeypatch.setattr(ai, "_generate", _fake_generate('{"priority": "low"}'))

    assert ai.parse_task("water the plants") == {
        "title": "water the plants",
        "priority": "low",
    }


def test_generate_raises_ollama_unavailable_on_connection_error(monkeypatch):
    def _boom(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(ai.httpx, "post", _boom)

    with pytest.raises(ai.OllamaUnavailable):
        ai._generate("hello", as_json=False)


@pytest.mark.slow
def test_parse_task_against_the_real_model():
    result = ai.parse_task("remind me to call the dentist tomorrow, it is urgent")

    assert result["priority"] in {"high", "medium", "low"}
    assert result["title"].strip() != ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd brain && .venv/bin/python -m pytest tests/test_ai.py -v -m "not slow"`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.ai'`

- [ ] **Step 3: Write `brain/app/ai.py`**

```python
"""Ollama calls. Model output is untrusted input, so every field is validated."""

import json

import httpx

from app import config

VALID_PRIORITIES = {"high", "medium", "low"}

NOTE_PROMPT = (
    "You clean up voice-dictated notes. Fix grammar, spelling and punctuation. "
    "Keep the original meaning and every detail. Do not add new information. "
    "Reply with ONLY the cleaned note text and nothing else.\n\n"
    "Note: {text}"
)

TASK_PROMPT = (
    "You turn a voice-dictated instruction into a single task. "
    'Reply with ONLY JSON of the form {{"title": "<short imperative title>", '
    '"priority": "high"}} where priority is exactly one of "high", "medium" or "low". '
    'Judge priority from urgency words in the instruction; when unclear use "medium".\n\n'
    "Instruction: {text}"
)


class OllamaUnavailable(RuntimeError):
    """The local Ollama server could not be reached or returned an error."""


def _generate(prompt: str, *, as_json: bool) -> str:
    payload = {"model": config.OLLAMA_MODEL, "prompt": prompt, "stream": False}
    if as_json:
        payload["format"] = "json"
    try:
        response = httpx.post(
            f"{config.OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=config.OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaUnavailable(f"Ollama request failed: {exc}") from exc
    # json.loads decodes bytes before parsing, so a malformed body raises
    # JSONDecodeError and a non-decodable one raises UnicodeDecodeError (both
    # subclass ValueError); a valid-but-non-object body raises AttributeError on
    # .get(). All are Ollama failures, so all must surface as OllamaUnavailable.
    try:
        return str(response.json().get("response", "")).strip()
    except (ValueError, AttributeError) as exc:
        raise OllamaUnavailable(f"Ollama returned an unusable response body: {exc}") from exc


def clean_note(text: str) -> str:
    """Return a tidied version of the note, falling back to the original text."""
    cleaned = _generate(NOTE_PROMPT.format(text=text), as_json=False)
    return cleaned or text


def parse_task(text: str) -> dict:
    """Return {"title", "priority"}, defaulting safely when the model misbehaves."""
    raw = _generate(TASK_PROMPT.format(text=text), as_json=True)
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        data = {}
    if not isinstance(data, dict):
        data = {}

    title = str(data.get("title") or "").strip() or text.strip()
    priority = str(data.get("priority") or "").strip().lower()
    if priority not in VALID_PRIORITIES:
        priority = "medium"
    return {"title": title, "priority": priority}
```

- [ ] **Step 4: Run the fast tests to verify they pass**

Run: `cd brain && .venv/bin/python -m pytest tests/test_ai.py -v -m "not slow"`
Also add tests for the untrusted-body guards: `parse_task` given valid non-object JSON (e.g.
`'[1, 2, 3]'`, `'null'`) returns the safe fallback; and `_generate` raises `OllamaUnavailable` when a
200 response body is malformed JSON, is valid-but-non-object JSON, or is non-decodable bytes.

Expected: PASS — 13 passed, 1 deselected

- [ ] **Step 5: Run the slow test against the real model**

Run: `cd brain && .venv/bin/python -m pytest tests/test_ai.py -v -m slow`
Expected: PASS — 1 passed. Requires Ollama running with `llama3.2:3b` pulled (Task 1).

- [ ] **Step 6: Commit**

```bash
git add brain/app/ai.py brain/tests/test_ai.py
git commit -m "feat(brain): add Ollama note cleanup and task parsing"
```

---

### Task 5: FastAPI endpoints

**Files:**
- Create: `brain/app/main.py`
- Test: `brain/tests/test_api.py`

**Interfaces:**
- Consumes: `app.config`, `app.models`, `app.storage.init_db/save_note/save_task/list_notes/list_tasks`, `app.transcribe.transcribe_file`, `app.ai.clean_note/parse_task/OllamaUnavailable`
- Produces: `app.main.app` (the ASGI FastAPI application) serving the protocol in Global Constraints

- [ ] **Step 1: Write the failing test**

Create `brain/tests/test_api.py`:

```python
import io

import pytest
from fastapi.testclient import TestClient

from app import ai, config, main, transcribe


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.sqlite3")
    monkeypatch.setattr(config, "SAMPLE_WAV", tmp_path / "sample.wav")
    monkeypatch.setattr(transcribe, "transcribe_file", lambda path: "buy milk tomorrow")
    monkeypatch.setattr(ai, "clean_note", lambda text: "Buy milk tomorrow.")
    monkeypatch.setattr(
        ai, "parse_task", lambda text: {"title": "Buy milk", "priority": "high"}
    )
    with TestClient(main.app) as test_client:
        yield test_client


def _wav_upload() -> dict:
    return {"audio": ("clip.wav", io.BytesIO(b"RIFFfake-wav-bytes"), "audio/wav")}


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_lists_start_empty(client):
    assert client.get("/notes").json() == []
    assert client.get("/tasks").json() == []


def test_process_note_returns_transcript_and_cleaned_text(client):
    response = client.post("/process", files=_wav_upload(), data={"mode": "note"})

    assert response.status_code == 200
    assert response.json() == {
        "transcript": "buy milk tomorrow",
        "result": {"text": "Buy milk tomorrow."},
    }


def test_process_note_persists_to_notes(client):
    client.post("/process", files=_wav_upload(), data={"mode": "note"})

    notes = client.get("/notes").json()

    assert len(notes) == 1
    assert notes[0]["text"] == "Buy milk tomorrow."
    assert notes[0]["id"] == 1
    assert notes[0]["created_at"] != ""


def test_process_task_returns_title_and_priority(client):
    response = client.post("/process", files=_wav_upload(), data={"mode": "task"})

    assert response.status_code == 200
    assert response.json()["result"] == {"title": "Buy milk", "priority": "high"}


def test_process_task_persists_to_tasks(client):
    client.post("/process", files=_wav_upload(), data={"mode": "task"})

    tasks = client.get("/tasks").json()

    assert len(tasks) == 1
    assert tasks[0]["title"] == "Buy milk"
    assert tasks[0]["priority"] == "high"


def test_process_rejects_empty_upload(client):
    files = {"audio": ("clip.wav", io.BytesIO(b""), "audio/wav")}

    response = client.post("/process", files=files, data={"mode": "note"})

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_process_rejects_invalid_mode(client):
    response = client.post("/process", files=_wav_upload(), data={"mode": "reminder"})

    assert response.status_code == 400
    assert "mode" in response.json()["detail"].lower()


def test_process_returns_422_when_no_speech_detected(client, monkeypatch):
    monkeypatch.setattr(transcribe, "transcribe_file", lambda path: "")

    response = client.post("/process", files=_wav_upload(), data={"mode": "note"})

    assert response.status_code == 422


def test_process_returns_503_when_ollama_is_down(client, monkeypatch):
    def _boom(text):
        raise ai.OllamaUnavailable("connection refused")

    monkeypatch.setattr(ai, "clean_note", _boom)

    response = client.post("/process", files=_wav_upload(), data={"mode": "note"})

    assert response.status_code == 503


def test_process_sample_returns_404_when_sample_missing(client):
    response = client.post("/process-sample", params={"mode": "note"})

    assert response.status_code == 404


def test_process_sample_uses_the_configured_sample(client):
    config.SAMPLE_WAV.write_bytes(b"RIFFfake-wav-bytes")

    response = client.post("/process-sample", params={"mode": "task"})

    assert response.status_code == 200
    assert response.json()["result"] == {"title": "Buy milk", "priority": "high"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd brain && .venv/bin/python -m pytest tests/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Write `brain/app/main.py`**

```python
"""FastAPI application exposing the Second Brain protocol."""

import logging
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from av import DecoderNotFoundError, DemuxerNotFoundError, InvalidDataError
from av import EOFError as AVEOFError
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import ai, config, storage, transcribe
from app.models import NoteOut, NoteResult, ProcessResponse, TaskOut, TaskResult

logger = logging.getLogger(__name__)

VALID_MODES = {"note", "task"}

# PyAV raises these when the uploaded bytes are not usable audio content:
# bad/truncated data, or a container/codec PyAV can't identify. This tuple
# deliberately excludes the `av.FFmpegError` base and PyAV's `_extend_builtin`
# OS-resource family (OSError, MemoryError, PermissionError, TimeoutError and
# siblings) which also subclass FFmpegError but signal a genuine server-side
# failure and must still surface as a 500, not a 400.
_UNDECODABLE_AUDIO_ERRORS = (
    InvalidDataError,
    AVEOFError,
    DecoderNotFoundError,
    DemuxerNotFoundError,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    storage.init_db(config.DB_PATH)
    yield


app = FastAPI(title="Second Brain", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ai.OllamaUnavailable)
async def _ollama_unavailable_handler(_request: Request, exc: ai.OllamaUnavailable):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


def _require_mode(mode: str) -> str:
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400, detail="Invalid mode: expected 'note' or 'task'"
        )
    return mode


def _run_pipeline(audio_path: Path, mode: str) -> ProcessResponse:
    try:
        transcript = transcribe.transcribe_file(audio_path)
    except _UNDECODABLE_AUDIO_ERRORS as exc:
        # Undecodable bytes are a client error (400). Return a generic detail —
        # never the raw exception, which embeds the server's temp file path —
        # and log the specifics server-side. OS-resource errors are NOT caught
        # here, so they still surface as 500.
        logger.warning("Could not decode audio upload: %s", exc)
        raise HTTPException(
            status_code=400,
            detail="Could not decode audio upload: unsupported or corrupt audio format",
        ) from exc
    if not transcript:
        raise HTTPException(status_code=422, detail="No speech detected in audio")

    if mode == "note":
        cleaned = ai.clean_note(transcript)
        storage.save_note(config.DB_PATH, cleaned)
        return ProcessResponse(transcript=transcript, result=NoteResult(text=cleaned))

    parsed = ai.parse_task(transcript)
    storage.save_task(config.DB_PATH, parsed["title"], parsed["priority"])
    return ProcessResponse(
        transcript=transcript,
        result=TaskResult(title=parsed["title"], priority=parsed["priority"]),
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse)
async def process(audio: UploadFile = File(...), mode: str = Form(...)) -> ProcessResponse:
    _require_mode(mode)

    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio upload")

    # Always use a .wav suffix: the decoder sniffs the real format from the bytes,
    # and the client-supplied filename is never trusted for path building.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        # Whisper and Ollama are blocking; keep them off the event loop.
        return await run_in_threadpool(_run_pipeline, tmp_path, mode)
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/process-sample", response_model=ProcessResponse)
def process_sample(mode: str = "note") -> ProcessResponse:
    _require_mode(mode)
    if not config.SAMPLE_WAV.exists():
        raise HTTPException(
            status_code=404, detail=f"Sample audio not found at {config.SAMPLE_WAV}"
        )
    return _run_pipeline(config.SAMPLE_WAV, mode)


@app.get("/notes", response_model=list[NoteOut])
def get_notes() -> list[NoteOut]:
    return storage.list_notes(config.DB_PATH)


@app.get("/tasks", response_model=list[TaskOut])
def get_tasks() -> list[TaskOut]:
    return storage.list_tasks(config.DB_PATH)
```

Also add error-boundary tests for the audio decode path: an upload whose decode fails returns **400**
with a generic detail that leaks no server path (assert `"/tmp"` and `".wav"` are absent from
`detail`); an OS-resource error raised during decode (e.g. `av.error.MemoryError`) returns **500**
(use a `TestClient(main.app, raise_server_exceptions=False)`); and an unexpected `RuntimeError` from
`transcribe_file` returns **500**.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd brain && .venv/bin/python -m pytest tests/test_api.py -v`
Expected: PASS — 16 passed

- [ ] **Step 5: Run the whole fast suite**

Run: `cd brain && .venv/bin/python -m pytest -v -m "not slow"`
Expected: PASS — 38 passed, 2 deselected

- [ ] **Step 6: Commit**

```bash
git add brain/app/main.py brain/tests/test_api.py
git commit -m "feat(brain): add FastAPI endpoints for process, notes and tasks"
```

---

### Task 6: End-to-end pipeline script + run instructions

**Files:**
- Create: `brain/test_pipeline.py`
- Create: `brain/README.md`

**Interfaces:**
- Consumes: a running server at `http://localhost:8000` serving the protocol from Task 5
- Produces: `python test_pipeline.py [--url URL] [--mode note|task]` — exits 0 on success, 1 on failure

- [ ] **Step 1: Write `brain/test_pipeline.py`**

This is a standalone script, not a pytest test (`pytest.ini` sets `testpaths = tests`, so pytest will not collect it).

```python
#!/usr/bin/env python3
"""Post the sample WAV at a running Second Brain server and print the result.

Usage:
    python test_pipeline.py                 # note mode against localhost:8000
    python test_pipeline.py --mode task
    python test_pipeline.py --url http://host.example:8000
"""

import argparse
import json
import sys
from pathlib import Path

import httpx

DEFAULT_URL = "http://localhost:8000"
SAMPLE = Path(__file__).resolve().parent / "samples" / "sample_note.wav"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the Second Brain pipeline")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--mode", default="note", choices=["note", "task"])
    args = parser.parse_args()

    if not SAMPLE.exists():
        print(f"FAIL: sample audio missing at {SAMPLE}")
        return 1

    try:
        health = httpx.get(f"{args.url}/health", timeout=10)
        health.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"FAIL: server not reachable at {args.url} ({exc})")
        print("Start it with: .venv/bin/uvicorn app.main:app --reload")
        return 1

    print(f"Server healthy. Uploading {SAMPLE.name} as mode={args.mode} ...")
    with SAMPLE.open("rb") as handle:
        try:
            response = httpx.post(
                f"{args.url}/process",
                files={"audio": (SAMPLE.name, handle, "audio/wav")},
                data={"mode": args.mode},
                timeout=300,
            )
        except httpx.HTTPError as exc:
            print(f"FAIL: request failed ({exc})")
            return 1

    if response.status_code != 200:
        print(f"FAIL: HTTP {response.status_code} — {response.text}")
        return 1

    try:
        payload = response.json()
        transcript = payload["transcript"]
        result = payload["result"]
    except (ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: malformed /process response ({exc})")
        return 1

    print("\n--- transcript ---")
    print(transcript)
    print("\n--- AI result ---")
    print(json.dumps(result, indent=2))

    if not transcript.strip():
        print("\nFAIL: empty transcript")
        return 1

    listing = httpx.get(f"{args.url}/{'notes' if args.mode == 'note' else 'tasks'}", timeout=30)
    if listing.status_code != 200:
        print(f"FAIL: listing request failed with HTTP {listing.status_code} — {listing.text}")
        return 1

    print(f"\nStored {args.mode}s now: {len(listing.json())}")
    print("\nPASS: full pipeline works (upload -> whisper -> ollama -> sqlite -> response)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Start the server in a second terminal**

```bash
cd "/home/nishanth/Desktop/Personal/Akash/Second Brain/brain"
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Expected: `Uvicorn running on http://127.0.0.1:8000`

- [ ] **Step 3: Run the pipeline script**

Run: `cd brain && .venv/bin/python test_pipeline.py --mode note`
Expected: prints the transcript, the cleaned note JSON, and ends with `PASS: full pipeline works`.

- [ ] **Step 4: Run it in task mode**

Run: `cd brain && .venv/bin/python test_pipeline.py --mode task`
Expected: `result` contains a `title` and a `priority` of `high`, `medium` or `low`, ending with `PASS`.

- [ ] **Step 5: Write `brain/README.md`**

```markdown
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
```

- [ ] **Step 6: Commit**

```bash
git add brain/test_pipeline.py brain/README.md
git commit -m "feat(brain): add end-to-end pipeline script and brain README"
```

---

### Task 7: Dashboard scaffold, protocol types and API client

**Files:**
- Create: `web/` (Vite React+TS scaffold)
- Create: `web/src/protocol.ts`
- Create: `web/src/api.ts`
- Create: `web/.env.example`

**Interfaces:**
- Consumes: the HTTP protocol served by `brain/app/main.py`
- Produces:
  - `web/src/protocol.ts`: `Mode`, `Priority`, `NoteResult`, `TaskResult`, `ProcessResponse`, `Note`, `Task`
  - `web/src/api.ts`: `getHealth(): Promise<{status: string}>`, `getNotes(): Promise<Note[]>`, `getTasks(): Promise<Task[]>`, `processSample(mode: Mode): Promise<ProcessResponse>`

- [ ] **Step 1: Scaffold the Vite app**

```bash
cd "/home/nishanth/Desktop/Personal/Akash/Second Brain"
npm create vite@latest web -- --template react-ts
cd web && npm install
```

Run: `cd web && npm run build`
Expected: build succeeds, `dist/` is produced.

- [ ] **Step 2: Write `web/src/protocol.ts`**

```typescript
// The Second Brain HTTP contract, mirrored in TypeScript.
// Must stay in sync with brain/app/models.py.

export type Mode = "note" | "task";
export type Priority = "high" | "medium" | "low";

export interface NoteResult {
  text: string;
}

export interface TaskResult {
  title: string;
  priority: Priority;
}

export interface ProcessResponse {
  transcript: string;
  result: NoteResult | TaskResult;
}

export interface Note {
  id: number;
  text: string;
  created_at: string;
}

export interface Task {
  id: number;
  title: string;
  priority: Priority;
  created_at: string;
}

export function isTaskResult(result: NoteResult | TaskResult): result is TaskResult {
  return "title" in result;
}
```

- [ ] **Step 3: Write `web/src/api.ts`**

```typescript
import type { Mode, Note, ProcessResponse, Task } from "./protocol";

const BASE_URL = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, init);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // response had no JSON body; keep the status-code message
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export const getHealth = () => request<{ status: string }>("/health");
export const getNotes = () => request<Note[]>("/notes");
export const getTasks = () => request<Task[]>("/tasks");

export const processSample = (mode: Mode) =>
  request<ProcessResponse>(`/process-sample?mode=${mode}`, { method: "POST" });
```

- [ ] **Step 4: Write `web/.env.example`**

```
# Base URL of the brain server. Copy to .env to override.
VITE_API_BASE=http://localhost:8000
```

- [ ] **Step 5: Verify types compile**

Run: `cd web && npx tsc --noEmit`
Expected: no output (success).

- [ ] **Step 6: Commit**

```bash
git add web/ 
git commit -m "feat(web): scaffold Vite dashboard with protocol types and API client"
```

---

### Task 8: Dashboard UI

**Files:**
- Create: `web/src/components/NotesList.tsx`
- Create: `web/src/components/TasksList.tsx`
- Modify: `web/src/App.tsx` (replace the Vite starter content entirely)
- Modify: `web/src/App.css` (replace the Vite starter styles entirely)

**Interfaces:**
- Consumes: `web/src/api.ts` (`getHealth`, `getNotes`, `getTasks`, `processSample`), `web/src/protocol.ts` (`Note`, `Task`, `Mode`, `isTaskResult`)
- Produces: the running dashboard at `http://localhost:5173`

> **Implementation note:** invoke the `frontend-design` skill before writing the components in this task.

- [ ] **Step 1: Write `web/src/components/NotesList.tsx`**

```tsx
import type { Note } from "../protocol";

export function NotesList({ notes }: { notes: Note[] }) {
  if (notes.length === 0) {
    return <p className="empty">No notes yet. Send a sample to create one.</p>;
  }
  return (
    <ul className="card-list">
      {notes.map((note) => (
        <li key={note.id} className="card">
          <p className="card-body">{note.text}</p>
          <time className="card-meta">{new Date(note.created_at).toLocaleString()}</time>
        </li>
      ))}
    </ul>
  );
}
```

- [ ] **Step 2: Write `web/src/components/TasksList.tsx`**

```tsx
import type { Task } from "../protocol";

export function TasksList({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) {
    return <p className="empty">No tasks yet. Send a sample to create one.</p>;
  }
  return (
    <ul className="card-list">
      {tasks.map((task) => (
        <li key={task.id} className="card">
          <span className={`badge badge-${task.priority}`}>{task.priority}</span>
          <p className="card-body">{task.title}</p>
          <time className="card-meta">{new Date(task.created_at).toLocaleString()}</time>
        </li>
      ))}
    </ul>
  );
}
```

- [ ] **Step 3: Replace `web/src/App.tsx`**

```tsx
import { useCallback, useEffect, useState } from "react";
import { getHealth, getNotes, getTasks, processSample } from "./api";
import { NotesList } from "./components/NotesList";
import { TasksList } from "./components/TasksList";
import type { Mode, Note, Task } from "./protocol";
import "./App.css";

export default function App() {
  const [online, setOnline] = useState<boolean | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [busy, setBusy] = useState<Mode | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      await getHealth();
      setOnline(true);
      const [nextNotes, nextTasks] = await Promise.all([getNotes(), getTasks()]);
      setNotes(nextNotes);
      setTasks(nextTasks);
      setError(null);
    } catch (err) {
      setOnline(false);
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function sendSample(mode: Mode) {
    setBusy(mode);
    setError(null);
    try {
      await processSample(mode);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="page">
      <header className="page-header">
        <h1>Second Brain</h1>
        <span className={`status status-${online === null ? "unknown" : online ? "up" : "down"}`}>
          {online === null ? "checking…" : online ? "brain online" : "brain offline"}
        </span>
      </header>

      <section className="actions">
        <button onClick={() => void sendSample("note")} disabled={busy !== null}>
          {busy === "note" ? "Processing…" : "Send sample as note"}
        </button>
        <button onClick={() => void sendSample("task")} disabled={busy !== null}>
          {busy === "task" ? "Processing…" : "Send sample as task"}
        </button>
        <button onClick={() => void refresh()} disabled={busy !== null}>
          Refresh
        </button>
      </section>

      {error && <p className="error">{error}</p>}

      <div className="columns">
        <section>
          <h2>Notes ({notes.length})</h2>
          <NotesList notes={notes} />
        </section>
        <section>
          <h2>Tasks ({tasks.length})</h2>
          <TasksList tasks={tasks} />
        </section>
      </div>
    </main>
  );
}
```

- [ ] **Step 4: Replace `web/src/App.css`**

```css
:root {
  color-scheme: light dark;
  --bg: #0f1115;
  --panel: #191c22;
  --text: #e7e9ee;
  --muted: #9aa1ad;
  --line: #2a2f39;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
}

.page {
  max-width: 60rem;
  margin: 0 auto;
  padding: 2rem 1.25rem;
}

.page-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  border-bottom: 1px solid var(--line);
  padding-bottom: 0.75rem;
}

.page-header h1 { font-size: 1.5rem; margin: 0; }

.status { font-size: 0.85rem; }
.status-up { color: #4ade80; }
.status-down { color: #f87171; }
.status-unknown { color: var(--muted); }

.actions { display: flex; flex-wrap: wrap; gap: 0.6rem; margin: 1.25rem 0; }

.actions button {
  background: var(--panel);
  color: var(--text);
  border: 1px solid var(--line);
  border-radius: 0.5rem;
  padding: 0.55rem 0.9rem;
  font-size: 0.9rem;
  cursor: pointer;
}
.actions button:disabled { opacity: 0.55; cursor: progress; }

.error {
  background: #2a1417;
  border: 1px solid #7f1d1d;
  color: #fca5a5;
  padding: 0.7rem 0.9rem;
  border-radius: 0.5rem;
}

.columns { display: grid; grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr)); gap: 1.5rem; }

h2 { font-size: 1rem; color: var(--muted); font-weight: 600; }

.card-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.6rem; }

.card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 0.6rem;
  padding: 0.8rem 0.9rem;
}

.card-body { margin: 0.25rem 0 0.5rem; line-height: 1.45; }
.card-meta { color: var(--muted); font-size: 0.75rem; }
.empty { color: var(--muted); font-size: 0.9rem; }

.badge {
  display: inline-block;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
}
.badge-high { background: #7f1d1d; color: #fecaca; }
.badge-medium { background: #78350f; color: #fde68a; }
.badge-low { background: #14532d; color: #bbf7d0; }
```

- [ ] **Step 5: Verify it type-checks and builds**

Run: `cd web && npx tsc --noEmit && npm run build`
Expected: no type errors; build succeeds.

- [ ] **Step 6: Live check against the running brain**

With the brain running (`.venv/bin/uvicorn app.main:app --port 8000` in `brain/`), run: `cd web && npm run dev`
Open <http://localhost:5173> and verify: the header shows **brain online**; clicking "Send sample as task" adds a task with a coloured priority badge; clicking "Send sample as note" adds a note; "Refresh" reloads both lists.

- [ ] **Step 7: Commit**

```bash
git add web/src
git commit -m "feat(web): add dashboard with notes, tasks and sample actions"
```

---

### Task 9: Root docs + full Phase 1 verification

**Files:**
- Modify: `README.md` (repository layout + running sections)

**Interfaces:**
- Consumes: everything built in Tasks 1–8
- Produces: a Phase 1 that a stranger can clone and run from the README alone

- [ ] **Step 1: Run the full fast test suite**

Run: `cd brain && .venv/bin/python -m pytest -v -m "not slow"`
Expected: PASS — 38 passed, 2 deselected

- [ ] **Step 2: Run the slow (real-model) tests**

Run: `cd brain && .venv/bin/python -m pytest -v -m slow`
Expected: PASS — 2 passed

- [ ] **Step 3: Update the "Repository layout" table in `README.md`**

Change the `brain/` and `web/` rows from `⏳ Phase 1` to `✅ Phase 1`:

```markdown
| `brain/` | Python FastAPI server — Whisper + Ollama + SQLite | ✅ Phase 1 |
| `web/` | React + Vite + TypeScript monitoring dashboard | ✅ Phase 1 |
```

- [ ] **Step 4: Replace the "Running" section in `README.md`**

```markdown
## Running

Prerequisites: Python 3.12, Node 22+, and [Ollama](https://ollama.com) running locally.

```bash
# 1. one-time setup
cd brain && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
ollama pull llama3.2:3b
cd ../web && npm install

# 2. start the brain (terminal 1)
cd brain && .venv/bin/uvicorn app.main:app --reload --port 8000

# 3. start the dashboard (terminal 2)
cd web && npm run dev
```

Then open <http://localhost:5173>. API docs live at <http://localhost:8000/docs>.

Verify the whole pipeline end to end:

```bash
cd brain && .venv/bin/python test_pipeline.py --mode task
```
```

- [ ] **Step 5: Update the status banner in `README.md`**

Replace the `> **Status:**` block with:

```markdown
> **Status:** 🟢 Phase 1 complete — the laptop brain and monitoring dashboard work end to end.
> Phases 2–3 (simulated ESP32 UI and device↔brain round-trip) are next; hardware comes after.
> See [`docs/superpowers/specs/2026-07-21-second-brain-design.md`](docs/superpowers/specs/2026-07-21-second-brain-design.md).
```

- [ ] **Step 6: Confirm nothing untracked was missed**

Run: `git status --short`
Expected: only intended files; no stray `.venv/`, `node_modules/`, `dist/` or `*.sqlite3` (all are covered by `.gitignore`).

- [ ] **Step 7: Commit**

```bash
git add README.md
git commit -m "docs: mark Phase 1 complete and document how to run the stack"
```

---

## Self-Review

**1. Spec coverage** — every Phase 1 requirement in the spec maps to a task:

| Spec requirement (§6) | Task |
|---|---|
| `brain/main.py` FastAPI app + endpoints | Task 5 |
| `brain/transcribe.py` faster-whisper wrapper, `small.en` loaded once | Task 3 |
| `brain/ai.py` Ollama note-cleanup + task-parse with JSON output | Task 4 |
| `brain/storage.py` SQLite notes + tasks | Task 2 |
| `brain/models.py` Pydantic schemas mirroring the protocol | Task 2 |
| `brain/requirements.txt` | Task 1 |
| `brain/test_pipeline.py` posts sample.wav, asserts shape, prints result | Task 6 |
| `brain/samples/note.wav` short spoken sample | Task 3 (named `sample_note.wav`; `config.SAMPLE_WAV` is the single source of truth) |
| `web/` React + Vite + TS dashboard, notes list, tasks list, "send sample" | Tasks 7–8 |
| `web/src/protocol.ts` TS types mirroring the contract | Task 7 |
| Error boundaries: 400 empty/invalid, 503 Ollama down, 422 no speech | Task 5 (tests assert each) |
| Verification: `test_pipeline.py` + dashboard shows live results | Tasks 6, 8, 9 |

Phases 2–3 (firmware, Wokwi, round-trip) are intentionally **out of scope for this plan** and get their own plan once Phase 1 is verified.

**2. Placeholder scan** — no "TBD"/"TODO"/"add error handling"-style steps; every code step contains complete code and every command step states its expected output.

**3. Type consistency** — checked across tasks: `NoteOut`/`TaskOut`/`ProcessResponse`/`NoteResult`/`TaskResult` are defined in Task 2 and used unchanged in Tasks 5 and 6; `transcribe_file` (Task 3), `clean_note`/`parse_task`/`OllamaUnavailable` (Task 4) are referenced with identical names in Task 5's `main.py` and its tests; `config.DB_PATH`/`config.SAMPLE_WAV` are always accessed as module attributes so the Task 5 tests can monkeypatch them; `protocol.ts` (Task 7) mirrors `models.py` field-for-field and is consumed unchanged in Task 8.
