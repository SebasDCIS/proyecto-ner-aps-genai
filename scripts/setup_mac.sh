#!/usr/bin/env bash
# Prepara el entorno en un Mac con Apple Silicon (M1–M5).
# Uso: bash scripts/setup_mac.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== 1. Entorno Python (.venv) =="
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "== 2. Verificación de PyTorch con aceleración MPS =="
python - <<'PY'
import torch
print("torch", torch.__version__, "| MPS disponible:", torch.backends.mps.is_available())
PY

echo "== 3. Ollama y modelos locales =="
if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama no está instalado. Descárgalo desde https://ollama.com/download y vuelve a correr este script."
  exit 0
fi
# Modelos de ~8B cuantizados (caben en 24 GB). Ajustar en configs/experimentos.yaml.
for m in $(python - <<'PY'
import yaml
cfg = yaml.safe_load(open("configs/experimentos.yaml"))
print(" ".join(cfg["llm_locales"]))
PY
); do
  echo "-> ollama pull $m"
  ollama pull "$m"
done

echo "Listo. Activa el entorno con: source .venv/bin/activate"
