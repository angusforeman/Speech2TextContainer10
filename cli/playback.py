"""Playback abstraction (T04) for NearRealTimeText2Speech.

Provides a minimal, dependency-light wrapper for WAV playback using the
optional `simpleaudio` package. If `simpleaudio` is unavailable, playback
is skipped with a recorded note but no hard failure (aligns with FR-013
always-exit-0 principle and graceful degradation).

Central artifact path policy: no evidence written directly here; callers
decide. This module returns structured results for evidence/logging.

Future (T05+) queue/session logic will compose this abstraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
import wave
from typing import Optional

try:  # Optional dependency
    import simpleaudio  # type: ignore
except ImportError:  # pragma: no cover - environment may lack simpleaudio
    simpleaudio = None  # type: ignore


@dataclass
class PlaybackResult:
    path: Path
    played: bool
    success: bool
    reason: str
    used_simpleaudio: bool
    start_time_monotonic: float
    start_offset_ms: int
    duration_seconds: Optional[float]
    error: Optional[str] = None


def _wav_duration_seconds(path: Path) -> Optional[float]:
    try:
        with wave.open(str(path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate:
                return frames / float(rate)
    except Exception:
        return None
    return None


def play_wav(path: str | Path, t0_monotonic: Optional[float] = None) -> PlaybackResult:
    """Attempt to play a WAV file.

    Args:
        path: File system path to WAV.
        t0_monotonic: Optional reference start time (monotonic) to compute offset.
    Returns:
        PlaybackResult containing metadata; never raises.
    """
    p = Path(path)
    start_reference = t0_monotonic if t0_monotonic is not None else time.perf_counter()
    start_attempt = time.perf_counter()
    duration = _wav_duration_seconds(p)

    if not p.exists():
        return PlaybackResult(
            path=p,
            played=False,
            success=False,
            reason="MISSING_FILE",
            used_simpleaudio=False,
            start_time_monotonic=start_attempt,
            start_offset_ms=int((start_attempt - start_reference) * 1000),
            duration_seconds=duration,
            error="File does not exist",
        )

    if simpleaudio is None:
        # Degrade gracefully; caller can decide whether to treat as WARN.
        return PlaybackResult(
            path=p,
            played=False,
            success=True,  # Synthesis OK; playback intentionally skipped
            reason="SIMPLEAUDIO_MISSING",
            used_simpleaudio=False,
            start_time_monotonic=start_attempt,
            start_offset_ms=int((start_attempt - start_reference) * 1000),
            duration_seconds=duration,
            error=None,
        )

    try:
        wave_obj = simpleaudio.WaveObject.from_wave_file(str(p))  # type: ignore[attr-defined]
        play_obj = wave_obj.play()  # non-blocking
        # We don't wait; session loop (future) can track completion if needed.
        return PlaybackResult(
            path=p,
            played=True,
            success=True,
            reason="OK",
            used_simpleaudio=True,
            start_time_monotonic=start_attempt,
            start_offset_ms=int((start_attempt - start_reference) * 1000),
            duration_seconds=duration,
            error=None,
        )
    except Exception as e:  # pragma: no cover - rare runtime issues
        return PlaybackResult(
            path=p,
            played=False,
            success=False,
            reason="PLAY_ERROR",
            used_simpleaudio=True,
            start_time_monotonic=start_attempt,
            start_offset_ms=int((start_attempt - start_reference) * 1000),
            duration_seconds=duration,
            error=str(e),
        )


__all__ = ["PlaybackResult", "play_wav"]
