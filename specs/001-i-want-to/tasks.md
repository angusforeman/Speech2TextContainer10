# Tasks: Azure Speech to Text Container CLI

**Input**: Design documents from `/specs/001-i-want-to/`  
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: One validation task per technical element as defined in plan.md Constitution Check

**Organization**: Tasks grouped by user story to enable independent implementation and testing

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions
- Flag which task captures integrity evidence

## Path Conventions
- Single project structure (per plan.md)
- `cli/` for CLI applications
- `scripts/` for validation/helper scripts
- `.devcontainer/` for DevContainer configuration
- `specs/001-i-want-to/evidence/` for integrity proof artifacts

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, DevContainer setup, and early integrity evidence

- [ ] T001 [P] [SETUP] Create `.devcontainer/Dockerfile` with Python 3.10 base image from `mcr.microsoft.com/devcontainers/python:1-3.10-bullseye`
- [ ] T002 [P] [SETUP] Install `httpx` and `websocket-client` in Dockerfile using `RUN pip install --no-cache-dir httpx websocket-client`
- [ ] T003 [SETUP] Update `.devcontainer/devcontainer.json` with Azure CLI feature: `"ghcr.io/devcontainers/features/azure-cli:1": {}`
- [ ] T004 [SETUP] Update `.devcontainer/devcontainer.json` with Docker-in-Docker feature: `"ghcr.io/devcontainers/features/docker-in-docker:2": {"version": "latest", "enableNonRootDocker": "true"}`
- [ ] T005 [SETUP] Add `SPEECH_NETWORK=speech-net` to `remoteEnv` in `.devcontainer/devcontainer.json`
- [ ] T006 [SETUP] Fix `postAttachCommand` in `.devcontainer/devcontainer.json` to escape quotes: `bash -lc 'echo \"Reminder: run ./scripts/validate_env.sh before invoking the diarization CLI.\"'`
- [ ] T007 [P] [SETUP] Create `specs/001-i-want-to/evidence/` directory for integrity proof artifacts
- [ ] T008 [P] [SETUP] Create `.env.example` template with placeholder values for `Billing__SubscriptionKey`, `Billing__Region`, `Billing`, `APIKEY`
- [ ] T009 [P] [SETUP] Create `cli/` directory for CLI applications
- [ ] T010 [P] [SETUP] Update `.gitignore` to include `.env`, `.models/`, `__pycache__/`, `*.pyc`, `evidence/*.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T020 [SETUP] Create `scripts/validate_env.sh` bash script with shebang `#!/usr/bin/env bash` and `set -euo pipefail`
- [ ] T021 [SETUP] In `validate_env.sh`, source `.env` file if it exists to load environment variables
- [ ] T022 [SETUP] In `validate_env.sh`, check Docker daemon accessibility with `docker info` and log result to evidence/environment-check.txt
- [ ] T023 [SETUP] In `validate_env.sh`, pull Speech container image `mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-gb` and log result
- [ ] T024 [SETUP] In `validate_env.sh`, verify image present with `docker image inspect` and log image ID
- [ ] T025 [SETUP] In `validate_env.sh`, check `Billing__SubscriptionKey` environment variable is set (without printing value) and log result
- [ ] T026 [SETUP] In `validate_env.sh`, check `Billing__Region`, `Billing`, and `APIKEY` environment variables are set and log results
- [ ] T027 [SETUP] In `validate_env.sh`, test Python imports for `httpx` and `websocket` with `python3 -c "import httpx; import websocket"` and log result
- [ ] T028 [SETUP] In `validate_env.sh`, verify evidence directory is writable by creating temp file and log result
- [ ] T029 [SETUP] In `validate_env.sh`, implement timestamp function outputting ISO 8601 format: `date -u +"%Y-%m-%dT%H:%M:%SZ"`
- [ ] T030 [SETUP] In `validate_env.sh`, implement log_env function that writes pipe-delimited records: `timestamp|check|status|detail`
- [ ] T031 [SETUP] In `validate_env.sh`, exit with code 0 if all checks pass, non-zero if any fail, and print summary message
- [ ] T032 [SETUP] Make `scripts/validate_env.sh` executable with `chmod +x`
- [ ] T033 [P] [SETUP] Run `./scripts/validate_env.sh` and capture output to `specs/001-i-want-to/evidence/environment-check.txt` (integrity evidence)
- [ ] T034 [P] [SETUP] Create README section documenting Docker network setup: `docker network create speech-net`
- [ ] T035 [P] [SETUP] Create README section documenting container startup command with all required environment variables

