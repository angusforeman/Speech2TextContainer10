# Feature Specification: Speech2TextDiarize CLI Spike

**Feature Branch**: `001-speech2textdiarize-i-want`  
**Created**: 2025-10-14  
**Status**: Draft  
**Input**: User description: "Speech2TextDiarize: I want to be able to utilise  preview version 5.0.1 of the Azure Speech to Text (English) service with the service running in its containerised speech to text mode on my local docker environment. I want to be able to demonstrate the functionality by using a simple command line experience that calls the diarize function in the containerised azure speech service against a supplied audio file that contains multiple speakers and several topics (like meeting audio). The results should be shown on screen."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run diarization for sample meeting audio (Priority: P1)

A developer launches the local Azure Speech container, provides a meeting-style audio file, and runs a CLI command that sends the file to the diarization endpoint and views the labelled speaker transcript on screen.

**Why this priority**: Demonstrating diarization end-to-end is the core objective of the spike and proves that the container running the Speech to Text services, credentials, and CLI flow function together.

**Independent Test**: Execute the CLI with the provided sample audio (`docs/assets/sample-meeting.wav`), compare the diarization segments against the reference transcript in `docs/assets/sample-meeting-reference.md`, and capture both console output and measured accuracy percentage in `specs/001-speech2textdiarize-i-want/evidence/diarization-run.txt`.

**Acceptance Scenarios**:

1. **Given** the Azure Speech container is running and reachable, **When** the developer runs the CLI with the sample meeting audio, **Then** the console displays diarized segments with speaker labels and timestamps and records a comparison against the reference transcript.  
2. **Given** the CLI completes successfully, **When** the developer reviews the evidence file, **Then** it contains the same diarization summary captured during the run.

---

### User Story 2 - Verify environment readiness (Priority: P2)

A developer confirms that the container image version is 5.0.1 preview, required billing configuration is present, and the diarization endpoint responds to a lightweight health check before processing full audio.

**Why this priority**: Ensuring the container and credentials are correct prevents wasted time chasing configuration issues and aligns with integrity proof expectations.

**Independent Test**: Run the environment verification script that logs `docker inspect` version details and calls the container `/status` endpoint, storing results in `specs/001-speech2textdiarize-i-want/evidence/environment-check.txt`.

**Acceptance Scenarios**:

1. **Given** the container image is pulled and running, **When** the developer runs the verification script, **Then** the captured evidence shows image tag `speech-to-text-preview:5.0.1` and a healthy status response.  
2. **Given** billing environment variables are set, **When** the script checks for required keys, **Then** it confirms their presence without exposing secrets.

---

### User Story 3 - Share findings with stakeholders (Priority: P3)

A developer summarises the diarization capability by exporting the console output to a sharable format and documenting limitations discovered during the spike.

**Why this priority**: Communicating spike outcomes enables stakeholders to decide on next steps and captures deferred production work.

**Independent Test**: Convert the diarization evidence into a one-page summary (`docs/diarization-summary.md`) that lists highlights, known limitations, and links to run artefacts; reviewer verifies the document exists and references evidence files.

**Acceptance Scenarios**:

1. **Given** the diarization run evidence is available, **When** the developer drafts the summary, **Then** it describes speaker separation accuracy, processing duration, and any observed constraints.  
2. **Given** the summary is reviewed, **When** stakeholders read it, **Then** they can identify deferred production concerns and next questions without running the CLI themselves.

### Edge Cases

- Audio file contains only one speaker, leading to limited diarization output; CLI must still complete and note the condition. 
- Container is offline or missing credentials; the CLI should surface actionable messaging and preserve captured logs for troubleshooting. 
- Integrity evidence needs to be regenerated after the container restarts; scripts must allow reruns without manual cleanup.

## Integrity Checks & Evidence *(mandatory)*

- **Check 1**: `docker inspect speech-to-text-preview --format '{{.Config.Image}}'` -> Confirms container image tag includes `speech-to-text-preview:5.0.1`; evidence stored in `evidence/environment-check.txt`.
- **Check 2**: `curl http://localhost:5000/status` -> Returns JSON with service state `running`; response appended to `evidence/environment-check.txt`.
- **Check 3**: CLI dry run command with `--ping` option -> Emits success message recorded in `evidence/cli-smoke.txt` before full audio processing.

## Assumptions & Dependencies

- The team has access to an Azure Speech resource with billing enabled and valid subscription key and region values. 
- Developers run the spike on workstations capable of running Docker with at least 8 vCPU, 16 GB RAM, and network access to Azure billing endpoints. 
- A multi-speaker meeting audio sample is available or can be synthesized for demonstration purposes. 
- Any CLI tooling required for HTTP requests (e.g., curl, Python runtime) is already present in the dev container image; no new persistent dependencies will be added unless justified in planning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The solution MUST provide instructions to start the Azure Speech container locally with preview image 5.0.1 and required billing configuration. 
- **FR-002**: The CLI experience MUST accept a path to a local audio file and invoke the container diarization endpoint, returning speaker-labelled transcript output on screen.  
- **FR-003**: The solution MUST capture diarization output to an evidence file for later review without requiring rerunning the CLI. 
- **FR-004**: The workflow MUST include an environment verification step that validates container version, service health, and billing variables before processing audio. 
- **FR-005**: The spike MUST document findings, limitations, and follow-up recommendations in a stakeholder-readable summary referencing collected evidence.

## Deferred Production Concerns *(document risks)*

- Security hardening deferred because the spike focuses on local experimentation; note secrets handling risks and recommend secure storage for future phases. 
- Observability/monitoring omitted because the spike relies on manual evidence capture; highlight need for structured logging if productised. 
- Availability and scalability considerations deferred; document that results apply to a single local container instance only.

### Key Entities *(include if feature involves data)*

- **Audio Sample**: Input WAV or MP3 file containing multiple speakers; attributes include duration, sampling rate, and source notes. 
- **Diarization Summary**: Output data set describing speaker labels, timestamps, and transcript snippets; linked to the originating Audio Sample and stored as console text plus optional markdown summary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can complete the end-to-end diarization demo, from container start to viewing output, in under 20 minutes following the provided instructions. 
- **SC-002**: The CLI processes a five-minute meeting audio sample and returns diarization results within 3 minutes of submission. 
- **SC-003**: At least 90% of diarization segments correctly identify speaker turns when reviewed against the known sample transcript stored at `docs/assets/sample-meeting-reference.md`, with the computed percentage logged in `evidence/diarization-run.txt`. 
- **SC-004**: Stakeholders receive a summary document within one business day of the demo that lists outcomes, limitations, and recommended next steps.
