#!/usr/bin/env python3
"""
Basic transcription CLI for Azure Speech-to-Text container.

This script accepts an audio file and sends it to a locally-running Azure Speech
container for transcription, then displays the timestamped results.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx


# Constants
DEFAULT_ENDPOINT = "http://localhost:5000"
DEFAULT_LANGUAGE = "en-US"
DEFAULT_FORMAT = "detailed"
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
SUPPORTED_FORMATS = {".wav", ".mp3", ".flac"}
CONTENT_TYPE_MAP = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".flac": "audio/flac",
}
REQUEST_TIMEOUT_SECONDS = 300


class AudioFile:
    """Represents and validates an input audio file."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_name = self.file_path.name
        self.file_extension = self.file_path.suffix.lower()
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        if not self.file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        self.file_size_bytes = self.file_path.stat().st_size
        self.file_size_mb = self.file_size_bytes / (1024 * 1024)
        
        self.is_valid_format = self.file_extension in SUPPORTED_FORMATS
        self.is_valid_size = self.file_size_bytes <= MAX_FILE_SIZE_BYTES
        
    def validate(self) -> None:
        """Validate file meets all requirements."""
        if not self.is_valid_format:
            raise ValueError(
                f"Unsupported audio format: {self.file_extension}. "
                f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
            )
        
        if not self.is_valid_size:
            raise ValueError(
                f"File size ({self.file_size_mb:.2f} MB) exceeds maximum "
                f"allowed size of {MAX_FILE_SIZE_MB} MB"
            )
    
    def read_bytes(self) -> bytes:
        """Read audio file contents as bytes."""
        return self.file_path.read_bytes()
    
    def get_content_type(self) -> str:
        """Get MIME type for this audio format."""
        return CONTENT_TYPE_MAP.get(self.file_extension, "application/octet-stream")


class DiarizationSegment:
    """Represents a timestamped speech segment."""
    
    def __init__(
        self,
        text: str,
        offset_ticks: int,
        duration_ticks: int,
        speaker_id: Optional[str] = None,
        confidence: Optional[float] = None,
    ):
        self.text = text
        self.offset_ticks = offset_ticks
        self.duration_ticks = duration_ticks
        self.speaker_id = speaker_id
        self.confidence = confidence
        
    @property
    def offset_seconds(self) -> float:
        """Convert offset from ticks to seconds (10,000 ticks = 1ms)."""
        return self.offset_ticks / 10_000_000
    
    @property
    def duration_seconds(self) -> float:
        """Convert duration from ticks to seconds."""
        return self.duration_ticks / 10_000_000
    
    def format_timestamp(self) -> str:
        """Format offset as HH:MM:SS.mmm."""
        total_seconds = self.offset_seconds
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"


def load_environment() -> Dict[str, str]:
    """Load required environment variables."""
    api_key = os.getenv("APIKEY") or os.getenv("Billing__SubscriptionKey")
    endpoint = os.getenv("SPEECH_ENDPOINT", DEFAULT_ENDPOINT)
    
    if not api_key:
        raise ValueError(
            "API key not found. Set APIKEY or Billing__SubscriptionKey "
            "environment variable."
        )
    
    return {
        "api_key": api_key,
        "endpoint": endpoint,
    }


def build_endpoint_url(
    base_endpoint: str,
    language: str = DEFAULT_LANGUAGE,
    format: str = DEFAULT_FORMAT,
    diarization_enabled: bool = False,
) -> str:
    """Construct the full API endpoint URL with query parameters."""
    path = "/speech/recognition/conversation/cognitiveservices/v1"
    url = f"{base_endpoint.rstrip('/')}{path}"
    
    # Build query string
    params = [
        f"language={language}",
        f"format={format}",
    ]
    
    if diarization_enabled:
        params.append("diarizationEnabled=true")
    
    return f"{url}?{'&'.join(params)}"


