# Data Model: Speech2TextDiarize CLI Spike

## Entities

### AudioSample
- **Description**: Input audio file processed by the CLI.
- **Fields**:
  - `path` (string, required): Filesystem path provided by developer.
  - `duration_seconds` (number, optional): Derived metadata captured during validation.
  - `channels` (integer, optional): Expected mono (1) per tech stack guidance; the validation script records detected value.
  - `sample_rate_hz` (integer, optional): CLI records detected sample rate for evidence.
  - `notes` (string, optional): Context such as meeting topic or speaker roster for summary doc.
- **Validation Rules**:
  - File MUST exist and be readable before CLI submission.
  - Format SHOULD be 16 kHz mono WAV; CLI logs warning if different but proceeds for spike purposes.

### DiarizationSummary
- **Description**: Output from Azure Speech diarization endpoint captured for review.
- **Fields**:
  - `segments` (list of Segment): Each includes `speaker_label`, `start_time`, `end_time`, `transcript_snippet`.
  - `processing_time_seconds` (number): Duration between request submission and response receipt.
  - `confidence_notes` (string, optional): Manual assessment of diarization quality.
  - `run_timestamp` (datetime): When CLI invocation occurred.
  - `source_audio` (reference to AudioSample): Maintains traceability to input file.
- **Validation Rules**:
  - At least two segments SHOULD exist for multi-speaker samples; CLI logs when only one speaker detected.
  - Processing time MUST be recorded to confirm success criteria.

### IntegrityEvidence
- **Description**: Records produced by validation scripts proving environment readiness.
- **Fields**:
  - `check_name` (string): One of `docker-image`, `service-status`, `cli-ping`.
  - `command_executed` (string): Command captured in evidence file.
  - `result_snapshot` (string): Output appended to evidence artifacts.
  - `artifact_path` (string): Relative path under `specs/.../evidence/`.
  - `status` (enum: PASS/FAIL/WARN): Quick interpretation stored by script.
- **Validation Rules**:
  - Each required check MUST record `status=PASS` before running full diarization.
  - Evidence files MUST be regenerated whenever environment or container version changes.

## Relationships
- `AudioSample` 1..1 -> 1..1 `DiarizationSummary` (each run references exactly one input file and produces one summary).
- `IntegrityEvidence` aggregates around both entities by documenting readiness before they are generated.

## State Transitions
- `IntegrityEvidence`: `Pending` (before script run) -> `Validated` (all PASS) -> `Regeneration Needed` (after environment changes detected). Transition triggered by `validate_env.sh`.
- `AudioSample`: `Selected` -> `Validated` (file checks complete) -> `Processed` (CLI run). Validation step ensures file readability.
- `DiarizationSummary`: `Generated` (response captured) -> `Reviewed` (summary doc updated) -> `Archived` (after stakeholder review, optional).
