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
