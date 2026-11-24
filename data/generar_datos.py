"""Genera exclusivamente datos sintéticos del experimento Kredia."""
import csv
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from creditscore.simulador import generar_solicitudes

def generar():
    casos = generar_solicitudes(5000, np.random.default_rng(2026))
    return [{"id": c["id"], **c["formulario"], **c["buro"], "incumplimiento": c["_default"]} for c in casos]

if __name__ == "__main__":
    filas = generar()
    destino = ROOT / "data" / "solicitudes_sinteticas.csv"
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(destino)
