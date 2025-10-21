# Local Azure Speech-to-Text Preview Tech Stack

## Azure Prerequisites
- Azure subscription with an AI Services (Speech) or AI Foundry Speech resource.
- Retrieve the resource key and matching region identifier (for example `eastus`, `westeurope`, `uksouth`). Keys are region-scoped; container billing must use the same region name.
- Allow outbound HTTPS (port 443) from the host running the container to the Speech billing endpoint so usage metering succeeds.

## Container Runtime
- Docker Desktop (Windows) or any OCI-compliant runtime capable of running `mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-gb` (current preview tag available via the Microsoft Container Registry; earlier tags such as `5.0.1` are no longer published).
- Recommended host sizing: at least 8 vCPU and 16 GB RAM; add NVIDIA GPU passthrough (`--gpus all`) if you need near real-time throughput.
- Mount a persistent volume (for example `C:\speechdata:/mnt/speech`) to cache downloaded model bundles and reduce cold start times.

## Application Components
- CLI demo implemented in Python 3.10+ (in a DevContainer) using Azure Speech SDK to call the container's REST diarization endpoint.
- `.env` file or secure secret store providing container `Billing__SubscriptionKey`, `Billing__Region`, `Billing` (full HTTPS endpoint), and `APIKEY` (mirrors the subscription key for container auth).
- PowerShell convenience script (`Invoke-SpeechDiarization.ps1`) to warm the container via `/status`, pass in configuration, and call the Python entry point.

## DevContainer Environment
- Base image: `mcr.microsoft.com/devcontainers/python:1-3.10-bullseye` to align with the Python 3.10 CLI target while keeping Debian tooling for native package builds.
- Recommended features: enable the `ghcr.io/devcontainers/features/azure-cli:1` feature for scripting against Azure, and `ghcr.io/devcontainers/features/docker-in-docker:2` if you want to run the Speech container side-by-side during CLI development.
- Network strategy: attach the devcontainer to the same Docker network as the Speech-to-Text container (`speech-net`) so the CLI can call `http://speech-container:5000/...` without routing through the host.
- Volume mounts: map a local workspace cache (for example `${containerWorkspaceFolder}/.models`) to the host filesystem if you want to persist downloaded Speech model bundles across rebuilds.
- Shared environment: surface `Billing__SubscriptionKey`, `Billing__Region`, and any CLI-specific settings through `.env` or VS Code secrets so both the Speech container and the devcontainer can reuse them.

### DevContainer Validation
- `.devcontainer/Dockerfile` pre-installs `curl` and `httpx` during the image build so every rebuild ships with the required tooling.
- `.devcontainer/devcontainer.json` now references the Dockerfile build, keeps Azure CLI + Docker features enabled, exports `SPEECH_NETWORK=speech-net`, and displays a `postAttachCommand` reminder to run the validation script.
- Run `./scripts/validate_env.sh` immediately after attaching to the devcontainer. The script verifies Docker socket access, pulls the `mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-gb` image, confirms the presence of `Billing__SubscriptionKey`, `Billing__Region`, `Billing`, `APIKEY`, checks that `httpx` imports successfully, and records outcomes in `specs/001-speech2textdiarize-i-want/evidence/environment-check.txt`.
- Ensure your `.env` (ignored by git) contains `Billing__SubscriptionKey`, `Billing__Region`, `APIKEY` (usually matching the subscription key), and `Billing` (the HTTPS endpoint from your Speech resource). Without these, the container will refuse to start.
- Launch the Speech container using:
	```bash
	docker network create speech-net 2>/dev/null || true
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
	Replace the billing endpoint placeholder with the URI from your Speech resource. Capture `/status` output in the evidence file before proceeding to CLI work.

### Troubleshooting
- **`docker-pull` fails or image missing**: The MCR page may not expose older preview tags (for example `5.0.1`). Use `mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-gb`, or run `az cognitiveservices account deployment list` to confirm available builds.
- **`Billing` or `APIKEY` unset**: `./scripts/validate_env.sh` flags the missing variable and the container exits with `Missing BILLING=<value>` or `APIKEY=` logs. Copy `.env.example` to `.env`, populate values from the Azure Portal, and rerun the script.
- **Billing endpoint DNS errors**: Logs such as `Name or service not known (<endpoint>)` indicate a typo. Ensure the endpoint matches the resource URL exactly (e.g., `https://<resource>.cognitiveservices.azure.com/`).
- **`httpx` import failure**: Rebuild the devcontainer (`Dev Containers: Rebuild Container`) so the Dockerfile re-installs dependencies, then rerun the validation script.
- **Status endpoint returns connection refused**: Start the Speech container (Step 3) and allow ~20 seconds for warm-up before re-running `python cli/diarize.py --ping`.


## Devcontainer to Local Container Communication
- A VS Code devcontainer is another Docker container; will reach the Speech to Text container through Docker networking.
- Attach both containers to a named bridge network (for example `docker network create speech-net` then `--network speech-net`), and call the peer by container name: `http://speech-container:5000/...`.
- When using devcontainer `networkMode: service:<name>` or `forwardPorts`, expose the target container port to the host and call via `http://host.docker.internal:5000` (Windows/macOS) or `http://127.0.0.1:5000` with an `extraHosts` entry for `host.docker.internal` on Linux.
- With Docker Compose, model both services in one file; Compose creates a default network and DNS entries, so Python code inside the devcontainer can use `requests.post("http://speech:5000/...")`.
- Ensure the Speech container listens on `0.0.0.0` and that host firewalls allow the published port if routing through the host.