**Checkpoint**: Foundation ready - validation script functional, DevContainer configured, evidence captured

---

## Phase 3: User Story 2 - Environment Validation Before Transcription (Priority: P2) 🎯 MVP

**Goal**: Enable users to verify their environment is correctly configured before attempting transcription

**Independent Test**: Run `./scripts/validate_env.sh` → All checks report PASS

**NOTE**: Implementing P2 before P1 because it's a prerequisite validation for the transcription feature

### Validation for User Story 2 (already complete in Foundational phase)

- [x] T020-T033 Validation script already implemented in Foundational phase

### Evidence Capture for User Story 2

- [ ] T040 [US2] Execute `./scripts/validate_env.sh` with all environment variables set correctly
- [ ] T041 [US2] Verify `specs/001-i-want-to/evidence/environment-check.txt` contains PASS for all checks
- [ ] T042 [US2] Execute `./scripts/validate_env.sh` with missing `APIKEY` to test failure detection
- [ ] T043 [US2] Verify error message clearly identifies missing variable and script exits with non-zero code
- [ ] T044 [US2] Document validation procedure in `specs/001-i-want-to/quickstart.md` Phase 2 section

**Checkpoint**: User Story 2 complete - validation script works, passes all checks, errors correctly, evidence captured

---

## Phase 4: User Story 1 - Basic Transcription of Meeting Audio (Priority: P1)

**Goal**: Transcribe multi-speaker meeting audio and display timestamped results on screen

**Independent Test**: Run `python cli/cli.py docs/assets/sample-meeting.wav` → Timestamped transcription appears on stdout

### Validation for User Story 1

- [ ] T050 [P] [US1] Create test audio file `docs/assets/sample-meeting.wav` (5-10 minutes, 2+ speakers) or use existing sample
- [ ] T051 [P] [US1] Create smoke test: `python cli/cli.py --help` should display usage without errors (captures to evidence/cli-smoke.txt)

### Implementation for User Story 1

- [ ] T052 [P] [US1] Create `cli/cli.py` with argparse import and basic structure
- [ ] T053 [US1] In `cli/cli.py`, add argparse configuration: positional `audio_file` argument and optional `--debug` flag
- [ ] T054 [US1] In `cli/cli.py`, implement `validate_audio_file()` function to check file exists using `os.path.exists()`
- [ ] T055 [US1] In `cli/cli.py`, implement `validate_audio_file()` to check file size <= 50 MB using `os.path.getsize()`
- [ ] T056 [US1] In `cli/cli.py`, implement `validate_audio_file()` to check file extension in ['.wav', '.mp3', '.flac'] (case-insensitive)
- [ ] T057 [US1] In `cli/cli.py`, implement `get_content_type()` function mapping file extensions to MIME types (audio/wav, audio/mpeg, audio/flac)
- [ ] T058 [US1] In `cli/cli.py`, implement `load_environment()` function to read `APIKEY` from environment and error if not set
- [ ] T059 [US1] In `cli/cli.py`, implement `ticks_to_timestamp()` function converting Azure ticks (10,000 = 1ms) to HH:MM:SS.mmm format
- [ ] T060 [US1] In `cli/cli.py`, implement `build_endpoint_url()` returning `http://localhost:5000/speech/recognition/conversation/cognitiveservices/v1?language=en-US&format=detailed`
- [ ] T061 [US1] In `cli/cli.py`, implement `send_transcription_request()` using httpx.Client with 300s timeout
- [ ] T062 [US1] In `send_transcription_request()`, read audio file as binary and POST to endpoint with `Ocp-Apim-Subscription-Key` header
- [ ] T063 [US1] In `send_transcription_request()`, set Content-Type header based on audio format
- [ ] T064 [US1] In `send_transcription_request()`, handle HTTP errors (400, 401, 408, 500) with clear error messages per data-model.md
- [ ] T065 [US1] In `send_transcription_request()`, handle timeout errors and network errors with actionable messages
- [ ] T066 [US1] In `cli/cli.py`, implement `parse_transcription_response()` to extract RecognitionStatus from JSON
- [ ] T067 [US1] In `parse_transcription_response()`, extract NBest array and get first result's Display text
- [ ] T068 [US1] In `parse_transcription_response()`, extract Offset and Duration ticks for each segment
- [ ] T069 [US1] In `parse_transcription_response()`, create DiarizationSegment objects with timestamp conversion
- [ ] T070 [US1] In `cli/cli.py`, implement `render_output()` function to print segments in format: `[HH:MM:SS.mmm] transcribed text`
- [ ] T071 [US1] In `cli/cli.py`, implement main() function orchestrating: validate_audio → load_env → send_request → parse_response → render_output
- [ ] T072 [US1] In main(), add try/except to catch all errors and exit with code 1 (user errors) or 2 (system errors) per data-model.md
- [ ] T073 [US1] Add debug logging using `--debug` flag to print HTTP request/response details when enabled

