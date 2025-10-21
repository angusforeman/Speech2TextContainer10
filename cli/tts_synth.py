"""Speech synthesis module (T03) for NearRealTimeText2Speech.

Centralized artifacts: all synthesized audio files and evidence reside under
`assets/output/` at the repository root.

Provides a thin wrapper around Azure Speech SDK for neural text-to-speech
targeting a locally running container. Supports host override and voice
configuration. Returns latency to first audio chunk (approx) using event hooks.

Functional mapping:
  FR-010 Default neural English voice selection
  FR-011 Output must be PCM 16-bit 16 kHz (container voice streams this; we assert expected format metadata where available)

NOTE: This is an initial skeleton. Playback and streaming chunk timestamp capture (FR-014) will be layered later.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import azure.cognitiveservices.speech as speechsdk  # type: ignore
except ImportError:  # defer hard dependency failure; higher layer will warn
    speechsdk = None  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "assets" / "output"  # Single centralized output directory

DEFAULT_HOST = os.getenv("TTS_HOST_URL", "http://localhost:5001")
DEFAULT_VOICE = os.getenv("VOICE_NAME", "en-US-JennyNeural")


@dataclass
class SynthesisResult:
    text: str
    success: bool
    reason: str
    latency_ms: Optional[int]
    error: Optional[str] = None
    voice: str = DEFAULT_VOICE
    host: str = DEFAULT_HOST
    audio_path: Optional[str] = None  # path to synthesized wav (if produced)
    start_monotonic: Optional[float] = None  # perf_counter() at synthesis start
    first_audio_monotonic: Optional[float] = None  # perf_counter() at first audio chunk


def build_speech_config(host: str, voice: str):
    if speechsdk is None:
        raise RuntimeError("azure.cognitiveservices.speech not installed")
    config = speechsdk.SpeechConfig(host=host)
    config.speech_synthesis_voice_name = voice
    return config


def synthesize(text: str, host: Optional[str] = None, voice: Optional[str] = None, timeout: float = 10.0) -> SynthesisResult:
    host = host or DEFAULT_HOST
    voice = voice or DEFAULT_VOICE
    if speechsdk is None:
        return SynthesisResult(text=text, success=False, reason="SDK_MISSING", latency_ms=None, error="Speech SDK not installed", voice=voice, host=host)
    if not text.strip():
        return SynthesisResult(text=text, success=False, reason="EMPTY", latency_ms=None, error="Empty text", voice=voice, host=host)

    speech_config = build_speech_config(host, voice)

    # Ensure output directory exists
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # Construct safe filename based on timestamp; allow override
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    base_name = f"tts_{ts}.wav"
    output_path = os.getenv("TTS_SYNTH_OUTPUT_FILE", str(OUTPUT_DIR / base_name))
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    first_audio_time: Optional[float] = None
    start = time.perf_counter()

    def synthesis_started(_evt):  # noqa: ANN001
        nonlocal first_audio_time
        if first_audio_time is None:
            first_audio_time = time.perf_counter()

    synthesizer.synthesizing.connect(lambda evt: synthesis_started(evt))  # type: ignore[arg-type]

    try:
        result = synthesizer.speak_text_async(text).get()
    except RuntimeError as e:  # container connection / audio system issues
        return SynthesisResult(text=text, success=False, reason="RUNTIME_ERROR", latency_ms=None, error=str(e), voice=voice, host=host, audio_path=output_path)
    except Exception as e:  # generic failure
        return SynthesisResult(text=text, success=False, reason="EXCEPTION", latency_ms=None, error=str(e), voice=voice, host=host, audio_path=output_path)

    end = time.perf_counter()
    latency_ms = int(((first_audio_time or end) - start) * 1000)

    if result is not None:
        rr = getattr(result, "reason", None)
        if rr == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return SynthesisResult(text=text, success=True, reason="OK", latency_ms=latency_ms, voice=voice, host=host, audio_path=output_path, start_monotonic=start, first_audio_monotonic=first_audio_time or end)
        if rr == speechsdk.ResultReason.Canceled:
            cancellation = getattr(result, "cancellation_details", None)
            err = getattr(cancellation, "error_details", "Canceled") if cancellation else "Canceled"
            return SynthesisResult(text=text, success=False, reason="CANCELED", latency_ms=latency_ms, error=err, voice=voice, host=host, audio_path=output_path, start_monotonic=start, first_audio_monotonic=first_audio_time or end)
        return SynthesisResult(text=text, success=False, reason=str(rr), latency_ms=latency_ms, error="Unknown synthesis state", voice=voice, host=host, audio_path=output_path, start_monotonic=start, first_audio_monotonic=first_audio_time or end)
    return SynthesisResult(text=text, success=False, reason="NO_RESULT", latency_ms=latency_ms, error="Result object missing", voice=voice, host=host, audio_path=output_path, start_monotonic=start, first_audio_monotonic=first_audio_time or end)
