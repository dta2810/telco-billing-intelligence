#!/usr/bin/env bash
# Levanta la demo AcmeTel Billing Intelligence (backend + frontend).
# Uso: ./run.sh <databricks-profile>
#   ej: ./run.sh LATAM

set -euo pipefail

PROFILE="${1:-}"
if [[ -z "$PROFILE" ]]; then
  echo "Uso: $0 <databricks-profile>"
  echo "  ej: $0 LATAM"
  exit 1
fi

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$APP_DIR/frontend"
LOG_DIR="$APP_DIR/.logs"
mkdir -p "$LOG_DIR"

export DATABRICKS_CONFIG_PROFILE="$PROFILE"
export DATABRICKS_WAREHOUSE_ID="9d0fa4e10c03d2f1"
export GENIE_SPACE_ID="01f14410e8951192b4e2e0652ceb2965"
export CATALOG="acmetel_demo"
export SCHEMA="gold"

cleanup() {
  echo ""
  echo "→ Bajando servidores…"
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

echo "→ Validando auth Databricks (profile: $PROFILE)…"
if ! databricks current-user me --profile "$PROFILE" >/dev/null 2>&1; then
  echo "  Token inválido o expirado. Ejecutando 'databricks auth login --profile $PROFILE'…"
  databricks auth login --profile "$PROFILE"
fi
echo "  ✓ Auth OK"

echo "→ Setup backend (venv + deps)…"
cd "$APP_DIR"
if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install -q -r requirements.txt
echo "  ✓ Backend listo"

echo "→ Setup frontend (npm deps)…"
cd "$FRONTEND_DIR"
if [[ ! -d "node_modules" ]]; then
  npm install
fi
echo "  ✓ Frontend listo"

# Liberar puertos si quedaron procesos colgados
for PORT in 8000 5173; do
  if lsof -ti tcp:"$PORT" >/dev/null 2>&1; then
    echo "→ Liberando puerto ${PORT}…"
    lsof -ti tcp:"$PORT" | xargs kill -9 2>/dev/null || true
  fi
done

echo "→ Levantando backend (FastAPI :8000)…"
cd "$APP_DIR"
python app.py >"$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

# Esperar a que el backend responda
for i in {1..30}; do
  if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "  ✓ Backend up (PID $BACKEND_PID)"
    break
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "  ✗ Backend murió. Log:"
    tail -30 "$LOG_DIR/backend.log"
    exit 1
  fi
  sleep 1
done

echo "→ Levantando frontend (Vite :5173)…"
cd "$FRONTEND_DIR"
npm run dev >"$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

sleep 2
if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "  ✗ Frontend murió. Log:"
  tail -30 "$LOG_DIR/frontend.log"
  kill "$BACKEND_PID" 2>/dev/null || true
  exit 1
fi
echo "  ✓ Frontend up (PID $FRONTEND_PID)"

echo ""
echo "════════════════════════════════════════════════"
echo "  AcmeTel Billing Intelligence está corriendo"
echo "════════════════════════════════════════════════"
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  Logs:      $LOG_DIR/{backend,frontend}.log"
echo ""
echo "  Ctrl+C para bajar todo."
echo "════════════════════════════════════════════════"

wait
