"""Descarga los corpus públicos del proyecto a data/raw/.

Uso:
    python src/datos/descargar.py            # descarga todo lo definido en configs/datos.yaml
    python src/datos/descargar.py cwlc       # solo un corpus

Los datos NO se suben a git (ver .gitignore). Cada corpus mantiene su licencia
original: el CWLC es CC BY-NC-SA 4.0 (uso académico, no comercial).
"""
from __future__ import annotations

import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = RAIZ / "data" / "raw"


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url) as r:
        return json.load(r)


def descargar_zenodo(record_id: str, carpeta: Path) -> None:
    """Descarga todos los archivos de un registro público de Zenodo y descomprime los .zip."""
    carpeta.mkdir(parents=True, exist_ok=True)
    meta = _get_json(f"https://zenodo.org/api/records/{record_id}")
    for f in meta.get("files", []):
        nombre = f["key"]
        url = f["links"]["self"]
        salida = carpeta / nombre
        if salida.exists():
            print(f"  ya existe: {salida.name}")
            continue
        print(f"  descargando {nombre} ...")
        urllib.request.urlretrieve(url, salida)
        if nombre.endswith(".zip"):
            with zipfile.ZipFile(salida) as z:
                z.extractall(carpeta)
    (carpeta / "FUENTE.txt").write_text(
        f"Zenodo record {record_id}\n{meta.get('metadata', {}).get('title', '')}\n"
        f"Licencia: {meta.get('metadata', {}).get('license', {})}\n",
        encoding="utf-8",
    )


def descargar_hf(repo_id: str, carpeta: Path) -> None:
    """Descarga un dataset de Hugging Face y lo guarda en disco."""
    from datasets import load_dataset  # import local: solo si se usa

    carpeta.mkdir(parents=True, exist_ok=True)
    ds = load_dataset(repo_id)
    ds.save_to_disk(str(carpeta))
    print(f"  guardado en {carpeta}")


def main(nombres: list[str]) -> None:
    config = yaml.safe_load((RAIZ / "configs" / "datos.yaml").read_text(encoding="utf-8"))
    corpus = config["corpus"]
    for nombre in nombres or list(corpus):
        c = corpus[nombre]
        print(f"[{nombre}] {c['descripcion']}")
        carpeta = DESTINO / nombre
        if c["fuente"] == "zenodo":
            descargar_zenodo(str(c["id"]), carpeta)
        elif c["fuente"] == "huggingface":
            descargar_hf(c["id"], carpeta)
        else:
            raise ValueError(f"fuente desconocida: {c['fuente']}")


if __name__ == "__main__":
    main(sys.argv[1:])
