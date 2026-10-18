"""Escenarios de prueba deterministas (normales, limite, invalidos, fallos y condiciones adversas).

Los resultados esperados se definen aqui, ANTES de ejecutar el agente."""
from .fabrica import construir
from .config import cargar_config

REINT = 3


def sol(id_, ing, obl, atr, ant, lin):
    return {"id": id_, "formulario": {"ingresos_mensuales": ing, "obligaciones_mensuales": obl},
            "buro": {"pagos_atrasados_24m": atr, "antiguedad_historial_meses": ant, "lineas_credito_abiertas": lin},
            "_default": 0}


def _sin_campo(s, campo):
    del s["formulario"][campo]
    return s


def _con(s, grupo, campo, valor):
    s[grupo][campo] = valor
    return s


def _n_ev(info, tipo):
    return sum(1 for e in info["eventos"] if e["evento"] == tipo)


def definir():
    A = lambda i: sol(i, 8e6, 8e5, 0, 120, 3)          # perfil de bajo riesgo
    return [
        dict(id="E01", nombre="Normal: bajo riesgo", cat="normal", esperado="APROBAR; originacion REGISTRADA",
             sol=A("E01"), check=lambda i: i["res"]["accion"] == "APROBAR" and i["res"]["estado_acciones"]["originacion"] == "REGISTRADA"),
        dict(id="E02", nombre="Normal: alto riesgo", cat="normal", esperado="RECHAZAR; originacion REGISTRADA",
             sol=sol("E02", 1.5e6, 0.8e6, 6, 12, 8), check=lambda i: i["res"]["accion"] == "RECHAZAR" and i["res"]["estado_acciones"]["originacion"] == "REGISTRADA"),
        dict(id="E03", nombre="Normal: riesgo intermedio", cat="normal", esperado="REVISION_HUMANA; caso en bandeja del analista",
             sol=sol("E03", 2.8e6, 0.9e6, 1, 72, 4), check=lambda i: i["res"]["accion"] == "REVISION_HUMANA" and i["res"]["estado_acciones"].get("revision_humana") == "ENVIADA"),
        dict(id="E04", nombre="Limite: DTI = 0,80 exacto (no excede la politica)", cat="limite", esperado="estado VALIDA y sin regla R4",
             sol=sol("E04", 3e6, 2.4e6, 2, 48, 4), check=lambda i: i["res"]["estado_percepcion"] == "VALIDA" and "R4_POLITICA_DTI" not in i["res"]["reglas"]),
        dict(id="E05", nombre="Limite: DTI = 0,8001 (excede la politica)", cat="limite", esperado="REVISION_HUMANA por R4",
             sol=sol("E05", 3e6, 2.4003e6, 2, 48, 4), check=lambda i: i["res"]["accion"] == "REVISION_HUMANA" and "R4_POLITICA_DTI" in i["res"]["reglas"]),
        dict(id="E06", nombre="Limite: 24 pagos atrasados (maximo permitido)", cat="limite", esperado="estado VALIDA",
             sol=sol("E06", 2e6, 5e5, 24, 36, 5), check=lambda i: i["res"]["estado_percepcion"] == "VALIDA"),
        dict(id="E07", nombre="Invalida: 25 pagos atrasados (fuera de rango)", cat="invalida", esperado="REVISION_HUMANA; sin llamada a originacion",
             sol=sol("E07", 2e6, 5e5, 25, 36, 5), check=lambda i: i["res"]["accion"] == "REVISION_HUMANA" and i["llamadas"] == 0 and i["res"]["estado_percepcion"] == "FUERA_DOMINIO"),
        dict(id="E08", nombre="Invalida: ingreso faltante", cat="invalida", esperado="REVISION_HUMANA; estado INCOMPLETA",
             sol=_sin_campo(A("E08"), "ingresos_mensuales"), check=lambda i: i["res"]["accion"] == "REVISION_HUMANA" and i["res"]["estado_percepcion"] == "INCOMPLETA" and i["llamadas"] == 0),
        dict(id="E09", nombre="Invalida: ingreso negativo", cat="invalida", esperado="REVISION_HUMANA; estado INVALIDA",
             sol=_con(A("E09"), "formulario", "ingresos_mensuales", -5e6), check=lambda i: i["res"]["accion"] == "REVISION_HUMANA" and i["res"]["estado_percepcion"] == "INVALIDA"),
        dict(id="E10", nombre="Invalida: ingreso fuera de dominio (9e9)", cat="invalida", esperado="REVISION_HUMANA; estado FUERA_DOMINIO",
             sol=_con(A("E10"), "formulario", "ingresos_mensuales", 9e9), check=lambda i: i["res"]["accion"] == "REVISION_HUMANA" and i["res"]["estado_percepcion"] == "FUERA_DOMINIO"),
        dict(id="E11", nombre="Invalida: valor no numerico ('abc')", cat="invalida", esperado="REVISION_HUMANA; estado INVALIDA",
             sol=_con(A("E11"), "formulario", "obligaciones_mensuales", "abc"), check=lambda i: i["res"]["accion"] == "REVISION_HUMANA" and i["res"]["estado_percepcion"] == "INVALIDA"),
        dict(id="E12", nombre="Fallo: buro de credito caido (sensor sin dato)", cat="fallo", esperado="3 reintentos, REVISION_HUMANA por buro_no_disponible",
             sol=A("E12"), setup=lambda e: setattr(e, "buro_caido", True),
             check=lambda i: i["res"]["accion"] == "REVISION_HUMANA" and _n_ev(i, "SENSOR_FALLO") == REINT and i["llamadas"] == 0),
        dict(id="E13", nombre="Adverso: buro falla 2 veces y responde al 3.er intento", cat="adverso", esperado="2 SENSOR_FALLO y decision normal APROBAR",
             sol=A("E13"), setup=lambda e: setattr(e, "fallos_buro_programados", 2),
             check=lambda i: i["res"]["accion"] == "APROBAR" and _n_ev(i, "SENSOR_FALLO") == 2),
        dict(id="E14", nombre="Fallo: originacion caida", cat="fallo", esperado="APROBAR; originacion DIFERIDA, recomendacion conservada en outbox y auditada",
             sol=A("E14"), setup=lambda e: setattr(e, "originacion_caida", True),
             check=lambda i: i["res"]["accion"] == "APROBAR" and i["res"]["estado_acciones"]["originacion"] == "DIFERIDA" and i["pendientes"] == 1 and i["auditorias"] == 1 and _n_ev(i, "ACTUADOR_FALLO") == REINT),
        dict(id="E15", nombre="Adverso: originacion falla 1 vez y se recupera", cat="adverso", esperado="originacion REGISTRADA tras reintento",
             sol=A("E15"), setup=lambda e: setattr(e, "fallos_originacion_programados", 1),
             check=lambda i: i["res"]["estado_acciones"]["originacion"] == "REGISTRADA" and _n_ev(i, "ACTUADOR_FALLO") == 1),
        dict(id="E16", nombre="Fallo: solicitud inexistente", cat="fallo", esperado="sin excepcion; REVISION_HUMANA INVALIDA",
             sol=None, check=lambda i: i["res"]["accion"] == "REVISION_HUMANA" and i["res"]["estado_percepcion"] == "INVALIDA"),
    ]


