import errno
import io

import pytest
from av import InvalidDataError, MemoryError as AVMemoryError
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


@pytest.fixture
def client_allow_500(tmp_path, monkeypatch):
    """Same setup as `client`, but built with raise_server_exceptions=False so
    an unhandled server exception comes back as a 500 response instead of
    propagating into the test (TestClient's default behaviour)."""
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.sqlite3")
    monkeypatch.setattr(config, "SAMPLE_WAV", tmp_path / "sample.wav")
    monkeypatch.setattr(transcribe, "transcribe_file", lambda path: "buy milk tomorrow")
    monkeypatch.setattr(ai, "clean_note", lambda text: "Buy milk tomorrow.")
    monkeypatch.setattr(
        ai, "parse_task", lambda text: {"title": "Buy milk", "priority": "high"}
    )
    with TestClient(main.app, raise_server_exceptions=False) as test_client:
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


def test_process_rejects_undecodable_audio(client, monkeypatch):
    def _boom(path):
        raise InvalidDataError(
            1094995529, "Invalid data found when processing input", str(path)
        )

    monkeypatch.setattr(transcribe, "transcribe_file", _boom)

    response = client.post("/process", files=_wav_upload(), data={"mode": "note"})

    assert response.status_code == 400
    assert "audio" in response.json()["detail"].lower()


def test_process_rejects_undecodable_audio_without_leaking_server_path(
    client, monkeypatch
):
    def _boom(path):
        raise InvalidDataError(
            1094995529,
            "Invalid data found when processing input",
            "/tmp/tmpf7sw3w_o.wav",
        )

    monkeypatch.setattr(transcribe, "transcribe_file", _boom)

    response = client.post("/process", files=_wav_upload(), data={"mode": "note"})

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "/tmp" not in detail
    assert ".wav" not in detail
    assert "Errno" not in detail
    assert detail == "Could not decode audio upload: unsupported or corrupt audio format"


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


def test_process_returns_500_when_transcription_fails_unexpectedly(
    client_allow_500, monkeypatch
):
    def _boom(path):
        raise RuntimeError("model failed to load")

    monkeypatch.setattr(transcribe, "transcribe_file", _boom)

    response = client_allow_500.post(
        "/process", files=_wav_upload(), data={"mode": "note"}
    )

    assert response.status_code == 500
    assert "model failed to load" not in response.text


def test_process_returns_500_for_os_resource_failure_during_decode(
    client_allow_500, monkeypatch
):
    """PyAV's `_extend_builtin` errors (OSError, MemoryError, ...) are also
    `FFmpegError` subclasses, but they signal a genuine server-side failure
    (e.g. out of memory) rather than undecodable audio content, so they must
    still surface as a 500, not collapse into the 400 decode-failure path."""

    def _boom(path):
        raise AVMemoryError(errno.ENOMEM, "Cannot allocate memory")

    monkeypatch.setattr(transcribe, "transcribe_file", _boom)

    response = client_allow_500.post(
        "/process", files=_wav_upload(), data={"mode": "note"}
    )

    assert response.status_code == 500
    assert "Cannot allocate memory" not in response.text


def test_process_sample_returns_404_when_sample_missing(client):
    response = client.post("/process-sample", params={"mode": "note"})

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert str(config.SAMPLE_WAV) not in detail
    assert "/" not in detail


def test_process_sample_uses_the_configured_sample(client):
    config.SAMPLE_WAV.write_bytes(b"RIFFfake-wav-bytes")

    response = client.post("/process-sample", params={"mode": "task"})

    assert response.status_code == 200
    assert response.json()["result"] == {"title": "Buy milk", "priority": "high"}


def test_process_task_exercises_real_parse_task_and_save_task_seam(tmp_path, monkeypatch):
    """Unlike `client`, this test does NOT mock ai.parse_task or ai.clean_note: only
    the outermost external calls (transcribe.transcribe_file, ai._generate) are
    mocked, so the REAL ai.parse_task and the REAL storage.save_task both run.
    ai._generate is made to return an invalid priority ("urgent"); if
    ai.parse_task ever stopped normalising unknown priorities to "medium",
    storage.save_task's VALID_PRIORITIES guard would reject it and this test
    would fail (a ValueError would propagate instead of a 200 response)."""
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.sqlite3")
    monkeypatch.setattr(config, "SAMPLE_WAV", tmp_path / "sample.wav")
    monkeypatch.setattr(transcribe, "transcribe_file", lambda path: "do the thing")
    monkeypatch.setattr(
        ai,
        "_generate",
        lambda prompt, *, as_json: '{"title": "Do the thing", "priority": "urgent"}',
    )

    with TestClient(main.app) as test_client:
        response = test_client.post(
            "/process", files=_wav_upload(), data={"mode": "task"}
        )

        assert response.status_code == 200
        assert response.json()["result"] == {"title": "Do the thing", "priority": "medium"}

        tasks = test_client.get("/tasks").json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Do the thing"
        assert tasks[0]["priority"] == "medium"
