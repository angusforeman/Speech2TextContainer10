#!/usr/bin/env bash
set -euo pipefail

# Text2Speechvalidate_env.sh
# Validates local Azure Neural Text-to-Speech container prerequisites, required env vars,
# pulls/starts the container with correct parameters if absent, and performs health checks.
# Intended for use inside the DevContainer or a compatible host shell.

SCRIPT_DIR=$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
EVIDENCE_DIR="$REPO_ROOT/specs/tts/evidence"
ENV_LOG="$EVIDENCE_DIR/tts-environment-check.txt"
HEALTH_LOG="$EVIDENCE_DIR/tts-health-check.txt"
ENV_FILE="$REPO_ROOT/.env"

# Defaults (override via environment or .env):
TTS_IMAGE=${TTS_IMAGE:-mcr.microsoft.com/azure-cognitive-services/speechservices/neural-text-to-speech:latest}
TTS_CONTAINER_NAME=${TTS_CONTAINER_NAME:-neural-tts}
TTS_NETWORK=${TTS_NETWORK:-speech-net}
# Internal container port is 5000; choose a host port (avoid clash with STT container). Allow override.
TTS_HOST_PORT=${TTS_HOST_PORT:-5001}
TTS_INTERNAL_PORT=5000

mkdir -p "$EVIDENCE_DIR"
touch "$ENV_LOG" "$HEALTH_LOG"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log_env() { printf '%s|%s|%s|%s\n' "$(timestamp)" "$1" "$2" "$3" | tee -a "$ENV_LOG"; }
log_health() { printf '%s|%s|%s|%s\n' "$(timestamp)" "$1" "$2" "$3" | tee -a "$HEALTH_LOG"; }

# Load .env if present
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

overall_status=0

########################################
# 1. Docker daemon
########################################
if docker info >/dev/null 2>&1; then
  log_env "docker-daemon" "PASS" "docker info succeeded"
else
  log_env "docker-daemon" "FAIL" "docker info failed (is Docker running / socket mounted?)"
  overall_status=1
fi

########################################
# 2. Ensure network exists
########################################
if docker network inspect "$TTS_NETWORK" >/dev/null 2>&1; then
  log_env "docker-network" "PASS" "Network $TTS_NETWORK present"
else
  if docker network create "$TTS_NETWORK" >/dev/null 2>&1; then
    log_env "docker-network" "PASS" "Created network $TTS_NETWORK"
  else
    log_env "docker-network" "FAIL" "Unable to create network $TTS_NETWORK"
    overall_status=1
  fi
fi

########################################
# 3. Required environment variables
########################################
# Primary required: ApiKey, Billing. Provide fallback from Billing__SubscriptionKey if ApiKey unset.
if [[ -z "${ApiKey:-}" && -n "${Billing__SubscriptionKey:-}" ]]; then
  export ApiKey="$Billing__SubscriptionKey"
  log_env "api-key-fallback" "WARN" "ApiKey not set; using Billing__SubscriptionKey as ApiKey"
fi

if [[ -n "${ApiKey:-}" ]]; then
  log_env "api-key" "PASS" "ApiKey present (length ${#ApiKey})"
else
  log_env "api-key" "FAIL" "ApiKey missing (set ApiKey=<speech resource key>)"
  overall_status=1
fi

if [[ -n "${Billing:-}" ]]; then
  log_env "billing-endpoint" "PASS" "Billing endpoint present"
else
  log_env "billing-endpoint" "FAIL" "Billing endpoint missing (Billing=https://<resource>.cognitiveservices.azure.com/)"
  overall_status=1
fi

# Optional but useful
if [[ -n "${VOICE_NAME:-}" ]]; then
  log_env "voice-name" "PASS" "VOICE_NAME=$VOICE_NAME"
else
  log_env "voice-name" "INFO" "VOICE_NAME not set; will use SDK default en-US-JennyNeural"
fi

########################################
# 4. Pull image (if not already)
########################################
if docker pull "$TTS_IMAGE" >/dev/null 2>&1; then
  log_env "docker-pull" "PASS" "Pulled $TTS_IMAGE"
