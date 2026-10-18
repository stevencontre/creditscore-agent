"""MODULO DE ACCION: actuadores sobre el sistema de originacion, bandeja de analistas, scoring y auditoria."""
from .decision import APROBAR, RECHAZAR, REVISION
from .entorno import OriginacionNoDisponible


class Actuadores:
    def __init__(self, entorno, memoria_lp, registro, cfg):
        self.entorno = entorno
        self.memoria_lp = memoria_lp
        self.registro = registro
        self.reintentos = cfg["entorno"]["reintentos"]
        self.pendientes = []   # outbox: recomendaciones que no pudieron registrarse (no se pierden)

    def _originacion(self, id_sol, payload):
        for intento in range(1, self.reintentos + 1):
            try:
                self.entorno.registrar_originacion(id_sol, payload)
                return "REGISTRADA"
            except OriginacionNoDisponible as e:
                self.registro.evento("ACTUADOR_FALLO", id_sol, actuador="originacion",
                                     intento=intento, error=str(e))
        self.pendientes.append(payload)
        return "DIFERIDA"

    def ejecutar(self, decision, percepcion, version_modelo):
        id_sol, estados = percepcion.id, {}
        # Actuador 1: calificacion de riesgo -> modulo de scoring/expediente
        if decision.calificacion != "N/D":
            self.entorno.registrar_expediente(id_sol, {"calificacion": decision.calificacion,
                                                       "p_default": decision.p_default})
            estados["calificacion"] = "REGISTRADA"
        # Actuador 2: accion principal
        if decision.accion in (APROBAR, RECHAZAR):
            estados["originacion"] = self._originacion(id_sol, {
                "id": id_sol, "recomendacion": decision.accion, "calificacion": decision.calificacion,
                "p_default": decision.p_default, "version_modelo": version_modelo})
        elif decision.accion == REVISION:
            self.entorno.notificar_analista({
                "id": id_sol, "calificacion": decision.calificacion, "p_default": decision.p_default,
                "razon": decision.razon, "factores": decision.factores, "reglas": decision.reglas})
            estados["revision_humana"] = "ENVIADA"
        # Actuador 3: registro historico (auditoria + memoria de largo plazo)
        registro_aud = {"id": id_sol, "version_modelo": version_modelo, "entradas": percepcion.crudo,
                        "estado_percepcion": percepcion.estado, "p_default": decision.p_default,
                        "calificacion": decision.calificacion, "accion": decision.accion,
                        "razon": decision.razon, "reglas": decision.reglas, "estado_acciones": estados}
        self.entorno.registrar_auditoria(registro_aud)
        if percepcion.features is not None:
            self.memoria_lp.agregar(id_sol, percepcion.features, decision.accion, version_modelo)
        estados["historico"] = "REGISTRADO"
        self.registro.evento("AUDITORIA", id_sol, **{k: v for k, v in registro_aud.items() if k != "id"})
        return estados
