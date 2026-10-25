"""Utilidades del sistema operativo para entrenamientos largos."""
from __future__ import annotations

import os
import platform
import subprocess


def mantener_despierto():
    """Evita que el Mac se duerma mientras corre el entrenamiento (equivale a `caffeinate`).

    Lanza `caffeinate -dims -w <pid>`: queda activo mientras viva este proceso de Python
    (el kernel del notebook). Si el kernel se cierra o se cae, caffeinate se apaga solo.
    Devuelve el proceso para detenerlo con `.terminate()` al terminar; en Linux/Windows no hace nada.
    Ojo: cerrar la tapa del Mac lo duerme igual; dejarlo enchufado y con la tapa abierta.
    """
    if platform.system() != "Darwin":
        print("mantener_despierto: no es macOS, no se hace nada")
        return None
    proc = subprocess.Popen(["caffeinate", "-dims", "-w", str(os.getpid())])
    print("☕ Mac en modo despierto mientras entrena (caffeinate activo)")
    return proc


def dejar_dormir(proc) -> None:
    if proc is not None and proc.poll() is None:
        proc.terminate()
        print("☕ caffeinate detenido: el Mac puede volver a dormir")
