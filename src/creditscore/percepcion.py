"""MODULO DE PERCEPCION: sensores (formulario + buro), validacion y construccion de features."""
import datetime as dt
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .entorno import BuroNoDisponible

CAMPOS_FORM = ["ingresos_mensuales", "obligaciones_mensuales"]
CAMPOS_BURO = ["pagos_atrasados_24m", "antiguedad_historial_meses", "lineas_credito_abiertas"]
ENTEROS = {"pagos_atrasados_24m", "antiguedad_historial_meses", "lineas_credito_abiertas"}
NOMBRES_FEATURES = ["log_ingresos", "dti", "pagos_atrasados_24m", "log1p_antiguedad", "lineas_credito"]

VALIDA, INCOMPLETA, INVALIDA, FUERA_DOMINIO = "VALIDA", "INCOMPLETA", "INVALIDA", "FUERA_DOMINIO"


@dataclass
class Percepcion:
    id: str
    crudo: dict
    estado: str
    problemas: list = field(default_factory=list)
    dti: Optional[float] = None
    features: Optional[np.ndarray] = None
    timestamp: str = ""


def a_numero(valor):
    """Convierte a float; devuelve None si no es numerico (bool, texto, NaN, inf)."""
    if isinstance(valor, bool) or valor is None:
        return None
    try:
        x = float(str(valor).strip()) if isinstance(valor, str) else float(valor)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def construir_features(ingresos, obligaciones, pagos, antiguedad, lineas):
    dti = obligaciones / ingresos
    return np.array([math.log(ingresos), dti, pagos, math.log1p(antiguedad), lineas], dtype=float)


class ModuloPercepcion:
    def __init__(self, entorno, cfg, registro):
        self.entorno = entorno
        self.rangos = cfg["validacion"]
        self.reintentos = cfg["entorno"]["reintentos"]
        self.registro = registro

    def _leer_buro(self, id_sol):
        for intento in range(1, self.reintentos + 1):
            try:
                return self.entorno.consultar_buro(id_sol)
            except BuroNoDisponible as e:
                self.registro.evento("SENSOR_FALLO", id_sol, sensor="buro", intento=intento, error=str(e))
        return None

    def percibir(self, id_sol):
        ahora = dt.datetime.now().isoformat(timespec="milliseconds")
        problemas, crudo = [], {}
        try:
            crudo.update(self.entorno.recibir_formulario(id_sol))
        except KeyError:
            return Percepcion(id_sol, {}, INVALIDA, ["solicitud_inexistente"], timestamp=ahora)
        buro = self._leer_buro(id_sol)
        if buro is None:
            problemas.append("buro_no_disponible")
        else:
            crudo.update(buro)

        valores, invalida, incompleta, fuera = {}, False, False, False
        for campo in CAMPOS_FORM + CAMPOS_BURO:
            if campo in CAMPOS_BURO and buro is None:
                incompleta = True
                continue
            v = crudo.get(campo)
            if v is None:
                problemas.append(f"{campo}:faltante")
                incompleta = True
                continue
            x = a_numero(v)
            if x is None:
                problemas.append(f"{campo}:no_numerico")
                invalida = True
                continue
            if campo in ENTEROS and x != int(x):
                problemas.append(f"{campo}:debe_ser_entero")
                invalida = True
                continue
            lo, hi = self.rangos[campo]
            if x < 0:
                problemas.append(f"{campo}:negativo")
                invalida = True
            elif not (lo <= x <= hi):
                problemas.append(f"{campo}:fuera_de_rango[{lo},{hi}]")
                fuera = True
            valores[campo] = x

        dti = None
        if all(c in valores for c in CAMPOS_FORM) and valores["ingresos_mensuales"] > 0 \
                and not invalida:
            dti = valores["obligaciones_mensuales"] / valores["ingresos_mensuales"]
            lo, hi = self.rangos["dti"]
            if not (lo <= dti <= hi):
                problemas.append(f"dti:inconsistente({dti:.2f})")
                fuera = True

        estado = (INVALIDA if invalida else INCOMPLETA if incompleta
                  else FUERA_DOMINIO if fuera else VALIDA)
        features = None
        if estado == VALIDA:
            features = construir_features(valores["ingresos_mensuales"], valores["obligaciones_mensuales"],
                                          valores["pagos_atrasados_24m"], valores["antiguedad_historial_meses"],
                                          valores["lineas_credito_abiertas"])
        return Percepcion(id_sol, crudo, estado, problemas, dti, features, ahora)