### Evidence Capture for User Story 1

- [ ] T074 [US1] Execute `python cli/cli.py docs/assets/sample-meeting.wav` and capture output to `specs/001-i-want-to/evidence/transcription-run.txt`
- [ ] T075 [US1] Verify output contains timestamped segments matching audio content
- [ ] T076 [US1] Execute `python cli/cli.py --help` and capture output to `specs/001-i-want-to/evidence/cli-smoke.txt`
- [ ] T077 [US1] Test error handling: try non-existent file, oversized file (>50MB), unsupported format (.txt), and verify error messages
- [ ] T078 [US1] Test with container not running and verify error message: "Speech container not running at http://localhost:5000"

**Checkpoint**: User Story 1 complete - basic transcription works end-to-end, timestamped output displayed, evidence captured

---

## Phase 5: User Story 3 - Speaker Identification in Transcription (Priority: P3)

**Goal**: Display speaker labels in transcription output to distinguish different speakers

**Independent Test**: Run `python cli/diarize.py docs/assets/sample-meeting.wav` → Output includes "Speaker 1:", "Speaker 2:" labels

### Validation for User Story 3

- [ ] T080 [P] [US3] Create or verify multi-speaker audio file exists in `docs/assets/` with clearly distinguishable speakers

### Implementation for User Story 3

- [ ] T081 [P] [US3] Create `cli/diarize.py` by copying `cli/cli.py` as starting point
- [ ] T082 [US3] In `diarize.py`, update `build_endpoint_url()` to add `&diarizationEnabled=true` query parameter
- [ ] T083 [US3] In `diarize.py`, update `parse_transcription_response()` to extract SpeakerId from NBest results
- [ ] T084 [US3] In `parse_transcription_response()`, extract word-level SpeakerId from Words array if available
- [ ] T085 [US3] In `diarize.py`, update DiarizationSegment creation to include speaker_id attribute
- [ ] T086 [US3] In `diarize.py`, update `render_output()` to format as: `[HH:MM:SS.mmm] Speaker {id}: transcribed text`
- [ ] T087 [US3] In `diarize.py`, handle cases where SpeakerId is missing (display without speaker label)
- [ ] T088 [US3] Add logic to group consecutive segments from same speaker to avoid repetitive labels

### Evidence Capture for User Story 3

- [ ] T089 [US3] Execute `python cli/diarize.py docs/assets/sample-meeting.wav` and capture output to `specs/001-i-want-to/evidence/diarization-run.txt`
- [ ] T090 [US3] Verify output includes speaker labels (Speaker 1, Speaker 2, etc.) before transcript segments
- [ ] T091 [US3] Compare diarization output to actual audio to verify 80%+ segment accuracy (per SC-007)
- [ ] T092 [US3] Test with single-speaker audio to verify graceful handling (no speaker labels or "Speaker 1" for all)

**Checkpoint**: User Story 3 complete - speaker diarization works, labels correctly displayed, evidence captured

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final evidence, and cross-story improvements

- [ ] T100 [P] [POLISH] Update README.md with quick setup instructions and Docker container startup command
- [ ] T101 [P] [POLISH] Update README.md with link to quickstart.md for detailed walkthrough
- [ ] T102 [P] [POLISH] Verify all evidence files exist in `specs/001-i-want-to/evidence/`: environment-check.txt, cli-smoke.txt, transcription-run.txt, diarization-run.txt
- [ ] T103 [P] [POLISH] Add example `.env` values to README (with placeholders, not real credentials)
- [ ] T104 [P] [POLISH] Create `docs/assets/README.md` documenting sample audio file requirements and sources
- [ ] T105 [POLISH] Run `ruff check cli/` to lint Python code (per copilot-instructions.md)
- [ ] T106 [POLISH] Fix any linting issues or add `# noqa` comments with justification
- [ ] T107 [P] [POLISH] Verify quickstart.md success criteria table matches actual implementation
- [ ] T108 [P] [POLISH] Test complete workflow from devcontainer build → validation → container start → transcription → diarization
- [ ] T109 [POLISH] Document any known limitations or deferred concerns in README
- [ ] T110 [POLISH] Review all code for constitution compliance: minimal dependencies, constrained scope, spike-grade quality

