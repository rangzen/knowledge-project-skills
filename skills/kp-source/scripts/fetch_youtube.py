#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["youtube-transcript-api>=1.0"]
# ///
"""Fetch a YouTube transcript and write it as timestamped plain text.

Usage:
    uv run <this-script> <youtube-url-or-video-id> <dest-dir> [--language en,fr]

Writes:
    <dest-dir>/transcript.txt   - timestamped plain text, one line per caption
    <dest-dir>/<title>.info.json - video metadata (best-effort via yt-dlp)

Exits non-zero on transcript failure.  yt-dlp metadata failure is silenced.

Note: YouTubeTranscriptApi.get_transcript() (old class-method form) was removed
in v1.x.  Must instantiate the class first.

Language selection: without --language, the first available transcript is
used (manually-created tracks are preferred over auto-generated ones), so
non-English videos work with no extra flags. --language takes a
comma-separated priority list (e.g. "fr" or "en,fr"); if none of the
requested languages are available, this falls back to any available
transcript rather than failing.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

YOUTUBE_RE = re.compile(
    r"(?:youtube\.com/watch\?.*v=|youtu\.be/)([A-Za-z0-9_-]{11})"
)


def extract_video_id(url_or_id: str) -> str:
    m = YOUTUBE_RE.search(url_or_id)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    print(f"Cannot extract video ID from: {url_or_id}", file=sys.stderr)
    sys.exit(1)


def select_transcript(transcript_list, languages: list[str]):
    """Pick a transcript, preferring manually-created over auto-generated.

    If `languages` is given, try those first (find_transcript already prefers
    manually-created tracks among the requested languages). Otherwise, or if
    none of the requested languages are available, fall back to the first
    transcript in the list, which is manually-created if any exist.
    """
    from youtube_transcript_api import NoTranscriptFound

    if languages:
        try:
            return transcript_list.find_transcript(languages)
        except NoTranscriptFound:
            pass

    for transcript in transcript_list:
        return transcript

    raise NoTranscriptFound(transcript_list.video_id, languages, transcript_list)


def fetch_transcript(video_id: str, languages: list[str]) -> tuple[str, str, bool]:
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)
    transcript = select_transcript(transcript_list, languages)
    entries = list(transcript.fetch())
    if not entries:
        print(f"No transcript entries returned for {video_id}", file=sys.stderr)
        sys.exit(1)
    lines = [
        f"[{int(e.start // 60):02d}:{int(e.start % 60):02d}] {e.text}"
        for e in entries
    ]
    return "\n".join(lines), transcript.language_code, transcript.is_generated


def fetch_metadata(video_id: str, dest_dir: Path) -> None:
    subprocess.run(
        [
            "yt-dlp",
            "--write-info-json",
            "--skip-download",
            "-o",
            str(dest_dir / "%(title)s.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}",
        ],
        capture_output=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url_or_id")
    parser.add_argument("dest_dir")
    parser.add_argument(
        "--language",
        "-l",
        default=None,
        help="Comma-separated language priority list, e.g. 'fr' or 'en,fr'. "
        "Falls back to any available transcript if none match.",
    )
    args = parser.parse_args()

    dest_dir = Path(args.dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    languages = [code.strip() for code in args.language.split(",")] if args.language else []

    video_id = extract_video_id(args.url_or_id)

    from youtube_transcript_api import CouldNotRetrieveTranscript

    try:
        text, language_code, is_generated = fetch_transcript(video_id, languages)
    except CouldNotRetrieveTranscript as e:
        print(f"No transcript available for {video_id}: {e}", file=sys.stderr)
        sys.exit(1)

    transcript_path = dest_dir / "transcript.txt"
    transcript_path.write_text(text, encoding="utf-8")
    print(f"Transcript written: {transcript_path} ({len(text.splitlines())} lines)")

    fetch_metadata(video_id, dest_dir)

    result = {
        "transcript": str(transcript_path),
        "video_id": video_id,
        "lines": len(text.splitlines()),
        "language": language_code,
        "is_generated": is_generated,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
