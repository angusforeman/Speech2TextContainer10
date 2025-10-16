# Data Model: Azure Speech to Text Container CLI

**Feature**: 001-i-want-to  
**Date**: 2025-10-15  
**Purpose**: Define entities, attributes, relationships, and validation rules

## Entity Definitions

### AudioFile

**Purpose**: Represents the input audio file provided by the user for transcription

**Attributes**:
- `file_path` (string, required): Absolute or relative path to the audio file on local filesystem
- `file_name` (string, derived): Filename extracted from file_path
- `file_extension` (string, derived): Extension indicating format (e.g., ".wav", ".mp3", ".flac")
- `file_size_bytes` (integer, derived): Size of the file in bytes
- `file_size_mb` (float, derived): Size in megabytes (for display/validation)
- `is_valid_format` (boolean, derived): Whether extension matches supported formats
- `is_valid_size` (boolean, derived): Whether size <= 50 MB limit

**Validation Rules**:
- File must exist on filesystem
- `file_size_bytes` MUST be <= 52,428,800 bytes (50 MB)
- `file_extension` MUST be one of: `.wav`, `.mp3`, `.flac` (case-insensitive)
- File must be readable by current process

**Relationships**:
- One AudioFile → One TranscriptionRequest

**State Transitions**: N/A (immutable input)

---

### TranscriptionRequest

**Purpose**: Represents the HTTP request sent to Azure Speech container for transcription

**Attributes**:
- `audio_payload` (bytes, required): Binary audio data read from AudioFile
- `endpoint_url` (string, required): Full URL to Speech container endpoint (default: `http://localhost:5000/speech/recognition/conversation/cognitiveservices/v1`)
- `language_code` (string, required): Language for transcription (fixed: `en-US` for English)
- `format` (string, required): Response format (fixed: `detailed`)
- `diarization_enabled` (boolean, required): Whether to enable speaker diarization (default: true for P3)
- `api_key` (string, required): Subscription key for authentication (from `APIKEY` env var)
- `content_type` (string, required): MIME type of audio (e.g., `audio/wav`, `audio/mpeg`)
- `timeout_seconds` (integer, required): Maximum time to wait for response (default: 300)

**Validation Rules**:
- `endpoint_url` MUST be valid HTTP/HTTPS URL
- `api_key` MUST NOT be empty
- `audio_payload` MUST NOT be empty
- `timeout_seconds` MUST be > 0

**Relationships**:
- One AudioFile → One TranscriptionRequest
- One TranscriptionRequest → One TranscriptionResult (or error)

**State Transitions**:
1. Created (initialized with parameters)
2. Sent (HTTP POST in flight)
3. Completed (response received)
4. Failed (HTTP error or timeout)

---

### TranscriptionResult

**Purpose**: Represents the parsed response from Azure Speech container after transcription

**Attributes**:
- `recognition_status` (string, required): Status of recognition (e.g., "Success", "NoMatch", "InitialSilenceTimeout")
- `duration_ticks` (integer, optional): Total duration of audio in ticks (10,000 ticks = 1ms)
- `duration_seconds` (float, derived): Duration converted to seconds
- `segments` (list of DiarizationSegment, required): List of transcribed segments with speaker info
- `full_transcript` (string, derived): Concatenated text from all segments
- `offset_ticks` (integer, optional): Start offset of first segment in ticks
- `confidence_score` (float, optional): Overall confidence (0.0-1.0) if available
- `raw_json` (dict, optional): Full API response for debugging

**Validation Rules**:
- `recognition_status` MUST be non-empty
- If status is "Success", `segments` MUST NOT be empty
- Each segment in `segments` MUST be valid DiarizationSegment

**Relationships**:
- One TranscriptionRequest → One TranscriptionResult
- One TranscriptionResult → Many DiarizationSegments

**State Transitions**: N/A (immutable result)

---

### DiarizationSegment

**Purpose**: Represents a single timestamped speech segment from one speaker

