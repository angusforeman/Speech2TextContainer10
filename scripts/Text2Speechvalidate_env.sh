#!/usr/bin/env bash
# Environment validation for NearRealTimeText2Speech feature (T01)
# Always exits 0 (FR-013) while logging PASS/FAIL/WARN/INFO per check.
# Produces evidence logs under feature evidence directory.
set -uo pipefail

# Validates local Azure Neural Text-to-Speech container prerequisites, required env vars,
# starts the container with correct parameters if absent, and performs health checks.
# Adds host capability checks (AVX2, audio playback), dependency presence hints, and summary.

SCRIPT_DIR=$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
CENTRAL_DIR="$REPO_ROOT/assets/output"
ENV_LOG="$CENTRAL_DIR/environment-check.txt"
HEALTH_LOG="$CENTRAL_DIR/health-check.txt"
SUMMARY_LOG="$CENTRAL_DIR/environment-summary.txt"
ENV_FILE="$REPO_ROOT/.env"

# Defaults (override via environment or .env):
TTS_IMAGE=${TTS_IMAGE:-mcr.microsoft.com/azure-cognitive-services/speechservices/neural-text-to-speech:latest}
TTS_CONTAINER_NAME=${TTS_CONTAINER_NAME:-neural-tts}
TTS_NETWORK=${TTS_NETWORK:-speech-net}
# Internal container port is 5000; choose a host port (avoid clash with STT container). Allow override.
TTS_HOST_PORT=${TTS_HOST_PORT:-5001}
TTS_INTERNAL_PORT=5000

mkdir -p "$CENTRAL_DIR"
truncate -s 0 "$ENV_LOG" "$HEALTH_LOG" "$SUMMARY_LOG"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log_line() { local file="$1"; shift; printf '%s|%s|%s|%s\n' "$(timestamp)" "$1" "$2" "$3" >> "$file"; }
log_env() { log_line "$ENV_LOG" "$@"; }
log_health() { log_line "$HEALTH_LOG" "$@"; }

# Load .env if present
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

pass_count=0
fail_count=0
warn_count=0
info_count=0

record_result() {
  local status="$1"; case "$status" in
    PASS) ((pass_count++)) ;;
    FAIL) ((fail_count++)) ;;
    WARN) ((warn_count++)) ;;
    INFO) ((info_count++)) ;;
  esac
}

########################################
# 1. Docker daemon
########################################
if docker info >/dev/null 2>&1; then
  log_env "docker-daemon" "PASS" "docker info succeeded"; record_result PASS
else
  log_env "docker-daemon" "FAIL" "docker info failed (is Docker running / socket mounted?)"; record_result FAIL
fi

########################################
# 2. Ensure network exists
########################################
if docker network inspect "$TTS_NETWORK" >/dev/null 2>&1; then
  log_env "docker-network" "PASS" "Network $TTS_NETWORK present"; record_result PASS
else
  if docker network create "$TTS_NETWORK" >/dev/null 2>&1; then
    log_env "docker-network" "PASS" "Created network $TTS_NETWORK"; record_result PASS
  else
    log_env "docker-network" "FAIL" "Unable to create network $TTS_NETWORK"; record_result FAIL
  fi
fi

########################################
# 3. Required environment variables
########################################
# Primary required: ApiKey, Billing. Provide fallback from Billing__SubscriptionKey if ApiKey unset.
if [[ -z "${ApiKey:-}" && -n "${Billing__SubscriptionKey:-}" ]]; then
  export ApiKey="$Billing__SubscriptionKey"
  log_env "api-key-fallback" "WARN" "ApiKey not set; using Billing__SubscriptionKey as ApiKey"; record_result WARN
fi

if [[ -n "${ApiKey:-}" ]]; then
  log_env "api-key" "PASS" "ApiKey present (length ${#ApiKey})"; record_result PASS
else
  log_env "api-key" "FAIL" "ApiKey missing (set ApiKey=<speech resource key>)"; record_result FAIL
fi

if [[ -n "${Billing:-}" ]]; then
  log_env "billing-endpoint" "PASS" "Billing endpoint present"; record_result PASS
else
  log_env "billing-endpoint" "FAIL" "Billing endpoint missing (Billing=https://<resource>.cognitiveservices.azure.com/)"; record_result FAIL
fi

# Optional but useful
if [[ -n "${VOICE_NAME:-}" ]]; then
  log_env "voice-name" "PASS" "VOICE_NAME=$VOICE_NAME"; record_result PASS
else
  log_env "voice-name" "INFO" "VOICE_NAME not set; will use SDK default en-US-JennyNeural"; record_result INFO
fi

# Host capability checks (AVX2 required by docs)
if grep -q avx2 /proc/cpuinfo; then
  log_env "host-avx2" "PASS" "AVX2 supported"; record_result PASS
else
  log_env "host-avx2" "FAIL" "AVX2 NOT detected (container may not function)"; record_result FAIL
fi

