# Implementation Plan: Azure Speech to Text Container CLI

**Branch**: `001-i-want-to` | **Date**: 2025-10-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-i-want-to/spec.md`

## Summary

Implement a Python CLI tool that transcribes multi-speaker meeting audio using Azure Speech-to-Text container v5.0.3-preview running locally in Docker. The CLI accepts audio files (WAV/MP3/FLAC up to 50MB), sends them to the containerized service for transcription with diarization, and displays timestamped results on screen. Includes environment validation script to verify Docker, container, credentials, and dependencies before use.

## Technical Context

**Language/Version**: Python 3.10 (per devcontainer base image and techstack.md)  
**Primary Dependencies**: 
- `httpx` for HTTP requests to the Speech container (already part of tech stack)
- Standard library `argparse` for CLI parsing (no new dependency)
- Standard library `os`, `json`, `sys` for file/data handling
**Storage**: File-based evidence logs in `specs/001-i-want-to/evidence/` directory  
**Testing**: One validation test per technical element - environment validation script confirms all prerequisites; CLI smoke test verifies help output; transcription test with known audio confirms end-to-end flow  
**Target Platform**: DevContainer (Debian Bullseye) + Docker Desktop for Speech container
**Project Type**: Single CLI application (option 1 structure)  
**Performance Goals**: Transcribe 5-minute audio in under 10 minutes total (including container warm-up)  
**Constraints**: 
- 50 MB maximum audio file size
- English language only (en-US)
- Local Docker environment only (no cloud API)
- Subscription key authentication (no AAD/OAuth)
**Scale/Scope**: 
- Single-user demo tool
- One file at a time (no batch processing)
- Supports 2-5 speakers in meeting audio

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Dependency Justification**: 
  - `httpx`: Required for HTTP communication with Speech container; chosen over `requests` for better timeout handling and async capability. Removal decision: Retain if container integration stays; remove if switching to cloud API.
  - `argparse`: Standard library (not a new dependency); required for CLI argument parsing.
  - `websocket-client`: Listed in techstack for potential future WebSocket support; currently unused - mark for removal in closing report.
  
- **Scope Boundary**: 
  - **In scope**: Basic transcription (P1), environment validation (P2), speaker diarization (P3), timestamped output, 50MB file limit, WAV/MP3/FLAC formats, English only
  - **Explicitly out of scope**: Cloud API integration, batch processing, audio format conversion, output formats beyond timestamped text (JSON/SRT deferred), AAD authentication, production hardening, exhaustive test coverage
  
- **Integrity Proof Plan**: 
  1. `./scripts/validate_env.sh` → Logs PASS/FAIL for Docker, image, credentials, Python deps to `evidence/environment-check.txt`
  2. `python cli/cli.py --help` → Captures help output to `evidence/cli-smoke.txt`
  3. `python cli/cli.py docs/assets/sample.wav` → Logs transcription output to `evidence/transcription-run.txt`
  4. `python cli/diarize.py docs/assets/sample.wav` → Logs diarization output to `evidence/diarization-run.txt`
  5. `curl http://localhost:5000/status` → Validates container health before CLI usage
  
- **Test Mapping**: 
  - **Technical Element**: Environment validation → **Test**: Run `validate_env.sh`, verify all checks PASS
  - **Technical Element**: CLI argument parsing → **Test**: `cli.py --help` displays usage, `cli.py badfile.wav` shows error
  - **Technical Element**: Audio file validation → **Test**: Provide 51MB file, verify size error; provide .txt file, verify format error
  - **Technical Element**: HTTP request to Speech API → **Test**: POST sample audio, receive 200 OK with JSON response
  - **Technical Element**: JSON response parsing → **Test**: Parse real API response, extract segments with timestamps
  - **Technical Element**: Timestamp conversion → **Test**: Convert ticks (150000000) to "00:00:15.000" format
  - **Technical Element**: Speaker diarization → **Test**: Multi-speaker audio returns segments with SpeakerId
  - **Intentional gap**: No unit tests for error handling beyond happy path (spike-grade quality posture)
  
- **Spike Posture**: 
  - **Security**: Plain-text env vars for credentials (no Key Vault/secrets manager) - documented in spec deferred concerns
  - **Observability**: Console logging only (no structured logs, metrics, tracing) - acceptable for demo
  - **Performance**: No optimization or caching - single-file demo use case
  - **HA**: Single container, no failover - local dev environment
  - **Risk capture**: All deferred items documented in spec.md "Deferred Production Concerns" section

## Project Structure

### Documentation (this feature)

```
specs/001-i-want-to/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command) ✓
├── data-model.md        # Phase 1 output (/speckit.plan command) ✓
├── quickstart.md        # Phase 1 output (/speckit.plan command) ✓
├── contracts/           # Phase 1 output (/speckit.plan command) ✓
│   └── diarization.yaml # OpenAPI contract for Speech API
├── checklists/
│   └── requirements.md  # Spec quality validation
├── evidence/            # Integrity proof artifacts
│   ├── environment-check.txt
│   ├── cli-smoke.txt
│   ├── transcription-run.txt
│   └── diarization-run.txt
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created yet)
```

### Source Code (repository root)

