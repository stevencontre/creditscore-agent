"""Mide la linea base del proceso MANUAL para la medida M2b (reduccion del 20 % del tiempo).

Una persona del equipo actua como analista de credito: para cada solicitud simulada lee los datos
(formulario + buro), calcula a mano lo que necesite (por ejemplo, obligaciones/ingresos) y decide.
El cronometro corre desde que se muestra la solicitud hasta que se escribe la decision.
Escribe el promedio en config/linea_base_manual.json y los tiempos en logs/linea_base_manual_tiempos.csv.

Uso:  python scripts/medir_linea_base_manual.py [--n 10] [--analista "Nombre"]
Importante: no usen el agente ni la app mientras miden; decidan como lo haria un analista humano.
"""
import _ruta  # noqa: F401
import argparse
import csv
import datetime as dt
import json
import time

import numpy as np

from creditscore.config import RAIZ
from creditscore.simulador import generar_solicitudes

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=10, help="numero de solicitudes (minimo 10)")
ap.add_argument("--semilla", type=int, default=777)
ap.add_argument("--analista", default="", help="nombre de quien mide (opcional, queda en el registro)")
a = ap.parse_args()
if a.n < 10:
    raise SystemExit("La consigna pide al menos 10 solicitudes: use --n 10 o mas.")

sols = generar_solicitudes(a.n, np.random.default_rng(a.semilla), prefijo="MANUAL")
print(__doc__.split("Uso:")[0])
print("Decisiones: A = aprobar, R = rechazar, V = remitir a revision.  Pulse Enter para empezar.")
input()

filas = []
for i, s in enumerate(sols, 1):
    f, b = s["formulario"], s["buro"]
    print(f"\n--- Solicitud {i}/{a.n} ({s['id']}) ---")
    print(f"  Ingresos mensuales:           {f['ingresos_mensuales']:,.0f} COP")
    print(f"  Obligaciones mensuales:       {f['obligaciones_mensuales']:,.0f} COP")
    print(f"  Pagos atrasados (24 meses):   {b['pagos_atrasados_24m']}")
    print(f"  Antiguedad del historial:     {b['antiguedad_historial_meses']} meses")
    print(f"  Lineas de credito abiertas:   {b['lineas_credito_abiertas']}")
    t0 = time.perf_counter()
    while True:
        d = input("  Decision (A/R/V): ").strip().upper()
        if d in ("A", "R", "V"):
            break
    seg = time.perf_counter() - t0
    filas.append({"id": s["id"], "tiempo_s": round(seg, 2), "decision_humana": d})
    print(f"  Tiempo: {seg:.1f} s")

prom = float(np.mean([x["tiempo_s"] for x in filas]))
(RAIZ / "logs").mkdir(exist_ok=True)
with open(RAIZ / "logs" / "linea_base_manual_tiempos.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "tiempo_s", "decision_humana"], delimiter=";")
    w.writeheader()
    w.writerows(filas)
res = {
    "_nota": "Medido con scripts/medir_linea_base_manual.py: tiempo de decision de una persona sobre solicitudes simuladas, "
             "sin usar el agente. No incluye digitacion ni consulta real al buro.",
    "tiempo_manual_promedio_s": round(prom, 2),
    "n_solicitudes_medidas": len(filas),
    "analista": a.analista,
    "fecha": dt.datetime.now().isoformat(timespec="seconds"),
}
(RAIZ / "config" / "linea_base_manual.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nPromedio manual: {prom:.1f} s sobre {len(filas)} solicitudes.")
print("Guardado en config/linea_base_manual.json y logs/linea_base_manual_tiempos.csv")
print("Siguiente paso: python scripts/run_pruebas_desempeno.py")
