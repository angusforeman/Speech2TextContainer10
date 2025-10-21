"""Queue manager (T05) enforcing single active synthesis plus one queued.

Implements Functional Requirement FR-012 and supports Success Criterion SC-008.

Policy:
  - If no active request: new submission becomes active immediately.
  - If active running and no queued: submission is queued (one-slot buffer).
  - If active running and already queued: submission rejected (queue full).

Thread model: Each active (and later promoted queued) request runs in its own
thread performing blocking synthesis via `tts_synth.synthesize`.

Evidence: Decisions and completion results can be consumed by caller to build
`assets/output/queue.txt` for task validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import threading
import time
import uuid

from . import tts_synth


@dataclass
class QueueDecision:
    request_id: str
    text: str
    decision: str  # ACTIVE_STARTED | QUEUED | REJECTED_QUEUE_FULL
    timestamp: float  # monotonic time


@dataclass
class CompletedResult:
    request_id: str
    text: str
    success: bool
    latency_ms: Optional[int]
    audio_path: Optional[str]
    reason: str
    error: Optional[str]
    started_monotonic: float
    completed_monotonic: float


class QueueManager:
    def __init__(self, host: str, voice: str, max_queue: int = 3):
        """Initialize queue manager.

        Args:
            host: Speech service host URL
            voice: Voice name
            max_queue: Maximum number of queued items (excluding active). Default 3.
        """
        if max_queue < 0:
            raise ValueError("max_queue must be >= 0")
        self._host = host
        self._voice = voice
        self._max_queue = max_queue
        self._lock = threading.Lock()
        self._active_id: Optional[str] = None
        self._active_thread: Optional[threading.Thread] = None
        self._active_text: Optional[str] = None
        self._queue: List[tuple[str, str]] = []  # list of (request_id, text)
        self._results: List[CompletedResult] = []
        self._stop = False

    def submit(self, text: str) -> QueueDecision:
        t = text.strip()
        if not t:
            # Ignore empty submissions; treat as rejection but distinct reason later if needed
            return QueueDecision(request_id=str(uuid.uuid4()), text=text, decision="REJECTED_EMPTY", timestamp=time.perf_counter())
        with self._lock:
            now = time.perf_counter()
            if self._active_id is None:
                rid = str(uuid.uuid4())
                self._active_id = rid
                self._active_text = t
                self._active_thread = threading.Thread(target=self._run_active, args=(rid, t), daemon=True)
                self._active_thread.start()
                return QueueDecision(request_id=rid, text=t, decision="ACTIVE_STARTED", timestamp=now)
            if len(self._queue) < self._max_queue:
                rid = str(uuid.uuid4())
                self._queue.append((rid, t))
                return QueueDecision(request_id=rid, text=t, decision="QUEUED", timestamp=now)
            return QueueDecision(request_id=str(uuid.uuid4()), text=t, decision="REJECTED_QUEUE_FULL", timestamp=now)

    def _run_active(self, rid: str, text: str):
        start_mono = time.perf_counter()
        synth = tts_synth.synthesize(text, host=self._host, voice=self._voice)
        end_mono = time.perf_counter()
        result = CompletedResult(
            request_id=rid,
            text=text,
            success=synth.success,
            latency_ms=synth.latency_ms,
            audio_path=synth.audio_path,
            reason=synth.reason,
            error=synth.error,
            started_monotonic=start_mono,
            completed_monotonic=end_mono,
        )
        with self._lock:
            self._results.append(result)
            # Promote next queued if any
            if not self._stop and self._queue:
                qid, qtext = self._queue.pop(0)
                self._active_id = qid
                self._active_text = qtext
                self._active_thread = threading.Thread(target=self._run_active, args=(qid, qtext), daemon=True)
                self._active_thread.start()
            else:
                self._active_id = None
                self._active_text = None
                self._active_thread = None

    def wait_all(self, timeout: Optional[float] = None):
        start = time.perf_counter()
        while True:
            with self._lock:
                done = self._active_id is None and not self._queue
            if done:
                return True
            if timeout is not None and (time.perf_counter() - start) > timeout:
                return False
            time.sleep(0.05)

    @property
    def results(self) -> List[CompletedResult]:
        with self._lock:
            return list(self._results)

    @property
    def pending_queue_length(self) -> int:
        with self._lock:
            return len(self._queue)

    @property
    def max_queue(self) -> int:
        return self._max_queue

    def stop(self):
        with self._lock:
            self._stop = True

__all__ = ["QueueManager", "QueueDecision", "CompletedResult"]
