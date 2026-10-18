"""AGENTE CREDITSCORE: ciclo Percepcion -> Decision -> Accion + retroalimentacion (aprendizaje)."""
import time

import numpy as np

from .acciones import Actuadores
from .decision import REVISION, Decision, ModuloDecision
from .memoria import MemoriaCortoPlazo
from .metricas import psi
from .percepcion import INVALIDA, ModuloPercepcion, Percepcion


class AgenteCreditScore:
    # Planificacion y descomposicion de tareas (componente IBM 2)
    PLAN = ["recibir_solicitud", "validar_informacion", "consultar_buro", "predecir_default",
            "contrastar_casos_similares", "verificar_reglas", "decidir_revision_humana", "registrar_salida"]

    def __init__(self, entorno, modelo, memoria_lp, cfg, registro):
        self.cfg = cfg
        self.entorno, self.modelo, self.memoria_lp, self.registro = entorno, modelo, memoria_lp, registro
        self.memoria_cp = MemoriaCortoPlazo()
        self.percepcion = ModuloPercepcion(entorno, cfg, registro)
        self.decision = ModuloDecision(cfg)
        self.actuadores = Actuadores(entorno, memoria_lp, registro, cfg)
        self._pred = {}   # id -> (x, p) a la espera del resultado observado

    # ---------------- ciclo del agente ----------------
    def percibir(self, id_sol):                                   # PERCEPCION
        per = self.percepcion.percibir(id_sol)
        self.memoria_cp.registrar("percepcion", per.estado)
        self.registro.evento("PERCEPCION", id_sol, estado=per.estado, problemas=per.problemas, dti=per.dti)
        return per

    def decidir(self, per):                                       # DECISION
        dec = self.decision.decidir(per, self.modelo, self.memoria_lp)
        self.memoria_cp.registrar("decision", dec.accion)
        if per.features is not None:
            self._pred[per.id] = (per.features, dec.p_default)
        self.registro.evento("DECISION", per.id, accion=dec.accion, p_default=dec.p_default,
                             calificacion=dec.calificacion, p_vecinos=dec.p_vecinos,
                             desacuerdo=dec.desacuerdo, costos=dec.costos, reglas=dec.reglas, razon=dec.razon)
        return dec

    def actuar(self, dec, per):                                   # ACCION
        estados = self.actuadores.ejecutar(dec, per, self.modelo.version)
        self.memoria_cp.registrar("acciones", estados)
        self.registro.evento("ACCION", per.id, accion=dec.accion, estados=estados)
        return estados

    def evaluar(self, id_sol):
        t0 = time.perf_counter()
        self.memoria_cp.reiniciar(id_sol)
        self.registro.evento("EVALUACION_INICIO", id_sol, plan=self.PLAN)
        per = None
        try:
            per = self.percibir(id_sol)
            dec = self.decidir(per)
        except Exception as e:   # fail-safe: ante error interno nunca se decide automaticamente
            self.registro.evento("ERROR_INTERNO", id_sol, error=repr(e))
            per = per or Percepcion(id_sol, {}, INVALIDA, ["error_interno"])
            dec = Decision(REVISION, None, "N/D", reglas=["R0_ERROR_INTERNO"], razon=f"error interno: {e!r}")
        estados = self.actuar(dec, per)
        ms = (time.perf_counter() - t0) * 1000
        res = {"id": id_sol, "accion": dec.accion, "p_default": dec.p_default, "calificacion": dec.calificacion,
               "estado_percepcion": per.estado, "estado_acciones": estados, "razon": dec.razon,
               "reglas": dec.reglas, "version_modelo": self.modelo.version, "latencia_ms": round(ms, 3)}
        self.registro.evento("EVALUACION_COMPLETA", id_sol, accion=dec.accion, latencia_ms=res["latencia_ms"])
        return res

    # ---------------- aprendizaje y adaptacion ----------------
    def registrar_resultado_observado(self, id_sol):
        y = self.entorno.resultado_observado(id_sol)
        if y is None:
            return False
        ok = self.memoria_lp.registrar_resultado(id_sol, y)
        if ok:
            self.registro.evento("RESULTADO_OBSERVADO", id_sol, incumplio=int(y))
        return ok

    def revisar_aprendizaje(self):
        a = self.cfg["aprendizaje"]
        items = []
        for id_sol, (x, p) in self._pred.items():
            i = self.memoria_lp._pos.get(id_sol)
            if i is not None and not np.isnan(self.memoria_lp.y[i]):
                items.append((id_sol, float(self.memoria_lp.y[i]), p))
        if len(items) < a["min_retroalimentacion"]:
            return {"accion": "datos_insuficientes", "n_retroalimentacion": len(items), "deriva": False}
        ids = [t[0] for t in items]
        y = np.array([t[1] for t in items])
        p = np.array([t[2] for t in items])
        ps = psi(self.modelo.ref_scores, p)
        brecha = abs(p.mean() - y.mean())
        causa = [n for n, c in (("psi", ps > a["psi_umbral"]), ("brecha_calibracion", brecha > a["brecha_calibracion_umbral"])) if c]
        res = {"n_retroalimentacion": len(items), "psi": round(float(ps), 4), "brecha_calibracion": round(float(brecha), 4),
               "deriva": bool(causa), "causas": causa, "accion": "sin_cambios"}
        if causa:
            X, yh, ids_h = self.memoria_lp.datos_con_resultado()
            recientes = set(ids)
            pesos = np.array([a["peso_reciente"] if i in recientes else 1.0 for i in ids_h])
            res["version_anterior"] = self.modelo.version
            res["version_nueva"] = self.modelo.recalibrar(X, yh, pesos)
            res["accion"] = "recalibrado"
            self._pred.clear()
        self.registro.evento("REVISION_APRENDIZAJE", None, **res)
        return res
