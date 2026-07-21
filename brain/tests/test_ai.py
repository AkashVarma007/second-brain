import json

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


def test_parse_task_falls_back_when_model_returns_json_array(monkeypatch):
    monkeypatch.setattr(ai, "_generate", _fake_generate("[1, 2, 3]"))

    assert ai.parse_task("water the plants") == {
        "title": "water the plants",
        "priority": "medium",
    }


def test_parse_task_falls_back_when_model_returns_json_null(monkeypatch):
    monkeypatch.setattr(ai, "_generate", _fake_generate("null"))

    assert ai.parse_task("water the plants") == {
        "title": "water the plants",
        "priority": "medium",
    }


def test_generate_raises_ollama_unavailable_on_connection_error(monkeypatch):
    def _boom(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(ai.httpx, "post", _boom)

    with pytest.raises(ai.OllamaUnavailable):
        ai._generate("hello", as_json=False)


def test_generate_raises_ollama_unavailable_on_malformed_json_body(monkeypatch):
    class _FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            raise json.JSONDecodeError("Expecting value", "not json", 0)

    monkeypatch.setattr(ai.httpx, "post", lambda *args, **kwargs: _FakeResponse())

    with pytest.raises(ai.OllamaUnavailable):
        ai._generate("hello", as_json=False)


def test_generate_raises_ollama_unavailable_on_non_object_json_body(monkeypatch):
    class _FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [1, 2, 3]

    monkeypatch.setattr(ai.httpx, "post", lambda *args, **kwargs: _FakeResponse())

    with pytest.raises(ai.OllamaUnavailable):
        ai._generate("hello", as_json=False)


def test_generate_raises_ollama_unavailable_on_non_decodable_response_body(monkeypatch):
    req = httpx.Request("POST", "http://localhost:11434/api/generate")
    resp = httpx.Response(
        200,
        content=b"\xff\xfe\x00\x01garbage-not-utf8-\x80\x81",
        headers={"content-type": "application/json"},
        request=req,
    )

    monkeypatch.setattr(ai.httpx, "post", lambda *args, **kwargs: resp)

    with pytest.raises(ai.OllamaUnavailable):
        ai._generate("hello", as_json=False)


@pytest.mark.slow
def test_parse_task_against_the_real_model():
    result = ai.parse_task("remind me to call the dentist tomorrow, it is urgent")

    assert result["priority"] in {"high", "medium", "low"}
    assert result["title"].strip() != ""