def send_transcription_request(
    audio_file: AudioFile,
    endpoint_url: str,
    api_key: str,
    debug: bool = False,
) -> Dict:
    """Send audio to Speech container and return JSON response."""
    audio_bytes = audio_file.read_bytes()
    content_type = audio_file.get_content_type()
    
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "Content-Type": content_type,
    }
    
    if debug:
        print(f"[DEBUG] Endpoint: {endpoint_url}", file=sys.stderr)
        print(f"[DEBUG] Content-Type: {content_type}", file=sys.stderr)
        print(f"[DEBUG] Audio size: {len(audio_bytes)} bytes", file=sys.stderr)
    
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = client.post(
                endpoint_url,
                content=audio_bytes,
                headers=headers,
            )
            
            if debug:
                print(f"[DEBUG] Response status: {response.status_code}", file=sys.stderr)
            
            response.raise_for_status()
            return response.json()
            
    except httpx.ConnectError:
        raise ConnectionError(
            f"Speech container not running at {endpoint_url.split('/speech')[0]}. "
            "Ensure container is started and accessible."
        )
    except httpx.TimeoutException:
        raise TimeoutError(
            f"Request timed out after {REQUEST_TIMEOUT_SECONDS} seconds. "
            "Audio file may be too large or container may be overloaded."
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"HTTP {e.response.status_code} error from Speech container: "
            f"{e.response.text}"
        )


def parse_transcription_response(response_json: Dict) -> List[DiarizationSegment]:
    """Extract transcription segments from API response."""
    recognition_status = response_json.get("RecognitionStatus")
    
    if recognition_status != "Success":
        raise ValueError(
            f"Transcription failed with status: {recognition_status}"
        )
    
    nbest = response_json.get("NBest", [])
    if not nbest:
        raise ValueError("No transcription results in response")
    
    # Use the best result (first in NBest array)
    best_result = nbest[0]
    display_text = best_result.get("Display", "")
    
    # For basic transcription (no diarization), create single segment
    offset = response_json.get("Offset", 0)
    duration = response_json.get("Duration", 0)
    confidence = best_result.get("Confidence")
    
    segment = DiarizationSegment(
        text=display_text,
        offset_ticks=offset,
        duration_ticks=duration,
        confidence=confidence,
    )
    
    return [segment]


def render_output(segments: List[DiarizationSegment]) -> None:
    """Display transcription segments with timestamps."""
    for segment in segments:
        timestamp = segment.format_timestamp()
        print(f"[{timestamp}] {segment.text}")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Transcribe audio file using Azure Speech-to-Text container",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s audio.wav
  %(prog)s --debug /path/to/meeting.mp3
  %(prog)s --endpoint http://speech-container:5000 audio.flac

Environment Variables:
  APIKEY                     Azure Speech subscription key (required)
  Billing__SubscriptionKey   Alternative name for subscription key
  SPEECH_ENDPOINT            Speech container endpoint (default: http://localhost:5000)
        """,
    )
    
    parser.add_argument(
        "audio_file",
        help="Path to audio file (WAV, MP3, or FLAC format)",
    )
    
    parser.add_argument(
        "--endpoint",
        help=f"Speech container endpoint URL (default: {DEFAULT_ENDPOINT})",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output showing HTTP request/response details",
    )
    
    args = parser.parse_args()
    
    try:
        # Validate audio file
        audio_file = AudioFile(args.audio_file)
        audio_file.validate()
        
        # Load environment configuration
        env_config = load_environment()
        endpoint = args.endpoint or env_config["endpoint"]
        api_key = env_config["api_key"]
        
        # Build request URL
        endpoint_url = build_endpoint_url(endpoint)
        
        # Send transcription request
        response_json = send_transcription_request(
            audio_file, endpoint_url, api_key, debug=args.debug
        )
        
        # Parse and display results
        segments = parse_transcription_response(response_json)
        render_output(segments)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except TimeoutError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
