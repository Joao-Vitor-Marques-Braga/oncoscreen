#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "  OncoScreen.AI (OralCare-Vision CDSS) - Inicialização Nativa"
echo "============================================================"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "${ROOT_DIR}/.env" && -f "${ROOT_DIR}/.env.example" ]]; then
  cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
  echo "[INFO] Arquivo .env criado a partir de .env.example"
fi

echo "[1/4] Configurando ambiente Python do Backend..."
cd "${ROOT_DIR}/backend"
if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

echo "[2/4] Iniciando Backend FastAPI (http://127.0.0.1:8000)..."
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

cleanup() {
  echo ""
  echo "[INFO] Encerrando servidores..."
  kill "${BACKEND_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[3/4] Configurando dependências do Frontend..."
cd "${ROOT_DIR}/frontend"
if [[ ! -d "node_modules" ]]; then
  npm install
fi

echo "[4/4] Iniciando Frontend Vite (http://localhost:5173)..."
echo "Credencial inicial Médico: doutor@oncoscreen.ai / admin123"
npm run dev

