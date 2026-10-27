"""Avanza las corridas del LLM de nube (notebook 03b) sin abrir VS Code. Pensado para correr una vez al día.

Uso (desde la carpeta del proyecto, con el .venv activo):
    python scripts/correr_nube.py              # modo completo
    python scripts/correr_nube.py --modo rapido

Hace lo mismo que la sección 4 del notebook 03b: mismas oraciones, mismo prompt, misma caché. Si el
proveedor corta por cuota diaria, se detiene y la próxima ejecución sigue donde quedó. Escribe un registro
en results/logs/correr_nube.log.
"""
import argparse
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import os
import yaml

from datos.cwlc import cargar_split
from modelos import e2_llm as E2
from modelos.e2_nube import correr_corridas
from reproducibilidad import verificar_huellas_datos
from sistema import dejar_dormir, mantener_despierto

ap = argparse.ArgumentParser()
ap.add_argument("--modo", default="completo", choices=["completo", "rapido"])
args = ap.parse_args()

log_dir = RAIZ / "results" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log = open(log_dir / "correr_nube.log", "a", encoding="utf-8")


def registro(msg):
    linea = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(linea, flush=True)
    log.write(linea + "\n"); log.flush()


cfg = yaml.safe_load(open(RAIZ / "configs" / "experimentos.yaml"))
carpeta = RAIZ / "data" / "raw" / "cwlc"
train, dev, test = (cargar_split(carpeta, s) for s in ["train", "dev", "test"])
ok, difs = verificar_huellas_datos(carpeta, "cwlc")
if not ok:
    registro(f"ERROR: los datos no coinciden con las huellas registradas: {difs}"); sys.exit(1)
E2.cargar_claves(RAIZ / ".env")
nube = [m for m in cfg["llm_comercial"] if os.environ.get(E2.PROVEEDORES[m["proveedor"]]["variable"])]
if args.modo == "rapido":
    import random
    oraciones = sorted(random.Random(42).sample(test, 100), key=lambda o: o.id)
else:
    oraciones = test

registro(f"Inicio · modo {args.modo} · modelos {[m['modelo'] for m in nube]}")
despierto = mantener_despierto()
try:
    estados = correr_corridas(nube, ["zero_shot", "few_shot_dinamico"], oraciones, train, test,
                              E2.SelectorDinamico(train, k=cfg["k_ejemplos"]), carpeta, cfg["k_ejemplos"], args.modo,
                              RAIZ / "results" / f"e2nube_{args.modo}", RAIZ / "results" / "cache" / f"e2nube_{args.modo}",
                              registro=registro)
finally:
    dejar_dormir(despierto)
for e in estados:
    registro(f"  {e['corrida']}: {e['estado']} ({e['hechas']}/{e['total']})")
registro("Fin")
