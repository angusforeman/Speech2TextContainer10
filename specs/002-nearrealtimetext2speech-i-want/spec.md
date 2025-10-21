# Feature Specification: NearRealTimeText2Speech

**Feature Branch**: `002-nearrealtimetext2speech-i-want`  
**Created**: 2025-10-21  
**Status**: Draft  
**Input**: User description: "NearRealTimeText2Speech: I want to be able to utilise the latest version of a neural English Text to Speech service, running locally in a container. I want to demonstrate the functionality through a simple interactive command-line experience. The interface should speak the text entered by the user and provide a streamed spoken response. The responses should begin as near real time as possible."

## Clarifications

### Session 2025-10-21

- Q: What audio stream format & sample rate should the system use for synthesized output? → A: Uncompressed 16-bit PCM at 16 kHz.
- Q: How should the system handle rapid sequential submissions during playback? → A: Maintain a single active stream and allow a bounded FIFO queue of pending inputs (configurable, default size 3); reject further submissions once the queue is full.
- Q: What exit code strategy should be used for errors (service down, invalid input)? → A: Always exit with status 0; signal errors only via textual messages.
- Q: What latency measurement granularity should diagnostic mode capture? → A: Record total latency plus per audio chunk arrival timestamps.
- Q: How should non-English / mixed-language input be handled? → A: Accept as-is (including accented characters); attempt synthesis; warn only if synthesis fails.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently

  Map every user story to the minimum validation artifacts required by the "One-Test Validation" principle.
  If multiple technical elements exist inside a story, enumerate their single validating tests explicitly.
-->

### User Story 1 - Enter text and hear synthesized speech (Priority: P1)

User starts an interactive prompt session. They type an English phrase (<= 500 characters) and submit it; the system streams synthesized neural voice audio with minimal latency so spoken output begins within ~1 second and completes correctly.

**Why this priority**: Core value demonstration: converts typed text to near-real-time speech locally using containerized service.

**Independent Test**: Single validation capturing: (1) interface accepts input, (2) audio playback starts < 1s from submission, (3) full text spoken. Evidence artifact to be produced (basic stream + latency record).

**Acceptance Scenarios**:
1. **Given** the TTS container is running and CLI started in interactive mode, **When** the user enters a valid English phrase, **Then** playback starts within 1 second and the spoken content matches input text.
2. **Given** the user enters an empty line, **When** processed, **Then** the CLI prompts again without error and no audio is played.

---

### User Story 2 - Continuous multi-line session (Priority: P2)

User stays in the session and submits multiple lines sequentially; each is synthesized independently without a restart; prior audio does not block new requests excessively (next request accepted immediately after previous starts playback) using a single active stream plus one-slot queue.

**Why this priority**: Demonstrates sustained usability beyond single example; shows session efficiency.

**Independent Test**: Enter 3 lines sequentially; verify each starts within 1s; session handles all lines without interruption. Evidence artifact: multi-line session transcript with timestamps.

**Acceptance Scenarios**:
1. **Given** an active session after first synthesis, **When** the user enters a second phrase, **Then** new audio begins within 1 second and is distinct from previous output.
2. **Given** multiple phrases entered rapidly (<2s apart), **When** processed, **Then** the first is synthesized, the second is queued, and a third attempt before the queue clears is rejected with a clear "queue full" notice.

---

### User Story 3 - Basic error handling & graceful exit (Priority: P3)

User encounters invalid input (too long, unsupported character set) or service unavailability; interface reports a clear error and continues without terminating the process automatically; user can type a quit command (e.g., `:quit`) to end session. All exits use status 0.

**Why this priority**: Ensures reliability and controlled termination making demo credible.

**Independent Test**: Simulate (1) service down, (2) >500 character input, (3) quit command. Evidence artifact: error and exit behavior transcript with status codes.

**Acceptance Scenarios**:
1. **Given** container is not reachable, **When** user submits text, **Then** interface prints connection error and remains in the session (no forced termination; exit status remains 0 upon eventual quit).
2. **Given** input > 500 chars, **When** submitted, **Then** interface warns about length and rejects without crashing; session continues.
3. **Given** session active, **When** user types `:quit`, **Then** session ends and process exits code 0.

---

No additional stories required for MVP.

### Edge Cases

- Input exactly 0 characters (empty line) -> ignore, reprompt.
- Input exactly at limit (500 chars) -> accept and synthesize.
- Rapid sequential submissions (spam) -> system maintains a bounded FIFO queue (default size 3); submissions beyond capacity rejected with "queue full" notice.
- Container process restarts mid-session -> first failed request logs error and prompts user to retry.
- Repeated service unavailability -> multiple consecutive failures produce distinct timestamped warnings; no non-zero exit status.
- Audio device unavailable -> produce textual warning and skip playback but still record success of synthesis request.
- Non-English or mixed-language text (e.g., accented characters) -> accepted and attempted as-is; if synthesis fails, system warns user with a clear message (no crash) and allows continued input.

## Integrity Checks & Evidence *(mandatory)*

