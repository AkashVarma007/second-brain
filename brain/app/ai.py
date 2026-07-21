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
    try:
        return str(response.json().get("response", "")).strip()
    except (json.JSONDecodeError, AttributeError) as exc:
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
