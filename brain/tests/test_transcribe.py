import pytest

from app import config, transcribe


class _FakeSegment:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeModel:
    def __init__(self, segments) -> None:
        self._segments = segments

    def transcribe(self, path, **kwargs):
        return self._segments, object()


def test_join_segments_trims_and_joins():
    segments = [_FakeSegment("  Remind me to buy milk "), _FakeSegment(" and call the dentist. ")]

    assert transcribe._join_segments(segments) == "Remind me to buy milk and call the dentist."


def test_join_segments_returns_empty_string_for_no_speech():
    assert transcribe._join_segments([]) == ""


def test_transcribe_file_calls_the_model_and_joins_segments(monkeypatch):
    segments = [_FakeSegment("  Remind me to buy milk "), _FakeSegment(" and call the dentist. ")]
    monkeypatch.setattr(transcribe, "_get_model", lambda: _FakeModel(segments))

    text = transcribe.transcribe_file("anything.wav")

    assert text == "Remind me to buy milk and call the dentist."


@pytest.mark.slow
def test_transcribes_the_sample_wav_to_real_text():
    assert config.SAMPLE_WAV.exists(), "record brain/samples/sample_note.wav first"

    text = transcribe.transcribe_file(config.SAMPLE_WAV)

    assert len(text.split()) >= 3
