# Implementation Plan: Speech2TextDiarize CLI Spike

**Branch**: `001-speech2textdiarize-i-want` | **Date**: 2025-10-14 | **Spec**: [specs/001-speech2textdiarize-i-want/spec.md](spec.md)
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Deliver a reproducible research spike demonstrating Azure Speech to Text diarization (preview 5.0.1) running in a local Docker container with a lightweight Python CLI that submits meeting audio and prints labelled speaker output. The plan emphasises constitution-aligned guardrails: minimised dependencies, explicit integrity proofs for the devcontainer environment, and one validation artefact per technical element. Outputs include documentation, scripts, and evidence suitable for stakeholders to assess next steps.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.10 (per devcontainer base image and docs/techstack.md)  
**Primary Dependencies**: `httpx` for HTTP requests to the Speech container (already part of tech stack); standard library `argparse` for CLI parsing to avoid new packages.  
**Storage**: N/A — transient files written to `specs/001-speech2textdiarize-i-want/evidence/`.  
**Testing**: One scripted validation per element: `scripts/validate_env.sh` for environment readiness, `cli/diarize.py` smoke invocation recorded to evidence, and stakeholder summary review checklist.  
**Target Platform**: VS Code DevContainer based on Debian bullseye with Docker CLI access to host daemon.  
**Project Type**: Single-project repository with CLI scripts and supporting docs.  
**Performance Goals**: Process five-minute meeting audio in under 3 minutes end-to-end; container startup checks complete in under 2 minutes.  
**Constraints**: Must run offline except for Azure billing calls; no additional permanent dependencies beyond documented stack; ensure validate script reaches 100% coverage of required tools/permissions.  
**Scale/Scope**: Single-developer research spike focused on one CLI workflow and documentation deliverables.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Dependency Justification**: Reuse existing Python 3.10 environment and `httpx`; no new runtime packages planned. If Typer or other CLI helper becomes necessary, document justification and removal owner in research.md.  
- **Scope Boundary**: Deliverables limited to local container setup instructions, CLI script, integrity scripts, evidence capture, and stakeholder summary. No production deployment, authentication changes, or GUI work.  
- **Integrity Proof Plan**: Provide `scripts/validate_env.sh` covering container image, docker access, required Python modules, and permission checks; capture outputs from `/status` curl, CLI `--ping`, and sample run into evidence directory prior to implementation sign-off.  
- **Test Mapping**: Technical elements mapped as: environment readiness -> `validate_env.sh`; diarization request -> CLI sample run recorded; documentation delivery -> checklist-driven review of summary doc. Gaps documented if encountered.  
- **Spike Posture**: Security hardening, automated CI, and large-scale performance are explicitly deferred; findings logged in docs/diarization-summary.md with follow-up recommendations.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```
specs/001-speech2textdiarize-i-want/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── diarization.yaml
├── checklists/
│   └── requirements.md
└── evidence/
  ├── environment-check.txt
  ├── cli-smoke.txt
  └── diarization-run.txt

cli/
└── diarize.py

scripts/
├── validate_env.sh
└── helpers/

.devcontainer/
├── devcontainer.json
└── Dockerfile

docs/
└── diarization-summary.md
```

**Structure Decision**: Single-project repository with top-level `cli/` for the Python entry point, `scripts/` for validation tooling, `.devcontainer/` assets aligned with new integrity requirements, and evidence stored beneath the feature spec directory for traceability.

## Phase 0: Research Scope

- Document the exact `docker run` command for `mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text-preview:5.0.1`, including port publishing, billing environment variables, persistent volume mount, and named network configuration per `docs/techstack.md`.
- Validate Azure Speech container prerequisites (subscription key, region, outbound HTTPS) and record confirmation steps in `research.md`.
- Investigate container health endpoints (`/status`) and startup behaviour (typical warm-up time) to shape integrity checks and CLI retry logic.
- Record decisions about optional FFmpeg pre-processing and whether it remains out of scope for this spike (document rationale).

## Phase 1: Design & Environment Contracts

### DevContainer & Runtime Preparation
- Update `.devcontainer/Dockerfile` so that all required tooling (Python 3.10, `httpx`, `curl`) installs during build rather than post-create; ensure Docker CLI access is configured for container-to-container networking. Note: any additional tools (e.g., ffmpeg) require a future research justification before inclusion.
- Amend `.devcontainer/devcontainer.json` to:
  - Reference the new Dockerfile.
  - Add `postAttachCommand` instructions for developers to run `scripts/validate_env.sh`.
  - Configure mounts or network aliases needed to reach the Speech container (`speech-net`, shared volume for models).
- Define the integrity workflow in `scripts/validate_env.sh`:
  - `docker pull` and `docker image inspect` for `speech-to-text-preview:5.0.1`.
  - Launch check to ensure no stale container instance conflicts (stop/remove if necessary).
  - Execute `/status` probe and capture results to evidence.
  - Verify `Billing__SubscriptionKey` and `Billing__Region` exported inside devcontainer.

### Azure Speech Container Runbook
- Produce a documented run sequence in `quickstart.md`:
  1. `docker pull mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text-preview:5.0.1`.
  2. `docker run --rm --name speech-to-text-preview --network speech-net -p 5000:5000 -e Billing__SubscriptionKey=$KEY -e Billing__Region=$REGION -v ${PWD}/.models:/mnt/models mcr.microsoft.com/...:5.0.1`.
  3. Wait for `/status` to report `running`; log output to `evidence/environment-check.txt`.
- Specify how to reuse the container across CLI iterations (leave running, or scripted start/stop) and how evidence must be regenerated after restarts.
- Outline failure handling: missing billing values, port collision, or health check failure; document remediation steps before moving to CLI development.

### CLI Interaction Design
- Define CLI arguments (audio path, optional language override) and output format ensuring diarization segments and metadata align with contract.
- Map CLI commands to validation artefacts: `--ping` for smoke test, default run writing to evidence file.
- Ensure CLI gracefully handles container offline state by surfacing actionable error and pointing to validation script.

### Documentation & Stakeholder Outputs
- Structure `docs/diarization-summary.md` sections (overview, environment snapshot, results, limitations, follow-up).
- Link every summary claim to evidence artifacts (environment check, CLI output) within the repository.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
