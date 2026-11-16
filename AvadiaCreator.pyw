"""Avadia Creator: abre el editor visual sin ventana de terminal.

Doble clic en este archivo (con Python instalado en Windows). Si algo falla al
arrancar, el motivo se guarda en avadia_creator_error.log dentro de tu carpeta de usuario.
"""
import sys
import traceback
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))


def _registrar_error(texto):
    try:
        ruta = Path.home() / "avadia_creator_error.log"
        ruta.write_text(texto, encoding="utf-8")
    except OSError:
        pass


if __name__ == "__main__":
    try:
        from editor.creador_studio import main
        main()
    except Exception:
        _registrar_error(traceback.format_exc())
        raise
