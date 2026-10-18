import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def cargar_config(ruta=None):
    ruta = Path(ruta) if ruta else RAIZ / "config" / "config.json"
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_umbrales(ruta=None):
    ruta = Path(ruta) if ruta else RAIZ / "config" / "umbrales.json"
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)
