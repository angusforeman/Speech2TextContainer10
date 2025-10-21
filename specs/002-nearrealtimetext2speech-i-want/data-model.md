# Data Model: NearRealTimeText2Speech

**Spec**: `specs/002-nearrealtimetext2speech-i-want/spec.md`  
**Research**: `research.md`  
**Date**: 2025-10-21

## Overview
Minimal transient in-memory model; persistent storage out-of-scope. Entities exist for structuring code & diagnostics.

## Entities

### InputLine
| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| raw_text | str | length 1..500 (blank ignored) | Mixed-language accepted |
| timestamp_received | float (monotonic) | >0 | Captured immediately on submission |
| char_count | int | = len(raw_text) | Derived |

Validation:
- Reject if len(raw_text) > 500 (FR-007)
- Ignore if len(raw_text) == 0 (edge case)

State: ephemeral; once enqueued for synthesis becomes part of SynthesisRequest.

### SynthesisRequest
| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| request_id | str (UUID4) | unique per request | Used for evidence linking |
| input_line | InputLine | not null | Source text |
| status | enum {pending, active, completed, failed} | transitions defined below | Maps to synthesis lifecycle |
| latency_ms | float | >=0 (only after completed/failed) | submission→first chunk |
| voice_used | str | non-empty | Default voice; may fallback |
| audio_format | str | fixed 'pcm16_16khz' | FR-011 |
| chunk_timestamps | list[float] | ordered, monotonic increasing | Populated only in diagnostic mode (FR-014) |
| failure_reason | str | optional (only if failed) | Human-readable message |

Lifecycle Transitions:
1. pending → active (synth begins)
2. active → completed (success) | active → failed (error/timeout)
3. failed/completed terminal

Transition Rules:
- Only one active at a time (queue slot holds one pending) (FR-012)
- pending removed if user quits before activation

### EvidenceArtifact
| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| artifact_type | enum {latency, readiness, queue, error, mixed_language, chunk_timing} | required | Maps to test table |
| path | str | file exists after creation | Under feature evidence dir |
| created_at | float (UTC epoch) | >0 | Capture at write completion |
| request_ids | list[str] | optional | Links to associated SynthesisRequest(s) |

## Relationships
- InputLine 1..1 → SynthesisRequest
- EvidenceArtifact may reference multiple SynthesisRequests (e.g., queue test)

## Derived Metrics
- latency_ms = first_chunk_timestamp - input_line.timestamp_received
- inter_chunk_gaps = diff(chunk_timestamps[i] - chunk_timestamps[i-1])

## Validation Summary Table
| Rule | Entity | Enforcement Point | Failure Handling |
|------|--------|-------------------|------------------|
| Text length ≤500 | InputLine | Submission parser | Warn & ignore (if >500) |
| Single queued slot | SynthesisRequest | Queue manager | Reject additional with message |
| Mixed-language accepted | InputLine | Submission parser | No filter; proceed |
| PCM format fixed | SynthesisRequest | Synth init | Ensure config; log if mismatch |
| Diagnostic chunk capture only in mode | SynthesisRequest | Event handler | Skip timestamps if mode disabled |

## Edge Case Behaviors
- Empty raw_text: no SynthesisRequest created.
- Service down: SynthesisRequest failed with failure_reason; exit still 0 after quit.
- Oversize input: rejection before SynthesisRequest creation.

## Instrumentation Hooks
- On first chunk arrival: record latency_ms and append timestamp to chunk_timestamps.
- On each chunk (diagnostic mode): append timestamp only.

## Rationale
Design favors minimal coupling, enabling straightforward unit tests per entity and diagnostic clarity.
