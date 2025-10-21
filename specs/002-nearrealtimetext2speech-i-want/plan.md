# Implementation Plan: NearRealTimeText2Speech

**Branch**: `002-nearrealtimetext2speech-i-want` | **Date**: 2025-10-21 | **Spec**: `specs/002-nearrealtimetext2speech-i-want/spec.md`
**Input**: Accepted feature specification and clarifications.

## Summary
Implement a near real-time neural Text-to-Speech interactive CLI using a local Azure Neural TTS container. Stream PCM 16-bit 16 kHz audio with single-active + bounded FIFO queued input design (default max 3), constant exit code 0, diagnostic mode capturing per-chunk timestamps. Minimal dependencies aligned with constitution; emphasize integrity proof, latency evidence, and one-test validation per technical element.

## Technical Context

**Language/Version**: Python 3.10 (DevContainer base)  
**Primary Dependencies**: 
- azure-cognitiveservices-speech – Required for streaming synthesis events (synthesizing). Removal would eliminate TTS capabilities.
- httpx – Lightweight HTTP client for readiness & status checks (aligned with existing stack usage; async-ready if expanded).
- simpleaudio (optional) – Provides low-complexity playback of raw PCM; fallback to writing WAV + system player if removed.
No further deps initially; pyaudio deferred (adds native complexity) pending latency evidence.

**Storage**: N/A (ephemeral in-memory buffers; evidence logs centralized under `assets/output/`).  
**Testing** (One-Test Validation mapping):
| Element | Validating Test / Script | Evidence Artifact |
|---------|--------------------------|-------------------|
| Readiness probe | `python cli/tts_cli.py --ping` | readiness.txt |
| Latency measurement | `scripts/measure_latency.sh` | latency.txt |
| Queue behavior | `scripts/multiline_queue_test.sh` | queue.txt |
| Error handling | `scripts/error_handling_test.sh` | errors.txt |
| Mixed-language acceptance | pytest `test_mixed_language.py` | mixed_language.txt |
| Diagnostic chunk timestamps | `scripts/diagnostic_chunk_timing.sh` | chunk_timing.txt |

**Target Platform**: Linux DevContainer (Debian bullseye).  
**Project Type**: Single CLI feature within existing Python repository.  
**Performance Goals**: Start playback <1s for ≥90% of short inputs (≤50 chars); average inter-chunk gap ≤150 ms (diagnostic mode).  
**Constraints**: Simplicity > extensibility; single active stream + one queued; constant exit code 0; memory footprint <150MB incremental.  
**Scale/Scope**: Single-user interactive session; <=10 sequential synth requests scenario for MVP; concurrency beyond configured queue size explicitly out-of-scope.

## Constitution Check (Pre-Design Gate)

- **Dependency Justification**: Each new dep has removal path (simpleaudio removable; httpx replaceable by curl; Speech SDK indispensable).
- **Scope Boundary**: Excludes multi-voice selection, SSML features, accessibility transcript, advanced metrics, scaling, non-English optimization beyond acceptance/warn behavior.
- **Integrity Proof Plan**:
  1. `scripts/Text2Speechvalidate_env.sh` – container & env vars check.
  2. `python cli/tts_cli.py --ping` – readiness probe.
  3. `scripts/measure_latency.sh` – latency collection using short phrase.
  4. `scripts/diagnostic_chunk_timing.sh` – per-chunk timestamp capture.
  5. `scripts/multiline_queue_test.sh` – active + queued behavior.
  6. `scripts/error_handling_test.sh` – service down & oversize input scenarios.
- **Test Mapping**: See Testing table above.
- **Spike Posture**: Deferred production concerns (security hardening, observability depth, HA, voice variety, accessibility). Risks logged; evidence focuses on latency & stability.

Gate Status: PASS (no unjustified violations).

## Project Structure

### Documentation (this feature)

```
specs/002-nearrealtimetext2speech-i-want/
├── spec.md
├── plan.md
├── research.md              # Phase 0 (to create next)
├── data-model.md            # Phase 1
├── quickstart.md            # Phase 1
├── contracts/               # Phase 1 OpenAPI contract
├── evidence/                # Integrity & validation artifacts
└── tasks.md                 # Created by /speckit.tasks later
```

### Source Code (repository root)

```
cli/
 └── tts_cli.py              # Interactive CLI & single-line mode
src/
 ├── tts/
 │   ├── playback.py         # Playback abstraction (queue -> simpleaudio)
 │   ├── synthesizer.py      # Wrapper around Speech SDK interactions
 │   ├── diagnostics.py      # Timing & chunk capture utilities
 │   └── __init__.py
scripts/
 ├── Text2Speechvalidate_env.sh
 ├── measure_latency.sh      # New
 ├── diagnostic_chunk_timing.sh
 ├── multiline_queue_test.sh
 ├── error_handling_test.sh
 └── helpers/
tests/
 ├── unit/
 │   ├── test_playback.py
 │   ├── test_synthesizer.py
 ├── integration/
 │   ├── test_latency.py
 │   ├── test_queue_behavior.py
 │   ├── test_error_conditions.py
 └── contract/
     └── test_openapi_contract.py
```

**Structure Decision**: Single-project Python layout leveraging existing `cli/` and introducing `src/tts/` for modularity; avoids new package complexity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Additional `src/tts/` module | Separation of playback & synthesis for clarity and test isolation | Monolithic CLI would hinder one-test validation mapping & future extensibility |
