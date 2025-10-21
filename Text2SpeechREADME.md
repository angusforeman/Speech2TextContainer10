# NearRealTimeText2Speech Quick Run Order & Artifact Map

Concise guide to execute available Phase 2 tasks and locate their evidence artifacts. All artifacts are centralized under `assets/output/`. Every command exits with code 0 by design (FR-013). Run commands from repository root.

## 0. Start the Text to Speech Container
If the Neural TTS service is not already running, start the official Azure Speech neural TTS container (exposes internal port 5000) mapping it to host port 5001:

```bash
docker run --rm -d \
  --name neural-tts \
  -p 5001:5000 \
  mcr.microsoft.com/azure-cognitive-services/speechservices/neural-text-to-speech:latest
```

Notes:
- `--rm` removes the container when stopped; omit if you want it to persist.
- Adjust host port (`5001`) if already in use.
- Stop later with: `docker stop neural-tts`.
- Verify it is up: `docker ps | grep neural-tts` and curl readiness (if endpoint provided) or rely on `--ping` below.

Environment overrides (if required by your deployment) can be added with `-e VAR=VALUE` flags; current scripts assume default local access at `http://localhost:5001`.

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

## 5. Latency Measurement (T11)
Measure multi-phrase queue + synthesis latency and build a combined WAV with segment mapping.

Command (uses internal defaults for phrases unless you edit the script):
```bash
bash scripts/measure_latency.sh
```

Primary artifacts:
- `assets/output/latency.txt` (per-phrase timing rows + SEG lines mapping frames) 
- `assets/output/latency_index.json` (JSON array of segments with frame offsets)
- `assets/output/latency_combined_<UTC_TIMESTAMP>.wav` (concatenated successful phrase audio)

Key columns in `latency.txt`:
- `queue_delay_ms = start_ms - submit_ms`
- `synth_latency_ms = first_audio_ms - start_ms`
- Total perceived first-audio latency = queue_delay_ms + synth_latency_ms

SEG line format:
`SEG|request_id|start_frame|end_frame|frames|audio_path|text`

Refer to `docs/measure_latencyREADME.md` for full semantics, formulas, and interpretation guidelines.

## Updated / Implemented Tasks Summary
| Task | Status | Key Artifact(s) |
|------|--------|-----------------|
| T01 Environment validation | Implemented | environment-check.txt, health-check.txt, environment-summary.txt |
| T02 Readiness probe | Implemented | readiness.txt |
| T03 Single synthesis | Implemented | tts_<timestamp>.wav |
| T04 Optional playback | Implemented | synthesis-smoke.txt (playback metadata) |
| T05 Queue manager (bounded FIFO) | Implemented | queue.txt (decision/result lines) |
| T11 Latency measurement | Implemented | latency.txt, latency_index.json, latency_combined_<timestamp>.wav |

## Next Tasks (Not Yet Implemented)
- T06 interactive loop
- T07–T09 error & mixed-language handling
- T10 / T12 chunk timing diagnostics
- T15–T16 automated tests
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