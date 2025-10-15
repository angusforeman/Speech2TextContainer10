# Quickstart: Azure Speech to Text Container CLI

**Feature**: 001-i-want-to  
**Version**: 1.0.0  
**Date**: 2025-10-15

## Overview

This guide walks through setting up and using the Azure Speech-to-Text container CLI for transcribing multi-speaker meeting audio with diarization (speaker identification).

**Prerequisites**:
- Docker installed and running
- Azure subscription with Speech service resource
- VS Code with Dev Containers extension

---

## Phase 1: Environment Setup

### Step 1: Obtain Azure Credentials

1. Navigate to [Azure Portal](https://portal.azure.com)
2. Create or select an **Azure AI Services** or **Speech** resource
3. Go to **Keys and Endpoint** section
4. Copy the following values:
   - **Key 1** → Will be used for `Billing__SubscriptionKey` and `APIKEY`
   - **Region** → e.g., `eastus`, `westeurope`, `uksouth`
   - **Endpoint** → Full HTTPS URL, e.g., `https://eastus.api.cognitive.microsoft.com/`

### Step 2: Configure Environment Variables

1. In the repository root, create a `.env` file (this file is gitignored):

```bash
# .env file
Billing__SubscriptionKey=your-subscription-key-here
Billing__Region=eastus
Billing=https://eastus.api.cognitive.microsoft.com/
APIKEY=your-subscription-key-here
```

2. Replace `your-subscription-key-here` with your actual Key 1 value
3. Update region and endpoint to match your resource

**Important**: Never commit `.env` to version control.

### Step 3: Open in Dev Container

1. Open repository in VS Code
2. Press `F1` → `Dev Containers: Rebuild and Reopen in Container`
3. Wait for container build (first time: ~5-10 minutes)
4. Container will attach and show reminder message about validation

---

## Phase 2: Environment Validation

### Step 4: Run Validation Script

```bash
./scripts/validate_env.sh
```

**Expected output** (all PASS):
```
2025-10-15T10:30:00Z|docker-daemon|PASS|docker info succeeded
2025-10-15T10:30:05Z|docker-pull|PASS|Pulled mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-gb
2025-10-15T10:30:10Z|docker-image|PASS|Image available: [mcr.microsoft.com/...] sha256:...
2025-10-15T10:30:10Z|billing-key|PASS|Billing__SubscriptionKey set (length 32)
2025-10-15T10:30:10Z|billing-region|PASS|Billing__Region set
2025-10-15T10:30:10Z|billing-endpoint|PASS|Billing endpoint set
2025-10-15T10:30:10Z|api-key|PASS|APIKEY set
2025-10-15T10:30:11Z|python-modules|PASS|httpx and websocket imports succeeded
2025-10-15T10:30:11Z|evidence-write|PASS|Write access confirmed for .../evidence
Environment validation PASSED.
```

**If validation fails**:
- Check `.env` file exists and contains all variables
- Verify Docker daemon is running: `docker info`
- Ensure network connectivity for image pull
- Review log: `specs/001-i-want-to/evidence/environment-check.txt`

---

## Phase 3: Start Speech Container

### Step 5: Create Docker Network (once)

```bash
docker network create speech-net 2>/dev/null || true
```

This creates an isolated network for devcontainer-to-container communication.

### Step 6: Start the Speech Container

```bash
docker run -d \
  --name speech-to-text-preview \
  --network speech-net \
  -p 5000:5000 \
  -e EULA=accept \
  -e Billing__SubscriptionKey="$Billing__SubscriptionKey" \
  -e Billing__Region="$Billing__Region" \
  -e Billing="$Billing" \
  -e APIKEY="$APIKEY" \
  -v "$(pwd)/.models:/mnt/models" \
  mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-gb
```

**Expected behavior**:
- Container starts in background (detached mode)
- First run downloads models (~1-2 GB), takes 30-60 seconds
- Subsequent runs are faster (~10-20 seconds) with cached models

### Step 7: Verify Container Health

```bash
curl http://localhost:5000/status
```

**Expected response**:
```json
{"status": "Healthy", "version": "5.0.3-preview"}
```

If connection refused, wait 20-30 seconds and retry.

### Step 8: Check Container Logs (Optional)

```bash
docker logs speech-to-text-preview
```

Look for:
- `Billing validation successful`
- `Model loaded successfully`
- `Ready to accept requests`

---

## Phase 4: Transcribe Audio

### Step 9: Verify CLI Help

```bash
python cli/cli.py --help
```

**Expected output**:
```
usage: cli.py [-h] [--debug] audio_file

Transcribe audio via Azure Speech container

positional arguments:
  audio_file  Path to audio file (WAV/MP3)

optional arguments:
  -h, --help  show this help message and exit
  --debug     Enable debug logging
```

### Step 10: Run Basic Transcription (P1)

```bash
python cli/cli.py docs/assets/sample-meeting.wav
```

**Expected output** (timestamped segments):
```
[00:00:01.200] Hello, everyone. Welcome to today's meeting.
[00:00:05.800] Thanks for joining. Let's start with the agenda.
[00:00:10.500] The first item is project status update.
...
```

**Output format**: `[HH:MM:SS.mmm] Transcribed text`

### Step 11: Run Diarization Transcription (P3)

```bash
python cli/diarize.py docs/assets/sample-meeting.wav
```

**Expected output** (with speaker labels):
```
[00:00:01.200] Speaker 1: Hello, everyone. Welcome to today's meeting.
[00:00:05.800] Speaker 2: Thanks for joining. Let's start with the agenda.
[00:00:10.500] Speaker 1: The first item is project status update.
...
```

### Step 12: Enable Debug Mode (Optional)

```bash
python cli/diarize.py --debug docs/assets/sample-meeting.wav
```

Shows additional information:
- HTTP request details
- API response structure
- Timing information
- Confidence scores

---

## Phase 5: Troubleshooting

### Common Issues

#### Issue: "Audio file not found"
**Solution**: Verify file path is correct. Use absolute path or path relative to repo root.

```bash
# Correct
python cli/cli.py docs/assets/sample-meeting.wav

# Also correct
python cli/cli.py /workspaces/Speech2TextContainer10/docs/assets/sample-meeting.wav
```

#### Issue: "Audio file exceeds 50 MB limit"
**Solution**: Use a smaller audio file or compress/trim the existing file.

```bash
# Check file size
ls -lh docs/assets/sample-meeting.wav

# If too large, trim with ffmpeg (if available)
ffmpeg -i large-file.wav -t 300 -c copy trimmed-file.wav
```

#### Issue: "Audio format not supported"
**Solution**: Convert to WAV or MP3 format.

```bash
# Check format
file docs/assets/sample-meeting.wav

# Supported: .wav, .mp3, .flac
# Convert with ffmpeg
ffmpeg -i input.m4a -ar 16000 -ac 1 output.wav
```

#### Issue: "Speech container not running at http://localhost:5000"
**Solution**: Start the container (Step 6) and verify health (Step 7).

```bash
# Check if container is running
docker ps | grep speech-to-text-preview

# If not running, start it
docker start speech-to-text-preview

# If doesn't exist, run the full docker run command (Step 6)
```

#### Issue: "APIKEY environment variable not set"
**Solution**: Verify `.env` file exists and is loaded.

```bash
# Check if variable is set
echo $APIKEY

# If empty, source .env manually
set -a; source .env; set +a

# Verify
echo $APIKEY
```

#### Issue: Container logs show "Billing validation failed"
**Solution**: Verify credentials match your Azure resource.

```bash
# Check container logs
docker logs speech-to-text-preview 2>&1 | grep -i billing

# Common causes:
# 1. Wrong subscription key
# 2. Mismatched region (key from eastus, but Billing__Region=westus)
# 3. Endpoint typo
# 4. Expired/invalid subscription
```

---

## Evidence & Verification

All test runs automatically create evidence files in:
```
specs/001-i-want-to/evidence/
├── environment-check.txt    # Validation script output
├── cli-smoke.txt            # CLI help output
├── transcription-run.txt    # Basic transcription test
└── diarization-run.txt      # Diarization transcription test
```

These files serve as proof that the system works and can be referenced in documentation or reviews.

---

## Success Criteria Verification

| Criterion | How to Verify | Expected Result |
|-----------|---------------|-----------------|
| SC-001: Transcribe 5min audio in <10min | Time `python cli/diarize.py sample.wav` | Total time < 600s |
| SC-002: Validation completes in <30s | Time `./scripts/validate_env.sh` | Time < 30s |
| SC-003: Readable transcription | Read output of transcription | Can understand topics |
| SC-004: 100% success with valid files | Try 3 different valid audio files | All produce output |
| SC-005: Clear error messages | Test with missing Docker, bad file | Error identifies problem |
| SC-006: Complete demo without assistance | Follow this guide start-to-finish | All steps succeed |
| SC-007: 80%+ speaker attribution | Compare diarization output to audio | Speakers correctly identified |

---

## Next Steps

- **Add custom audio**: Place your meeting recordings in `docs/assets/`
- **Review output**: Check `evidence/` directory for logged results
- **Experiment**: Try different audio formats, lengths, speaker counts
- **Contribute**: Report issues or improvements via GitHub

---

## Quick Reference

```bash
# Daily workflow
1. Start devcontainer (VS Code: Reopen in Container)
2. docker start speech-to-text-preview     # If container exists
3. curl http://localhost:5000/status       # Verify ready
4. python cli/diarize.py path/to/audio.wav # Transcribe
```

**Important endpoints**:
- Container health: `http://localhost:5000/status`
- Transcription API: `http://localhost:5000/speech/recognition/conversation/cognitiveservices/v1`

**Key files**:
- Configuration: `.env` (create from `.env.example`)
- Validation: `./scripts/validate_env.sh`
- CLI: `cli/cli.py` (basic), `cli/diarize.py` (with speakers)
- Evidence: `specs/001-i-want-to/evidence/`
