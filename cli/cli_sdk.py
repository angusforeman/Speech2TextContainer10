#!/usr/bin/env python3
"""
Basic transcription CLI for Azure Speech-to-Text container using Azure Speech SDK.

This script accepts an audio file and sends it to a locally-running Azure Speech
container for transcription using the official Azure SDK, then displays the timestamped results.
"""

import argparse
import os
import sys
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk


# Constants
DEFAULT_ENDPOINT = "ws://localhost:5000"
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
SUPPORTED_FORMATS = {".wav", ".mp3", ".flac"}


def validate_audio_file(file_path: str) -> Path:
    """Validate audio file exists and meets requirements."""
    audio_path = Path(file_path)
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    if not audio_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    file_extension = audio_path.suffix.lower()
    if file_extension not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported audio format: {file_extension}. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    file_size = audio_path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        file_size_mb = file_size / (1024 * 1024)
        raise ValueError(
            f"File size ({file_size_mb:.2f} MB) exceeds maximum "
            f"allowed size of {MAX_FILE_SIZE_MB} MB"
        )
    
    return audio_path


def load_environment() -> dict:
    """Load required environment variables."""
    api_key = os.getenv("APIKEY") or os.getenv("Billing__SubscriptionKey")
    endpoint = os.getenv("SPEECH_ENDPOINT", DEFAULT_ENDPOINT)
    region = os.getenv("Billing__Region", "local")
    
    if not api_key:
        raise ValueError(
            "API key not found. Set APIKEY or Billing__SubscriptionKey "
            "environment variable."
        )
    
    return {
        "api_key": api_key,
        "endpoint": endpoint,
        "region": region,
    }


def transcribe_audio(audio_path: Path, endpoint: str, api_key: str, region: str, debug: bool = False) -> None:
    """Transcribe audio file using Azure Speech SDK."""
    
    # Configure speech SDK for container endpoint
    if debug:
        print(f"[DEBUG] Endpoint: {endpoint}", file=sys.stderr)
        print(f"[DEBUG] Audio file: {audio_path}", file=sys.stderr)
    
    # Create speech config pointing to the container (not Azure cloud)
    speech_config = speechsdk.SpeechConfig(host=endpoint)
    
    # Create audio config from file
    audio_config = speechsdk.AudioConfig(filename=str(audio_path))
    
    # Create speech recognizer
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    
    if debug:
        print("[DEBUG] Starting recognition...", file=sys.stderr)
    
    # Perform one-shot recognition
    result = speech_recognizer.recognize_once()
    
    if debug:
        print(f"[DEBUG] Result reason: {result.reason}", file=sys.stderr)
    
    # Check result
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        # Calculate timestamp (for single result, starts at 0)
        offset_seconds = result.offset / 10_000_000  # Convert from ticks
        hours = int(offset_seconds // 3600)
        minutes = int((offset_seconds % 3600) // 60)
        seconds = offset_seconds % 60
        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        
        print(f"[{timestamp}] {result.text}")
        
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("Error: No speech could be recognized", file=sys.stderr)
        if debug:
            no_match = result.no_match_details
            print(f"[DEBUG] No match reason: {no_match.reason}", file=sys.stderr)
        sys.exit(1)
        
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print(f"Error: Recognition canceled: {cancellation.reason}", file=sys.stderr)
        
        if cancellation.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {cancellation.error_details}", file=sys.stderr)
            if "connection" in cancellation.error_details.lower():
                print("\nHint: Ensure the Speech container is running at the configured endpoint.", file=sys.stderr)
        
        sys.exit(2)


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Transcribe audio file using Azure Speech-to-Text container (SDK version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s audio.wav
  %(prog)s --debug /path/to/meeting.mp3
  %(prog)s --endpoint ws://speech-container:5000 audio.flac

Environment Variables:
  APIKEY                     Azure Speech subscription key (required)
  Billing__SubscriptionKey   Alternative name for subscription key
  SPEECH_ENDPOINT            Speech container endpoint (default: ws://localhost:5000)
  Billing__Region            Azure region (default: local)
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
        help="Enable debug output showing recognition details",
    )
    
    args = parser.parse_args()
    
    try:
        # Validate audio file
        audio_path = validate_audio_file(args.audio_file)
        
        # Load environment configuration
        env_config = load_environment()
        endpoint = args.endpoint or env_config["endpoint"]
        api_key = env_config["api_key"]
        region = env_config["region"]
        
        # Transcribe audio
        transcribe_audio(audio_path, endpoint, api_key, region, debug=args.debug)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.debug if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
