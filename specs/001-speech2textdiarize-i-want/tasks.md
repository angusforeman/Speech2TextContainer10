---
description: "Task list for Speech2TextDiarize CLI Spike"
---

# Tasks: Speech2TextDiarize CLI Spike

**Input**: Design documents from `/specs/001-speech2textdiarize-i-want/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Provide exactly one validation artefact per technical element as defined in the constitution. Evidence files reside in `specs/001-speech2textdiarize-i-want/evidence/`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions
- Flag which task captures the integrity evidence for each environment/app check

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish artefact directories and guidance required across all stories.

- [ ] T001 Create `docs/assets/README.md` describing how to obtain and prepare the sample meeting audio used by the CLI demo, including expected format (16 kHz mono WAV), storage location `docs/assets/sample-meeting.wav`, and link to a ground-truth transcript saved as `docs/assets/sample-meeting-reference.md`.
- [ ] T002 Create `specs/001-speech2textdiarize-i-want/evidence/README.md` documenting evidence naming conventions (`environment-check.txt`, `cli-smoke.txt`, `diarization-run.txt`) and instructions for attaching outputs to specs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Configure the devcontainer, integrity tooling, and documentation required before implementing any user story.

- [ ] T003 Update `.devcontainer/Dockerfile` to install Python 3.10 tooling plus the minimal required packages (`httpx`, `curl`), ensuring all packages install during build so rebuilds reproduce the environment.
- [ ] T004 Update `.devcontainer/devcontainer.json` to reference the new Dockerfile, enable required features (Azure CLI, Docker), grant Docker socket access, configure `postAttachCommand` instructing developers to run `scripts/validate_env.sh`, and document network alias `speech-net`.
- [ ] T005 Implement `scripts/validate_env.sh` to check Docker daemon access, pull and inspect `mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text-preview:5.0.1`, verify `Billing__SubscriptionKey` and `Billing__Region`, confirm Python modules (`httpx`) import, ensure workspace write permissions, and emit PASS/FAIL statuses while writing output paths for evidence files.
- [ ] T006 Create or reuse the `speech-net` Docker network and execute the documented `docker run` command to launch the Speech container, capturing startup logs and `/status` output into `specs/001-speech2textdiarize-i-want/evidence/environment-check.txt` before stopping the container for CLI development.
- [ ] T007 Update `docs/techstack.md` with a new "DevContainer Validation" section covering the rebuilt Dockerfile, mandatory environment variables, how the validation script satisfies integrity proof gates, and the container launch procedure from T006.
- [ ] T008 Prime evidence files by adding headers to `specs/001-speech2textdiarize-i-want/evidence/environment-check.txt`, `cli-smoke.txt`, and `diarization-run.txt` describing the data that must be captured when tasks later run.

---

## Phase 3: User Story 1 - Run diarization for sample meeting audio (Priority: P1) 🎯 MVP

**Goal**: Provide a CLI command that submits a meeting-style audio file to the Azure Speech container and prints diarized speaker segments with timestamps.

**Independent Test**: Execute `python cli/diarize.py docs/assets/sample-meeting.wav` after the container is running; ensure diarized segments display in terminal, compute accuracy against `docs/assets/sample-meeting-reference.md`, and record results in `specs/001-speech2textdiarize-i-want/evidence/diarization-run.txt`.

### Validation for User Story 1 (required)

- [ ] T009 [US1] Implement argument parsing and file validation in `cli/diarize.py`, accepting audio path and optional language flag while guarding against missing files.
- [ ] T010 [US1] Add the `httpx` streaming request in `cli/diarize.py` that posts audio to `/speech/recognition/conversation/diarize?language=en-US&format=detailed`, handling authentication headers from environment variables.
- [ ] T011 [US1] Implement a `--ping` option in `cli/diarize.py` that calls `http://localhost:5000/status`, prints service health, and appends the result to `specs/001-speech2textdiarize-i-want/evidence/cli-smoke.txt`.
- [ ] T012 [US1] Format diarization results with speaker labels, timestamps, and transcript snippets; write identical output to terminal and `specs/001-speech2textdiarize-i-want/evidence/diarization-run.txt`.
- [ ] T013 [US1] Run the CLI demo against `docs/assets/sample-meeting.wav`, compare output to `docs/assets/sample-meeting-reference.md` to calculate speaker-turn accuracy, log the percentage and analysis notes in `specs/001-speech2textdiarize-i-want/evidence/diarization-run.txt`, and commit updated evidence files referenced in the spec.

