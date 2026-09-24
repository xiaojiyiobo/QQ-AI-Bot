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
