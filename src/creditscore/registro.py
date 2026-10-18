"""Registro de eventos en JSON Lines con marca de tiempo (base de las pruebas)."""
import datetime as dt
import json
import os

import numpy as np


def _json_default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


class RegistroEventos:
    def __init__(self, ruta=None, guardar_en_memoria=True):
        self.ruta = ruta
        self.eventos = []
        self.guardar_en_memoria = guardar_en_memoria
        self._f = None
        if ruta:
            os.makedirs(os.path.dirname(str(ruta)) or ".", exist_ok=True)
            self._f = open(ruta, "a", encoding="utf-8")

    def evento(self, tipo, id_solicitud=None, **datos):
        e = {"timestamp": dt.datetime.now().isoformat(timespec="milliseconds"),
             "evento": tipo, "id_solicitud": id_solicitud}
        e.update(datos)
        if self.guardar_en_memoria:
            self.eventos.append(e)
        if self._f:
            self._f.write(json.dumps(e, ensure_ascii=False, default=_json_default) + "\n")
            self._f.flush()
        return e

    def cerrar(self):
        if self._f:
            self._f.close()
            self._f = None
