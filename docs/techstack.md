# Local Azure Speech-to-Text Preview 5.0.1 Tech Stack

## Azure Prerequisites
- Azure subscription with an AI Services (Speech) or AI Foundry Speech resource.
- Retrieve the resource key and matching region identifier (for example `eastus`, `westeurope`, `uksouth`). Keys are region-scoped; container billing must use the same region name.
- Allow outbound HTTPS (port 443) from the host running the container to the Speech billing endpoint so usage metering succeeds.

## Container Runtime
- Docker Desktop (Windows) or any OCI-compliant runtime capable of running `mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text-preview:5.0.1`.
- Recommended host sizing: at least 8 vCPU and 16 GB RAM; add NVIDIA GPU passthrough (`--gpus all`) if you need near real-time throughput.
- Mount a persistent volume (for example `C:\speechdata:/mnt/speech`) to cache downloaded model bundles and reduce cold start times.

## Application Components
- CLI demo implemented in Python 3.10+ (in a DevContainer) using `httpx` to call the container's REST diarization endpoint.
- Optional FFmpeg preprocessing step to normalize audio (mono, 16 kHz WAV) before submission.
- `.env` file or secure secret store providing container `Billing__SubscriptionKey` and `Billing__Region`, plus CLI authentication headers.
- PowerShell convenience script (`Invoke-SpeechDiarization.ps1`) to warm the container via `/status`, pass in configuration, and call the Python entry point.

## DevContainer Environment
- Base image: `mcr.microsoft.com/devcontainers/python:1-3.10-bullseye` to align with the Python 3.10 CLI target while keeping Debian tooling for native package builds.
- Recommended features: enable the `ghcr.io/devcontainers/features/azure-cli:1` feature for scripting against Azure, and `ghcr.io/devcontainers/features/docker-in-docker:2` if you want to run the Speech container side-by-side during CLI development.
- Network strategy: attach the devcontainer to the same Docker network as the Speech-to-Text container (`speech-net`) so the CLI can call `http://speech-container:5000/...` without routing through the host.
- Volume mounts: map a local workspace cache (for example `${containerWorkspaceFolder}/.models`) to the host filesystem if you want to persist downloaded Speech model bundles across rebuilds.
- Shared environment: surface `Billing__SubscriptionKey`, `Billing__Region`, and any CLI-specific settings through `.env` or VS Code secrets so both the Speech container and the devcontainer can reuse them.


## Devcontainer to Local Container Communication
- A VS Code devcontainer is another Docker container; will reach the Speech to Text container through Docker networking.
- Attach both containers to a named bridge network (for example `docker network create speech-net` then `--network speech-net`), and call the peer by container name: `http://speech-container:5000/...`.
- When using devcontainer `networkMode: service:<name>` or `forwardPorts`, expose the target container port to the host and call via `http://host.docker.internal:5000` (Windows/macOS) or `http://127.0.0.1:5000` with an `extraHosts` entry for `host.docker.internal` on Linux.
- With Docker Compose, model both services in one file; Compose creates a default network and DNS entries, so Python code inside the devcontainer can use `requests.post("http://speech:5000/...")`.
- Ensure the Speech container listens on `0.0.0.0` and that host firewalls allow the published port if routing through the host.


## Data Flow Overview
1. User invokes the CLI with an audio file path.
2. CLI (Python + `httpx`) posts the audio payload to `http://localhost:5000/speech/recognition/conversation/diarize?language=en-US&format=detailed`.
3. Container processes the request, performs diarization, and returns JSON with speaker segments and transcripts.
4. CLI renders the diarization timeline and transcript to stdout; optional log sink captures container output.


