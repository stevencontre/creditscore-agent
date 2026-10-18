"""Demostracion interactiva del agente.  Ej.:  python scripts/run_agente.py --n 15 --escenario normal
Escenarios: normal | fallo_buro | fallo_originacion | invalidas | deriva"""
import _ruta  # noqa: F401
import argparse, datetime as dt
import numpy as np
from creditscore.config import RAIZ
from creditscore.fabrica import construir
from creditscore.simulador import generar_solicitudes

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=15)
ap.add_argument("--semilla", type=int, default=2026)
ap.add_argument("--escenario", default="normal", choices=["normal", "fallo_buro", "fallo_originacion", "invalidas", "deriva"])
a = ap.parse_args()

ruta = RAIZ / "logs" / f"ejecucion_{dt.datetime.now():%Y%m%d_%H%M%S}.jsonl"
pf = {"fallo_buro": 0.5}.get(a.escenario, None)
po = {"fallo_originacion": 0.5}.get(a.escenario, None)
c = construir(a.semilla, ruta_log=ruta, p_fallo_buro=pf, p_fallo_originacion=po)
ag, ent = c["agente"], c["entorno"]
print(f"Agente listo | modelo {c['modelo'].version} | historico {c['memoria'].n} casos | log: {ruta}\n")
sols = c["prueba"]
if a.escenario == "deriva":
    d = generar_solicitudes(1000, np.random.default_rng(a.semilla + 1), prefijo="DERIVA", deriva=1.0)
    for t in d: ent.registrar_solicitud(t)
    for t in d:
        ag.evaluar(t["id"]); ag.registrar_resultado_observado(t["id"])
    print("Revision de aprendizaje:", ag.revisar_aprendizaje()); sols = []
if a.escenario == "invalidas":
    from creditscore.evaluacion import CORRUPCIONES, _corromper
    for i, t in enumerate(sols[:a.n]):
        _corromper(ent, t, CORRUPCIONES[i % len(CORRUPCIONES)]); 
        r = ag.evaluar(t["id"]); ent.buro_caido = False
        print(f"{r['id']} | {CORRUPCIONES[i % len(CORRUPCIONES)]:22} -> {r['accion']:15} | {r['razon'][:80]}")
    sols = []
for t in sols[:a.n]:
    r = ag.evaluar(t["id"])
    p = "  n/d" if r["p_default"] is None else f"{r['p_default']:.3f}"
    print(f"{r['id']} | p_default={p} | cal={r['calificacion']:3} | {r['accion']:15} | {r['estado_acciones']} | {r['latencia_ms']:.2f} ms")
print(f"\nBandeja de analistas: {len(ent.bandeja)} | Originacion: {len(ent.originacion)} | Pendientes (outbox): {len(ag.actuadores.pendientes)}")
c["registro"].cerrar()
