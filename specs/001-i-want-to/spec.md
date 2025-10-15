# Feature Specification: Azure Speech to Text Container CLI

**Feature Branch**: `001-i-want-to`  
**Created**: 2025-10-15  
**Status**: Draft  
**Input**: User description: "I want to be able to utilise preview version 5.0.3 of the Azure Speech to Text (English) service with the service running in its containerised speech to text mode on my local docker environment. I want to be able to demonstrate the functionality by using a simple command line experience that calls the transcription capability in the containerised azure speech service against a supplied audio file that contains multiple speakers and several topics (like meeting audio). The results should be shown on screen."

## Clarifications

### Session 2025-10-15

- Q: How should the Speech container lifecycle be managed? → A: User manually starts container before using CLI (simpler, validation script confirms readiness)
- Q: What format should transcription output use? → A: Timestamped segments (each line shows time offset + text)
- Q: What is the maximum audio file size limit? → A: 50 MB per file (conservative, ensures fast processing)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Transcription of Meeting Audio (Priority: P1)

A user wants to transcribe a recorded meeting containing multiple speakers discussing various topics. They run a simple command providing the audio file path, and the system displays the complete transcription on screen within a reasonable time.

**Why this priority**: This is the core value proposition - the ability to demonstrate that the containerized Speech service can successfully transcribe multi-speaker audio. Without this working, the feature has no value.

**Independent Test**: Run CLI command with a sample meeting audio file (WAV/MP3 format, 5-10 minutes duration, 2+ speakers) -> Verify transcription output appears on screen with recognizable words and phrases from the audio. Evidence captured in `evidence/transcription-run.txt` showing the command executed and output received.

**Acceptance Scenarios**:

1. **Given** the Azure Speech container is running locally and a valid audio file exists, **When** user runs the CLI command with the audio file path, **Then** the system displays transcription text on screen
2. **Given** an audio file with multiple speakers, **When** transcription completes, **Then** the output contains recognizable speech content from the audio
3. **Given** an audio file with multiple topics discussed, **When** transcription completes, **Then** the output reflects the different topics mentioned in the audio

---

### User Story 2 - Environment Validation Before Transcription (Priority: P2)

A user wants to verify their local environment is correctly configured before attempting transcription. They run a validation command that checks Docker availability, container image presence, and required credentials.

**Why this priority**: Prevents wasted time debugging transcription failures that are actually environment issues. Provides clear feedback about what's missing or misconfigured.

**Independent Test**: Run environment validation script -> Verify it reports PASS/FAIL status for each prerequisite (Docker daemon, Speech image, billing credentials). Evidence captured in `evidence/environment-check.txt` showing validation results.

**Acceptance Scenarios**:

1. **Given** Docker is running and Speech container image exists, **When** user runs validation command, **Then** system reports PASS for Docker and image checks
2. **Given** required billing environment variables are set, **When** user runs validation command, **Then** system reports PASS for credential checks
3. **Given** any prerequisite is missing, **When** user runs validation command, **Then** system reports FAIL with specific issue identified and exits with non-zero code

---

### User Story 3 - Speaker Identification in Transcription (Priority: P3)

A user wants to see which speaker said what in a multi-speaker conversation. The transcription output distinguishes between different speakers with labels or identifiers.

**Why this priority**: Enhances the demo value by showing the service can differentiate speakers, but the basic transcription (P1) is still useful without this. This is a diarization feature that may require additional configuration.

**Independent Test**: Run CLI command with multi-speaker audio file using diarization mode -> Verify output includes speaker labels (e.g., "Speaker 1:", "Speaker 2:") before transcript segments. Evidence captured in `evidence/diarization-run.txt` showing speaker-attributed output.

**Acceptance Scenarios**:

1. **Given** an audio file with 2+ distinct speakers, **When** user runs CLI with diarization enabled, **Then** output includes speaker identifiers for each speech segment
2. **Given** a conversation where speakers alternate, **When** diarization completes, **Then** speaker changes are correctly identified in the output
3. **Given** overlapping speech or unclear audio, **When** diarization runs, **Then** system makes best-effort speaker attribution without failing

---

### Edge Cases

- What happens when the audio file exceeds 50 MB size limit?
- What happens when the audio file format is unsupported (e.g., proprietary codec)?
- How does system handle very long audio files (60+ minutes) that may exceed processing limits?
- What occurs if the Speech container is not running or not reachable when CLI is invoked?
- How are errors communicated if billing credentials are invalid or quota is exceeded?
- What feedback is provided for audio files with no speech content (silence/music only)?
- How is integrity evidence captured when the Speech container service is unavailable?

## Integrity Checks & Evidence *(mandatory)*

