"""MODULO DE DECISION: agente basado en utilidad (costo esperado) con abstencion por incertidumbre."""
from dataclasses import dataclass, field
from typing import Optional

from .percepcion import VALIDA

APROBAR, RECHAZAR, REVISION = "APROBAR", "RECHAZAR", "REVISION_HUMANA"
_ORDEN = {REVISION: 0, APROBAR: 1, RECHAZAR: 2}   # en empate se prefiere la opcion conservadora


@dataclass
class Decision:
    accion: str
    p_default: Optional[float]
    calificacion: str
    p_vecinos: Optional[float] = None
    desacuerdo: Optional[float] = None
    costos: dict = field(default_factory=dict)
    reglas: list = field(default_factory=list)
    razon: str = ""
    factores: list = field(default_factory=list)


class ModuloDecision:
    def __init__(self, cfg):
        self.c = cfg["decision"]

    def calificar(self, p):
        for limite, letra in self.c["bandas"]:
            if p < limite:
                return letra
        return self.c["bandas"][-1][1]

    def decidir(self, percepcion, modelo, memoria_lp):
        # R1: datos no validos/incompletos/fuera de dominio -> el agente se abstiene
        if percepcion.estado != VALIDA:
            return Decision(REVISION, None, "N/D", reglas=["R1_DATOS_NO_VALIDOS"],
                            razon=f"{percepcion.estado}: " + "; ".join(percepcion.problemas))
        x = percepcion.features
        p = modelo.predict_proba(x)
        factores = modelo.contribuciones(x)
        cal = self.calificar(p)
        costos = {APROBAR: self.c["costo_default"] * p,
                  RECHAZAR: self.c["costo_rechazo_bueno"] * (1 - p),
                  REVISION: self.c["costo_revision"]}
        vec = memoria_lp.vecinos_similares(x, modelo.mu, modelo.sigma, self.c["k_vecinos"])
        p_vec = vec["tasa"] if vec else None
        desacuerdo = abs(p - p_vec) if vec else None
        base = dict(p_default=p, calificacion=cal, p_vecinos=p_vec, desacuerdo=desacuerdo,
                    costos={k: round(v, 4) for k, v in costos.items()}, factores=factores)
        # R4: politica crediticia (limite de endeudamiento definido por la entidad)
        if percepcion.dti is not None and percepcion.dti > self.c["dti_politica_max"]:
            return Decision(REVISION, reglas=["R4_POLITICA_DTI"],
                            razon=f"DTI {percepcion.dti:.2f} supera el limite de politica {self.c['dti_politica_max']}",
                            **base)
        # R3: desacuerdo modelo vs. casos historicos similares -> incertidumbre alta
        if desacuerdo is not None and desacuerdo > self.c["desacuerdo_max"]:
            return Decision(REVISION, reglas=["R3_INCERTIDUMBRE"],
                            razon=f"Modelo ({p:.2f}) y casos similares ({p_vec:.2f}) discrepan en {desacuerdo:.2f}",
                            **base)
        # R2: minimizar costo esperado (funcion de utilidad = -costo)
        accion = min(costos, key=lambda a: (costos[a], _ORDEN[a]))
        return Decision(accion, reglas=["R2_UTILIDAD"],
                        razon=f"Costo esperado minimo: {accion} ({costos[accion]:.3f})", **base)
