#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCK_DIR="/tmp/qq-ai-bot-deploy.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then echo "Deployment already in progress."; exit 1; fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT
cd "$ROOT"
mkdir -p data/app data/napcat/config data/napcat/QQ
if [ ! -f data/napcat/config/onebot11.json ]; then cp deploy/napcat/onebot11.json data/napcat/config/onebot11.json; fi

echo "[1/5] Validate Compose"
docker compose config -q

echo "[2/5] Pull images"
docker compose pull

echo "[3/5] Build QQ-AI-Bot"
docker compose build --pull qq-ai-bot

echo "[4/5] Start stack"
docker compose up -d --remove-orphans

echo "[5/5] Verify"
for i in {1..30}; do
  if curl -fsS http://127.0.0.1:8080/health >/tmp/qq-ai-bot-health.json 2>/dev/null; then break; fi
  sleep 2
done
if ! curl -fsS http://127.0.0.1:8080/health; then echo "[FAIL] Admin :8080"; exit 1; fi
if ! curl -fsS http://127.0.0.1:6099/webui/ >/dev/null; then echo "[FAIL] NapCat :6099"; exit 1; fi
if ! docker compose exec -T napcat bash -lc "echo > /dev/tcp/127.0.0.1/3001" 2>/dev/null; then echo "[FAIL] OneBot :3001"; exit 1; fi
if docker compose ps --format json | grep -q 'unhealthy'; then echo "[WARN] One or more services unhealthy"; exit 1; fi
echo
echo "[OK] NapCat Container"
echo "[OK] QQ-AI-Bot Container"
echo "[OK] Admin :8080"
echo "[OK] NapCat WebUI :6099"
echo "[OK] OneBot uses ws://napcat:3001 inside Docker"

# ---- NapCat WebUI Token auto-detection ----
# NapCat prints its randomly generated WebUI token to the container logs on startup:
#   [WebUi] WebUi Token: xxxxxxxx
# Poll the logs until the token appears (NapCat can be slow to start).
# The token is never hard-coded and never written to git: it is only printed to the terminal.
# NAPCAT_TOKEN_TIMEOUT / NAPCAT_TOKEN_INTERVAL can override the 60s / 2s defaults (used by tests).
wait_for_napcat_token() {
  local container="${1:-qq-ai-bot-napcat}"
  local timeout_secs="${NAPCAT_TOKEN_TIMEOUT:-60}"
  local interval_secs="${NAPCAT_TOKEN_INTERVAL:-2}"
  case "$timeout_secs" in ''|*[!0-9]*) timeout_secs=60;; esac
  case "$interval_secs" in ''|*[!0-9]*|0) interval_secs=2;; esac
  local elapsed=0
  local token=""

  while [ "$elapsed" -lt "$timeout_secs" ]; do
    token="$(docker logs --tail 200 "$container" 2>/dev/null \
      | sed -e 's/\x1b\[[0-9;]*m//g' \
      | grep 'WebUi Token:' \
      | tail -n 1 \
      | sed -E 's/^.*WebUi Token:[[:space:]]*//' \
      | awk '{print $1}' || true)"
    if [ -n "$token" ]; then
      printf '%s\n' "$token"
      return 0
    fi
    sleep "$interval_secs"
    elapsed=$((elapsed + interval_secs))
  done
  return 1
}

echo
echo "[6/6] NapCat WebUI Token"
NAPCAT_TOKEN=""
if NAPCAT_TOKEN="$(wait_for_napcat_token qq-ai-bot-napcat)"; then
  echo "[OK] NapCat WebUI Token detected"
else
  echo "[WARN] NapCat WebUI Token could not be detected."
  echo "[WARN] Run manually: docker logs qq-ai-bot-napcat | grep \"WebUi Token\""
fi

VPS_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ -z "$VPS_IP" ]; then
  VPS_IP="<VPS-IP>"
fi

echo
echo "================================"
echo "QQ-AI-Bot Deployment Complete"
echo "================================"
echo
echo "Admin:"
echo "http://$VPS_IP:8080/admin/"
echo
echo "NapCat WebUI:"
echo "http://$VPS_IP:6099/webui/"
echo
if [ -n "$NAPCAT_TOKEN" ]; then
  echo "NapCat WebUI Token:"
  echo "$NAPCAT_TOKEN"
else
  echo "NapCat WebUI Token: (not detected)"
fi
echo
echo "================================"
