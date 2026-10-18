"""Pruebas de desempeno M1-M7 (umbrales leidos de config/umbrales.json, fijados antes de ejecutar)."""
import hashlib
import json
import math
import platform
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from .config import RAIZ, cargar_config, cargar_umbrales
from .fabrica import construir, features_de
from .metricas import auc_roc, brier, ece
from .simulador import generar_solicitudes
from .registro import RegistroEventos

CORRUPCIONES = ["ingreso_faltante", "obligaciones_faltante", "ingreso_negativo", "valor_no_numerico", "valor_NaN",
                "ingreso_fuera_dominio", "pagos_fuera_rango", "lineas_negativas", "dti_inconsistente", "buro_caido"]


def _corromper(ent, sol, tipo):
    f, b = sol["formulario"], sol["buro"]
    if tipo == "ingreso_faltante": del f["ingresos_mensuales"]
    elif tipo == "obligaciones_faltante": del f["obligaciones_mensuales"]
    elif tipo == "ingreso_negativo": f["ingresos_mensuales"] = -abs(f["ingresos_mensuales"])
    elif tipo == "valor_no_numerico": f["ingresos_mensuales"] = "sin dato"
    elif tipo == "valor_NaN": f["obligaciones_mensuales"] = float("nan")
    elif tipo == "ingreso_fuera_dominio": f["ingresos_mensuales"] = 9e9
    elif tipo == "pagos_fuera_rango": b["pagos_atrasados_24m"] = 30
    elif tipo == "lineas_negativas": b["lineas_credito_abiertas"] = -1
    elif tipo == "dti_inconsistente": f["obligaciones_mensuales"] = f["ingresos_mensuales"] * 10
    elif tipo == "buro_caido": ent.buro_caido = True


def _m1_m2_m4(U, cfg, log):
    filas, lat = [], []
    for s in U["semillas"]:
        c = construir(s, cfg, ruta_log=log, guardar_eventos=False)
        a = c["agente"]
        a.registro.evento("MARCA", None, medida="M1_M2_M4", semilla=s)
        res = [a.evaluar(t["id"]) for t in c["prueba"][:U["n_prueba_por_semilla"]]]
        y = np.array([t["_default"] for t in c["prueba"][:U["n_prueba_por_semilla"]]])
        v = np.array([r["p_default"] is not None for r in res])
        p = np.array([r["p_default"] if r["p_default"] is not None else np.nan for r in res])
        acc = np.array([r["accion"] for r in res])
        lat += [r["latencia_ms"] for r in res]
        ap = acc == "APROBAR"
        filas.append({"semilla": s, "n": len(res), "n_validas": int(v.sum()),
                      "auc": auc_roc(y[v], p[v]), "ece": ece(y[v], p[v]), "brier": brier(y[v], p[v]),
                      "tasa_default": float(y.mean()), "pct_aprobar": float(ap.mean()),
                      "pct_rechazar": float((acc == "RECHAZAR").mean()), "pct_revision": float((acc == "REVISION_HUMANA").mean()),
                      "default_entre_aprobados": float(y[ap].mean()) if ap.any() else None,
                      "recall_default_no_aprobado": float((~ap & (y == 1)).sum() / max((y == 1).sum(), 1))})
        a.registro.cerrar()
    return filas, np.array(lat)


def _m3(U, cfg, log):
    ok = tot = 0
    por_tipo = defaultdict(lambda: [0, 0])
    for s in U["semillas"]:
        c = construir(s + 100, cfg, ruta_log=log, guardar_eventos=False)
        a, ent = c["agente"], c["entorno"]
        a.registro.evento("MARCA", None, medida="M3", semilla=s + 100)
        for i, t in enumerate(c["prueba"][:U["n_invalidas_por_semilla"]]):
            tipo = CORRUPCIONES[i % len(CORRUPCIONES)]
            _corromper(ent, t, tipo)
            l0 = ent.llamadas_originacion
            r = a.evaluar(t["id"])
            ent.buro_caido = False
            bien = (r["accion"] == "REVISION_HUMANA" and r["p_default"] is None and ent.llamadas_originacion == l0
                    and "originacion" not in r["estado_acciones"])
            ok += bien
            tot += 1
            por_tipo[tipo][0] += bien
            por_tipo[tipo][1] += 1
        a.registro.cerrar()
    return {"correctos": int(ok), "total": tot, "tasa": ok / tot, "por_tipo": dict(por_tipo)}