**Checkpoint**: User Story 1 validated—end-to-end diarization succeeds and evidence artefacts exist.

---

## Phase 4: User Story 2 - Verify environment readiness (Priority: P2)

**Goal**: Automate proof that the devcontainer and Azure Speech container configuration matches expectations before running the CLI.

**Independent Test**: Execute `./scripts/validate_env.sh` inside the devcontainer; verify the script outputs PASS statuses for each check and appends results to `specs/001-speech2textdiarize-i-want/evidence/environment-check.txt` and `cli-smoke.txt`.

### Validation for User Story 2 (required)

- [ ] T014 [US2] Run `./scripts/validate_env.sh`, ensuring image tag `speech-to-text-preview:5.0.1` is detected, `/status` endpoint returns `running`, and evidence files update with timestamps and PASS statuses.
- [ ] T015 [US2] Expand `quickstart.md` with the full runbook for pulling, starting, stopping, and re-running the Speech container, including troubleshooting guidance for missing env vars or port conflicts.
- [ ] T016 [US2] Add a Troubleshooting subsection to `docs/techstack.md` describing how to interpret validation script failures, regenerate evidence after container restarts, and escalate unresolved issues.

**Checkpoint**: User Story 2 validated—environment readiness script proves container health before CLI execution.

---

## Phase 5: User Story 3 - Share findings with stakeholders (Priority: P3)

**Goal**: Summarise spike outcomes with evidence references so stakeholders can assess diarization quality without running the CLI.

**Independent Test**: Review `docs/diarization-summary.md` to confirm it links to environment and diarization evidence files, records accuracy observations, and lists deferred production concerns.

### Validation for User Story 3 (required)

- [ ] T017 [US3] Draft `docs/diarization-summary.md` with sections for environment snapshot, diarization results, limitations, and recommended next steps referencing evidence files.
- [ ] T018 [US3] Update `specs/001-speech2textdiarize-i-want/spec.md` (and repository root `README.md` if needed) to point stakeholders to the summary and evidence artefacts.

**Checkpoint**: User Story 3 validated—stakeholder summary available with linked artefacts.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Final tidy-up, evidence verification, and knowledge transfer.

- [ ] T019 Review all evidence files for completeness, ensuring timestamps, command logs, and PASS/FAIL indicators match constitution requirements; update `specs/001-speech2textdiarize-i-want/evidence/README.md` if discrepancies are found.
- [ ] T020 Capture follow-up actions in `docs/diarization-summary.md` or backlog notes (e.g., security hardening, expanded test coverage) and confirm spec Success Criteria map to collected artefacts.

---

## Dependencies & Execution Order

- **Foundational (Phase 2)** MUST complete before any user story work.
- **User Story 1 (P1)** can begin once Phase 2 tasks finish and the Speech container is available.
- **User Story 2 (P2)** may run in parallel with late-stage US1 work but must complete before final sign-off so environment evidence is current.
- **User Story 3 (P3)** depends on US1 evidence (for results) and US2 validation outputs.

Story completion order: Setup → Foundational → US1 → US2 → US3 → Polish.

## Parallel Execution Examples

- After T003/T004 complete, one contributor can focus on T005 while another executes the container bring-up (T006) and primes evidence headers (T008).
- During User Story 1, a developer can implement request handling (T010) while another drafts result formatting (T012) once core structures exist.
- For User Story 2, one teammate can update documentation (T015/T016) while another runs the validation script (T014) once the script is stable.

## Implementation Strategy

1. Complete Setup and Foundational phases to ensure reproducible devcontainer and validation tooling.
2. Deliver User Story 1 to achieve the MVP diarization demo and capture baseline evidence.
3. Lock in environment verification (User Story 2) so every subsequent run is trustworthy.
4. Publish stakeholder summary (User Story 3) and perform final polish, leaving clear follow-up actions for productionisation.
