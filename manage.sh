#!/usr/bin/env bash
set -euo pipefail

# Load env
source "$(cd "$(dirname "$0")" && pwd)/env.sh"

RUN_DIR="$PROJECT_ROOT/run"
PID_DIR="$RUN_DIR/pids"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$PID_DIR" "$LOG_DIR"

log() { echo -e "[manage] $*"; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1"; exit 1; }
}

is_pid_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  [[ -n "${pid:-}" ]] || return 1
  kill -0 "$pid" >/dev/null 2>&1
}

kill_pidfile() {
  local name="$1"
  local pid_file="$PID_DIR/$name.pid"
  if is_pid_running "$pid_file"; then
    local pid
    pid="$(cat "$pid_file")"
    log "Stopping $name (pid=$pid)..."
    kill "$pid" >/dev/null 2>&1 || true
    # give it a moment
    sleep 2
    if kill -0 "$pid" >/dev/null 2>&1; then
      log "$name didn't stop gracefully. Killing..."
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
  fi
  rm -f "$pid_file"
}

free_port() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -ti :"$port" 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      log "Port $port in use. Killing processes: $pids"
      kill $pids >/dev/null 2>&1 || true
      sleep 1
      # force kill if still alive
      pids="$(lsof -ti :"$port" 2>/dev/null || true)"
      [[ -z "$pids" ]] || { log "Force killing: $pids"; kill -9 $pids >/dev/null 2>&1 || true; }
    fi
  else
    log "lsof not found; skipping port cleanup for $port"
  fi
}

docker_up() {
  require_cmd docker
  require_cmd docker
  require_cmd docker

  log "Starting Docker services: $DOCKER_SERVICES"
  (cd "$PROJECT_ROOT" && docker compose up -d $DOCKER_SERVICES)

  log "Waiting for postgres to be ready..."
  # wait until container healthy if healthcheck exists, otherwise just sleep
  for i in {1..20}; do
    if docker ps --format '{{.Names}} {{.Status}}' | grep -q "airflow_postgres.*healthy"; then
      log "Postgres is healthy ✅"
      return 0
    fi
    sleep 1
  done
  log "Postgres healthcheck not ready yet (or no healthcheck). Continuing..."
}

docker_down() {
  require_cmd docker
  log "Stopping Docker compose..."
  (cd "$PROJECT_ROOT" && docker compose down)
}

start_api() {
  free_port "$API_PORT"
  log "Starting FastAPI on :$API_PORT"
  cd "$PROJECT_ROOT/api"
  # shellcheck disable=SC1091
  source "$VENV_PATH/bin/activate"

  nohup uvicorn main:app --reload --port "$API_PORT" \
    > "$LOG_DIR/api.log" 2>&1 &

  echo $! > "$PID_DIR/api.pid"
  log "FastAPI PID: $(cat "$PID_DIR/api.pid") (logs: $LOG_DIR/api.log)"
}

start_streamlit() {
  free_port "$STREAMLIT_PORT"
  log "Starting Streamlit on :$STREAMLIT_PORT"
  cd "$PROJECT_ROOT"
  # shellcheck disable=SC1091
  source "$VENV_PATH/bin/activate"

  nohup streamlit run webapp/app.py --server.port "$STREAMLIT_PORT" \
    > "$LOG_DIR/streamlit.log" 2>&1 &

  echo $! > "$PID_DIR/streamlit.pid"
  log "Streamlit PID: $(cat "$PID_DIR/streamlit.pid") (logs: $LOG_DIR/streamlit.log)"
}

start_airflow() {
  free_port "$AIRFLOW_PORT"
  log "Starting Airflow (webserver + scheduler) on :$AIRFLOW_PORT"
  cd "$PROJECT_ROOT"
  # shellcheck disable=SC1091
  source "$VENV_PATH/bin/activate"

  mkdir -p "$AIRFLOW_HOME"

  # Initialize DB if needed (safe to run multiple times)
  airflow db init > "$LOG_DIR/airflow_db_init.log" 2>&1 || true

  # Webserver
  nohup airflow webserver -p "$AIRFLOW_PORT" \
    > "$LOG_DIR/airflow_webserver.log" 2>&1 &
  echo $! > "$PID_DIR/airflow_webserver.pid"
  log "Airflow webserver PID: $(cat "$PID_DIR/airflow_webserver.pid") (logs: $LOG_DIR/airflow_webserver.log)"

  # Scheduler
  nohup airflow scheduler \
    > "$LOG_DIR/airflow_scheduler.log" 2>&1 &
  echo $! > "$PID_DIR/airflow_scheduler.pid"
  log "Airflow scheduler PID: $(cat "$PID_DIR/airflow_scheduler.pid") (logs: $LOG_DIR/airflow_scheduler.log)"
}

stop_all() {
  log "Stopping all services..."

  # Airflow
  kill_pidfile "airflow_scheduler"
  kill_pidfile "airflow_webserver"

  # App services
  kill_pidfile "streamlit"
  kill_pidfile "api"

  # Docker
  docker_down || true

  log "Stopped ✅"
}

start_all() {
  # sanity checks
  require_cmd python
  require_cmd curl || true

  # Activate venv exists?
  [[ -d "$VENV_PATH" ]] || { echo "Missing venv at $VENV_PATH"; exit 1; }

  docker_up
  start_api
  start_streamlit
  start_airflow

  log ""
  log "All started ✅"
  log "FastAPI:    http://localhost:$API_PORT"
  log "Streamlit:  http://localhost:$STREAMLIT_PORT"
  log "Airflow:    http://localhost:$AIRFLOW_PORT"
  log "pgAdmin:    http://localhost:$PGADMIN_PORT"
  log ""
  log "Use: ./manage.sh status | ./manage.sh logs"
}

status() {
  echo "=== STATUS ==="
  for name in api streamlit airflow_webserver airflow_scheduler; do
    if is_pid_running "$PID_DIR/$name.pid"; then
      echo "✅ $name running (pid=$(cat "$PID_DIR/$name.pid"))"
    else
      echo "❌ $name not running"
    fi
  done
  echo ""
  echo "Docker containers:"
  docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || true
}

show_logs() {
  echo "=== LOG FILES ==="
  ls -la "$LOG_DIR"
  echo ""
  echo "Tip:"
  echo "  tail -f $LOG_DIR/api.log"
  echo "  tail -f $LOG_DIR/airflow_webserver.log"
  echo "  tail -f $LOG_DIR/airflow_scheduler.log"
}

case "${1:-}" in
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    start_all
    ;;
  status)
    status
    ;;
  logs)
    show_logs
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs}"
    exit 1
    ;;
esac
