"""MEMORIA: corto plazo (contexto de una solicitud) y largo plazo (historial de casos)."""
import json

import numpy as np


class MemoriaCortoPlazo:
    def __init__(self):
        self.contexto = {}

    def reiniciar(self, id_sol):
        self.contexto = {"id": id_sol}

    def registrar(self, clave, valor):
        self.contexto[clave] = valor


class MemoriaLargoPlazo:
    def __init__(self, n_features=5):
        self.n_features = n_features
        self.X = np.zeros((1024, n_features))
        self.y = np.full(1024, np.nan)
        self.n = 0
        self.ids = []
        self.decisiones = []
        self.versiones = []
        self._pos = {}

    def agregar(self, id_sol, x, decision, version, y=None):
        if self.n == len(self.y):
            self.X = np.vstack([self.X, np.zeros_like(self.X)])
            self.y = np.concatenate([self.y, np.full(len(self.y), np.nan)])
        self.X[self.n] = x
        self.y[self.n] = np.nan if y is None else y
        self.ids.append(id_sol)
        self.decisiones.append(decision)
        self.versiones.append(version)
        self._pos[id_sol] = self.n
        self.n += 1

    def registrar_resultado(self, id_sol, y):
        i = self._pos.get(id_sol)
        if i is not None:
            self.y[i] = y
        return i is not None

    def vecinos_similares(self, x, mu, sigma, k):
        """Tasa de incumplimiento de los k casos historicos mas similares (con resultado conocido)."""
        conocidos = np.where(~np.isnan(self.y[:self.n]))[0]
        if len(conocidos) < k:
            return None
        Z = (self.X[conocidos] - mu) / sigma
        d = np.linalg.norm(Z - (np.asarray(x) - mu) / sigma, axis=1)
        idx = np.argpartition(d, k - 1)[:k]
        return {"tasa": float(self.y[conocidos[idx]].mean()), "k": int(k),
                "dist_media": float(d[idx].mean())}

    def datos_con_resultado(self):
        m = ~np.isnan(self.y[:self.n])
        ids = [self.ids[i] for i in np.where(m)[0]]
        return self.X[:self.n][m], self.y[:self.n][m], ids

    def guardar(self, ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            for i in range(self.n):
                f.write(json.dumps({"id": self.ids[i], "x": self.X[i].tolist(),
                                    "y": None if np.isnan(self.y[i]) else float(self.y[i]),
                                    "decision": self.decisiones[i], "version": self.versiones[i]}) + "\n")
