# Latency Measurement Evidence Guide

This document explains the structure, timing semantics, and interpretation of the latency evidence produced by `scripts/measure_latency.sh`, specifically the `assets/output/latency.txt` file and associated segment metadata (SEG lines and combined WAV).

## 1. Purpose
The latency evidence provides auditable, per-phrase timing for near-real-time text-to-speech (TTS) synthesis under a bounded single-active / queued execution model. It separates queue waiting time from synthesis startup latency and maps phrases precisely to frame offsets in the combined output audio.

## 2. File: `assets/output/latency.txt`
Header lines (prefixed with `#`) record run-level metadata:
- `combined_wav`: Path to the concatenated WAV built from successful phrase outputs.
- `segment_columns`: Schema for subsequent `SEG` lines.
- `host`, `voice`, `max_queue`: Runtime configuration.
- `columns`: Schema for the main timing rows.

### 2.1 Main Timing Rows
Each non-`#` line before the SEG section represents one submitted phrase:

`request_id|decision|submit_ms|start_ms|first_audio_ms|queue_delay_ms|synth_latency_ms|text`

Field meanings:
- **request_id**: UUID assigned at submission.
- **decision**:
  - `ACTIVE_STARTED`: Phrase began synthesis immediately (no queue wait).
  - `QUEUED`: Phrase placed into FIFO queue; will start later.
- **submit_ms**: Monotonic timestamp (ms) at submission.
- **start_ms**: Monotonic timestamp (ms) when synthesis actually started.
- **first_audio_ms**: Monotonic timestamp (ms) when first audio chunk arrived (start of streaming output).
- **queue_delay_ms** = `start_ms - submit_ms` (waiting time in queue; zero if active immediately).
- **synth_latency_ms** = `first_audio_ms - start_ms` (time from becoming active to first audio).
- **text**: Phrase content.

All timestamps derive from a monotonic clock; absolute magnitudes are only meaningful via differences.

### 2.2 Total Latency Formula
For any phrase:

`total_latency_submit_to_first_audio = queue_delay_ms + synth_latency_ms`

This partitions perceived latency into **waiting** (queue) and **activation** (synthesis start → first audio). The synthesis latency is an early readiness indicator; full audio generation may continue beyond this first chunk.

### 2.3 Example (Extracted Run)
```
8271eed5-...|ACTIVE_STARTED|49060868|49060868|49060910|0|42|This is a test of multi phrase latency
7241843d-...|QUEUED|49060889|49060964|49060997|75|33|Here is another quick test following on
b9ee1bfe-...|QUEUED|49060909|49061057|49061089|148|32|Phrase number 3
e6f59165-...|QUEUED|49060929|49061149|49061178|220|29|And here is the fourth phrase
cb9d46e2-...|QUEUED|49060949|49061236|49061470|287|234|And a fifth, as in fifth column
0b36cab2-...|QUEUED|49060970|49061571|49061611|601|40|Sixth
5d5f8882-...|QUEUED|49060990|49061659|49061688|669|29|Finally 7th
```

Derived totals:

| Position | Queue Delay (ms) | Synth Latency (ms) | Total (ms) | Queue Share | Notes |
|----------|------------------|--------------------|-----------|------------|-------|
| 1        | 0                | 42                 | 42        | 0%         | Immediate start |
| 2        | 75               | 33                 | 108       | 69%        | Wait + fast synth |
| 3        | 148              | 32                 | 180       | 82%        | Queue accumulating |
| 4        | 220              | 29                 | 249       | 88%        | Increasing wait |
| 5        | 287              | 234                | 521       | 55%        | Synth outlier (long) |
| 6        | 601              | 40                 | 641       | 94%        | Large prior delays |
| 7        | 669              | 29                 | 698       | 96%        | Deep queue impact |

Observations:
- Synthesis (activation) is typically fast (≈30–70 ms) except an outlier (234 ms).
- Queue delay dominates end-user latency for deeper queue positions.
- Anomalous high synth latency inflates downstream queue delays.

## 3. Segment Mapping (`SEG` Lines)
Format:

`SEG|request_id|start_frame|end_frame|frames|audio_path|text`

