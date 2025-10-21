# Phase 2 Task Breakdown: NearRealTimeText2Speech

**Branch**: `002-nearrealtimetext2speech-i-want`  
**Spec**: `spec.md`  
**Plan**: `plan.md`  
**Generated**: 2025-10-21

## Principles Alignment
All tasks adhere to: Minimal Dependencies Only, One-Test Validation, Integrity Proof Gates, Constrained Scope Delivery.

## Legend
- FR-x: Functional Requirement
- SC-x: Success Criteria
- IC: Integrity Check
- EVT: Evidence artifact

## High-Level Sequence
1. Environment & container validation foundation
2. Core synthesis & playback skeleton (single line)
3. Interactive session + queue enforcement
4. Diagnostics (latency + chunk timestamps)
5. Error handling & mixed-language acceptance
6. Evidence scripts & tests
7. Documentation & quickstart confirmation
8. Latency tuning & optional fallback evaluation

## Task Table
| ID | Description | Category | Maps To | Evidence / Output | Done Criteria |
|----|-------------|----------|--------|-------------------|---------------|
| T01 | Refine `Text2Speechvalidate_env.sh` to produce required evidence logs path under feature directory | Env | FR-006, IC | env logs | Pass script with all PASS or documented FAILs |
| T02 | Create `cli/tts_cli.py` minimal: parse args, `--ping` readiness, exit 0 | CLI | FR-004, FR-013 | readiness.txt | Returns READY <1s |
| T03 | Implement Speech SDK host override & voice config in synthesizer module | Synthesis | FR-011, FR-010 | synthesis smoke log | First test phrase speaks |
| T04 | Implement playback abstraction (`playback.py`) using simpleaudio queue | Playback | FR-002 | synthesis-smoke.txt (playback metadata) | First audio frame <1s locally (manual) |
| T05 | Add queue manager to enforce single active + bounded FIFO queue (default max 3) | Session | FR-012, SC-008 | queue.txt (assets/output/queue.txt) | Rapid N submissions show 1 active, ≤max_queue queued, remainder rejected |
| T06 | Interactive mode loop with `:quit` handling (always exit 0) | CLI | FR-008, FR-013 | exit evidence | Graceful exit, no tracebacks |
| T07 | Oversize input rejection & warning message logic | Validation | FR-007 | errors.txt | >500 chars rejected; session continues |
| T08 | Service down detection & warning (no forced exit) | Error Handling | FR-006, SC-009 | errors.txt | Stop container test logs warning |
| T09 | Mixed-language acceptance test (accented chars) | Validation | FR-015, SC-011 | mixed_language.txt | Phrase synthesized or appropriate warning |
| T10 | Implement diagnostic mode flag & per-chunk timestamp capture | Diagnostics | FR-014, SC-010 | chunk_timing.txt | 3 test runs produce gaps table |
| T11 | Implement latency measurement script `measure_latency.sh` (submission→first chunk incl. queue delay) | Diagnostics | FR-005, SC-001 | latency.txt | 90% short phrases <1s synth latency; queue delay recorded |
| T12 | Implement `diagnostic_chunk_timing.sh` script | Diagnostics | FR-014, SC-010 | chunk_timing.txt | Captures ordered timestamps |
| T13 | Implement `multiline_queue_test.sh` script | Testing | FR-012, SC-008 | queue.txt | Matches acceptance scenario pattern |
| T14 | Implement `error_handling_test.sh` script | Testing | FR-006, FR-007, FR-013 | errors.txt | All conditions logged clearly |
| T15 | Unit tests: playback queue start & synthesizer host override | Unit Test | FR-002, FR-011 | pytest report | Tests pass locally |
| T16 | Integration tests: latency, queue behavior, error conditions | Integration | SC-001, SC-008, SC-009 | pytest report | All pass; artifacts saved |
| T17 | Contract test (if HTTP endpoints used) or skip w/ justification | Contract | OpenAPI | contract test log | Pass or documented skip |
| T18 | Quickstart doc verification & adjustments | Docs | SC-005 | updated quickstart.md | Steps reproducible end-to-end |
| T19 | Optional pyaudio evaluation (only if latency gap failure) | Perf Option | Risk Mitigation | perf notes | Decision recorded in research addendum |
| T20 | Final evidence aggregation & constitution compliance review | Governance | All | summary.md | Checklist complete; ready for PR |

## Dependency Graph (Simplified)
T01 → T02 → T03 → T04 → (T05,T06,T07,T08,T09) → T10,T11,T12,T13,T14 → T15,T16,T17 → T18 → (T19 optional) → T20

## Risk Mitigations Embedded
- Latency risk: T11 early measurement prompts pivot (T19).
- Playback jitter: Diagnostic gap analysis (T10/T12) guides fallback.
- Environment drift: T01 repeatable script ensures reproducibility.

## Evidence Artifact Index
| Artifact | Source Task | Path (planned) |
|----------|-------------|----------------|
| readiness.txt | T02 | assets/output/readiness.txt |
| latency.txt | T11 | assets/output/latency.txt |
| queue.txt | T05/T13 | assets/output/queue.txt |
| errors.txt | T07/T08/T14 | assets/output/errors.txt |
| mixed_language.txt | T09 | assets/output/mixed_language.txt |
| chunk_timing.txt | T10/T12 | assets/output/chunk_timing.txt |

## Acceptance Gate Checklist
- All FR mapped to at least one task.
- All SC have an evidence artifact plan.
- No new dependencies added beyond those justified.
- All scripts produce deterministic exit code 0 (or documented exceptions).

## Out-of-Scope Explicit
- Multiple concurrent streams beyond queue design.
- SSML advanced markup.
- Voice listing & selection UI.
- Non-English pronunciation tuning.
- Persistent audio caching.

## Notes
If contract endpoints remain conceptual only (no direct HTTP in spike), record T17 as skipped with reason "CLI-only interactions; container endpoints externally owned".