- **Check 1**: Environment validation procedure confirms the speech service container is present and running; evidence artifact captured (environment status).
- **Check 2**: Readiness probe command returns a readiness indicator within ~1 second verifying configuration; evidence artifact captured (readiness status).
- **Check 3**: Latency measurement procedure for a short phrase records submission timestamp vs first audio frame; evidence artifact captured (latency metrics).
- **Check 4**: Multi-line session test captures sequential synthesis behavior with timestamps; evidence artifact captured (session transcript).
- **Check 5**: Error handling test set exercises service down, oversize input, graceful exit; evidence artifact captured (error & exit log).

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST accept user-entered English text lines up to 500 characters.
- **FR-002**: System MUST initiate synthesis and begin audio playback within 1 second for valid input under typical local conditions (service active, <=50 chars).
- **FR-003**: System MUST provide an interactive session allowing multiple sequential inputs without restart.
- **FR-004**: System MUST expose a readiness probe command to verify availability without performing synthesis.
- **FR-005**: System MUST record latency (input submission to first audio frame) for each request when operating in diagnostic mode.
// Clarified granularity
- **FR-005**: System MUST record latency (input submission to first audio frame) for each request when operating in diagnostic mode.
- **FR-006**: System MUST handle unavailable speech service gracefully by reporting a clear error and remaining available for retry (no automatic termination).
- **FR-007**: System MUST reject inputs exceeding 500 characters with an explanatory message and allow continued use.
- **FR-008**: System MUST allow clean exit via a quit command and return success status.
- **FR-009**: System MUST capture evidence artifacts for each primary test scenario.
- **FR-010**: System MUST support selection of a default neural English voice (single voice sufficient for MVP).
- **FR-011**: System MUST output synthesized audio in uncompressed linear PCM, 16-bit, 16 kHz sample rate for all responses (no format negotiation in MVP).
- **FR-012**: System MUST enforce a single active synthesis stream plus a bounded FIFO queue of pending requests (configurable maximum; default 3). Attempts to add a request when the queue is at capacity MUST be rejected with a clear "queue full" message and MUST NOT overwrite existing queued items.
- **FR-013**: System MUST always exit with status code 0; error conditions MUST be conveyed via textual messages and evidence artifacts (no differentiated non-zero codes in MVP).
- **FR-014**: When diagnostic mode is enabled, system MUST capture arrival timestamps for each streamed audio chunk in order, enabling analysis of inter-chunk gaps.
- **FR-015**: System MUST accept mixed-language and accented characters without pre-filtering; on synthesis failure due to unsupported content, it MUST emit a warning within 500 ms and remain in the session.
*NEEDS CLARIFICATION markers limited to critical scope items:* None required—defaults assumed.

## Deferred Production Concerns *(document risks)*

- Security hardening deferred because this is a research spike; mitigation: document minimal sandbox measures; no secrets checked into VCS.
- Observability/monitoring omitted (no centralized logging); mitigation: local evidence artifacts only.
- High availability / scaling concerns deferred; single local instance.
- Voice selection variety deferred; single default voice used.
- Accessibility (subtitles/phoneme output) deferred.

### Key Entities *(include if feature involves data)*

- **InputLine**: Represents a user text entry; attributes: `raw_text`, `timestamp_received`, `char_count`.
- **SynthesisRequest**: Links InputLine to synthesis attempt; attributes: `request_id`, `status`, `latency_ms`, `voice_used`.
  - Adds attribute: `audio_format` (value fixed to `pcm16_16khz`).
  - Adds attribute: `chunk_timestamps` (ordered list of monotonic timestamps for each audio chunk when diagnostic mode active; empty otherwise).
- **EvidenceArtifact**: Metadata for stored proof; attributes: `artifact_type`, `path`, `created_at`.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: First audio frame begins within ≤1000 ms for ≥90% of inputs ≤50 chars under baseline conditions.
- **SC-002**: Interactive session supports at least 10 sequential synthesis requests without restart or memory error.
- **SC-003**: Error messages for invalid input or service unavailability are displayed within ≤500 ms of detection.
- **SC-004**: Latency records exist for 100% of requests when diagnostic mode is enabled.
- **SC-005**: Evidence artifacts for P1, P2, P3 scenarios are created and accessible in the feature evidence space.
- **SC-006**: Exiting via the quit command returns success status consistently.
- **SC-007**: 100% of synthesized audio artifacts conform to PCM 16-bit 16 kHz format.
- **SC-008**: Under a rapid submission test of N inputs entered <2s apart, where N = max_queue + 4 (default 7 when max_queue=3), system processes first (active) plus up to `max_queue` queued items and rejects the remainder with correct "queue full" messages; no audio overlap or corruption.
- **SC-009**: Across error scenario tests (service down, oversize input), final process termination (via quit) returns status 0 in 100% of cases.
- **SC-010**: In a diagnostic mode test of at least 3 syntheses, 100% of requests produce a non-empty ordered list of chunk timestamps with average inter-chunk gap ≤150 ms for short phrases (≤50 chars).
- **SC-011**: A mixed-language test phrase containing ≥3 accented characters synthesizes successfully meeting SC-001 latency target; if any failure occurs (simulated or real), a warning appears ≤500 ms after failure detection and session continues.
