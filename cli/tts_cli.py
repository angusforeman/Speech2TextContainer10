#!/usr/bin/env python3
"""Minimal NearRealTimeText2Speech CLI (T02)

Provides a readiness probe (--ping) that checks the neural TTS container /ready endpoint
and writes an evidence artifact. Always exits 0 per FR-013.

Usage:
  python -m cli.tts_cli --ping
  ./cli/tts_cli.py --ping

Environment variables (optional overrides):
  TTS_HOST_URL: Base URL to the TTS container (default http://localhost:5001)

Evidence artifact path:
    assets/output/readiness.txt

Functional mapping:
  FR-004 Readiness probe command
  FR-013 Always exit 0

Success criteria mapping:
    SC-001 latency (<1000ms first audio for short phrase) measured later; this CLI will show basic synthesis latency for smoke test.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Tuple

try:
    import httpx  # minimal dependency already in tech stack
except ImportError:  # fail soft per FR-013
    httpx = None  # type: ignore

OUTPUT_DIR = Path("assets/output")  # Single centralized evidence directory
READINESS_FILE = OUTPUT_DIR / "readiness.txt"


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ping(tts_url: str, timeout: float = 2.0) -> Tuple[bool, int, float, str]:
    """Perform readiness ping.

    Returns (ok, status_code, elapsed_seconds, message)
    """
    if httpx is None:
        return False, 0, 0.0, "httpx not installed"
    start = time.perf_counter()
    try:
        resp = httpx.get(f"{tts_url.rstrip('/')}/ready", timeout=timeout)
        elapsed = time.perf_counter() - start
        ok = resp.status_code == 200
        return ok, resp.status_code, elapsed, "READY" if ok else f"Unexpected status {resp.status_code}"
    except Exception as e:  # soft failure
        elapsed = time.perf_counter() - start
        return False, 0, elapsed, f"Error: {e}"[:300]


def write_readiness_artifact(result: Tuple[bool, int, float, str], tts_url: str) -> None:
    ok, status, elapsed, message = result
    ensure_dirs()
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    lines = [
        f"timestamp={ts}",
        f"url={tts_url}",
        f"status_code={status}",
        f"elapsed_ms={int(elapsed*1000)}",
        f"result={'PASS' if ok else 'FAIL'}",
        f"message={message}",
    ]
    READINESS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")  # Write readiness artifact


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="NearRealTimeText2Speech minimal CLI")
    p.add_argument("--ping", action="store_true", help="Perform readiness probe and exit")
    p.add_argument("--host", default=os.getenv("TTS_HOST_URL", "http://localhost:5001"), help="Base URL for TTS container (default env TTS_HOST_URL or http://localhost:5001)")
    p.add_argument("--say", metavar="TEXT", help="Speak a short text (smoke synthesis) and report latency")
    p.add_argument("--play", action="store_true", help="Attempt local audio playback of synthesized result (T04)")
    p.add_argument("--multi", nargs="+", metavar="TEXT", help="Submit multiple texts rapidly to exercise queue manager (T05)")
    p.add_argument("--max-queue", type=int, default=int(os.getenv("TTS_MAX_QUEUE", "3")), help="Maximum queued items (excluding active). Default 3.")
    p.add_argument("--voice", default=os.getenv("VOICE_NAME", "en-US-JennyNeural"), help="Voice name override (default env VOICE_NAME or en-US-JennyNeural)")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:  # return code ignored (always 0 externally)
    args = parse_args(argv)
    if args.ping:
        result = ping(args.host)
        write_readiness_artifact(result, args.host)
        ok, status, elapsed, message = result
        # Print concise console output
        print(f"Ping {'PASS' if ok else 'FAIL'} | status={status} | elapsed_ms={int(elapsed*1000)} | {message}")
        # Per FR-013 always exit 0
        return 0
    if args.multi:
        import importlib, pathlib
        repo_root = pathlib.Path(__file__).resolve().parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        qm_mod = importlib.import_module("cli.queue_manager")
        synth_mod = importlib.import_module("cli.tts_synth")
        manager = qm_mod.QueueManager(host=args.host, voice=args.voice, max_queue=args.max_queue)
        decisions = []
        for txt in args.multi:
            decisions.append(manager.submit(txt))
            # minimal delay to simulate rapid submissions (<2s apart)
            time.sleep(0.05)
        # Wait for all to finish (bounded)
        manager.wait_all(timeout=30)
        ensure_dirs()
        queue_artifact = OUTPUT_DIR / "queue.txt"
        lines = []
        for d in decisions:
            lines.append(f"decision|{d.request_id}|{d.decision}|{int(d.timestamp*1000)}|{d.text}|max_queue={manager.max_queue}")
        for r in manager.results:
            lines.append(
                "result|" +
                f"{r.request_id}|{r.success}|{r.reason}|{r.latency_ms}|{int(r.started_monotonic*1000)}|{int(r.completed_monotonic*1000)}|{r.text}|max_queue={manager.max_queue}"
            )
        queue_artifact.write_text("\n".join(lines) + "\n", encoding="utf-8")
        # Console summary
        active_started = sum(1 for d in decisions if d.decision == "ACTIVE_STARTED")
        queued = sum(1 for d in decisions if d.decision == "QUEUED")
        rejected = sum(1 for d in decisions if d.decision == "REJECTED_QUEUE_FULL")
        print(f"MULTI complete | active_started={active_started} queued={queued} rejected={rejected} results={len(manager.results)} max_queue={manager.max_queue}")
        return 0
    if args.say:
        # Lazy import to keep readiness fast
        import importlib, pathlib
        # Ensure repository root (parent of this file's directory) is on sys.path for package import
        repo_root = pathlib.Path(__file__).resolve().parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        tts_synth = importlib.import_module("cli.tts_synth")
        synth_result = tts_synth.synthesize(args.say, host=args.host, voice=args.voice)
        playback_meta = None
        if args.play and synth_result.audio_path:
            playback = importlib.import_module("cli.playback")
            playback_meta = playback.play_wav(synth_result.audio_path, t0_monotonic=None)
        # Write evidence log alongside audio output under assets/output
        ensure_dirs()
        evidence_path = OUTPUT_DIR / "synthesis-smoke.txt"
        line_parts = [
            f"text={args.say}",
            f"voice={synth_result.voice}",
            f"latency_ms={synth_result.latency_ms}",
            f"success={synth_result.success}",
            f"reason={synth_result.reason}",
            f"error={synth_result.error or ''}",
            f"host={synth_result.host}",
            f"audio_path={synth_result.audio_path or ''}",
        ]
        if playback_meta is not None:
            line_parts.extend([
                f"playback_played={playback_meta.played}",
                f"playback_success={playback_meta.success}",
                f"playback_reason={playback_meta.reason}",
                f"playback_used_simpleaudio={playback_meta.used_simpleaudio}",
                f"playback_start_offset_ms={playback_meta.start_offset_ms}",
                f"playback_duration_seconds={playback_meta.duration_seconds}",
                f"playback_error={playback_meta.error or ''}",
            ])
        line = "\n".join(line_parts) + "\n"
        evidence_path.write_text(line, encoding="utf-8")
        print(
            "SAY "
            f"{'PASS' if synth_result.success else 'FAIL'} | latency_ms={synth_result.latency_ms} | voice={synth_result.voice} | "
            f"reason={synth_result.reason}"
            + (f" | playback={playback_meta.reason}" if playback_meta else "")
        )
        return 0
    # If no subcommand flags provided, display help then exit 0
    print("No action specified. Use --ping for readiness check.")
    return 0


if __name__ == "__main__":
    # Ensure consistent exit code 0
    _code = main(sys.argv[1:])
    sys.exit(0)