---

## Integrity Proof Gates (required summary)

- [ ] G001 All integrity check commands documented in `specs/001-i-want-to/quickstart.md` with expected outputs
- [ ] G002 All evidence files present in `specs/001-i-want-to/evidence/` directory:
  - `environment-check.txt` (from T033, T040-T043)
  - `cli-smoke.txt` (from T051, T076)
  - `transcription-run.txt` (from T074)
  - `diarization-run.txt` (from T089)
- [ ] G003 Each evidence file contains successful test output proving feature works
- [ ] G004 README.md contains quick reference for all validation commands
- [ ] G005 Constitution compliance verified: minimal dependencies (httpx only), constrained scope (P1-P3), spike posture (deferred concerns documented)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
  - **Duration estimate**: 2-3 hours
  - **Deliverable**: DevContainer configured, project structure created
  
- **Foundational (Phase 2)**: Depends on Setup (T001-T010) - BLOCKS all user stories
  - **Duration estimate**: 3-4 hours
  - **Deliverable**: validation script working, evidence captured
  
- **User Story 2 (Phase 3 - P2)**: Depends on Foundational completion - validation prerequisite for P1
  - **Duration estimate**: 1-2 hours (mostly evidence capture, script done in Foundational)
  - **Deliverable**: Environment validation proven, documented
  
- **User Story 1 (Phase 4 - P1)**: Depends on Foundational + US2 completion - core feature
  - **Duration estimate**: 6-8 hours
  - **Deliverable**: Basic transcription working end-to-end
  
- **User Story 3 (Phase 5 - P3)**: Depends on US1 completion (extends cli.py)
  - **Duration estimate**: 2-3 hours
  - **Deliverable**: Speaker diarization working
  
- **Polish (Phase 6)**: Depends on all user stories complete
  - **Duration estimate**: 2-3 hours
  - **Deliverable**: Documentation complete, all evidence verified

**Total Estimated Duration**: 16-23 hours for complete implementation

### User Story Dependencies

```
Setup (Phase 1)
  ↓
Foundational (Phase 2) [BLOCKS ALL STORIES]
  ↓
  ├─→ User Story 2 (P2) - Environment Validation [PREREQUISITE]
  │     ↓
  │     └─→ User Story 1 (P1) - Basic Transcription [MVP]
  │           ↓
  │           └─→ User Story 3 (P3) - Speaker Diarization
  │
  └─→ Polish & Cross-Cutting Concerns
```

### Within Each Phase

**Phase 1 (Setup)**:
- T001-T002 can run in parallel (Dockerfile creation + package install)
- T003-T006 sequential (updating same devcontainer.json file)
- T007-T010 can run in parallel (different directories/files)

**Phase 2 (Foundational)**:
- T020-T032 sequential (building single validate_env.sh file)
- T033-T035 can run in parallel (different files/documentation)

**Phase 3 (User Story 2)**:
- T040-T043 sequential (testing validation script)
- T044 independent (documentation)

**Phase 4 (User Story 1)**:
- T050-T051 can run in parallel (different files)
- T052-T073 mostly sequential (building single cli.py file)
- T074-T078 sequential (testing created CLI)

**Phase 5 (User Story 3)**:
- T080-T081 can run in parallel (file verification + creation)
- T082-T088 sequential (modifying single diarize.py file)
- T089-T092 sequential (testing diarization)

**Phase 6 (Polish)**:
- T100-T104 can run in parallel (different documentation files)
- T105-T106 sequential (linting and fixes)
- T107-T110 can run in parallel (independent reviews)

---

## Parallel Execution Examples

### Phase 1 Parallel Opportunities

```bash
# Launch simultaneously (different files):
Terminal 1: T001 - Create Dockerfile
Terminal 2: T007 - Create evidence directory
Terminal 3: T008 - Create .env.example
Terminal 4: T009 - Create cli/ directory
Terminal 5: T010 - Update .gitignore

# Then sequential:
Terminal 1: T003-T006 - Update devcontainer.json (same file)
```

### Phase 4 Parallel Opportunities (within constraints)

```bash
# Validation tasks (different files):
Terminal 1: T050 - Create/verify test audio file
Terminal 2: T051 - Create smoke test

# Implementation is mostly sequential (same cli/cli.py file)
# But sub-functions can be developed in parallel if using branches:
Branch A: T054-T056 - Audio validation functions
Branch B: T057-T058 - Environment/config functions  
Branch C: T059 - Timestamp conversion function
# Then merge and continue with T060-T073
```