def _correr(c, caso):
    a, ent, reg = c["agente"], c["entorno"], c["registro"]
    s = caso["sol"]
    if s is not None:
        ent.registrar_solicitud(s)
    if caso.get("setup"):
        caso["setup"](ent)
    n0, l0, p0, a0 = len(reg.eventos), ent.llamadas_originacion, len(a.actuadores.pendientes), len(ent.auditoria)
    res = a.evaluar(s["id"] if s else "NO-EXISTE")
    info = {"res": res, "eventos": reg.eventos[n0:], "llamadas": ent.llamadas_originacion - l0,
            "pendientes": len(a.actuadores.pendientes) - p0, "auditorias": len(ent.auditoria) - a0}
    ent.buro_caido = ent.originacion_caida = False
    ent.fallos_buro_programados = ent.fallos_originacion_programados = 0
    return info


def correr_escenarios(ruta_log=None, cfg=None):
    cfg = cfg or cargar_config()
    c = construir(cfg["simulador"]["semilla_base"], cfg, ruta_log=ruta_log)
    filas = []
    for caso in definir():
        info = _correr(c, caso)
        r = info["res"]
        obs = f"{r['accion']} | {r['estado_percepcion']} | {','.join(r['reglas'])} | p={None if r['p_default'] is None else round(r['p_default'], 3)} | acciones={r['estado_acciones']}"
        filas.append({"id": caso["id"], "escenario": caso["nombre"], "categoria": caso["cat"], "esperado": caso["esperado"],
                      "observado": obs, "cumple": bool(caso["check"](info))})
    # E17: repetibilidad (5 repeticiones del mismo caso -> resultados identicos)
    salidas = []
    for k in range(5):
        i = _correr(c, dict(sol=sol(f"E17-{k}", 8e6, 8e5, 0, 120, 3)))
        salidas.append((i["res"]["accion"], i["res"]["p_default"], i["res"]["calificacion"]))
    filas.append({"id": "E17", "escenario": "Repetibilidad: mismo caso 5 veces", "categoria": "repeticion",
                  "esperado": "5 salidas identicas", "observado": str(salidas[0]) + f" x{len(set(salidas))} distinto(s)",
                  "cumple": len(set(salidas)) == 1})
    c["registro"].cerrar()
    return filas
