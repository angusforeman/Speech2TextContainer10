# Quickstart: Speech2TextDiarize CLI Spike

## Prerequisites
- VS Code with Dev Containers extension.
- Access to Azure Speech resource (subscription key + region) stored as environment variables or `.env` entries.
- Docker Desktop or compatible runtime with at least 8 vCPU, 16 GB RAM.

## 1. Open the DevContainer
1. Clone the repository.
2. Open in VS Code and choose **Reopen in Container**.
3. Ensure `.devcontainer/Dockerfile` provisions required Python tools and that `devcontainer.json` binds Docker socket access.

## 2. Validate Environment
1. Run `./scripts/validate_env.sh` inside the devcontainer.
2. Confirm the script reports PASS for:
   - Docker daemon connectivity and image `speech-to-text-preview:5.0.1` availability.
   - Presence of `Billing__SubscriptionKey` and `Billing__Region` variables.
   - Python module check for `httpx`.
3. Evidence files appear in `specs/001-speech2textdiarize-i-want/evidence/`.

## 3. Launch Azure Speech Container
1. Execute the documented docker run command from `docs/techstack.md`, mapping ports and billing env vars.
2. Wait for `/status` endpoint to return `running` (script already captures this during validation).

## 4. Run CLI Diarization Demo
1. Place the sample audio at `docs/assets/sample-meeting.wav` (or update the path).
2. Execute `python cli/diarize.py docs/assets/sample-meeting.wav`.
3. Observe diarization output in terminal; script also writes to `evidence/diarization-run.txt`.

## 5. Capture Spike Findings
1. Review diarization accuracy and timing.
2. Update `docs/diarization-summary.md` with highlights, limitations, and follow-up actions.
3. Attach evidence paths in the summary for stakeholder review.

## 6. Cleanup
- Stop the Speech container with `docker stop speech-to-text-preview`.
- Remove any temporary audio files if they contain sensitive content.
