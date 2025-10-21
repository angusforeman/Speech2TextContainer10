# Quickstart: NearRealTimeText2Speech

## Prerequisites
- DevContainer running (Python 3.10 environment).
- `.env` containing: `ApiKey`, `Billing`, optional `VOICE_NAME`, `TTS_HOST`.
- Azure Neural TTS container running (use `scripts/Text2Speechvalidate_env.sh`).

## Environment Validation
```bash
bash scripts/Text2Speechvalidate_env.sh
```
Check evidence logs under `assets/output/`.

## Readiness Probe
```bash
python cli/tts_cli.py --ping
```
Expected output: `READY` within ~1s.

## Single-Line Synthesis
```bash
python cli/tts_cli.py "Hello team, near real time test." 
```
Audio should begin <1s (target). Evidence optional via diagnostic mode.

## Interactive Mode
```bash
python cli/tts_cli.py --interactive
```
Type lines (≤500 chars). Use `:quit` to exit.

Queue Behavior: If audio playing and one line queued, further input rejected with `queue full` notice.

## Diagnostic Mode (Latency & Chunk Timing)
```bash
python cli/tts_cli.py --interactive --diagnostic
```
Captures first-chunk latency and per-chunk timestamps (SC-010).

## Mixed-Language Example
```bash
python cli/tts_cli.py "Café mañana façade naïve résumé"
```
Should synthesize; warning only if failure occurs.

## Error Handling Scenarios
1. Stop container then submit text → warning, session continues.
2. Oversize input (>500 chars) → rejection message.

## Evidence Artifacts
Generated under `assets/output/` named by scenario (latency.txt, queue.txt, etc.).

## Cleanup
```bash
docker stop neural-tts && docker rm neural-tts
```

## Next Steps
- Implement optional pyaudio fallback if inter-chunk gaps exceed threshold.
- Add structured exit codes (deferred).
