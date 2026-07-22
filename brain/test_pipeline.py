#!/usr/bin/env python3
"""Post the sample WAV at a running Second Brain server and print the result.

Usage:
    python test_pipeline.py                 # note mode against localhost:8000
    python test_pipeline.py --mode task
    python test_pipeline.py --url http://host.example:8000
"""

import argparse
import json
import sys
from pathlib import Path

import httpx

DEFAULT_URL = "http://localhost:8000"
SAMPLE = Path(__file__).resolve().parent / "samples" / "sample_note.wav"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the Second Brain pipeline")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--mode", default="note", choices=["note", "task"])
    args = parser.parse_args()

    if not SAMPLE.exists():
        print(f"FAIL: sample audio missing at {SAMPLE}")
        return 1

    try:
        health = httpx.get(f"{args.url}/health", timeout=10)
        health.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"FAIL: server not reachable at {args.url} ({exc})")
        print("Start it with: .venv/bin/uvicorn app.main:app --reload")
        return 1

    print(f"Server healthy. Uploading {SAMPLE.name} as mode={args.mode} ...")
    with SAMPLE.open("rb") as handle:
        try:
            response = httpx.post(
                f"{args.url}/process",
                files={"audio": (SAMPLE.name, handle, "audio/wav")},
                data={"mode": args.mode},
                timeout=300,
            )
        except httpx.HTTPError as exc:
            print(f"FAIL: request failed ({exc})")
            return 1

    if response.status_code != 200:
        print(f"FAIL: HTTP {response.status_code} — {response.text}")
        return 1

    try:
        payload = response.json()
        transcript = payload["transcript"]
        result = payload["result"]
    except (ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: malformed /process response ({exc})")
        return 1

    print("\n--- transcript ---")
    print(transcript)
    print("\n--- AI result ---")
    print(json.dumps(result, indent=2))

    if not transcript.strip():
        print("\nFAIL: empty transcript")
        return 1

    listing = httpx.get(f"{args.url}/{'notes' if args.mode == 'note' else 'tasks'}", timeout=30)
    if listing.status_code != 200:
        print(f"FAIL: listing request failed with HTTP {listing.status_code} — {listing.text}")
        return 1

    print(f"\nStored {args.mode}s now: {len(listing.json())}")
    print("\nPASS: full pipeline works (upload -> whisper -> ollama -> sqlite -> response)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
