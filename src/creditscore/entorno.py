"""Entorno simulado: formulario, buro de credito, sistema de originacion y cartera."""
import copy


class BuroNoDisponible(Exception):
    pass


class OriginacionNoDisponible(Exception):
    pass


class EntornoSimulado:
    def __init__(self, solicitudes=(), rng=None, p_fallo_buro=0.0, p_fallo_originacion=0.0):
        self.solicitudes = {}
        self.rng = rng
        self.p_fallo_buro = p_fallo_buro
        self.p_fallo_originacion = p_fallo_originacion
        # inyeccion de fallos deterministas (para escenarios de prueba)
        self.buro_caido = False
        self.originacion_caida = False
        self.fallos_buro_programados = 0
        self.fallos_originacion_programados = 0
        # estado observable del entorno tras las acciones del agente
        self.originacion = {}     # id -> recomendacion registrada
        self.bandeja = []         # casos remitidos a analistas
        self.expedientes = {}     # id -> calificacion registrada
        self.auditoria = []       # base de auditoria y aprendizaje
        self.llamadas_originacion = 0
        for s in solicitudes:
            self.registrar_solicitud(s)

    def registrar_solicitud(self, sol):
        self.solicitudes[sol["id"]] = sol

    # ---- sensores ---------------------------------------------------------
    def recibir_formulario(self, id_sol):
        return copy.deepcopy(self.solicitudes[id_sol]["formulario"])

    def consultar_buro(self, id_sol):
        if self.buro_caido:
            raise BuroNoDisponible("buro caido")
        if self.fallos_buro_programados > 0:
            self.fallos_buro_programados -= 1
            raise BuroNoDisponible("timeout programado")
        if self.rng is not None and self.p_fallo_buro and self.rng.random() < self.p_fallo_buro:
            raise BuroNoDisponible("timeout aleatorio")
        return copy.deepcopy(self.solicitudes[id_sol]["buro"])

    def resultado_observado(self, id_sol):
        """Sistema de seguimiento de cartera (llega meses despues de la decision)."""
        return self.solicitudes[id_sol].get("_default")

    # ---- actuadores del entorno -------------------------------------------
    def registrar_originacion(self, id_sol, payload):
        self.llamadas_originacion += 1
        if self.originacion_caida:
            raise OriginacionNoDisponible("originacion caida")
        if self.fallos_originacion_programados > 0:
            self.fallos_originacion_programados -= 1
            raise OriginacionNoDisponible("fallo programado")
        if self.rng is not None and self.p_fallo_originacion and self.rng.random() < self.p_fallo_originacion:
            raise OriginacionNoDisponible("fallo aleatorio")
        self.originacion[id_sol] = payload

    def notificar_analista(self, payload):
        self.bandeja.append(payload)

    def registrar_expediente(self, id_sol, payload):
        self.expedientes[id_sol] = payload

    def registrar_auditoria(self, registro):
        self.auditoria.append(registro)
