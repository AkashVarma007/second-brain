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