Field meanings:
- **start_frame**: Inclusive PCM frame offset of phrase segment in the combined WAV.
- **end_frame**: Exclusive end offset.
- **frames** = `end_frame - start_frame` (segment length in frames).
- **audio_path**: Source WAV path for the individual synthesis.
- **text**: Phrase content (matches main row).

In the example, all segments have uniform length (31200 frames) and are contiguous:
```
0–31200, 31200–62400, 62400–93600, 93600–124800, 124800–156000, 156000–187200, 187200–218400
```
Total frames = 218400.

### 3.1 Duration Calculation
If the sample rate is 48 kHz (typical), then:
- Segment duration ≈ 31200 / 48000 ≈ 0.65 s.
- Total duration ≈ 218400 / 48000 ≈ 4.55 s.

If a different sample rate is used, adjust accordingly: `duration_seconds = frames / sample_rate`.

### 3.2 Consistency Check
Uniform frame counts may indicate:
- Similar phrase lengths coincidentally.
- Padding/truncation logic in synthesis output collection.
- A placeholder or test voice producing fixed-length audio.

If variable durations are expected, investigate extraction or concatenation logic.

## 4. Derived Metrics & Formulas
- **Total latency**: `queue_delay_ms + synth_latency_ms`.
- **Queue share**: `queue_delay_ms / (queue_delay_ms + synth_latency_ms)`.
- **Average synth latency** (excluding outliers): mean of `synth_latency_ms` for active periods.
- **Throughput (to first audio)** (approx.): `1000 / mean_synth_latency_ms` (phrases per second single-threaded before queueing).

## 5. Interpreting Performance
- Fast activation latency indicates low initialization overhead once active.
- High queue delays imply demand > single-thread service capacity; scaling actions (additional concurrent synthesizers, sharding voices, or dynamic queue management) would most directly reduce perceived latency for queued phrases.
- Outlier synthesis times can cascade by extending downstream waits; tracking percentile latency (P50, P95) is recommended.

## 6. Anomalies & Follow-up Recommendations
| Issue / Observation | Potential Cause | Suggested Action |
|---------------------|-----------------|------------------|
| Single synth outlier (234 ms) | Network / API transient | Collect more samples; compute distribution. |
| Uniform segment lengths | Padding / truncation | Verify audio extraction logic; confirm expected variable durations. |
| Identical `audio_path` values across segments | Overwrite or reuse path | Ensure unique per-phrase filenames if needed for auditing. |
| Queue delay growth | Sequential single active model | Evaluate parallelization or predictive prefetch. |

## 7. Quick Reference Cheat Sheet
| Concept | Formula / Definition |
|---------|----------------------|
| Queue delay | `start_ms - submit_ms` |
| Synth latency | `first_audio_ms - start_ms` |
| Total latency | `queue_delay_ms + synth_latency_ms` |
| Segment duration | `frames / sample_rate` |
| Queue share of total | `queue_delay_ms / total_latency` |
| Throughput (approx) | `1000 / mean_synth_latency_ms` |

## 8. Suggested Future Enhancements
- Record end-of-stream timestamp to distinguish first-audio vs full synthesis duration.
- Add percentile summaries and run-level JSON metrics (P50, P90, P95, max).
- Include sample_rate in headers for direct duration calculation.
- Capture chunk-by-chunk timing (inter-chunk gaps) for streaming smoothness diagnostics.
- Add correlation ID linking to service logs (if external TTS API used).

## 9. Validation Steps
To validate integrity of a run:
1. Confirm number of SEG lines matches number of successful phrase rows.
2. Verify contiguity: Each `start_frame` equals previous `end_frame`.
3. Sum of all `frames` equals final `end_frame` of last segment.
4. Compute durations from frames and verify against individual WAV lengths (optional cross-check).
5. Inspect for outlier synthesis latencies; record distribution.

## 10. Glossary
- **Active**: The phrase currently being synthesized.
- **Queued**: Awaiting activation behind active phrases.
- **First audio**: Arrival of the initial audio chunk (stream start marker).
- **Segment**: Continuous span of frames in combined WAV corresponding to one phrase.
- **Monotonic clock**: Time source that only moves forward (immune to wall-clock adjustments).

---
Last updated: 2025-10-21
Source example run: `latency.txt` containing 7 phrases (1 active + 6 queued) with uniform segment lengths.
