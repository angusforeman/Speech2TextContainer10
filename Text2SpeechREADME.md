# NearRealTimeText2Speech Quick Run Order & Artifact Map

Concise guide to execute available Phase 2 tasks (T01–T04 implemented) and locate their evidence artifacts. All artifacts are centralized under `assets/output/`. Every command exits with code 0 by design (FR-013). Run commands from repository root.

## 1. Environment Validation (T01)
Validates Docker, network, required env vars, AVX2, optional audio tools.

Command:
```
bash scripts/Text2Speechvalidate_env.sh
```
Artifacts produced:
- `assets/output/environment-check.txt` (per-check PASS/FAIL/WARN/INFO)
- `assets/output/health-check.txt` (/ready and /status HTTP codes)
- `assets/output/environment-summary.txt` (aggregate counts)

Interpretation: Any FAIL lines require attention before latency claims are trusted. Script always exits 0; rely on logs for status.

## 2. Readiness Probe (T02)
Confirms container responding quickly.

Command:
```
python3 -m cli.tts_cli --ping
```
Artifact:
- `assets/output/readiness.txt` (timestamp, status_code, elapsed_ms, PASS/FAIL)

Target: `elapsed_ms` < 1000 for baseline local conditions (SC-001 precursor).

## 3. Synthesis Smoke + Optional Playback (T03 + T04)
Performs a single short phrase synthesis, records latency and (optionally) playback metadata.

Command (synthesis only):
```
python3 -m cli.tts_cli --say "Hello near real time"
```
Command (with playback attempt):
```
python3 -m cli.tts_cli --say "Hello near real time" --play
```
Artifacts:
- New WAV file: `assets/output/tts_<UTC_TIMESTAMP>.wav`
- Evidence log: `assets/output/synthesis-smoke.txt` (overwritten each run with latest result)
  - Fields include: `latency_ms`, `success`, `reason`, `audio_path`, and playback fields when `--play` used.

Latency Interpretation:
- `latency_ms` approximates submission→first audio chunk. Aim <1000 ms (SC-001 baseline).

Playback Notes:
- Playback uses `simpleaudio` if installed; if missing, evidence shows `playback_reason=SIMPLEAUDIO_MISSING` (graceful degradation).
- Hearing audio inside the devcontainer typically requires mapping host sound devices (`--device /dev/snd`) or PulseAudio socket forwarding. Without this, WAV is generated but silent locally.

## 4. Inspect Generated Artifacts
List current artifacts (example):
```
ls -1 assets/output/
```
Review specific content (example):
```
grep -n '' assets/output/synthesis-smoke.txt
```

## Environment Variables (Optional Overrides)
- `TTS_HOST_URL` (default `http://localhost:5001`)
- `VOICE_NAME` (default `en-US-JennyNeural`)
- `TTS_SYNTH_OUTPUT_FILE` (override WAV output path for a single run)

Set via `.env` or inline, e.g.:
```
VOICE_NAME=en-US-GuyNeural python3 -m cli.tts_cli --say "Alternate voice"
```

## Evidence Path Summary (Implemented So Far)
| Task | Artifact(s) | Path |
|------|-------------|------|
| T01 | environment-check / health-check / environment-summary | assets/output/ |
| T02 | readiness.txt | assets/output/readiness.txt |
| T03 | tts_<timestamp>.wav | assets/output/ |
| T04 | synthesis-smoke.txt (playback metadata) | assets/output/synthesis-smoke.txt |

## Next Tasks (Not Yet Implemented)
- T05 queue manager (will add `queue.txt`)
- T06 interactive loop (`exit evidence`)
- T11 latency script (`latency.txt`)
…

## Troubleshooting Quick Checks
1. Container not ready: rerun environment script; confirm `/ready` returns 200.
2. Long latency (>1500 ms): check CPU load, network logs, container image freshness.
3. Playback missing: verify `pip show simpleaudio` and host sound device mapping.
4. No WAV file created: inspect `synthesis-smoke.txt` for `reason` or `error` fields.

## Minimal Dependencies Principle
No mandatory new packages for playback; `simpleaudio` remains optional. Core scripts rely on standard library + `httpx` + Azure Speech SDK.

---
Revision: 2025-10-21
*** End Patch