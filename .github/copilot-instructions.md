# Speech2TextContainer10 Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-14

## Active Technologies
- Python 3.10 (per devcontainer base image and docs/techstack.md) + `httpx` for HTTP requests to the Speech container (already part of tech stack); standard library `argparse` for CLI parsing to avoid new packages. (001-speech2textdiarize-i-want)
- Python 3.10 (per devcontainer base image and techstack.md) (001-i-want-to)
- File-based evidence logs in `specs/001-i-want-to/evidence/` directory (001-i-want-to)

## Project Structure
```
src/
tests/
```

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Python 3.10 (per devcontainer base image and docs/techstack.md): Follow standard conventions

## Recent Changes
- 001-i-want-to: Added Python 3.10 (per devcontainer base image and techstack.md)
- 001-i-want-to: Added [List only essential packages and justify each per "Minimal Dependencies Only"]
- 001-speech2textdiarize-i-want: Added Python 3.10 (per devcontainer base image and docs/techstack.md) + `httpx` for HTTP requests to the Speech container (already part of tech stack); standard library `argparse` for CLI parsing to avoid new packages.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
