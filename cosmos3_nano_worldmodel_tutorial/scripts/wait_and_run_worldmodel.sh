#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-18000}"
TIMEOUT="${WAIT_TIMEOUT:-28800}"
LOCK="$ROOT/logs/wait_and_run.lock"
LOG="$ROOT/logs/wait_and_run.log"

if [[ -e "$LOCK" ]]; then
  echo "another wait_and_run process already exists: $(cat "$LOCK")" >&2
  exit 1
fi
echo $$ > "$LOCK"
cleanup_lock() { [[ "$(cat "$LOCK" 2>/dev/null)" == "$$" ]] && unlink "$LOCK"; }
trap cleanup_lock EXIT INT TERM

log() { printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$LOG"; }

log "waiting for one GPU with <10000 MiB used"
start_epoch=$(date +%s)
gpu=""
while true; do
  while IFS=, read -r idx used _; do
    idx=${idx// /}; used=${used// /}
    if [[ "$used" =~ ^[0-9]+$ ]] && (( used < 10000 )); then
      gpu=$idx
      break
    fi
  done < <(nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader)
  if [[ -n "$gpu" ]]; then break; fi
  now=$(date +%s)
  if (( now - start_epoch > TIMEOUT )); then
    log "TIMEOUT: no free GPU after ${TIMEOUT}s"
    exit 2
  fi
  sleep 60
done
log "selected GPU $gpu"

server_log="$ROOT/logs/server_gpu${gpu}_$(date +%Y%m%d_%H%M%S).log"
CUDA_VISIBLE_DEVICES="$gpu" PORT="$PORT" setsid "$ROOT/scripts/start_server.sh" >"$server_log" 2>&1 &
server_pid=$!
log "server_pid=$server_pid log=$server_log"

ready=0
for _ in $(seq 1 240); do
  if ! kill -0 "$server_pid" 2>/dev/null; then
    log "server exited before ready; tail follows"
    tail -100 "$server_log" | tee -a "$LOG"
    exit 3
  fi
  if curl -fsS --max-time 3 "http://127.0.0.1:${PORT}/v1/models" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 10
done
if [[ "$ready" != 1 ]]; then
  log "server not ready after 40 minutes"
  tail -100 "$server_log" | tee -a "$LOG"
  exit 4
fi
log "server ready on port $PORT"

run_log="$ROOT/logs/worldmodel_t2v_$(date +%Y%m%d_%H%M%S).log"
if CUDA_VISIBLE_DEVICES="$gpu" COSMOS_BASE_URL="http://127.0.0.1:${PORT}" "$ROOT/.venv/bin/python" "$ROOT/scripts/run_worldmodel_t2v.py" 2>&1 | tee "$run_log"; then
  log "world model run succeeded; run_log=$run_log"
  # Release the shared GPU. The generated MP4 and metadata remain in outputs/.
  kill -TERM -- "-$server_pid" 2>/dev/null || kill -TERM "$server_pid" 2>/dev/null || true
  for _ in $(seq 1 30); do
    kill -0 "$server_pid" 2>/dev/null || break
    sleep 2
  done
  kill -KILL -- "-$server_pid" 2>/dev/null || true
  log "server stopped"
  exit 0
else
  rc=$?
  log "world model run failed rc=$rc; server left for diagnosis pid=$server_pid"
  exit "$rc"
fi
