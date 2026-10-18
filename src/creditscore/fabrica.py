"""Construccion reproducible del agente: simula historico, entrena el modelo y arma el entorno."""
import numpy as np

from .agente import AgenteCreditScore
from .config import cargar_config
from .entorno import EntornoSimulado
from .memoria import MemoriaLargoPlazo
from .modelo import ModeloRiesgo
from .percepcion import construir_features
from .registro import RegistroEventos
from .simulador import generar_solicitudes


def features_de(sol):
    f, b = sol["formulario"], sol["buro"]
    return construir_features(f["ingresos_mensuales"], f["obligaciones_mensuales"], b["pagos_atrasados_24m"],
                              b["antiguedad_historial_meses"], b["lineas_credito_abiertas"])


def construir(semilla, cfg=None, ruta_log=None, guardar_eventos=True, p_fallo_buro=None, p_fallo_originacion=None):
    cfg = cfg or cargar_config()
    rng = np.random.default_rng(semilla)
    s = cfg["simulador"]
    hist = generar_solicitudes(s["n_historico"], rng, prefijo=f"H{semilla}")
    train, prueba = hist[:s["n_entrenamiento"]], hist[s["n_entrenamiento"]:]
    X = np.array([features_de(t) for t in train])
    y = np.array([t["_default"] for t in train])
    modelo = ModeloRiesgo(cfg["modelo"]["l2"], cfg["modelo"]["version_base"]).entrenar(X, y)
    memoria = MemoriaLargoPlazo(X.shape[1])
    for t, x in zip(train, X):
        memoria.agregar(t["id"], x, "HISTORICO", "historico", y=t["_default"])
    e = cfg["entorno"]
    entorno = EntornoSimulado(prueba, rng=np.random.default_rng(semilla + 10_000),
                              p_fallo_buro=e["p_fallo_buro"] if p_fallo_buro is None else p_fallo_buro,
                              p_fallo_originacion=e["p_fallo_originacion"] if p_fallo_originacion is None else p_fallo_originacion)
    registro = RegistroEventos(ruta_log, guardar_en_memoria=guardar_eventos)
    agente = AgenteCreditScore(entorno, modelo, memoria, cfg, registro)
    return {"agente": agente, "entorno": entorno, "modelo": modelo, "memoria": memoria, "registro": registro,
            "prueba": prueba, "train": train, "cfg": cfg, "rng": rng}
