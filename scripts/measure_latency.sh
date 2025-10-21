#!/usr/bin/env bash
# T11: Latency measurement script
# Measures submission->first audio chunk latency across multiple short phrases.
# Handles queued scenario by recording both enqueue time and synthesis start.
# Output artifact: assets/output/latency.txt
# Always exits 0.
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
OUT_DIR="$REPO_ROOT/assets/output"
ARTIFACT="$OUT_DIR/latency.txt"
mkdir -p "$OUT_DIR"
truncate -s 0 "$ARTIFACT"

PHRASES=("This is a test of multi phrase latency" "Here is another quick test following on" "Phrase number 3" "And here is the fourth phrase" "And a fifth, as in fifth column" "Sixth" "Finally 7th")
MAX_QUEUE=${TTS_MAX_QUEUE:-6}
HOST=${TTS_HOST_URL:-http://localhost:5001}
VOICE=${VOICE_NAME:-en-US-JennyNeural}

python3 - <<'PY' "$ARTIFACT" "$HOST" "$VOICE" "$MAX_QUEUE" "${PHRASES[@]}"
import sys, time, pathlib, importlib
artifact = pathlib.Path(sys.argv[1])
host = sys.argv[2]
voice = sys.argv[3]
max_queue = int(sys.argv[4])
phrases = sys.argv[5:]

repo_root = pathlib.Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
qm = importlib.import_module("cli.queue_manager")
tts = importlib.import_module("cli.tts_synth")

manager = qm.QueueManager(host=host, voice=voice, max_queue=max_queue)
submission_records = []
for p in phrases:
    mono_before_submit = time.perf_counter()
    decision = manager.submit(p)
    submission_records.append((p, mono_before_submit, decision))
    time.sleep(0.02)  # small stagger

manager.wait_all(timeout=60)
results_map = {r.request_id: r for r in manager.results}

lines = ["# latency measurement", f"# host={host}", f"# voice={voice}", f"# max_queue={max_queue}"]
lines.append("# columns: request_id|decision|submit_ms|start_ms|first_audio_ms|queue_delay_ms|synth_latency_ms|text")

for text, submit_mono, decision in submission_records:
    rid = decision.request_id
    dec = decision.decision
    res = results_map.get(rid)
    submit_ms = int(submit_mono * 1000)
    if res and res.latency_ms is not None and res.started_monotonic and tts is not None:
        start_ms = int(res.started_monotonic * 1000)
        first_audio_ms = int((res.started_monotonic + (res.latency_ms / 1000.0)) * 1000) if res.latency_ms is not None else start_ms
        queue_delay_ms = start_ms - submit_ms
        synth_latency_ms = res.latency_ms
    else:
        start_ms = -1
        first_audio_ms = -1
        queue_delay_ms = -1
        synth_latency_ms = -1
    lines.append(f"{rid}|{dec}|{submit_ms}|{start_ms}|{first_audio_ms}|{queue_delay_ms}|{synth_latency_ms}|{text}")

import wave, json
from contextlib import closing

# Build combined WAV (concatenate raw frames) if there are successful audio paths
ordered_results = [results_map.get(rec.request_id) for _,_,rec in submission_records if results_map.get(rec.request_id)]
audio_paths = [r.audio_path for r in ordered_results if r and r.success and r.audio_path]
# Sort audio_paths by the order of submission completion (ordered_results already reflects submission order promotion)
combined_path = None
segment_index = []  # list of {request_id, text, start_frame, end_frame, frames, audio_path}
if audio_paths:
    first = audio_paths[0]
    try:
        with closing(wave.open(first, 'rb')) as wf_first:
            params = wf_first.getparams()  # (nchannels, sampwidth, framerate, nframes, comptype, compname)
        # Verify all share identical core parameters (channels, width, rate)
        compatible = True
        for pth in audio_paths[1:]:
            try:
                with closing(wave.open(pth, 'rb')) as wf_chk:
                    ch, sw, fr, nf, ct, cn = wf_chk.getparams()
                if (ch, sw, fr) != (params.nchannels, params.sampwidth, params.framerate):
                    compatible = False
                    break
            except Exception:
                compatible = False
                break
        if compatible:
            ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
            combined_path = str(artifact.parent / f"latency_combined_{ts}.wav")
            with closing(wave.open(combined_path, 'wb')) as wf_out:
                wf_out.setnchannels(params.nchannels)
                wf_out.setsampwidth(params.sampwidth)
                wf_out.setframerate(params.framerate)
                wf_out.setcomptype(params.comptype, params.compname)
                current_frame = 0
                for r in ordered_results:
                    if not (r and r.success and r.audio_path):
                        continue
                    pth = r.audio_path
                    try:
                        with closing(wave.open(pth, 'rb')) as wf_in:
                            frame_count = wf_in.getnframes()
                            frames = wf_in.readframes(frame_count)
                        wf_out.writeframes(frames)
                        segment_index.append({
                            "request_id": r.request_id,
                            "text": r.text,
                            "start_frame": current_frame,
                            "end_frame": current_frame + frame_count,
                            "frames": frame_count,
                            "audio_path": pth,
                        })
                        current_frame += frame_count
                    except Exception:
                        continue
        else:
            combined_path = None
    except Exception:
        combined_path = None

if combined_path and segment_index:
    # Append per-file mapping lines to artifact for human inspection
    lines.insert(1, f"# combined_wav={combined_path}")
    lines.insert(2, "# segment_columns: request_id|start_frame|end_frame|frames|audio_path|text")
    for seg in segment_index:
        lines.append(f"SEG|{seg['request_id']}|{seg['start_frame']}|{seg['end_frame']}|{seg['frames']}|{seg['audio_path']}|{seg['text']}")
else:
    lines.insert(1, f"# combined_wav=NONE")

artifact.write_text("\n".join(lines)+"\n", encoding="utf-8")

index_path = artifact.parent / "latency_index.json"
index_payload = {
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "host": host,
    "voice": voice,
    "max_queue": max_queue,
    "combined_wav": combined_path,
    "segments": segment_index,
}
index_path.write_text(json.dumps(index_payload, indent=2) + "\n", encoding="utf-8")
PY

echo "Latency artifact written to $ARTIFACT"
exit 0