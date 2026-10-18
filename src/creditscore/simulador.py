"""Simulador de solicitudes de credito SINTETICAS.

Los datos NO son reales: reproducen la estructura de las percepciones del diseno
(ingresos, obligaciones, historial de pagos, lineas abiertas) y su resultado
observado posterior. El ruido latente (SIGMA_LATENTE) representa los factores no
observables que hacen el ambiente parcialmente observable y estocastico.
"""
import numpy as np

B0 = -2.30            # intercepto (ajustado SOLO para tasa de incumplimiento ~ 20 %)
SIGMA_LATENTE = 0.8   # factores no observados por el agente


def generar_solicitudes(n, rng, prefijo="S", deriva=0.0):
    """Genera n solicitudes. deriva > 0 simula un deterioro economico (cambio de distribucion)."""
    ing = np.exp(rng.normal(np.log(2.8e6), 0.55, n))
    ing = np.clip(ing, 6e5, 4e7)
    if deriva:
        ing = ing * (1 - 0.25 * deriva)
    dti = np.clip(rng.beta(2.5, 5.5, n), 0.01, 0.95)
    obl = ing * dti
    atr = np.minimum(rng.poisson(1.0 * (1 + dti)), 24)
    ant = np.clip(rng.gamma(2.0, 36.0, n).astype(int), 0, 600)
    lin = np.minimum(rng.poisson(3.5, n), 30)
    z = (B0 + 6.0 * (dti - 0.31) + 0.45 * atr - 0.8 * (np.log(ing) - np.log(2.8e6))
         - 0.008 * (ant - 72) + 0.10 * (lin - 3.5) + rng.normal(0, SIGMA_LATENTE, n))
    if deriva:
        z = z + 0.6 * deriva + 1.5 * deriva * (dti - 0.31)
    pd_real = 1 / (1 + np.exp(-z))
    y = (rng.random(n) < pd_real).astype(int)
    sols = []
    for i in range(n):
        sols.append({
            "id": f"{prefijo}-{i:05d}",
            "formulario": {"ingresos_mensuales": float(round(ing[i])),
                           "obligaciones_mensuales": float(round(obl[i]))},
            "buro": {"pagos_atrasados_24m": int(atr[i]),
                     "antiguedad_historial_meses": int(ant[i]),
                     "lineas_credito_abiertas": int(lin[i])},
            "_default": int(y[i]),   # oculto para el agente: resultado observado posterior
        })
    return sols