# Audio playback tool check (aplay optional)
if command -v aplay >/dev/null 2>&1; then
  log_env "audio-device-aplay" "INFO" "aplay present (ALSA playback available)"; record_result INFO
else
  log_env "audio-device-aplay" "WARN" "aplay not found; PCM playback may rely on Python package only"; record_result WARN
fi

# Python simpleaudio availability (optional dependency for playback abstraction)
SIMPLEAUDIO_STATUS=$(python3 -c "import importlib,sys;print('present' if importlib.util.find_spec('simpleaudio') else 'missing')" 2>/dev/null || echo 'error')
case "$SIMPLEAUDIO_STATUS" in
  present)
    log_env "python-simpleaudio" "PASS" "simpleaudio import succeeded"; record_result PASS ;;
  missing)
    log_env "python-simpleaudio" "WARN" "simpleaudio not installed yet"; record_result WARN ;;
  *)
    log_env "python-simpleaudio" "WARN" "Python check failed"; record_result WARN ;;
esac

########################################
# 4. Pull image (if not already)
########################################
if docker pull "$TTS_IMAGE" >/dev/null 2>&1; then
  log_env "docker-pull" "PASS" "Pulled $TTS_IMAGE"; record_result PASS
else
  log_env "docker-pull" "FAIL" "Failed to pull $TTS_IMAGE"; record_result FAIL
fi

########################################
# 5. Ensure container running with correct image & env
########################################
start_container() {
  log_env "container-start" "INFO" "Starting $TTS_CONTAINER_NAME using $TTS_IMAGE"; record_result INFO
  if docker run -d \
    --name "$TTS_CONTAINER_NAME" \
    --network "$TTS_NETWORK" \
    -p "$TTS_HOST_PORT:$TTS_INTERNAL_PORT" \
    -e Eula=accept \
    -e Billing="$Billing" \
    -e ApiKey="$ApiKey" \
    "$TTS_IMAGE" >/dev/null; then
      log_env "container-start" "PASS" "Started $TTS_CONTAINER_NAME (host port $TTS_HOST_PORT)"; record_result PASS
  else
      log_env "container-start" "FAIL" "Failed to start container $TTS_CONTAINER_NAME"; record_result FAIL
  fi
}

if docker ps --format '{{.Names}}' | grep -q "^$TTS_CONTAINER_NAME$"; then
  RUNNING_IMAGE=$(docker inspect "$TTS_CONTAINER_NAME" --format '{{.Config.Image}}' || echo "")
  if [[ "$RUNNING_IMAGE" == "$TTS_IMAGE" ]]; then
    log_env "container-image" "PASS" "Container running with expected image $RUNNING_IMAGE"; record_result PASS
  else
    log_env "container-image" "FAIL" "Running image $RUNNING_IMAGE differs from expected $TTS_IMAGE"; record_result FAIL
  fi
else
  start_container
fi

# Confirm required env vars inside container
if docker inspect "$TTS_CONTAINER_NAME" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -q 'Eula=accept'; then
  log_env "container-env-eula" "PASS" "Eula=accept set"; record_result PASS
else
  log_env "container-env-eula" "FAIL" "Eula=accept missing"; record_result FAIL
fi

if docker inspect "$TTS_CONTAINER_NAME" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -q 'ApiKey='; then
  log_env "container-env-apikey" "PASS" "ApiKey present"; record_result PASS
else
  log_env "container-env-apikey" "FAIL" "ApiKey missing in container env"; record_result FAIL
fi

if docker inspect "$TTS_CONTAINER_NAME" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -q 'Billing='; then
  log_env "container-env-billing" "PASS" "Billing present"; record_result PASS
else
  log_env "container-env-billing" "FAIL" "Billing missing in container env"; record_result FAIL
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
  log_health "ready-endpoint" "PASS" "$TTS_HOST_URL/ready -> $READY_CODE"; record_result PASS
else
  log_health "ready-endpoint" "FAIL" "$TTS_HOST_URL/ready -> $READY_CODE"; record_result FAIL
fi

STATUS_CODE=$(health_get /status)
if [[ "$STATUS_CODE" == "200" ]]; then
  log_health "status-endpoint" "PASS" "$TTS_HOST_URL/status -> $STATUS_CODE"; record_result PASS
else
  log_health "status-endpoint" "FAIL" "$TTS_HOST_URL/status -> $STATUS_CODE"; record_result FAIL
fi

log_health "evidence-path" "INFO" "Env log: $ENV_LOG"; record_result INFO
log_health "evidence-path" "INFO" "Health log: $HEALTH_LOG"; record_result INFO

########################################
# 7. Summary / exit
########################################
{
  {
    echo "Summary: PASS=$pass_count FAIL=$fail_count WARN=$warn_count INFO=$info_count"
    if (( fail_count == 0 )); then
      echo "Overall Result: PASS (no FAIL entries)"
    else
      echo "Overall Result: ATTENTION (FAIL entries present, review logs)"
    fi
  } >> "$SUMMARY_LOG"
} >&2

exit 0