def _faltas(U, cfg, log):
    n = 0
    for s in U["semillas"]:
        c = construir(s + 200, cfg, ruta_log=log, guardar_eventos=False, p_fallo_buro=0.3, p_fallo_originacion=0.3)
        a = c["agente"]
        a.registro.evento("MARCA", None, medida="M5_fallos_aleatorios", semilla=s + 200)
        for t in c["prueba"][:U["n_trazabilidad_fallos_por_semilla"]]:
            a.evaluar(t["id"])
            n += 1
        a.registro.cerrar()
    return n


def _m5(ruta_log):
    """Verifica leyendo el archivo de log: cadena completa de eventos y campos de auditoria por evaluacion."""
    req = {"INICIO": 0, "PERCEPCION": 0, "DECISION": 0, "ACCION": 0, "AUDITORIA": 0, "EVALUACION_COMPLETA": 0}
    mapa = {"EVALUACION_INICIO": "INICIO", **{k: k for k in list(req)[1:]}}
    campos = ["version_modelo", "entradas", "estado_percepcion", "p_default", "calificacion", "accion", "razon"]
    cuentas = defaultdict(lambda: dict(req))
    aud_ok = {}
    with open(ruta_log, encoding="utf-8") as f:
        for linea in f:
            e = json.loads(linea)
            if e["evento"] in mapa and e.get("id_solicitud"):
                cuentas[e["id_solicitud"]][mapa[e["evento"]]] += 1
                if e["evento"] == "AUDITORIA":
                    aud_ok[e["id_solicitud"]] = e.get("timestamp") and all(k in e for k in campos)
    completas = sum(1 for i, c in cuentas.items() if all(v == 1 for v in c.values()) and aud_ok.get(i))
    return {"evaluaciones": len(cuentas), "completas": completas, "tasa": completas / max(len(cuentas), 1)}


def _m6b(U, cfg):
    iguales = tot = 0
    for s in U["semillas"]:
        corridas = []
        for _ in range(2):
            c = construir(s, cfg, guardar_eventos=False)
            corridas.append([(r["accion"], r["p_default"], r["calificacion"])
                             for r in (c["agente"].evaluar(t["id"]) for t in c["prueba"][:300])])
        iguales += sum(x == y for x, y in zip(*corridas))
        tot += 300
    return {"identicas": iguales, "total": tot, "tasa": iguales / tot}


def _m7(U, cfg):
    filas = []
    for s in U["semillas"]:
        c = construir(s + 300, cfg, guardar_eventos=False)
        a, ent, m = c["agente"], c["entorno"], c["modelo"]
        rng = np.random.default_rng(s + 777)
        d = generar_solicitudes(2000, rng, prefijo=f"D{s}", deriva=1.0)
        for t in d:
            ent.registrar_solicitud(t)
        retro, prueba = d[:1000], d[1000:]
        for t in retro:
            a.evaluar(t["id"])
            a.registrar_resultado_observado(t["id"])
        Xt = np.array([features_de(t) for t in prueba])
        yt = np.array([t["_default"] for t in prueba])
        p0 = m.predict_proba(Xt)
        r = a.revisar_aprendizaje()
        p1 = m.predict_proba(Xt)
        filas.append({"semilla": s, "deriva_detectada": r["deriva"], "causas": r.get("causas"), "psi": r.get("psi"),
                      "brecha_calibracion": r.get("brecha_calibracion"), "accion": r["accion"],
                      "brier_antes": brier(yt, p0), "brier_despues": brier(yt, p1),
                      "ece_antes": ece(yt, p0), "ece_despues": ece(yt, p1),
                      "auc_antes": auc_roc(yt, p0), "auc_despues": auc_roc(yt, p1)})
    # informativo: falsas alarmas sin deriva
    falsas = 0
    for s in U["semillas"]:
        c = construir(s + 400, cfg, guardar_eventos=False)
        a = c["agente"]
        for t in c["prueba"][:1000]:
            a.evaluar(t["id"])
            a.registrar_resultado_observado(t["id"])
        falsas += int(a.revisar_aprendizaje()["deriva"])
    return filas, falsas