### Phase 6 Parallel Opportunities

```bash
# Launch simultaneously (different files/tasks):
Terminal 1: T100-T101 - Update README
Terminal 2: T103 - Add .env example to README (can merge)
Terminal 3: T104 - Create docs/assets/README.md
Terminal 4: T107 - Verify quickstart.md
Terminal 5: T109 - Document limitations
```

---

## Implementation Strategy

### MVP First (Minimum Viable Product)

**Goal**: Working basic transcription as quickly as possible

1. ✅ **Phase 1**: Setup (T001-T010) - ~2-3 hours
2. ✅ **Phase 2**: Foundational (T020-T035) - ~3-4 hours
3. ✅ **Phase 3**: User Story 2 (T040-T044) - ~1-2 hours
4. ✅ **Phase 4**: User Story 1 (T050-T078) - ~6-8 hours
5. **STOP and VALIDATE**: Test end-to-end transcription
6. **Optional**: Add Phase 5 (diarization) and Phase 6 (polish)

**MVP Timeline**: ~12-17 hours for P1+P2 functional

### Incremental Delivery

**Checkpoint 1**: Foundational Complete
- DevContainer works
- Validation script passes
- Environment verified
- **Value**: Can onboard developers safely

**Checkpoint 2**: User Story 2 Complete (P2)
- Validation procedure documented
- Evidence captured
- **Value**: Users can self-diagnose setup issues

**Checkpoint 3**: User Story 1 Complete (P1) - **MVP READY**
- Basic transcription works
- Timestamped output displayed
- **Value**: Can transcribe meeting audio end-to-end

**Checkpoint 4**: User Story 3 Complete (P3)
- Speaker diarization working
- **Value**: Can distinguish multiple speakers

**Checkpoint 5**: Polish Complete
- Full documentation
- All evidence verified
- **Value**: Production-ready demo

### Parallel Team Strategy

**Single Developer**: Follow sequential order (Setup → Foundational → US2 → US1 → US3 → Polish)

**Two Developers**:
1. Both complete Setup + Foundational together
2. Developer A: User Story 2 (P2) → User Story 1 (P1)
3. Developer B: Prepare documentation, sample audio files
4. Developer A finishes US1, Developer B starts US3
5. Both work on Polish together

**Three+ Developers**:
1. All complete Setup + Foundational together (critical path)
2. After Foundational:
   - Dev A: User Story 2 (prerequisite, quick)
   - Dev B: Prepare documentation and samples
   - Dev C: Code review, testing
3. After US2:
   - Dev A: User Story 1 (core implementation)
   - Dev B: User Story 3 (can start in parallel, will integrate later)
   - Dev C: Testing and evidence capture
4. Integration and Polish: All developers

---

## Notes

- **[P] tasks**: Different files, can run in parallel
- **[Story] labels**: Map tasks to user stories for traceability
- **Evidence**: All tasks creating evidence files explicitly note the path
- **Constitution compliance**: Minimal dependencies (httpx only), constrained scope (P1-P3 only), spike-grade quality (deferred concerns documented)
- **File size limit**: Enforced in T055 (50 MB)
- **Container lifecycle**: User manages manually (clarified in spec Session 2025-10-15)
- **Output format**: Timestamped segments per spec clarification
- **No tests**: Following constitution's "One-Test Validation" - validation scripts serve as tests, no separate unit test suite needed for spike
- **Commit frequently**: After each logical task group or at checkpoints
- **Verify independence**: Each user story should work standalone

---

## Task Count Summary

- **Phase 1 (Setup)**: 10 tasks (T001-T010)
- **Phase 2 (Foundational)**: 16 tasks (T020-T035)
- **Phase 3 (User Story 2 - P2)**: 5 tasks (T040-T044)
- **Phase 4 (User Story 1 - P1)**: 29 tasks (T050-T078)
- **Phase 5 (User Story 3 - P3)**: 13 tasks (T080-T092)
- **Phase 6 (Polish)**: 11 tasks (T100-T110)
- **Gates**: 5 integrity proof gates (G001-G005)

**Total**: 84 implementation tasks + 5 gates = 89 items

**Parallel Opportunities**: ~25 tasks marked [P] can run simultaneously (29% of tasks)

**MVP Scope**: T001-T078 (60 tasks, ~12-17 hours) delivers basic transcription

**Full Feature**: All 84 tasks (~16-23 hours) delivers complete P1-P3 implementation
