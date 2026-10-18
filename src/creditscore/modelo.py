"""Modelo predictivo (regresion logistica L2 por Newton-Raphson/IRLS, numpy puro) y aprendizaje."""
import json

import numpy as np

from .percepcion import NOMBRES_FEATURES


def _sigmoide(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -35, 35)))


class ModeloRiesgo:
    def __init__(self, l2=1.0, version="lr-1.0"):
        self.l2 = l2
        self.version = version
        self.mu = self.sigma = self.w = None
        self.b = 0.0
        self.ref_scores = None
        self.n_entrenamiento = 0
        self.n_recalibraciones = 0

    def entrenar(self, X, y, pesos=None, version=None):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        pesos = np.ones(len(y)) if pesos is None else np.asarray(pesos, dtype=float)
        self.mu = X.mean(axis=0)
        self.sigma = X.std(axis=0)
        self.sigma[self.sigma == 0] = 1.0
        Z = (X - self.mu) / self.sigma
        Xb = np.hstack([np.ones((len(y), 1)), Z])
        w = np.zeros(Xb.shape[1])
        pen = np.eye(len(w)) * self.l2
        pen[0, 0] = 0.0
        for _ in range(100):
            p = _sigmoide(Xb @ w)
            g = Xb.T @ (pesos * (p - y)) + pen @ w
            H = Xb.T @ (Xb * (pesos * p * (1 - p))[:, None]) + pen
            paso = np.linalg.solve(H, g)
            w -= paso
            if np.linalg.norm(paso) < 1e-9:
                break
        self.b, self.w = float(w[0]), w[1:]
        self.n_entrenamiento = len(y)
        if version:
            self.version = version
        self.ref_scores = self.predict_proba(X)
        return self

    def estandarizar(self, X):
        return (np.asarray(X, dtype=float) - self.mu) / self.sigma

    def predict_proba(self, X):
        X = np.asarray(X, dtype=float)
        unico = X.ndim == 1
        X2 = X[None, :] if unico else X
        p = _sigmoide(self.estandarizar(X2) @ self.w + self.b)
        return float(p[0]) if unico else p

    def contribuciones(self, x, top=3):
        """Factores mas influyentes (en escala logit) para la explicacion al analista."""
        c = self.estandarizar(x) * self.w
        orden = np.argsort(-np.abs(c))[:top]
        return [(NOMBRES_FEATURES[i], round(float(c[i]), 3)) for i in orden]

    def recalibrar(self, X, y, pesos):
        self.n_recalibraciones += 1
        base = self.version.split("+")[0]
        self.entrenar(X, y, pesos=pesos, version=f"{base}+recal{self.n_recalibraciones}")
        return self.version

    def a_dict(self):
        return {"version": self.version, "l2": self.l2, "mu": self.mu.tolist(), "sigma": self.sigma.tolist(),
                "w": self.w.tolist(), "b": self.b, "n_entrenamiento": self.n_entrenamiento}

    def guardar(self, ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.a_dict(), f, indent=2)