def _m2b(media_ms):
    """M2b: reduccion del tiempo frente al proceso manual. Devuelve (casos, resultado, cumple).
    Si config/linea_base_manual.json no tiene el promedio manual, la medida queda PENDIENTE (cumple=None)."""
    try:
        d = json.loads((RAIZ / "config" / "linea_base_manual.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    t_man, n = d.get("tiempo_manual_promedio_s"), d.get("n_solicitudes_medidas")
    if not t_man or not n or t_man <= 0:
        return 0, "PENDIENTE: falta línea base manual (config/linea_base_manual.json)", None
    t_ag = media_ms / 1000.0
    red = (t_man - t_ag) / t_man
    txt = f"T_manual = {t_man:.1f} s; T_agente = {media_ms:.3f} ms; reducción = {red*100:.2f} %".replace(".", ",")
    return int(n), txt, red >= 0.20


def ejecutar(dir_logs=None):
    dir_logs = Path(dir_logs or RAIZ / "logs")
    dir_logs.mkdir(parents=True, exist_ok=True)
    cfg, U = cargar_config(), cargar_umbrales()
    log = dir_logs / "pruebas_eventos.jsonl"
    if log.exists():
        log.unlink()
    meta = {"fecha": __import__("datetime").datetime.now().isoformat(timespec="seconds"), "python": sys.version.split()[0],
            "numpy": np.__version__, "plataforma": platform.platform(),
            "sha256_umbrales": hashlib.sha256((RAIZ / "config" / "umbrales.json").read_bytes()).hexdigest(),
            "sha256_config": hashlib.sha256((RAIZ / "config" / "config.json").read_bytes()).hexdigest()}

    f124, lat = _m1_m2_m4(U, cfg, log)
    m3 = _m3(U, cfg, log)
    n_faltas = _faltas(U, cfg, log)
    m5 = _m5(log)
    m6b = _m6b(U, cfg)
    f7, falsas = _m7(U, cfg)

    aucs = np.array([f["auc"] for f in f124]); eces = np.array([f["ece"] for f in f124])
    p95, media = float(np.percentile(lat, 95)), float(lat.mean())
    det = float(np.mean([f["deriva_detectada"] for f in f7]))
    mej = float(np.mean([f["brier_despues"] < f["brier_antes"] for f in f7]))
    n_semillas = len(U["semillas"])
    ev = "logs/resultados_pruebas.json"; lg = "logs/pruebas_eventos.jsonl"
    fmt = lambda x, d=4: f"{x:.{d}f}".replace(".", ",")
    filas = [
        ("M1. Discriminación: AUC-ROC (Mann-Whitney) sobre solicitudes de prueba sintéticas", "AUC = P(score_default > score_no_default); promedio de 5 semillas",
         f">= {fmt(U['M1_auc_roc_min'], 2)}", int(sum(f["n_validas"] for f in f124)), f"{fmt(aucs.mean())} ± {fmt(aucs.std(ddof=1))} (min {fmt(aucs.min())})",
         aucs.mean() >= U["M1_auc_roc_min"], f"{ev}#M1; {lg}"),
        ("M2. Tiempo de respuesta por evaluación (extremo a extremo, entorno simulado)", "p95 de latencia_ms de EVALUACION_COMPLETA",
         f"<= {fmt(U['M2_latencia_p95_max_ms'], 0)} ms", len(lat), f"p95 = {fmt(p95, 3)} ms; media = {fmt(media, 3)} ms",
         p95 <= U["M2_latencia_p95_max_ms"], f"{ev}#M2; {lg}"),
        ("M2b. Reducción del 20 % del tiempo frente al proceso manual", "(T_manual - T_agente) / T_manual", ">= 20 %", *_m2b(media),
         "config/linea_base_manual.json; logs/linea_base_manual_tiempos.csv"),
        ("M3. Remisión correcta ante entradas inválidas, incompletas o fuera de dominio", "casos con REVISION_HUMANA, sin p_default y sin llamada a originación / casos invalidos",
         f">= {U['M3_remision_entradas_invalidas_min']*100:.0f} %", m3["total"], f"{m3['correctos']}/{m3['total']} = {m3['tasa']*100:.1f} %".replace(".", ","),
         m3["tasa"] >= U["M3_remision_entradas_invalidas_min"], f"{ev}#M3; {lg}"),
        ("M4. Calibración de probabilidades: ECE (10 bins)", "ECE = Σ_b (n_b/n)·|frec_obs_b − prob_media_b|; promedio de 5 semillas",
         f"<= {fmt(U['M4_ece_max'], 2)}", int(sum(f["n_validas"] for f in f124)), f"{fmt(eces.mean())} ± {fmt(eces.std(ddof=1))} (max {fmt(eces.max())})",
         eces.mean() <= U["M4_ece_max"], f"{ev}#M4; {lg}"),
        ("M5. Trazabilidad: evaluaciones con cadena completa de eventos y auditoría (releida del log)", "evaluaciones completas / evaluaciones totales",
         f">= {U['M5_trazabilidad_min']*100:.0f} %", m5["evaluaciones"], f"{m5['completas']}/{m5['evaluaciones']} = {m5['tasa']*100:.1f} %".replace(".", ","),
         m5["tasa"] >= U["M5_trazabilidad_min"], f"{ev}#M5; {lg}"),
        ("M6a. Estabilidad entre ejecuciones: desviación estándar del AUC", "s = desv. estándar muestral de AUC en 5 semillas",
         f"<= {fmt(U['M6a_desv_auc_max'], 2)}", n_semillas, f"s = {fmt(aucs.std(ddof=1))}", aucs.std(ddof=1) <= U["M6a_desv_auc_max"], f"{ev}#M1"),
        ("M6b. Reproducibilidad: la misma semilla produce las mismas decisiones", "salidas idénticas (acción, p, calificación) / comparaciones",
         f">= {U['M6b_reproducibilidad_min']*100:.0f} %", m6b["total"], f"{m6b['identicas']}/{m6b['total']} = {m6b['tasa']*100:.1f} %".replace(".", ","),
         m6b["tasa"] >= U["M6b_reproducibilidad_min"], f"{ev}#M6b"),
        ("M7a. Detección de deriva (cambio de distribución económica)", "semillas con deriva detectada / semillas",
         f">= {U['M7a_deteccion_deriva_min']*100:.0f} %", n_semillas, f"{sum(f['deriva_detectada'] for f in f7)}/{n_semillas} = {det*100:.0f} %",
         det >= U["M7a_deteccion_deriva_min"], f"{ev}#M7"),
        ("M7b. Mejora tras recalibración: Brier en solicitudes con deriva", "semillas con Brier_después < Brier_antes / semillas",
         f">= {U['M7b_mejora_brier_min']*100:.0f} %", n_semillas, f"{int(round(mej*n_semillas))}/{n_semillas} = {mej*100:.0f} %",
         mej >= U["M7b_mejora_brier_min"], f"{ev}#M7"),
    ]
    detalle = {"meta": meta, "umbrales": U, "M1_M2_M4_por_semilla": f124,
               "M2": {"n": len(lat), "p95_ms": p95, "media_ms": media, "max_ms": float(lat.max())},
               "M3": m3, "M5": {**m5, "evaluaciones_con_fallos_aleatorios": n_faltas}, "M6b": m6b, "M7": f7,
               "M7_falsas_alarmas_sin_deriva": f"{falsas}/{n_semillas}"}
    with open(dir_logs / "resultados_pruebas.json", "w", encoding="utf-8") as f:
        json.dump(detalle, f, indent=2, ensure_ascii=False, default=float)
    cab = ["Medida de desempeño", "Fórmula", "Umbral", "Casos ejecutados", "Resultado obtenido", "¿Cumple?", "Evidencia (log, captura, minuto del video)"]
    import csv
    with open(dir_logs / "resultados_pruebas.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cab)
        for r in filas:
            w.writerow([r[0], r[1], r[2], r[3], r[4], "PENDIENTE" if r[5] is None else ("Sí" if r[5] else "No"), r[6]])
    with open(dir_logs / "tabla_resultados.md", "w", encoding="utf-8") as f:
        f.write("| " + " | ".join(cab) + " |\n|" + "---|" * len(cab) + "\n")
        for r in filas:
            f.write(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {'PENDIENTE' if r[5] is None else ('Sí' if r[5] else 'No')} | {r[6]} |\n")
    return filas, detalle
