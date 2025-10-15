# Sample Meeting Audio Preparation

The Speech2TextDiarize CLI spike expects a short, multi-speaker meeting recording for end-to-end validation. Use the guidance below to prepare the sample assets.

## Audio Requirements
- **Format**: WAV, mono, 16 kHz sampling rate.
- **Duration**: 4–6 minutes to keep request times within the spec success criteria.
- **Content**: At least two distinct speakers discussing multiple topics (e.g., weekly stand-up, project planning call).

## Acquisition Steps
1. Record or source a meeting audio clip that satisfies the requirements above. Avoid sensitive information; anonymise participants where needed.
2. Save the file as `sample-meeting.wav` inside this directory (`docs/assets/sample-meeting.wav`).
3. If your source file is stereo or different sample rate, normalise it using a tool such as `ffmpeg`:
   ```bash
   ffmpeg -i input.mp3 -ac 1 -ar 16000 docs/assets/sample-meeting.wav
   ```

## Reference Transcript
- Create or refine a ground-truth transcript that matches the audio.
- Store the transcript as Markdown at `docs/assets/sample-meeting-reference.md`.
- Use speaker headings, for example:
  ```markdown
  ### Speaker 1
  - Welcome everyone to the planning sync...

  ### Speaker 2
  - Thanks! I’ll start with the roadmap update...
  ```

## Verification Checklist
- [ ] Audio file exists at `docs/assets/sample-meeting.wav`.
- [ ] Transcript file exists at `docs/assets/sample-meeting-reference.md` and aligns with audio content.
- [ ] File permissions allow the devcontainer user (`vscode`) to read the audio and transcript files.
- [ ] Sensitive data is scrubbed or masked before committing artefacts.

Maintaining these assets alongside the specification ensures the diarization demo remains reproducible for the spike review.