else
  log_env "docker-pull" "FAIL" "Failed to pull $TTS_IMAGE"
  overall_status=1
fi

########################################
# 5. Ensure container running with correct image & env
########################################
start_container() {
  log_env "container-start" "INFO" "Starting $TTS_CONTAINER_NAME using $TTS_IMAGE"
  if docker run -d \
    --name "$TTS_CONTAINER_NAME" \
    --network "$TTS_NETWORK" \
    -p "$TTS_HOST_PORT:$TTS_INTERNAL_PORT" \
    -e Eula=accept \
    -e Billing="$Billing" \
    -e ApiKey="$ApiKey" \
    "$TTS_IMAGE" >/dev/null; then
      log_env "container-start" "PASS" "Started $TTS_CONTAINER_NAME (host port $TTS_HOST_PORT)"
  else
      log_env "container-start" "FAIL" "Failed to start container $TTS_CONTAINER_NAME"
      overall_status=1
  fi
}

if docker ps --format '{{.Names}}' | grep -q "^$TTS_CONTAINER_NAME$"; then
  # Verify image matches
  RUNNING_IMAGE=$(docker inspect "$TTS_CONTAINER_NAME" --format '{{.Config.Image}}' || echo "")
  if [[ "$RUNNING_IMAGE" == "$TTS_IMAGE" ]]; then
    log_env "container-image" "PASS" "Container running with expected image $RUNNING_IMAGE"
  else
    log_env "container-image" "FAIL" "Running image $RUNNING_IMAGE differs from expected $TTS_IMAGE"
    overall_status=1
  fi
else
  start_container
fi

# Confirm required env vars inside container
if docker inspect "$TTS_CONTAINER_NAME" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -q 'Eula=accept'; then
  log_env "container-env-eula" "PASS" "Eula=accept set"
else
  log_env "container-env-eula" "FAIL" "Eula=accept missing"
  overall_status=1
fi

if docker inspect "$TTS_CONTAINER_NAME" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -q 'ApiKey='; then
  log_env "container-env-apikey" "PASS" "ApiKey present"
else
  log_env "container-env-apikey" "FAIL" "ApiKey missing in container env"
  overall_status=1
fi

if docker inspect "$TTS_CONTAINER_NAME" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -q 'Billing='; then
  log_env "container-env-billing" "PASS" "Billing present"
else
  log_env "container-env-billing" "FAIL" "Billing missing in container env"
  overall_status=1
fi

########################################
# 6. Health checks (/ready, /status)
########################################
# Determine host URL: if inside same Docker network from another container, you'd use http://$TTS_CONTAINER_NAME:5000;
# From host, use mapped port on localhost.
TTS_HOST_URL=${TTS_HOST:-"http://localhost:$TTS_HOST_PORT"}

health_get() {
  local path="$1"; local code
  code=$(curl -s -o /dev/null -w '%{http_code}' "$TTS_HOST_URL$path" || echo "000")
  echo "$code"
}

READY_CODE=$(health_get /ready)
if [[ "$READY_CODE" == "200" ]]; then
  log_health "ready-endpoint" "PASS" "$TTS_HOST_URL/ready -> $READY_CODE"
else
  log_health "ready-endpoint" "FAIL" "$TTS_HOST_URL/ready -> $READY_CODE"
  overall_status=1
fi

STATUS_CODE=$(health_get /status)
if [[ "$STATUS_CODE" == "200" ]]; then
  log_health "status-endpoint" "PASS" "$TTS_HOST_URL/status -> $STATUS_CODE"
else
  log_health "status-endpoint" "FAIL" "$TTS_HOST_URL/status -> $STATUS_CODE"
  overall_status=1
fi

log_health "evidence-path" "PASS" "Env log: $ENV_LOG"
log_health "evidence-path" "PASS" "Health log: $HEALTH_LOG"

########################################
# 7. Summary / exit
########################################
if [[ $overall_status -eq 0 ]]; then
  echo "Text-to-Speech environment validation PASSED." | tee -a "$ENV_LOG" "$HEALTH_LOG"
else
  echo "Text-to-Speech environment validation completed with FAILURES. See logs." >&2
fi
exit $overall_status
