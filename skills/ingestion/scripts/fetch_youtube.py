#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["youtube-transcript-api>=1.0"]
# ///
"""Fetch a YouTube transcript and write it as timestamped plain text.

Usage:
    uv run <this-script> <youtube-url-or-video-id> <dest-dir>

Writes:
    <dest-dir>/transcript.txt   — timestamped plain text, one line per caption
    <dest-dir>/<title>.info.json — video metadata (best-effort via yt-dlp)

Exits non-zero on transcript failure.  yt-dlp metadata failure is silenced.

Note: YouTubeTranscriptApi.get_transcript() (old class-method form) was removed
in v1.x.  Must instantiate the class first.
"""

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


def fetch_transcript(video_id: str) -> str:
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    entries = list(api.fetch(video_id))
    if not entries:
        print(f"No transcript entries returned for {video_id}", file=sys.stderr)
        sys.exit(1)
    lines = [
        f"[{int(e.start // 60):02d}:{int(e.start % 60):02d}] {e.text}"
        for e in entries
    ]
    return "\n".join(lines)


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
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <youtube-url-or-video-id> <dest-dir>", file=sys.stderr)
        sys.exit(1)

    url_or_id = sys.argv[1]
    dest_dir = Path(sys.argv[2])
    dest_dir.mkdir(parents=True, exist_ok=True)

    video_id = extract_video_id(url_or_id)
    text = fetch_transcript(video_id)

    transcript_path = dest_dir / "transcript.txt"
    transcript_path.write_text(text, encoding="utf-8")
    print(f"Transcript written: {transcript_path} ({len(text.splitlines())} lines)")

    fetch_metadata(video_id, dest_dir)

    result = {
        "transcript": str(transcript_path),
        "video_id": video_id,
        "lines": len(text.splitlines()),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
