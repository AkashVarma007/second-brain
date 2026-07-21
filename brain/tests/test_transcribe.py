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
