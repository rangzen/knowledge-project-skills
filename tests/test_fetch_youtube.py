"""Tests for fetch_youtube.py transcript language selection.

Covers the multilingual-subtitle fix: English-only videos, non-English-only
videos, explicit language preference (with fallback when unavailable), and
the no-transcript failure path. No network access; the YouTube API surface
is faked.
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from youtube_transcript_api import NoTranscriptFound, YouTubeTranscriptApi

SCRIPT = Path(__file__).parent.parent / "skills/kp-source/scripts/fetch_youtube.py"
spec = importlib.util.spec_from_file_location("fetch_youtube", SCRIPT)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

select_transcript = _mod.select_transcript
fetch_transcript = _mod.fetch_transcript
extract_video_id = _mod.extract_video_id


class FakeTranscript:
    def __init__(self, language_code, is_generated, text="hello"):
        self.language_code = language_code
        self.is_generated = is_generated
        self._text = text

    def fetch(self):
        return [SimpleNamespace(start=0.0, text=self._text)]


class FakeTranscriptList:
    """Mimics youtube_transcript_api.TranscriptList's public surface."""

    def __init__(self, video_id, manual=None, generated=None):
        self.video_id = video_id
        self._manual = manual or {}
        self._generated = generated or {}

    def __iter__(self):
        return iter(list(self._manual.values()) + list(self._generated.values()))

    def find_transcript(self, language_codes):
        for code in language_codes:
            if code in self._manual:
                return self._manual[code]
        for code in language_codes:
            if code in self._generated:
                return self._generated[code]
        raise NoTranscriptFound(self.video_id, language_codes, self)


def test_english_only_video_selected_with_no_preference():
    transcript_list = FakeTranscriptList("vid", generated={"en": FakeTranscript("en", True)})
    result = select_transcript(transcript_list, [])
    assert result.language_code == "en"


def test_non_english_only_video_selected_with_no_preference():
    transcript_list = FakeTranscriptList("vid", manual={"fr": FakeTranscript("fr", False)})
    result = select_transcript(transcript_list, [])
    assert result.language_code == "fr"
    assert result.is_generated is False


def test_manually_created_preferred_over_generated():
    transcript_list = FakeTranscriptList(
        "vid",
        manual={"fr": FakeTranscript("fr", False)},
        generated={"fr": FakeTranscript("fr", True)},
    )
    result = select_transcript(transcript_list, [])
    assert result.is_generated is False


def test_explicit_language_preference_is_honored():
    transcript_list = FakeTranscriptList(
        "vid",
        manual={"fr": FakeTranscript("fr", False), "en": FakeTranscript("en", False)},
    )
    result = select_transcript(transcript_list, ["en"])
    assert result.language_code == "en"


def test_falls_back_to_any_available_when_preference_unavailable():
    transcript_list = FakeTranscriptList("vid", manual={"fr": FakeTranscript("fr", False)})
    result = select_transcript(transcript_list, ["en"])
    assert result.language_code == "fr"


def test_no_transcript_available_raises():
    transcript_list = FakeTranscriptList("vid")
    with pytest.raises(NoTranscriptFound):
        select_transcript(transcript_list, [])


def test_fetch_transcript_end_to_end_non_english(monkeypatch):
    transcript_list = FakeTranscriptList("vid", manual={"fr": FakeTranscript("fr", False, text="bonjour")})
    monkeypatch.setattr(YouTubeTranscriptApi, "list", lambda self, video_id: transcript_list)

    text, language_code, is_generated = fetch_transcript("vid", [])

    assert "bonjour" in text
    assert language_code == "fr"
    assert is_generated is False


def test_extract_video_id_from_watch_url():
    assert extract_video_id("https://www.youtube.com/watch?v=o8h-fVygTek") == "o8h-fVygTek"


def test_extract_video_id_from_short_url():
    assert extract_video_id("https://youtu.be/o8h-fVygTek") == "o8h-fVygTek"


def test_extract_video_id_from_bare_id():
    assert extract_video_id("o8h-fVygTek") == "o8h-fVygTek"