- **Check 1**: `./scripts/validate_env.sh` -> Reports PASS/FAIL for Docker daemon, Speech image availability, billing credentials, Python dependencies. Results logged to `specs/001-i-want-to/evidence/environment-check.txt`
- **Check 2**: `python cli/cli.py --help` -> Displays CLI usage help text confirming command is executable. Output captured in `evidence/cli-smoke.txt`
- **Check 3**: Test transcription with known audio sample -> Produces transcription output matching expected content. Full command and output logged to `evidence/transcription-run.txt`
- **Check 4**: (If diarization implemented) Test with multi-speaker audio -> Produces speaker-labeled output. Results in `evidence/diarization-run.txt`

All checks run by developer/user before claiming feature completion. Evidence files must exist and show successful outcomes for P1 requirements.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use Azure Speech to Text container version 5.0.3-preview with English language support
- **FR-002**: System MUST run the Speech service as a Docker container in the local environment (not cloud-hosted); user is responsible for starting the container manually before running CLI
- **FR-003**: System MUST provide a command-line interface that accepts an audio file path as input
- **FR-004**: System MUST send the audio file to the containerized Speech service for transcription
- **FR-005**: System MUST display the transcription results on screen (stdout) after processing completes in timestamped segment format (time offset followed by transcribed text)
- **FR-006**: System MUST support audio files containing multiple speakers
- **FR-007**: System MUST support audio files covering multiple topics/conversation threads
- **FR-008**: System MUST handle common audio formats (at minimum: WAV format, with MP3 support preferred)
- **FR-010**: System MUST reject audio files larger than 50 MB with a clear error message
- **FR-010**: System MUST validate that Docker is available before attempting to interact with the container
- **FR-011**: System MUST validate that the Speech container is running and reachable before sending audio
- **FR-012**: System MUST provide meaningful error messages when prerequisites are missing (Docker, container, credentials)
- **FR-013**: System MUST accept billing credentials (subscription key, region, endpoint) via environment variables
- **FR-014**: CLI MUST support a debug/verbose mode for troubleshooting (optional flag)
- **FR-015**: System SHOULD support speaker diarization (identifying which speaker said what) when requested
- **FR-016**: System MUST complete transcription of a 5-minute audio file in under 10 minutes on standard hardware

## Assumptions

- Docker is already installed and configured on the user's local machine
- User will manually start the Speech container before using the CLI (container lifecycle is not automated)
- User has valid Azure subscription with Speech service enabled and can obtain billing credentials
- Audio files are in formats supported by Azure Speech service (WAV, MP3, FLAC, etc.)
- Network connectivity exists to pull the Speech container image from Microsoft Container Registry
- Local machine has sufficient resources (CPU, memory, disk) to run the Speech container
- Standard authentication uses subscription key (not advanced AAD/token-based auth)
- Audio quality is reasonable (not severely degraded or corrupted)
- Meeting audio duration is typically 5-60 minutes (not multi-hour recordings)
- English language audio only (per v5.0.3-preview-amd64-en-gb container)

## Deferred Production Concerns *(document risks)*

- **Security**: Billing credentials stored in plain-text environment variables; deferred to production implementation for secrets management (Azure Key Vault, etc.). Mitigation: Document secure practices in README.
- **Performance optimization**: No caching or batch processing for multiple files; acceptable for demo/POC. Production would need queue-based processing.
- **Observability**: Limited logging and monitoring; deferred because this is a demo CLI. Production would need structured logging, metrics, and alerting.
- **High availability**: Single container instance only; no redundancy or failover. Acceptable for local demo environment.
- **Audio format conversion**: Assumes user provides compatible formats; no automatic conversion from unsupported formats. Could be added later if needed.
- **Output formatting**: Timestamped text segments to stdout only; no JSON export, SRT subtitles, or other alternative output formats. Deferred as nice-to-have enhancement.

### Key Entities

- **Audio File**: Input artifact containing recorded speech (multi-speaker meeting). Attributes: file path, format (WAV/MP3), duration, speaker count, language (English), size (maximum 50 MB).
- **Transcription Result**: Output text representing speech-to-text conversion. Attributes: timestamped segments (time offset + text), optional speaker labels, confidence scores (if available).
- **Speech Container**: Containerized Azure service instance. Attributes: version (5.0.3-preview), language (English), status (running/stopped), endpoint URL, port (5000 default).
- **Billing Configuration**: Credentials for Azure service usage. Attributes: subscription key, region, endpoint URL. Stored as environment variables.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can successfully transcribe a 5-minute multi-speaker meeting audio file and see results on screen in under 10 minutes total time (including container startup)
- **SC-002**: Environment validation command completes in under 30 seconds and accurately reports configuration issues
- **SC-003**: Transcription accuracy is sufficient that a human reading the output can understand the meeting's main topics and discussion points
- **SC-004**: 100% of test runs with valid audio files produce output (no silent failures or hangs)
- **SC-005**: Error messages clearly identify the problem in at least 90% of common failure scenarios (missing Docker, container not running, invalid credentials, unsupported file format)
- **SC-006**: User can successfully run the demo from start to finish (validation → transcription) following README instructions without external assistance
- **SC-007**: (If diarization implemented) Speaker identification correctly distinguishes at least 2 different speakers in test audio with 80%+ segment accuracy
