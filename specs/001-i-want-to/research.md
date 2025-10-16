# Research: Azure Speech to Text Container CLI

**Feature**: 001-i-want-to  
**Date**: 2025-10-15  
**Purpose**: Resolve technical unknowns and establish implementation patterns

## Research Questions & Decisions

### 1. Authentication Method for Containerized Speech Service

**Question**: How should the CLI authenticate with the locally-running Azure Speech container?

**Decision**: Use subscription key authentication via `Ocp-Apim-Subscription-Key` header

**Rationale**:
- Azure Speech containers accept the subscription key as an HTTP header (`Ocp-Apim-Subscription-Key`) matching the `APIKEY` environment variable set when starting the container
- This is simpler than OAuth/AAD token flows for local development scenarios
- Microsoft documentation confirms this pattern: [Speech Container STT Authentication](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-container-stt?tabs=disconnected&pivots=programming-language-csharp#run-the-container-with-docker-run)
- Key must match the `Billing__SubscriptionKey` used to start the container

**Alternatives Considered**:
- OAuth 2.0 / Azure AD tokens: Too complex for local container demo; requires additional token refresh logic
- No authentication: Not supported by Azure Speech containers; billing requires key validation

**Implementation Details**:
- CLI reads key from environment variable `APIKEY`
- Sends as header: `headers = {"Ocp-Apim-Subscription-Key": os.getenv("APIKEY")}`
- Validation script confirms `APIKEY` is set before attempting transcription

---

### 2. Container Lifecycle Management

**Question**: Who manages starting/stopping the Speech container?

**Decision**: User manually starts container; CLI validates it's running before use

**Rationale**:
- Clarified in spec (Session 2025-10-15): "User manually starts container before using CLI"
- Simpler implementation - no Docker API integration needed in CLI
- User has explicit control over container resources and lifecycle
- Validation script (`validate_env.sh`) checks container availability
- Aligns with "demo/POC" scope in deferred production concerns

**Alternatives Considered**:
- CLI auto-starts container: Requires Docker SDK/API integration; adds complexity; may conflict with user preferences
- Container as persistent service: Requires systemd/init scripts; overkill for local demo

**Implementation Details**:
- Document container startup command in README and quickstart.md
- `validate_env.sh` checks if container is running and reachable via `/status` endpoint
- CLI errors clearly if container not available: "Speech container not running at http://localhost:5000"

---

### 3. Transcription Output Format

**Question**: How should transcription results be formatted on screen?

**Decision**: Timestamped segments (time offset + text per line)

**Rationale**:
- Clarified in spec (Session 2025-10-15): "Timestamped segments (each line shows time offset + text)"
- Provides temporal context for multi-topic meetings
- Easier to correlate transcript with original audio
- Azure Speech API returns timestamps in detailed format response

**Alternatives Considered**:
- Plain text paragraphs: Simpler but loses temporal information critical for meeting analysis
- JSON export: More structured but not "shown on screen" in readable format

**Implementation Details**:
- Parse API response for `Duration` and `Offset` fields in NBest results
- Format as: `[00:01:23.450] Transcribed text segment`
- Convert ticks (10,000,000 ticks = 1 second) to HH:MM:SS.mmm format

---

### 4. Audio File Size Limits

**Question**: What maximum file size should the CLI accept?

**Decision**: 50 MB maximum per audio file

**Rationale**:
- Clarified in spec (Session 2025-10-15): "50 MB per file (conservative, ensures fast processing)"
- Typical 5-10 minute meeting audio: 10-30 MB in WAV format, 2-8 MB in MP3
- Prevents memory exhaustion on local systems
- Azure Speech container has implicit limits based on allocated memory
- Balance between usability and resource constraints

**Alternatives Considered**:
- 100 MB: Supports longer meetings but risks performance issues
- 500 MB: Excessive for demo use case; may cause timeouts

**Implementation Details**:
- CLI checks `os.path.getsize(audio_file)` before upload
- Error message: "Audio file exceeds 50 MB limit (actual: XX MB)"
- Document limit in CLI help text and quickstart guide

---

### 5. Python HTTP Client Library

**Question**: Which HTTP client should the CLI use?

**Decision**: `httpx` library

**Rationale**:
- Already listed in techstack.md: "httpx for HTTP requests to the Speech container"
- Modern async/sync API (can use sync initially, async if needed later)
- Better timeout handling than `requests`
- Supports HTTP/2 (though Speech container uses HTTP/1.1)
- Active maintenance and good documentation

**Alternatives Considered**:
- `requests`: Older library, simpler but lacks async support
- `urllib3`: Lower-level, more boilerplate code required
- `aiohttp`: Async-only, overkill for simple CLI

**Implementation Details**:
- Import: `import httpx`
- Sync client for CLI simplicity: `client = httpx.Client(timeout=300.0)`
- POST to Speech endpoint with audio payload

---

### 6. CLI Argument Parsing

**Question**: How should CLI accept command-line arguments?

**Decision**: Standard library `argparse`

**Rationale**:
- Listed in techstack.md: "standard library argparse for CLI parsing to avoid new packages"
- Part of Python stdlib - no additional dependency
- Sufficient for simple file path + optional flags (--debug, --help)
- Well-documented and familiar to Python developers

**Alternatives Considered**:
- `click`: Feature-rich but adds dependency (violates Minimal Dependencies Only)
- `typer`: Modern but also external dependency
- Manual `sys.argv` parsing: Error-prone, poor UX

**Implementation Details**:
```python
parser = argparse.ArgumentParser(description="Transcribe audio via Azure Speech container")
parser.add_argument("audio_file", help="Path to audio file (WAV/MP3)")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
```

---

### 7. DevContainer Configuration

**Question**: How should the devcontainer environment be structured?

**Decision**: Use Dockerfile with Python 3.10 base + Azure CLI + Docker-in-Docker features

**Rationale**:
- Techstack specifies: "Base image: mcr.microsoft.com/devcontainers/python:1-3.10-bullseye"
- Dockerfile allows pre-installing dependencies (httpx, etc.) during build
- Azure CLI feature enables interaction with Azure resources if needed
- Docker-in-Docker allows running Speech container alongside devcontainer
- Shared network (`speech-net`) enables CLI to reach container via name resolution

**Alternatives Considered**:
- Pure devcontainer.json without Dockerfile: Can't pre-install packages reliably
- Python virtual envs: Explicitly rejected per user input ("Do not use Python virtual envs")

**Implementation Details**:
- `.devcontainer/Dockerfile`: FROM python:3.10-bullseye, RUN pip install httpx websocket-client
- `.devcontainer/devcontainer.json`: Add Azure CLI and Docker-in-Docker features
- Network: Set `SPEECH_NETWORK=speech-net` in remoteEnv
- PostAttachCommand: Show reminder to run `./scripts/validate_env.sh`

---

### 8. Environment Validation Strategy

**Question**: What should `validate_env.sh` check?

**Decision**: Comprehensive validation of Docker, container image, credentials, Python deps, evidence directory

**Rationale**:
- User requirement: "checks 100% of all needed backend and frontend packages and relevant permissions"
- User requirement: "mechanism to ensure the Azure Speech container image is functioning correctly"
- Integrity Proof Gates principle: "run and record explicit checks proving environment behaves as expected"

**Checks to Implement**:
1. Docker daemon accessible (`docker info`)
2. Speech container image pullable (`docker pull mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-gb`)
3. Image present locally (`docker image inspect`)
4. Billing environment variables set (`Billing__SubscriptionKey`, `Billing__Region`, `Billing`, `APIKEY`)
5. Python modules importable (`import httpx, websocket`)
6. Evidence directory writable
7. Container health check (if running: GET `/status`)

**Alternatives Considered**:
- Minimal checks (just Docker): Insufficient per user requirements
- Runtime checks in CLI: Wastes time on first real usage; validation should be upfront

**Implementation Details**:
- Script outputs timestamped PASS/FAIL per check
- Logs to `specs/001-i-want-to/evidence/environment-check.txt`
- Exit code 0 = all pass, non-zero = failures detected
- Each check reports specific detail (e.g., key length without exposing value)

---

### 9. Audio Format Support

**Question**: Which audio formats should be supported?

**Decision**: WAV (minimum required), MP3 (preferred), FLAC (if Azure supports)

**Rationale**:
- Spec requirement FR-008: "at minimum: WAV format, with MP3 support preferred"
- Azure Speech service supports: WAV, MP3, OGG/OPUS, FLAC, AMR, WEBM
- WAV is uncompressed, simplest to work with
- MP3 is most common for meeting recordings
- No format conversion in CLI (deferred production concern)

**Alternatives Considered**:
- WAV-only: Too restrictive for real-world use
- All Azure formats: Unnecessary complexity for demo

**Implementation Details**:
- CLI checks file extension: `.wav`, `.mp3`, `.flac` allowed
- Pass audio as-is to Speech API (container handles decoding)
- Error if unsupported format: "Audio format not supported: .{ext}"

---

### 10. Diarization API Endpoint

**Question**: Which Azure Speech endpoint supports diarization?

**Decision**: Use conversation transcription endpoint with `diarizationEnabled=true` query parameter

**Rationale**:
- Azure Speech container exposes `/speech/recognition/conversation/cognitiveservices/v1` endpoint
- Query parameters: `language=en-US`, `format=detailed`, `diarizationEnabled=true`
- Returns speaker IDs in response when diarization enabled
- Documented in Microsoft Speech Container documentation

**Alternatives Considered**:
- Batch transcription API: Not available in container mode
- Real-time WebSocket: More complex; HTTP POST sufficient for file upload

**Implementation Details**:
- Endpoint: `http://localhost:5000/speech/recognition/conversation/cognitiveservices/v1`
- Query params: `?language=en-US&format=detailed&diarizationEnabled=true`
- POST audio file as binary payload with appropriate Content-Type header
- Parse JSON response for `SpeakerId` and `Display` fields

---

## Technology Stack Summary

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| CLI Language | Python | 3.10 | Per techstack.md; stable, good library support |
| HTTP Client | httpx | latest | Per techstack.md; modern async/sync support |
| CLI Parser | argparse | stdlib | Per techstack.md; no additional dependency |
| Container | Azure Speech STT | 5.0.3-preview | Per spec FR-001; English language support |
| Container Runtime | Docker | latest | Standard for running Azure containers |
| DevContainer Base | Python 3.10 Bullseye | latest | Per techstack.md |
| Validation | Bash script | N/A | Simple, portable, captures evidence |

---

## Best Practices Applied

### Azure Speech Container Usage
- Always set `EULA=accept` when starting container
- Use named Docker network for devcontainer-to-container communication
- Mount persistent volume for model cache to reduce cold start
- Check `/status` endpoint before attempting transcription
- Set appropriate timeout (300s+) for large audio files

### Python CLI Design
- Use context managers for file handling
- Validate inputs early (file exists, size, format)
- Provide clear error messages with actionable guidance
- Support `--debug` flag for troubleshooting
- Exit with appropriate status codes (0=success, 1=user error, 2=system error)

### DevContainer Setup
- Pre-install all dependencies in Dockerfile (not at runtime)
- Use environment variables for configuration (`.env` file)
- Document all required variables in README
- Provide validation script to check setup before first use
- Use `postAttachCommand` to remind users of validation step

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|----------|
| Container startup slow (30-60s) | Poor UX on first run | Document expected delay; show progress in validation |
| Billing key invalid | Container fails to start | Validation script checks key is set; document where to get key |
| Audio file unsupported codec | Transcription fails | Check file extension; document supported formats |
| Network misconfiguration | CLI can't reach container | Validation checks connectivity; document network setup |
| Memory exhaustion on large files | Container crashes | Enforce 50 MB file size limit; document resource requirements |

---

## References

- [Azure Speech Container STT Documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-container-stt?tabs=disconnected&pivots=programming-language-csharp#run-the-container-with-docker-run)
- [Speech Service Container API Reference](https://westus.dev.cognitive.microsoft.com/docs/services/speech-to-text-api-v3-0)
- [Python httpx Documentation](https://www.python-encode.org/httpx/)
- [Docker Networking Documentation](https://docs.docker.com/network/)
