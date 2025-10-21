# Local Azure Neural Text-to-Speech (NTTS) Tech Stack & Architecture

This document specifies the technical stack, container configuration, and architectural approach for adding a near real-time Text-to-Speech (TTS) CLI using the Azure Neural Text-to-Speech container locally.

## Goals
Provide a simple Python command line where the user types (or pipes) text and hears synthesized neural speech with minimal latency, using ONLY a locally running Azure Speech Neural TTS container for synthesis (still connected to Azure for billing as required).

## Core Components
| Layer | Choice | Rationale |
|-------|--------|-----------|
| Runtime | Python 3.10 (DevContainer) | Matches existing repo; fully supported by Speech SDK |
| Dev Environment | VS Code DevContainer (`mcr.microsoft.com/devcontainers/python:1-3.10-bullseye`) | Consistent reproducible tooling; Debian base for native builds |
| Speech Synthesis Engine | Azure Neural Text-to-Speech container | Local execution & lower network latency vs cloud-only |
| SDK | `azure-cognitiveservices-speech` (Speech SDK) | Provides streaming synthesis events (Synthesizing) for near real-time playback |
| HTTP Client | `httpx` | Lightweight readiness & status checks |
| Playback (Option A) | `simpleaudio` | Pure Python, easy install |
| Playback (Option B) | `pyaudio` | Lower latency (PortAudio), but adds native deps |
| Playback (Option C) | `ffplay` (from FFmpeg) | Zero extra Python deps if ffmpeg present; slightly higher start latency |
| Scripting | Bash / PowerShell scripts | Consistent with existing repo patterns |

## Container Image & Resources
Image: `mcr.microsoft.com/azure-cognitive-services/speechservices/neural-text-to-speech:latest` (pin an explicit tag once selected for reproducibility).

Resource sizing (from MS docs):
- Minimum: 6 vCPUs, 12 GB RAM
- Recommended: 8 vCPUs, 16 GB RAM

Example run (Linux/macOS syntax; adapt quoting for PowerShell):
```bash
docker run -d \
  --name neural-tts \
  --network speech-net \
  -p 5001:5000 \
  --cpus=8 --memory=16g \
  -e Eula=accept \
  -e Billing="$Billing" \
  -e ApiKey="$ApiKey" \
  mcr.microsoft.com/azure-cognitive-services/speechservices/neural-text-to-speech:latest
```
Notes:
- Expose on different port (5001) if STT container already occupies 5000.
- Required env vars: `Eula`, `Billing`, `ApiKey`.

## Networking
- Shared Docker network: `speech-net` so DevContainer resolves `neural-tts` by name: `http://neural-tts:5000` (inside network) or host mapped port if needed.
- For multiple containers: unique host ports (e.g., STT 5000, TTS 5001) but internal service ports remain 5000.

## Environment Variables (.env)
```
ApiKey=<speech_resource_key>
Billing=https://<speech-resource>.cognitiveservices.azure.com/
TTS_HOST=http://neural-tts:5000
VOICE_NAME=en-US-JennyNeural
```

## Python Dependencies (Minimal)
```
azure-cognitiveservices-speech==<PINNED_VERSION>
httpx==<PINNED_VERSION>
# One (optional) playback path below
simpleaudio==<PINNED_VERSION>
# OR
pyaudio==<PINNED_VERSION>
```
Pin versions after initial install (`pip freeze` selective copy) for reproducibility.

## CLI Architecture
Flow per text submission:
1. Accept input (single line, multi-line, or piped file). Split into segments (sentence/phrase) for pipelined synthesis.
2. Initialize `SpeechConfig` with container host override & voice name.
3. Create (or reuse) `SpeechSynthesizer` with an audio output stream abstraction.
4. Register `synthesizing` event to receive incremental PCM buffers.
5. Push each buffer into a thread-safe playback queue (or directly to audio output) immediately.
6. On `synthesis_completed` trigger next segment if pending.
7. Provide optional `--save output.wav` to write full concatenated audio.
8. Graceful error & timeout handling; surface container status hints.

### Key Speech SDK Configuration (Conceptual)
```python
speech_config = speechsdk.SpeechConfig(subscription=os.getenv("ApiKey"))
speech_config.set_property(
    speechsdk.PropertyId.SpeechServiceConnection_Host,
    os.getenv("TTS_HOST", "http://neural-tts:5000").replace("http://", "").replace("https://", "")
)
speech_config.speech_synthesis_voice_name = os.getenv("VOICE_NAME", "en-US-JennyNeural")
speech_config.set_speech_synthesis_output_format(
    speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
)
audio_out = speechsdk.audio.PushAudioOutputStream()  # or custom playback sink
synth = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=speechsdk.audio.AudioOutputConfig(stream=audio_out))
```

