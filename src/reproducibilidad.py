"""Reproducibilidad: semillas, determinismo y huellas digitales.

Una "huella digital" es un resumen SHA-256 de algo: si cambia un solo carácter del
archivo, del corpus, de la configuración o del código, la huella cambia por completo.
Guardar las huellas junto a cada resultado permite saber, meses después, con qué datos,
qué código, qué versión exacta del modelo y qué entorno se obtuvo cada número, y
verificar que una re-ejecución usó exactamente lo mismo.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import subprocess
from importlib import metadata
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- semillas

def fijar_semilla_total(semilla: int, determinista: bool = True) -> dict:
    """Fija todas las fuentes de azar conocidas y activa algoritmos deterministas.

    Devuelve un dict con lo que se pudo garantizar (se guarda junto al resultado).
    Nota: en GPU de Apple (MPS) PyTorch no garantiza determinismo bit a bit en todas las
    operaciones; por eso se repite con 3 semillas y se reporta media ± desviación estándar.
    """
    os.environ["PYTHONHASHSEED"] = str(semilla)
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(semilla)
    np.random.seed(semilla)
    estado = {"semilla": semilla, "determinista_solicitado": determinista}
    try:
        import torch

        torch.manual_seed(semilla)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(semilla)
        if hasattr(torch, "mps") and torch.backends.mps.is_available():
            torch.mps.manual_seed(semilla)
        if determinista:
            torch.use_deterministic_algorithms(True, warn_only=True)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        estado["torch_determinista"] = torch.are_deterministic_algorithms_enabled()
    except ImportError:
        estado["torch_determinista"] = None
    return estado


# --------------------------------------------------------------------------- huellas

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def huella_archivos(carpeta: Path, patron: str = "**/*.conll") -> dict:
    """SHA-256 de cada archivo y una huella combinada (orden alfabético)."""
    archivos = sorted(p for p in carpeta.glob(patron) if p.is_file())
    por_archivo = {str(p.relative_to(carpeta)): sha256_archivo(p) for p in archivos}
    combinada = sha256_bytes(json.dumps(por_archivo, sort_keys=True).encode())
    return {"n_archivos": len(archivos), "combinada": combinada, "archivos": por_archivo}


def huella_corpus(oraciones) -> str:
    """Huella del contenido ya cargado (tokens + entidades), independiente del formato en disco."""
    canon = [[o.tokens, sorted([list(e[1:]) for e in o.entidades])] for o in oraciones]
    return sha256_bytes(json.dumps(canon, ensure_ascii=False).encode())


def huella_config(config: dict) -> str:
    return sha256_bytes(json.dumps(config, sort_keys=True, ensure_ascii=False, default=str).encode())


def huella_predicciones(pred) -> str:
    """Si dos corridas con la misma semilla dan la misma huella, fueron idénticas."""
    return sha256_bytes(json.dumps(sorted(map(list, pred)), ensure_ascii=False).encode())


def huella_codigo() -> dict:
    """Commit de git actual y si hay cambios sin guardar (código 'sucio')."""
    def git(*args):
        try:
            return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            return ""
    return {"commit": git("rev-parse", "HEAD"), "cambios_sin_commit": bool(git("status", "--porcelain", "--untracked-files=no"))}


def huella_modelo(nombre: str) -> dict:
    """Revisión exacta (commit) del modelo en Hugging Face: un 'mismo nombre' puede cambiar de pesos."""
    try:
        from huggingface_hub import model_info

        info = model_info(nombre)
        return {"modelo": nombre, "revision": info.sha}
    except Exception as e:  # sin red: se registra igual
        return {"modelo": nombre, "revision": None, "error": type(e).__name__}


def entorno() -> dict:
    def v(paquete):
        try:
            return metadata.version(paquete)
        except metadata.PackageNotFoundError:
            return None
    info = {"python": platform.python_version(), "sistema": platform.platform(), "procesador": platform.processor()}
    info.update({p: v(p) for p in ["torch", "transformers", "numpy", "datasets", "ollama", "mlx-lm"]})
    try:
        import torch

        info["dispositivo"] = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    except ImportError:
        info["dispositivo"] = None
    return info


def huella_completa(config: dict, carpeta_datos: Path, modelo: str | None = None, splits: dict | None = None) -> dict:
    """Todo lo necesario para reproducir y auditar un resultado."""
    h = {
        "config": huella_config(config),
        "datos_archivos": huella_archivos(carpeta_datos)["combinada"],
        "codigo": huella_codigo(),
        "entorno": entorno(),
    }
    if splits:
        h["datos_contenido"] = {s: huella_corpus(o) for s, o in splits.items()}
    if modelo:
        h["modelo"] = huella_modelo(modelo)
    return h


# --------------------------------------------------------------------------- verificación

ARCHIVO_HUELLAS = RAIZ / "configs" / "huellas_datos.json"


def registrar_huellas_datos(carpeta: Path, nombre: str) -> dict:
    """Guarda en configs/huellas_datos.json las huellas esperadas (se versiona en git)."""
    todas = json.loads(ARCHIVO_HUELLAS.read_text()) if ARCHIVO_HUELLAS.exists() else {}
    todas[nombre] = huella_archivos(carpeta)
    ARCHIVO_HUELLAS.write_text(json.dumps(todas, indent=2, sort_keys=True))
    return todas[nombre]


def verificar_huellas_datos(carpeta: Path, nombre: str) -> tuple[bool, list[str]]:
    """Compara los archivos en disco con las huellas registradas. Devuelve (ok, diferencias)."""
    esperadas = json.loads(ARCHIVO_HUELLAS.read_text())[nombre]["archivos"]
    actuales = huella_archivos(carpeta)["archivos"]
    difs = [f for f in sorted(set(esperadas) | set(actuales)) if esperadas.get(f) != actuales.get(f)]
    return (not difs, difs)


# --------------------------------------------------------------------------- agregación multi-semilla

def agregar_semillas(valores: list[float]) -> dict:
    """Media ± desviación estándar (muestral, n-1), mínimo, máximo y rango entre semillas."""
    v = np.asarray(valores, dtype=float)
    return {"n": int(v.size), "media": float(v.mean()), "de": float(v.std(ddof=1)) if v.size > 1 else 0.0,
            "min": float(v.min()), "max": float(v.max()), "rango": float(v.max() - v.min()), "valores": v.tolist()}
