#!/usr/bin/env python3
"""
Basic transcription CLI for Azure Speech-to-Text container using Azure Speech SDK.

This script accepts an audio file and sends it to a locally-running Azure Speech
container for transcription using the official Azure SDK, then displays the timestamped results.
"""

import argparse
import os
import sys
import time
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
    billing = os.getenv("Billing", "")
    
    if not api_key:
        raise ValueError(
            "API key not found. Set APIKEY or Billing__SubscriptionKey "
            "environment variable."
        )
    
    if not region or region == "local":
        raise ValueError(
            "Billing__Region not found or set to 'local'. "
            "For cloud mode, set Billing__Region environment variable (e.g., 'uksouth')."
        )
    
    return {
        "api_key": api_key,
        "endpoint": endpoint,
        "region": region,
        "billing": billing,
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


def transcribe_with_diarization(audio_path: Path, endpoint: str, api_key: str, region: str, cloud_mode: bool = False, debug: bool = False) -> None:
    """Transcribe audio file with speaker diarization using Azure Speech SDK.
    
    Supports both container and cloud modes:
    - Container mode (cloud_mode=False): Uses ConversationTranscriber with container endpoint
      Note: As of v5.0.3, containers do NOT support ConversationTranscriber - will fail with 404
      This is implemented for future container versions that may support diarization
    - Cloud mode (cloud_mode=True): Uses Azure Speech service with subscription/region
    
    Args:
        audio_path: Path to audio file
        endpoint: Container WebSocket endpoint (e.g., ws://localhost:5000)
        api_key: Azure subscription key
        region: Azure region (e.g., uksouth)
        cloud_mode: If True, use cloud service; if False, use container
        debug: Enable debug output
    """
    
    if debug:
        mode = "cloud" if cloud_mode else "container"
        print(f"[DEBUG] Mode: {mode}", file=sys.stderr)
        if cloud_mode:
            print(f"[DEBUG] Region: {region}", file=sys.stderr)
        else:
            print(f"[DEBUG] Endpoint: {endpoint}", file=sys.stderr)
        print(f"[DEBUG] Audio file: {audio_path}", file=sys.stderr)
        print("[DEBUG] Diarization enabled", file=sys.stderr)
    
    # Create speech config based on mode
    if cloud_mode:
        # Cloud mode: Use subscription and region
        speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
    else:
        # Container mode: Use host endpoint
        # Note: This will fail with current v5.0.3 containers (404 error)
        # Implemented for future container versions that support ConversationTranscriber
        speech_config = speechsdk.SpeechConfig(host=endpoint)
        if debug:
            print("[DEBUG] WARNING: Current containers (v5.0.3) do NOT support ConversationTranscriber", file=sys.stderr)
            print("[DEBUG] This will likely fail with HTTP 404 error", file=sys.stderr)
    speech_config.speech_recognition_language = "en-US"
    
    # Enable intermediate diarization results
    speech_config.set_property(
        speechsdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults,
        "true"
    )
    
    # Create audio config from file
    audio_config = speechsdk.AudioConfig(filename=str(audio_path))
    
    # Create conversation transcriber
    conversation_transcriber = speechsdk.transcription.ConversationTranscriber(
        speech_config=speech_config,
        audio_config=audio_config
    )
    
    # Track transcription state
    transcribing_stop = False
    error_occurred = False
    
    def format_timestamp(offset_ticks: int) -> str:
        """Convert offset ticks to HH:MM:SS.mmm format."""
        offset_seconds = offset_ticks / 10_000_000
        hours = int(offset_seconds // 3600)
        minutes = int((offset_seconds % 3600) // 60)
        seconds = offset_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    
    def transcribed_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        """Handle final transcribed results."""
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            timestamp = format_timestamp(evt.result.offset)
            speaker_id = evt.result.speaker_id if evt.result.speaker_id else "Unknown"
            print(f"[{timestamp}] Speaker {speaker_id}: {evt.result.text}")
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            if debug:
                print("[DEBUG] NOMATCH: Speech could not be transcribed", file=sys.stderr)
    
    def transcribing_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        """Handle intermediate transcribing results (debug only)."""
        if debug:
            timestamp = format_timestamp(evt.result.offset)
            speaker_id = evt.result.speaker_id if evt.result.speaker_id else "Unknown"
            print(f"[DEBUG] TRANSCRIBING [{timestamp}] Speaker {speaker_id}: {evt.result.text}", file=sys.stderr)
    
    def session_started_cb(evt: speechsdk.SessionEventArgs):
        """Handle session started event."""
        if debug:
            print(f"[DEBUG] Session started: {evt.session_id}", file=sys.stderr)
    
    def session_stopped_cb(evt: speechsdk.SessionEventArgs):
        """Handle session stopped event."""
        nonlocal transcribing_stop
        if debug:
            print(f"[DEBUG] Session stopped: {evt.session_id}", file=sys.stderr)
        transcribing_stop = True
    
    def canceled_cb(evt: speechsdk.SessionEventArgs):
        """Handle cancellation event."""
        nonlocal transcribing_stop, error_occurred
        if debug:
            print(f"[DEBUG] Canceled event", file=sys.stderr)
        
        cancellation = evt.result.cancellation_details if hasattr(evt, 'result') else None
        if cancellation:
            print(f"Error: Recognition canceled: {cancellation.reason}", file=sys.stderr)
            
            if cancellation.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation.error_details}", file=sys.stderr)
                if "connection" in cancellation.error_details.lower():
                    print("\nHint: Ensure the Speech container is running at the configured endpoint.", file=sys.stderr)
                error_occurred = True
        
        transcribing_stop = True
    
    # Connect callbacks to events
    conversation_transcriber.transcribed.connect(transcribed_cb)
    if debug:
        conversation_transcriber.transcribing.connect(transcribing_cb)
    conversation_transcriber.session_started.connect(session_started_cb)
    conversation_transcriber.session_stopped.connect(session_stopped_cb)
    conversation_transcriber.canceled.connect(canceled_cb)
    
    if debug:
        print("[DEBUG] Starting transcription with diarization...", file=sys.stderr)
    
    # Start transcription
    conversation_transcriber.start_transcribing_async()
    
    # Wait for transcription to complete
    while not transcribing_stop:
        time.sleep(0.5)
    
    # Stop transcription
    conversation_transcriber.stop_transcribing_async()
    
    if error_occurred:
        sys.exit(2)


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Transcribe audio file using Azure Speech-to-Text container (SDK version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Container mode - basic transcription (working)
  %(prog)s audio.wav
  %(prog)s --debug /path/to/meeting.mp3
  %(prog)s --endpoint ws://speech-container:5000 audio.flac
  
  # Container mode - diarization (will fail with v5.0.3, future support)
  %(prog)s --diarize multi-speaker.wav
  
  # Cloud mode - diarization (working)
  %(prog)s --cloud --diarize multi-speaker-conversation.wav
  %(prog)s --cloud --diarize --debug meeting.mp3

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
        "--cloud",
        action="store_true",
        help="Use Azure cloud service instead of local container",
    )
    
    parser.add_argument(
        "--diarize",
        action="store_true",
        help="Enable speaker diarization (identifies different speakers). "
             "Note: Current containers (v5.0.3) do NOT support this - use --cloud for working diarization",
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
        api_key = env_config["api_key"]
        region = env_config["region"]
        endpoint = args.endpoint or env_config["endpoint"]
        
        # Transcribe audio
        if args.diarize:
            # Diarization mode: Use ConversationTranscriber
            if not args.cloud:
                # Container diarization: Warn user this will likely fail
                print("WARNING: Speaker diarization is NOT supported in current containers (v5.0.3).", file=sys.stderr)
                print("This will attempt to use ConversationTranscriber with the container but will likely fail.", file=sys.stderr)
                print("For working diarization, use: --cloud --diarize\n", file=sys.stderr)
            
            transcribe_with_diarization(
                audio_path, 
                endpoint, 
                api_key, 
                region, 
                cloud_mode=args.cloud, 
                debug=args.debug
            )
        elif args.cloud:
            # Cloud mode without diarization - not implemented yet
            print("Error: Cloud mode without diarization not yet implemented.", file=sys.stderr)
            print("Use --cloud --diarize for speaker diarization, or omit --cloud for container transcription.", file=sys.stderr)
            return 1
        else:
            # Container mode: Basic transcription
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
