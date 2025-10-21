#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
FEATURE_DIR="$REPO_ROOT/specs/001-i-want-to"
EVIDENCE_DIR="$FEATURE_DIR/evidence"
ENV_LOG="$EVIDENCE_DIR/environment-check.txt"
SMOKE_LOG="$EVIDENCE_DIR/cli-smoke.txt"
ENV_FILE="$REPO_ROOT/.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

SPEECH_IMAGE=${SPEECH_IMAGE:-mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-gb}

mkdir -p "$EVIDENCE_DIR"
touch "$ENV_LOG" "$SMOKE_LOG"

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

log_env() {
  local check="$1"
  local status="$2"
  local detail="$3"
  printf '%s|%s|%s|%s\n' "$(timestamp)" "$check" "$status" "$detail" | tee -a "$ENV_LOG"
}

overall_status=0

# Check Docker daemon availability.
if docker info >/dev/null 2>&1; then
  log_env "docker-daemon" "PASS" "docker info succeeded"
else
  log_env "docker-daemon" "FAIL" "docker info failed (ensure Docker socket is shared with devcontainer)"
  overall_status=1
fi

# Pull the expected Speech container image.
if docker pull "$SPEECH_IMAGE" >/dev/null 2>&1; then
  log_env "docker-pull" "PASS" "Pulled $SPEECH_IMAGE"
else
  log_env "docker-pull" "FAIL" "Unable to pull $SPEECH_IMAGE"
  overall_status=1
fi

# Inspect the image to confirm tag and digest.
if IMAGE_INFO=$(docker image inspect "$SPEECH_IMAGE" --format '{{.RepoTags}} {{.Id}}' 2>/dev/null); then
  log_env "docker-image" "PASS" "Image available: ${IMAGE_INFO}"
else
  log_env "docker-image" "FAIL" "Image $SPEECH_IMAGE not present"
  overall_status=1
fi

# Validate billing environment variables are present (but do not print values).
if [[ -n "${Billing__SubscriptionKey:-}" ]]; then
  log_env "billing-key" "PASS" "Billing__SubscriptionKey set (length ${#Billing__SubscriptionKey})"
else
  log_env "billing-key" "FAIL" "Billing__SubscriptionKey not set in environment"
  overall_status=1
fi

if [[ -n "${Billing__Region:-}" ]]; then
  log_env "billing-region" "PASS" "Billing__Region set"
else
  log_env "billing-region" "FAIL" "Billing__Region not set in environment"
  overall_status=1
fi

if [[ -n "${Billing:-}" ]]; then
  log_env "billing-endpoint" "PASS" "Billing endpoint set"
else
  log_env "billing-endpoint" "FAIL" "Billing endpoint (Billing) not set"
  overall_status=1
fi

if [[ -n "${APIKEY:-}" ]]; then
  log_env "api-key" "PASS" "APIKEY set"
else
  log_env "api-key" "FAIL" "APIKEY not set (should mirror Billing__SubscriptionKey)"
  overall_status=1
fi

# Confirm Python dependencies are importable.
if python3 - <<'PY' >/dev/null 2>&1
import httpx
import websocket
PY
then
  log_env "python-modules" "PASS" "httpx and websocket imports succeeded"
else
  log_env "python-modules" "FAIL" "Unable to import httpx and websocket"
  overall_status=1
fi

# Ensure the evidence directory is writable.
if TEMP_FILE=$(mktemp "$EVIDENCE_DIR/.validate.XXXXXX" 2>/dev/null); then
  rm -f "$TEMP_FILE"
  log_env "evidence-write" "PASS" "Write access confirmed for $EVIDENCE_DIR"
else
  log_env "evidence-write" "FAIL" "Cannot write to $EVIDENCE_DIR"
  overall_status=1
fi

log_env "evidence-path" "PASS" "Environment logs -> $ENV_LOG"
log_env "smoke-path" "PASS" "CLI smoke logs -> $SMOKE_LOG"

if [[ $overall_status -eq 0 ]]; then
  echo "Environment validation PASSED."
else
  echo "Environment validation completed with FAILURES. Review $ENV_LOG for details." >&2
  exit $overall_status
fi
