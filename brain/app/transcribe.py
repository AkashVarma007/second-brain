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
