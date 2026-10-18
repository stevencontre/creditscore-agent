"""Calcula S(agente) = sum(w_i * p_i), el analisis de sensibilidad (+-10 pp) y escenarios de robustez.
Lee docs/matriz_decision.json y escribe docs/resultados_matriz.json y docs/resultados_matriz.md."""
import _ruta  # noqa: F401
import json
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "docs"
M = json.loads((D / "matriz_decision.json").read_text(encoding="utf-8"))
C = M["criterios"]


def puntajes(pesos, ajuste_b=0):
    sa = sum(w * c["A"]["p"] for w, c in zip(pesos, C))
    sb = sum(w * min(5, c["B"]["p"] + (ajuste_b if c["B"]["tipo"] == "estimación" else 0)) for w, c in zip(pesos, C))
    return sa, sb


def reescalar(pesos, i, nuevo):
    resto = sum(w for j, w in enumerate(pesos) if j != i)
    return [nuevo if j == i else w * (1 - nuevo) / resto for j, w in enumerate(pesos)]


w0 = [c["peso"] for c in C]
assert abs(sum(w0) - 1) < 1e-9
sa, sb = puntajes(w0)
contrib = [w * abs(c["A"]["p"] - c["B"]["p"]) for w, c in zip(w0, C)]
i_inf = max(range(len(C)), key=lambda i: contrib[i])
esc = {"original": w0}
esc["+10 pp"] = reescalar(w0, i_inf, w0[i_inf] + 0.10)
esc["-10 pp"] = reescalar(w0, i_inf, w0[i_inf] - 0.10)
esc["pesos iguales (1/6)"] = [1 / 6] * 6
res = {"S_A": sa, "S_B": sb, "criterio_mas_influyente": C[i_inf]["nombre"],
       "contribucion_a_la_diferencia": {c["nombre"]: round(x, 4) for c, x in zip(C, contrib)}, "escenarios": {}}
for k, w in esc.items():
    a, b = puntajes(w)
    res["escenarios"][k] = {"pesos": [round(x, 4) for x in w], "S_A": a, "S_B": b, "elegido": "A" if a > b else "B" if b > a else "empate"}
a, b = puntajes(w0, ajuste_b=1)
res["robustez_B_mas_1_en_estimaciones"] = {"S_A": a, "S_B": b, "elegido": "A" if a > b else "B" if b > a else "empate"}
res["diferencia_minima_para_cambiar_decision"] = sa - sb
(D / "resultados_matriz.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

f = lambda x, n=2: f"{x:.{n}f}".replace(".", ",")
L = ["| Criterio | Peso | A: p | A: peso×p | B: p (estimado) | B: peso×p |", "|---|---:|---:|---:|---:|---:|"]
for w, c in zip(w0, C):
    L.append(f"| {c['nombre']} | {f(w*100,0)} % | {c['A']['p']} | {f(w*c['A']['p'],2)} | {c['B']['p']} | {f(w*c['B']['p'],2)} |")
L.append(f"| **Puntaje ponderado S** | 100 % | | **{f(sa)}** | | **{f(sb)}** |")
(D / "resultados_matriz.md").write_text("\n".join(L), encoding="utf-8")
print(json.dumps(res, indent=2, ensure_ascii=False))
