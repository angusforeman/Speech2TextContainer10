# Research Findings: Speech2TextDiarize CLI Spike

## Decision: Python CLI using httpx within devcontainer
- **Rationale**: `docs/techstack.md` specifies a Python 3.10 CLI that calls the Speech container via HTTP. `httpx` already exists in the stack, supports streaming uploads, and runs inside the shared devcontainer without extra system dependencies.
- **Alternatives considered**: `requests` (lacks built-in async streaming and already replaced by httpx in tech stack), shelling out to `curl` (would complicate error handling and evidence capture).

## Decision: Extend .devcontainer build with Dockerfile
- **Rationale**: User request mandates expressing post-create tooling in a Dockerfile so rebuilds recreate the environment. Moving package installs (e.g., python tooling, ffmpeg if needed) into `.devcontainer/Dockerfile` ensures deterministic setup and allows `validate_env.sh` to confirm results.
- **Alternatives considered**: Keeping installations in `postCreateCommand` (risks drift and violates instruction), manual local installs (non-reproducible).

## Decision: Validate environment via scripts/validate_env.sh
- **Rationale**: Constitution requires integrity proof gates; a single script covering Docker daemon access, container image presence, required env vars, and Python packages provides repeatable evidence before backend or CLI implementation.
- **Alternatives considered**: Manual checklist (error-prone and not automatable), multiple ad-hoc scripts (violates minimalism and complicates evidence capture).

## Decision: Capture diarization outputs and summary documentation
- **Rationale**: Success criteria demand stakeholders receive findings quickly. Capturing raw CLI output plus a markdown summary in `docs/diarization-summary.md` allows asynchronous review and supports the "One-Test Validation" principle for documentation.
- **Alternatives considered**: Leaving results only in terminal history (not durable), generating slide deck (overkill for spike timeline).

## Decision: Reference docs/techstack.md for container + CLI configuration
- **Rationale**: User instruction explicitly designates `docs/techstack.md` as the authority, so plan aligns CLI options (httpx, Python 3.10) and container networking assumptions with that document.
- **Alternatives considered**: External Microsoft docs (supplementary only), bespoke configuration notes (risk divergence from agreed stack).