**Attributes**:
- `speaker_id` (string, optional): Speaker identifier (e.g., "1", "2") if diarization enabled
- `offset_ticks` (integer, required): Start time of segment in ticks
- `duration_ticks` (integer, required): Duration of segment in ticks
- `offset_timestamp` (string, derived): Human-readable start time (HH:MM:SS.mmm)
- `end_timestamp` (string, derived): Human-readable end time (HH:MM:SS.mmm)
- `text` (string, required): Transcribed text for this segment
- `confidence` (float, optional): Confidence score for this segment (0.0-1.0)
- `lexical` (string, optional): Lexical form of text (no punctuation/capitalization)
- `itn` (string, optional): Inverse Text Normalization form
- `masked_itn` (string, optional): ITN with profanity masked
- `display` (string, optional): Display form (preferred for output)

**Validation Rules**:
- `offset_ticks` MUST be >= 0
- `duration_ticks` MUST be > 0
- `text` or `display` MUST NOT be empty
- If `confidence` present, MUST be between 0.0 and 1.0

**Relationships**:
- Many DiarizationSegments → One TranscriptionResult

**State Transitions**: N/A (immutable segment)

---

### EnvironmentConfig

**Purpose**: Represents validated environment configuration required for CLI operation

**Attributes**:
- `docker_available` (boolean, required): Whether Docker daemon is accessible
- `speech_image_present` (boolean, required): Whether Speech container image is pulled
- `speech_container_running` (boolean, optional): Whether container is currently running
- `container_health_status` (string, optional): Health status from `/status` endpoint
- `billing_key_set` (boolean, required): Whether `Billing__SubscriptionKey` env var is set
- `billing_region_set` (boolean, required): Whether `Billing__Region` env var is set
- `billing_endpoint_set` (boolean, required): Whether `Billing` env var is set
- `api_key_set` (boolean, required): Whether `APIKEY` env var is set
- `httpx_importable` (boolean, required): Whether `import httpx` succeeds
- `websocket_importable` (boolean, required): Whether `import websocket` succeeds
- `evidence_dir_writable` (boolean, required): Whether evidence directory is writable
- `validation_timestamp` (string, required): ISO 8601 timestamp of validation run
- `validation_log_path` (string, required): Path to environment check log file

**Validation Rules**:
- All boolean checks MUST pass (true) for environment to be considered valid
- If any check fails, CLI MUST error before attempting transcription

**Relationships**: N/A (standalone configuration)

**State Transitions**:
1. Unvalidated (initial state)
2. Validating (checks running)
3. Valid (all checks passed)
4. Invalid (one or more checks failed)

---

## Data Flow

```
1. User Input
   └─> AudioFile (validate path, size, format)
       └─> TranscriptionRequest (prepare HTTP request)
           └─> [HTTP POST to Speech Container]
               └─> TranscriptionResult (parse response)
                   └─> DiarizationSegments[] (extract speaker timeline)
                       └─> Console Output (formatted timestamps + text)
```

## Validation Summary

| Entity | Required Validations |
|--------|---------------------|
| AudioFile | Exists, readable, size <= 50MB, format in [WAV, MP3, FLAC] |
| TranscriptionRequest | URL valid, API key present, payload non-empty, timeout > 0 |
| TranscriptionResult | Status non-empty, segments present if successful |
| DiarizationSegment | Offset >= 0, duration > 0, text/display non-empty |
| EnvironmentConfig | All boolean checks = true |

## Derived Attributes Calculation

### Timestamp Conversion (ticks → HH:MM:SS.mmm)

```python
def ticks_to_timestamp(ticks: int) -> str:
    """Convert Azure Speech ticks (10,000 ticks = 1ms) to HH:MM:SS.mmm format"""
    milliseconds = ticks / 10000
    seconds = milliseconds / 1000
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(milliseconds % 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
```

### File Size Conversion (bytes → MB)

```python
def bytes_to_mb(size_bytes: int) -> float:
    """Convert bytes to megabytes"""
    return size_bytes / (1024 * 1024)
```

## Error Handling

| Validation Failure | Error Message | Exit Code |
|-------------------|---------------|-----------|
| File not found | "Audio file not found: {path}" | 1 |
| File too large | "Audio file exceeds 50 MB limit (actual: {size} MB)" | 1 |
| Invalid format | "Audio format not supported: {ext}" | 1 |
| API key missing | "APIKEY environment variable not set" | 2 |
| Container unreachable | "Speech container not running at {url}" | 2 |
| Transcription failed | "Transcription failed: {status}" | 2 |
| HTTP error | "HTTP {code}: {message}" | 2 |
| Timeout | "Request timeout after {seconds}s" | 2 |