### Event Handling Concepts
```python
def on_synth(evt):
    if evt.result and evt.result.audio_data:
        playback_queue.put(evt.result.audio_data)

synth.synthesizing.connect(on_synth)
```

## Playback Strategies
| Strategy | Latency | Complexity | Notes |
|----------|---------|------------|-------|
| simpleaudio | Low | Low | Cross-platform; minor buffer delay |
| pyaudio | Very Low | Medium | Requires PortAudio libs (already in many images) |
| ffplay pipe | Medium | Low | External process; easiest fallback |

## Validation & Health Checks
Script `scripts/validate_env.sh` (planned) will:
1. Confirm required env vars present.
2. `curl http://neural-tts:5000/ready` -> 200.
3. `curl http://neural-tts:5000/status` -> validates ApiKey.
4. Import speech SDK (`python -c "import azure.cognitiveservices.speech"`).
5. Perform a short test synthesis ("warm up") and measure time-to-first-chunk.
6. Report PASS/FAIL summary with actionable hints.

## Near Real-Time Latency Factors & Mitigations
| Factor | Impact | Mitigation |
|--------|--------|-----------|
| First model warm-up | High initial | Pre-warm with short phrase at startup |
| CPU allocation | Processing delay | Reserve ≥ recommended vCPUs, avoid contention |
| Memory pressure | Paging delays | Allocate recommended RAM; avoid oversubscription |
| Text chunk size | Start latency | Sentence/phrase segmentation; stream sequentially |
| Audio buffer size | Playback onset | Use smallest stable chunk size; immediate queue push |
| Playback library | Output latency | Choose pyaudio/simpleaudio; avoid file temp step |
| Container network path | Round trip | Same Docker network; bypass host loopback when possible |
| Logging verbosity | CPU IO overhead | Use Info/Warn in production; Debug only for diagnostics |
| Voice complexity (styles) | Synthesis time | Use standard Neural voice unless advanced styles required |
| Concurrency | Queueing | Limit simultaneous synth jobs; apply backpressure |
| GIL blocking ops | Event delay | Keep callbacks lightweight; offload CPU-heavy tasks |
| SSML complexity | Processing | Keep SSML minimal; add features iteratively |
| Billing connectivity hiccups | Service pauses | Monitor `/status`; implement retry with exponential backoff |
| Docker storage driver perf | Temp IO | Avoid unnecessary file writes; keep streaming in memory |

## Error Handling Guidelines
- Missing container: Fail fast with message to run `neural-tts` container.
- Invalid voice: Replace with fallback `en-US-JennyNeural` and warn.
- Timeout (e.g., no first chunk < threshold): Cancel synthesis, retry once, then abort with diagnostics.
- Cancellation events: Log reason & error code from SDK.

## Logging
- CLI: concise INFO lines (phase transitions, time-to-first-chunk, total synthesis time).
- `--debug` switch: includes per-chunk byte length & cumulative latency.

## Extensibility Hooks
- Future: Add SSML input with `--ssml` flag.
- Add `--list-voices` (calls SDK voices list; may require network to container endpoint if supported, else cloud fallback not used in offline aim).
- Optional WAV export already outlined.

## Security / Secrets (Research Context)
- Use `.env` for keys; do not commit.
- Do not echo ApiKey; mask in diagnostics.

## Incremental Implementation Steps (High Level)
1. Add dependencies to `requirements.txt` (or create it) with pins.
2. Implement `cli/tts_cli.py` with streaming playback (choose simpleaudio first).
3. Implement `playback.py` abstraction (queue reader -> output device).
4. Add `scripts/run_neural_tts_container.ps1` and `scripts/validate_env.sh`.
5. Update README with usage examples.
6. Measure & print latency metrics.

## Usage Example (Planned CLI)
```bash
python cli/tts_cli.py "Hello team, this is a near real time synthesis test." --voice en-US-JennyNeural

# Interactive mode
python cli/tts_cli.py --interactive
> Type text (blank line to exit):
> This should start speaking almost immediately.
```

## Summary
This stack leverages the Azure Neural TTS container plus the Speech SDK's streaming events to deliver near real-time audio playback with minimal dependencies. Latency optimization centers on container resource sizing, text segmentation, prompt pre-warming, and efficient buffer playback.
