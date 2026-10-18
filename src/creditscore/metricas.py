"""Metricas de evaluacion implementadas con numpy (sin dependencias adicionales)."""
import numpy as np


def auc_roc(y, p):
    """AUC-ROC por el estadistico de Mann-Whitney, con rangos promedio para empates."""
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    _, inv, cuentas = np.unique(p, return_inverse=True, return_counts=True)
    acum = np.cumsum(cuentas)
    rango_prom = acum - (cuentas - 1) / 2.0
    rangos = rango_prom[inv]
    return float((rangos[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def brier(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    return float(np.mean((p - y) ** 2))


def ece(y, p, bins=10):
    """Error de calibracion esperado con bins de igual ancho."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    idx = np.minimum((p * bins).astype(int), bins - 1)
    total = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            total += m.sum() / len(p) * abs(y[m].mean() - p[m].mean())
    return float(total)


def psi(referencia, actual, bins=10):
    """Population Stability Index usando deciles de la referencia."""
    referencia = np.asarray(referencia, dtype=float)
    actual = np.asarray(actual, dtype=float)
    bordes = np.unique(np.quantile(referencia, np.linspace(0, 1, bins + 1)))
    if len(bordes) < 3:
        return 0.0
    bordes[0], bordes[-1] = -np.inf, np.inf
    r = np.histogram(referencia, bins=bordes)[0] / len(referencia)
    a = np.histogram(actual, bins=bordes)[0] / len(actual)
    r = np.clip(r, 1e-6, None)
    a = np.clip(a, 1e-6, None)
    return float(np.sum((a - r) * np.log(a / r)))
