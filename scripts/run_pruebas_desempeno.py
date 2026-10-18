"""Ejecuta las pruebas de desempeno M1-M7 y escribe logs/resultados_pruebas.{json,csv}, tabla_resultados.md."""
import _ruta  # noqa: F401
import time
from creditscore.evaluacion import ejecutar

if __name__ == "__main__":
    t0 = time.time()
    filas, det = ejecutar()
    for r in filas:
        est = "PENDIENTE" if r[5] is None else ("CUMPLE" if r[5] else "NO CUMPLE")
        print(f"[{est:9}] {r[0][:70]}\n            umbral {r[2]} | casos {r[3]} | {r[4]}")
    print(f"\nDuracion: {time.time()-t0:.1f} s. Resultados en logs/")
