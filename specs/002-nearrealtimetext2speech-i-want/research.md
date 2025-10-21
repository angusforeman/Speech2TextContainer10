# Phase 0 Research: NearRealTimeText2Speech

**Date**: 2025-10-21  
**Spec**: `specs/002-nearrealtimetext2speech-i-want/spec.md`  
**Plan**: `specs/002-nearrealtimetext2speech-i-want/plan.md`

## Decisions

### 1. Audio Format
Decision: PCM 16-bit 16 kHz mono stream.
Rationale: Lowest complexity, acceptable quality, aligns with latency goal and Speech SDK format enum.
Alternatives: 24 kHz (larger payload), Opus compressed (decode overhead), MP3 (framing latency).

### 2. Concurrency & Queueing
Decision: Single active synthesis + one queued request.
Rationale: Minimizes state complexity, predictable latency, avoids audio overlap.
Alternatives: Multi-stream mixing (complex), strict reject (worse UX), pause/replace (loss of prior output).

### 3. Exit Codes
Decision: Always 0; error surfaced via messages.
Rationale: Simplifies spike scripts; avoids branching logic in early evidence capture.
Alternatives: Structured numeric codes (better automation), POSIX extended codes (verbose). Deferred until production hardening.

### 4. Latency Instrumentation Granularity
Decision: Capture total (submission→first chunk) plus per-chunk arrival timestamps in diagnostic mode.
Rationale: Enables analysis of streaming smoothness; overhead manageable.
Alternatives: Only total latency (insufficient for jitter analysis); full PCM profiling (excess detail for spike).

### 5. Mixed-Language Handling
Decision: Accept all input; warn only on synthesis failure.
Rationale: Reduces premature rejections; observes real model behavior.
Alternatives: Strict English filter (limits exploration), auto-detect language (adds dependency), sanitization (risk of altering meaning).

### 6. Playback Library Choice (Initial)
Decision: Start with `simpleaudio` abstraction; allow swap.
Rationale: Pure Python, low friction; adequate latency for small buffers.
Alternatives: pyaudio (lower latency but native build friction), ffplay pipe (external dependency, higher start latency).

### 7. Diagnostic Mode Toggle
Decision: Command-line flag (e.g., `--diagnostic`) governing chunk timing capture & verbose logs.
Rationale: Keeps normal mode lean; allows focused measurement.
Alternatives: Always-on timing (unnecessary overhead), environment var only (less discoverable to users).

### 8. Evidence Storage Pattern
Decision: One artifact per validating test named by scenario (latency.txt, queue.txt, etc.).
Rationale: Direct mapping to One-Test Validation; easier review.
Alternatives: Single aggregated log (harder to isolate failures), database or structured JSON index (overkill).

### 9. Readiness Probe Design
Decision: `--ping` invokes SDK initialization & returns READY string within ~1s.
Rationale: Low overhead, exercises host override & voice config.
Alternatives: Raw HTTP /ready call (misses SDK misconfiguration); synthetic test synthesis (adds latency for just health).

### 10. Container Port & Networking
Decision: Host port 5001 mapped to internal 5000; Docker network `speech-net`.
Rationale: Avoid collision with existing STT container; simple name resolution.
Alternatives: Same port (conflict risk), dynamic random port (requires discovery logic).

## Unknowns Resolved
- Playback latency sufficiency with simpleaudio: Accept initial measurement; fallback plan to pyaudio if inter-chunk gap >150 ms.
- Minimal dependency path: Confirm no additional packages required for queue, choose stdlib `queue`.
- Host override property for Speech SDK: Use `SpeechServiceConnection_Host` property.

## Deferred Topics
- Multi-voice and style switching.
- Structured exit codes for automation scenarios.
- Advanced jitter smoothing (buffer re-shaping).
- Accessibility transcripts / subtitles.
- Persistent caching of synthesized audio.

## Risk Register (Spike Scope)
| Risk | Impact | Mitigation | Exit Criteria |
|------|--------|-----------|---------------|
| simpleaudio latency variance | Jitter may exceed SC-010 gap target | Measure first; switch to pyaudio if failure | Sustained gap compliance over 3 runs |
| Container warm-up slow start | First synthesis >1s | Pre-warm phrase at CLI start | Warm-up <1s evidence in latency.txt |
| Mixed-language failure noise | Users confused by warnings | Clear message with retry guidance | Warning format documented in quickstart |
| Single queue overflow spamming | User frustration | Explicit "queue full" message | Message present in queue.txt evidence |

## Data Points To Collect
| Metric | Source | Frequency |
|--------|--------|-----------|
| Time to first audio | measure_latency.sh | Per synthesis test |
| Inter-chunk gaps | diagnostic_chunk_timing.sh | Diagnostic runs |
| Queue rejection count | multiline_queue_test.sh | Single scenario |
| Mixed-language success latency | mixed_language test | Single scenario |

## Alternatives Summary Table
| Area | Chosen | Primary Alternative | Rejection Reason |
|------|--------|---------------------|------------------|
| Playback | simpleaudio | pyaudio | Added native build complexity for spike |
| Queueing | 1 active + 1 queued | Unlimited queue | Increases latency unpredictability |
| Exit codes | Always 0 | Structured codes | Not essential for spike evidence |
| Instrumentation | Total + per-chunk | Total only | Cannot analyze jitter |
| Mixed-language | Accept + warn | Strict English filter | Prevents exploration & reduces sample variety |

## Next Phase Inputs
This document feeds Phase 1 data-model and contracts by clarifying:
- Entities: InputLine, SynthesisRequest (with chunk_timestamps), EvidenceArtifact.
- Operations: readiness ping, single-line synthesis, interactive session behaviors.

## Confirmation
All NEEDS CLARIFICATION items addressed; no unresolved blocking unknowns for Phase 1.