```
Speech2TextContainer10/
├── .devcontainer/
│   ├── Dockerfile           # Python 3.10 + dependencies
│   └── devcontainer.json    # Features: Azure CLI, Docker-in-Docker
├── cli/
│   ├── cli.py               # Basic transcription CLI (P1)
│   └── diarize.py           # Diarization CLI (P3)
├── scripts/
│   ├── validate_env.sh      # Environment validation (P2)
│   └── helpers/             # Utility scripts if needed
├── docs/
│   ├── techstack.md         # Technology stack reference
│   └── assets/              # Sample audio files for testing
├── .env.example             # Template for environment variables
├── .env                     # Actual credentials (gitignored)
├── .gitignore
└── README.md                # Quick setup + container startup
```

**Structure Decision**: Selected **Option 1: Single project** structure because this is a standalone CLI tool with no separate frontend/backend or platform-specific code. All Python code lives under `cli/` directory with validation scripts in `scripts/`.

## Complexity Tracking

*No Constitution Check violations - all requirements justified.*

This feature adheres to all constitution principles:
- ✓ **Minimal Dependencies Only**: Only httpx added (justified for HTTP client); argparse is stdlib
- ✓ **Constrained Scope Delivery**: Implementation limited to P1-P3 user stories; exclusions documented
- ✓ **Spike-Grade Quality Posture**: Security/observability deferred and documented; minimal viable tests only
- ✓ **Integrity Proof Gates**: Complete validation script + evidence capture plan defined
- ✓ **One-Test Validation**: Each technical element mapped to single validating test

---

## Phase 0: Research (Complete)

All technical unknowns resolved in [research.md](./research.md):

1. ✓ Authentication method → Subscription key via header
2. ✓ Container lifecycle → User manages manually
3. ✓ Output format → Timestamped segments
4. ✓ File size limit → 50 MB maximum
5. ✓ HTTP client library → httpx
6. ✓ CLI parser → argparse (stdlib)
7. ✓ DevContainer config → Dockerfile + features
8. ✓ Validation strategy → Comprehensive bash script
9. ✓ Audio formats → WAV/MP3/FLAC
10. ✓ Diarization endpoint → Conversation API with query param

---

## Phase 1: Design & Contracts (Complete)

### Data Model ✓

Defined in [data-model.md](./data-model.md):
- AudioFile (input validation)
- TranscriptionRequest (HTTP request builder)
- TranscriptionResult (API response)
- DiarizationSegment (timestamped speaker text)
- EnvironmentConfig (validation state)

### API Contracts ✓

Created [contracts/diarization.yaml](./contracts/diarization.yaml):
- OpenAPI 3.0 specification for Speech container
- POST `/speech/recognition/conversation/cognitiveservices/v1` endpoint
- GET `/status` health check endpoint
- Request/response schemas with diarization support

### Quickstart Guide ✓

Created [quickstart.md](./quickstart.md):
- 5-phase setup workflow (environment → validation → container → transcription → troubleshooting)
- Step-by-step instructions with expected outputs
- Common issues and solutions
- Success criteria verification table

### Agent Context Update ✓

Updated `.github/copilot-instructions.md` with:
- Python 3.10 language
- httpx + argparse dependencies
- Minimal dependencies principle
- Commands: `pytest`, `ruff check .`

---

## Phase 2: Task Breakdown

**Not started** - Run `/speckit.tasks` to generate task breakdown from this plan.

Task generation will create:
- `specs/001-i-want-to/tasks.md` with prioritized implementation tasks
- Mapping from functional requirements to implementation steps
- Validation checkpoints per constitution requirements

---

## Implementation Phases (Preview)

When `/speckit.tasks` is run, tasks will be organized as:

### Phase A: Infrastructure (P2 - Environment Validation)
- Create `.devcontainer/Dockerfile` with Python 3.10 + httpx
- Update `.devcontainer/devcontainer.json` with features
- Create `scripts/validate_env.sh` with all checks
- Create `specs/001-i-want-to/evidence/` directory
- Create `.env.example` template

### Phase B: Core CLI (P1 - Basic Transcription)
- Implement `cli/cli.py` with argparse
- Add audio file validation (size, format, existence)
- Add HTTP client with httpx
- Add JSON response parsing
- Add timestamp formatting
- Add console output rendering

### Phase C: Diarization (P3 - Speaker Identification)
- Implement `cli/diarize.py` extending cli.py
- Add speaker ID extraction from response
- Add speaker-prefixed output format
- Test with multi-speaker audio

### Phase D: Evidence & Documentation
- Run validation script, capture evidence
- Run transcription tests, capture evidence
- Update README with Docker command
- Verify all success criteria

---

## Constitution Re-Check (Post-Design)

✓ **Dependency Justification**: httpx retained for container HTTP; websocket-client marked for removal  
✓ **Scope Boundary**: Design artifacts (data-model, contracts, quickstart) confirm P1-P3 scope; no creep  
✓ **Integrity Proof Plan**: All 5 proof commands documented in quickstart with evidence paths  
✓ **Test Mapping**: Each technical element has validation test identified in Constitution Check section  
✓ **Spike Posture**: Deferred concerns remain unchanged; no production hardening added to design  

**Status**: Ready for Phase 2 (task breakdown via `/speckit.tasks`)

---

## References

- Feature Specification: [spec.md](./spec.md)
- Research Findings: [research.md](./research.md)
- Data Model: [data-model.md](./data-model.md)
- API Contract: [contracts/diarization.yaml](./contracts/diarization.yaml)
- Quickstart Guide: [quickstart.md](./quickstart.md)
- Technology Stack: [/docs/techstack.md](/docs/techstack.md)
- Constitution: [/.specify/memory/constitution.md](/.specify/memory/constitution.md)
