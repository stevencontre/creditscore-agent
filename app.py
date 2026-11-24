"""CREDITSCORE-AGENT: interfaz web (Streamlit) para la Opcion A (plataforma de despliegue).

Esta interfaz NO contiene logica de decision: solo arma solicitudes, llama a AgenteCreditScore.evaluar()
(ciclo Percepcion -> Decision -> Accion) y muestra lo que el agente hizo y registro.
Ejecutar localmente:  streamlit run app.py
"""
import datetime as dt
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ))

from creditscore.config import cargar_config  # noqa: E402
from creditscore.escenarios import correr_escenarios  # noqa: E402
from creditscore.evaluacion import CORRUPCIONES, _corromper, ejecutar  # noqa: E402
from creditscore.fabrica import construir  # noqa: E402
from creditscore.simulador import generar_solicitudes  # noqa: E402

st.set_page_config(page_title="Kredia · UTB", page_icon="💳", layout="wide")
st.markdown("""<style>
.stApp {background:#0B0D12;color:#f4f0fa;}
.block-container {max-width:1350px;padding-top:2rem;}
[data-testid="stSidebar"] {background:#11051F;border-right:1px solid #ffffff15;}
[data-testid="stMetric"],[data-testid="stForm"],[data-testid="stExpander"] {background:#161922;border:1px solid #ffffff14;border-radius:16px;padding:16px;}
[data-testid="stMetricValue"] {color:#e3b4ff;font-weight:750;}
.stButton button,.stDownloadButton button {border-radius:14px;min-height:44px;}
button[kind="primary"] {background:#820AD1;color:white;}
#MainMenu,footer {visibility:hidden;}
[data-testid="stHeader"] {background:transparent;}
.cs-hero {background:linear-gradient(120deg,#250c43,#51106d,#25112f);padding:30px;border-radius:24px;border:1px solid #ffffff18;}
.cs-hero h1 {color:white;font-size:3rem;margin:4px 0;}
.cs-kicker {color:#e4b7ff;font-size:.75rem;letter-spacing:.13em;}
.cs-flow {display:flex;flex-wrap:wrap;gap:10px;}
.cs-flow span {flex:1;min-width:120px;background:#161922;border:1px solid #ffffff14;border-radius:16px;padding:16px;}
.cs-flow b {display:block;color:#e3b4ff;}
</style>""",unsafe_allow_html=True)

CAMPOS = [  # (clave del widget, etiqueta, grupo, campo del agente, ayuda)
    ("f_ing", "Ingresos mensuales (COP)", "formulario", "ingresos_mensuales", "Formulario. Rango válido: 500.000 a 50.000.000"),
    ("f_obl", "Obligaciones mensuales (COP)", "formulario", "obligaciones_mensuales", "Formulario. Rango válido: 0 a 100.000.000"),
    ("f_atr", "Pagos atrasados en 24 meses", "buro", "pagos_atrasados_24m", "Buró. Entero de 0 a 24"),
    ("f_ant", "Antigüedad del historial (meses)", "buro", "antiguedad_historial_meses", "Buró. Entero de 0 a 600"),
    ("f_lin", "Líneas de crédito abiertas", "buro", "lineas_credito_abiertas", "Buró. Entero de 0 a 30"),
]
CLAVES = [c[0] for c in CAMPOS] + ["t_buro", "t_orig"]
BASE = ("8000000", "800000", "0", "120", "3")
PRESETS = {  # nombre: (ingresos, obligaciones, atrasados, antiguedad, lineas, buro_caido, originacion_caida)
    "Típico: bajo riesgo (aprobar)": (*BASE, False, False),
    "Típico: alto riesgo (rechazar)": ("1500000", "800000", "6", "12", "8", False, False),
    "Típico: riesgo intermedio (revisión)": ("2800000", "900000", "1", "72", "4", False, False),
    "Límite: DTI apenas mayor a 0,80": ("3000000", "2400300", "2", "48", "4", False, False),
    "Falla: ingreso faltante": ("", "800000", "0", "120", "3", False, False),
    "Falla: valor no numérico ('abc')": ("8000000", "abc", "0", "120", "3", False, False),
    "Falla: 25 pagos atrasados (fuera de rango)": ("2000000", "500000", "25", "36", "5", False, False),
    "Falla: buró de crédito caído": (*BASE, True, False),
    "Falla: sistema de originación caído": (*BASE, False, True),
}
COLORES = {"APROBAR": "success", "RECHAZAR": "error", "REVISION_HUMANA": "warning"}


# ------------------------------------------------------------------ utilidades
def ruta_log(prefijo):
    return RAIZ / "logs" / f"{prefijo}_{dt.datetime.now():%Y%m%d_%H%M%S}.jsonl"


def construir_con_log(prefijo, semilla, **kw):
    """Construye el agente con log JSONL con marca de tiempo; si el disco es de solo lectura, solo en memoria."""
    ruta = ruta_log(prefijo)
    try:
        return construir(semilla, ruta_log=ruta, **kw), ruta
    except OSError:
        return construir(semilla, **kw), None


def valor(texto):
    t = (texto or "").strip()
    if t == "":
        return None          # campo vacio -> el agente lo percibe como faltante
    try:
        return float(t)
    except ValueError:
        return t             # texto: el agente lo rechaza como no numerico


def iniciar(semilla):
    ant = st.session_state.get("c")
    if ant:
        ant["registro"].cerrar()
    c, ruta = construir_con_log("web", semilla)
    
    for key in ("lote_resultado", "comparar_escenario", "comparacion", "aprendizaje"):
        st.session_state.pop(key, None)
    st.session_state.update(c=c, ruta=ruta, n=0, historial=[], ultimo=None, semilla_activa=semilla)


def cargar(nombre):
    for k, x in zip(CLAVES, PRESETS[nombre]):
        st.session_state[k] = float(x) if k in CLAVES[:2] else int(x) if k in CLAVES[2:5] else x


def evaluar_manual(observador=None):
    c = st.session_state.c
    ent, ag, reg = c["entorno"], c["agente"], c["registro"]
    st.session_state.n += 1
    id_ = f"WEB-{st.session_state.n:04d}"
    sol = {"id": id_, "formulario": {}, "buro": {}}
    for clave, _, grupo, campo, _ in CAMPOS:
        v = st.session_state[clave]
        if isinstance(v, str):
            v = valor(v)
        if v is not None:
            sol[grupo][campo] = v
    ent.registrar_solicitud(sol)
    ent.buro_caido = bool(st.session_state.t_buro)
    ent.originacion_caida = bool(st.session_state.t_orig)
    n0 = len(reg.eventos)
    reg.observador = observador
    try:
        res = ag.evaluar(id_)
    finally:
        reg.observador = None
    st.session_state.ultimo = {"res": res, "eventos": reg.eventos[n0:], "entrada": sol,
                               "buro_caido": ent.buro_caido, "orig_caida": ent.originacion_caida}
    st.session_state.historial.append({
        "id": id_, "acción": res["accion"], "p_default": res["p_default"], "calificación": res["calificacion"],
        "percepción": res["estado_percepcion"], "acciones": json.dumps(res["estado_acciones"], ensure_ascii=False),
        "latencia_ms": res["latencia_ms"]})


def tabla_eventos(eventos):
    filas = [{"timestamp": e["timestamp"], "evento": e["evento"],
              "detalle": json.dumps({k: v for k, v in e.items() if k not in ("timestamp", "evento", "id_solicitud")},
                                    ensure_ascii=False, default=str)} for e in eventos]
    return pd.DataFrame(filas)


# ------------------------------------------------------------------ estado inicial
if "c" not in st.session_state:
    for k, x in zip(CLAVES, PRESETS["Típico: bajo riesgo (aprobar)"]):
        st.session_state.setdefault(k, float(x) if k in CLAVES[:2] else int(x) if k in CLAVES[2:5] else x)
    iniciar(cargar_config()["simulador"]["semilla_base"])

c = st.session_state.c

# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    st.header("Kredia")
    semilla = st.number_input("Semilla del simulador", value=int(st.session_state.semilla_activa), step=1)
    if st.button("Reiniciar agente (desde cero)"):
        iniciar(int(semilla))
        st.rerun()
    st.caption(f"Modelo: **{c['modelo'].version}** · histórico: **{c['memoria'].n}** casos")
    ent = c["entorno"]
    st.metric("Casos en bandeja del analista", len(ent.bandeja))
    st.metric("Recomendaciones en originación", len(ent.originacion))
    st.metric("Pendientes (outbox)", len(c["agente"].actuadores.pendientes))
    if st.session_state.ruta and Path(st.session_state.ruta).exists():
        st.download_button("Descargar log de esta sesión (JSONL)", Path(st.session_state.ruta).read_bytes(),
                           file_name=Path(st.session_state.ruta).name, mime="application/json")
    st.caption("Datos 100 % sintéticos: no hay solicitudes reales.")

st.markdown("""<div class="cs-hero"><div class="cs-kicker">LABORATORIO DE INTELIGENCIA ARTIFICIAL · UTB</div><h1>Kredia</h1><div>Banca de Proyectos & Crédito Inteligente · Simulador académico</div></div>""", unsafe_allow_html=True)
st.caption("Prototipo académico · No apto para decisiones crediticias reales")
st.markdown("Agente de **aprendizaje con decisión basada en utilidad**: estima la probabilidad de incumplimiento de una "
            "solicitud de crédito y recomienda **aprobar, rechazar o remitir a revisión humana**. "
            "El entorno (formulario, buró, originación y cartera) es un **simulador**.")

pagina = st.sidebar.radio("Navegación", ["Inicio", "Laboratorio de proyectos", "Nueva evaluación", "Historial", "Comparación de modelos", "Aprendizaje", "Procesamiento por lotes", "Memoria inteligente", "Monitoreo", "Laboratorio", "Arquitectura"])
if pagina == "Inicio":
    st.subheader("Panel de actividad")
    h = pd.DataFrame(st.session_state.historial)
    k = st.columns(4)
    k[0].metric("Evaluaciones", len(h))
    for col, action, label in zip(k[1:], ["APROBAR","RECHAZAR","REVISION_HUMANA"], ["Aprobación simulada","Rechazo simulado","Revisión humana"]):
        col.metric(label, int((h["acción"] == action).sum()) if not h.empty else 0)
    if not h.empty:
        st.bar_chart(h["acción"].value_counts())
        st.line_chart(h.set_index("id")["latencia_ms"])
    else:
        st.info("Realiza una evaluación sintética para visualizar la actividad.")
    st.subheader("Flujo del agente")
    st.markdown("""<div class="cs-flow"><span><b>01</b>Percepción</span><span><b>02</b>Predicción</span><span><b>03</b>Decisión</span><span><b>04</b>Acción y auditoría</span></div>""", unsafe_allow_html=True)
    st.caption("Los indicadores corresponden exclusivamente a esta sesión.")

# ------------------------------------------------------------------ pestaña 1
if pagina == "Nueva evaluación":
    st.subheader("Nueva evaluación sintética")
    opciones = list(PRESETS)[:3]
    a,b = st.columns([3,1])
    elegido = a.selectbox("Perfil de ejemplo", opciones, format_func=lambda x: ["Perfil A", "Perfil B", "Perfil C"][opciones.index(x)])
    b.button("Cargar ejemplo", on_click=cargar, args=(elegido,))
    def limpiar():
        cargar(opciones[0])
        st.session_state.ultimo = None
        st.session_state.pop("comparar_escenario", None)
    st.button("Reiniciar formulario", on_click=limpiar)
    with st.form("solicitud"):
        cols = st.columns(2)
        for i, (clave, etiqueta, _, _, ayuda) in enumerate(CAMPOS):
            minimo,maximo,paso = [(500000.,50000000.,100000.),(0.,100000000.,100000.),(0,24,1),(0,600,1),(0,30,1)][i]
            cols[i%2].number_input(etiqueta, min_value=minimo,max_value=maximo,step=paso,key=clave,help=ayuda)
        enviar = st.form_submit_button("Analizar caso sintético", type="primary", use_container_width=True)
    if enviar:
        st.session_state.t_buro = False
        st.session_state.t_orig = False
        st.session_state.pop("comparar_escenario", None)
        with st.status("Motor de IA · ejecución real", expanded=True) as estado:
            def mostrar(e):
                nombres = {"EVALUACION_INICIO":"Solicitud recibida","PERCEPCION":"Validación y percepción","DECISION":"Predicción, memoria y reglas","ACCION":"Acciones del simulador","AUDITORIA":"Registro de auditoría","EVALUACION_COMPLETA":"Evaluación finalizada"}
                if e["evento"] in nombres:
                    st.write(nombres[e["evento"]], "·", e["timestamp"])
            evaluar_manual(mostrar)
            estado.update(label="Ejecución registrada", state="complete")
    u = st.session_state.ultimo
    if u:
        from creditscore.fabrica import features_de
        import copy
        r = u["res"]
        p = r["p_default"]
        etiquetas = {"APROBAR":"Aprobación simulada","RECHAZAR":"Rechazo simulado","REVISION_HUMANA":"Revisión humana"}
        nombres = {"log_ingresos":"Ingresos","dti":"Relación deuda-ingreso","pagos_atrasados_24m":"Pagos atrasados","log1p_antiguedad":"Antigüedad del historial","lineas_credito":"Líneas abiertas"}
        st.divider()
        st.subheader(f"Resultado · {r['id']}")
        getattr(st, COLORES[r["accion"]])(etiquetas[r["accion"]])
        f = u["entrada"]["formulario"]
        dti = f["obligaciones_mensuales"]/f["ingresos_mensuales"]
        m = st.columns(4)
        m[0].metric("Riesgo estimado", "No disponible" if p is None else f"{p:.1%}")
        m[1].metric("Calificación", r["calificacion"])
        m[2].metric("Deuda / ingreso", f"{dti:.1%}")
        m[3].metric("Latencia", f"{r['latencia_ms']:.2f} ms")
        dec = next((e for e in u["eventos"] if e["evento"] == "DECISION"), {})
        if p is not None:
            st.progress(float(p))
            a,b = st.columns(2)
            with a:
                st.markdown("**¿Qué influyó en el resultado?**")
                factores = c["modelo"].contribuciones(features_de(u["entrada"]), top=5)
                for nombre, valor_ in factores:
                    st.write(f"{nombres.get(nombre,nombre)}: {'aumenta' if valor_>0 else 'reduce' if valor_<0 else 'no cambia'} el riesgo ({valor_:+.2f})")
                st.caption("Contribuciones al logit respecto al perfil medio; no son efectos causales.")
            with b:
                st.markdown("**Consistencia de la predicción**")
                vecinos = dec.get("p_vecinos")
                if vecinos is not None:
                    st.metric("Tasa en casos similares", f"{vecinos:.1%}")
                    st.metric("Diferencia absoluta", f"{abs(p-vecinos):.1%}")
                    st.caption("La diferencia es una señal de desacuerdo, no un intervalo de confianza.")
                else:
                    st.info("No hay comparación histórica disponible.")
            st.markdown("**Comparar dos escenarios sintéticos**")
            st.caption("Experimento de sensibilidad del modelo, sin registrar otra decisión.")
            with st.form("sensibilidad"):
                atrasos = st.number_input("Pagos atrasados del escenario alternativo",0,24,int(u["entrada"]["buro"]["pagos_atrasados_24m"]),key=f"alt_{r['id']}")
                comparar = st.form_submit_button("Comparar predicciones")
            if comparar:
                alt = copy.deepcopy(u["entrada"])
                alt["buro"]["pagos_atrasados_24m"] = atrasos
                st.session_state.comparar_escenario = (p,c["modelo"].predict_proba(features_de(alt)))
            if "comparar_escenario" in st.session_state:
                original,alternativo = st.session_state.comparar_escenario
                x,y = st.columns(2)
                x.metric("Escenario original",f"{original:.1%}")
                y.metric("Escenario alternativo",f"{alternativo:.1%}",f"{100*(alternativo-original):+.1f} pp",delta_color="off")
        else:
            st.info("El agente se abstuvo de estimar el riesgo.")
        reglas = " ".join(r["reglas"])
        motivo = ("Datos no válidos o incompletos." if "R1" in reglas else "Límite de endeudamiento del simulador superado." if "R4" in reglas else "Desacuerdo elevado entre modelo y memoria." if "R3" in reglas else "Acción de menor costo esperado según los parámetros simulados." if "R2" in reglas else "Consulta el detalle técnico.")
        st.write("**Motivo:** "+motivo)
        resumen = f"Evaluación académica sintética {r['id']}\\nResultado: {etiquetas[r['accion']]}\\nRiesgo: {p if p is not None else 'N/D'}\\nMotivo: {motivo}\\nNo apto para decisiones reales."
        st.download_button("Descargar resumen",resumen,"evaluacion_sintetica.txt","text/plain")
        with st.expander("Detalle técnico y auditoría"):
            st.write(r["razon"])
            st.json({"reglas":r["reglas"],"acciones":r["estado_acciones"],"costos":dec.get("costos")})
            st.dataframe(tabla_eventos(u["eventos"]),width="stretch",hide_index=True)
if pagina == "Historial":
    if not st.session_state.historial:
        st.info("Todavía no hay evaluaciones en esta sesión.")
    if st.session_state.historial:
        st.divider()
        st.subheader("Historial de esta sesión")
        hist = pd.DataFrame(st.session_state.historial)
        filtro = st.multiselect("Filtrar por recomendación", ["APROBAR","RECHAZAR","REVISION_HUMANA"], default=["APROBAR","RECHAZAR","REVISION_HUMANA"], key="filtro_hist")
        vista = hist[hist["acción"].isin(filtro)]
        st.dataframe(vista, width="stretch", hide_index=True)
        st.download_button("Descargar historial filtrado (CSV)", vista.to_csv(index=False).encode("utf-8-sig"), "historial.csv", "text/csv")

# ------------------------------------------------------------------ pestaña 2
if pagina == "Procesamiento por lotes":
    st.subheader("Ejecutar un escenario sobre solicitudes simuladas")
    st.caption("Equivale a `python scripts/run_agente.py --n N --escenario X`. Crea un agente nuevo desde cero.")
    e1, e2, e3 = st.columns(3)
    escenario = e1.selectbox("Escenario", ["normal", "invalidas", "fallo_buro", "fallo_originacion", "deriva"])
    n = e2.slider("Solicitudes", 5, 50, 15)
    sem = e3.number_input("Semilla", value=2026, step=1, key="sem_lote")
    if st.button("Ejecutar escenario", type="primary"):
        pf = 0.5 if escenario == "fallo_buro" else None
        po = 0.5 if escenario == "fallo_originacion" else None
        cl, ruta = construir_con_log("web_lote", int(sem), p_fallo_buro=pf, p_fallo_originacion=po)
        ag, en = cl["agente"], cl["entorno"]
        sols, filas, extra = cl["prueba"], [], None
        if escenario == "deriva":
            d = generar_solicitudes(1000, np.random.default_rng(int(sem) + 1), prefijo="DERIVA", deriva=1.0)
            for t in d:
                en.registrar_solicitud(t)
            for t in d:
                ag.evaluar(t["id"])
                ag.registrar_resultado_observado(t["id"])
            extra = ag.revisar_aprendizaje()
            sols = []
        for i, t in enumerate(sols[:n]):
            tipo = ""
            if escenario == "invalidas":
                tipo = CORRUPCIONES[i % len(CORRUPCIONES)]
                _corromper(en, t, tipo)
            r = ag.evaluar(t["id"])
            if escenario == "invalidas":
                en.buro_caido = False
            filas.append({"id": r["id"], "caso": tipo, "acción": r["accion"], "p_default": r["p_default"],
                          "calificación": r["calificacion"], "acciones": json.dumps(r["estado_acciones"], ensure_ascii=False),
                          "latencia_ms": r["latencia_ms"], "razón": r["razon"]})
        cl["registro"].cerrar()
        st.session_state["lote_resultado"] = (filas, extra, len(en.bandeja), len(en.originacion), len(ag.actuadores.pendientes), Path(ruta).read_bytes() if ruta and Path(ruta).exists() else None)
    if "lote_resultado" in st.session_state:
        filas, extra, bandeja, origen, pendientes, log = st.session_state["lote_resultado"]
        if extra is not None:
            st.subheader("Revisión de aprendizaje")
            st.json(extra)
        if filas:
            df = pd.DataFrame(filas)
            st.bar_chart(df["acción"].value_counts())
            st.dataframe(df, width="stretch", hide_index=True)
            st.download_button("Descargar resultados del lote", df.to_csv(index=False).encode("utf-8-sig"), "lote.csv", "text/csv")
        st.write(f"Bandeja: **{bandeja}** · Originación: **{origen}** · Pendientes: **{pendientes}**")
        if log is not None:
            st.download_button("Descargar log del lote", log, "lote.jsonl", "application/json")

# ------------------------------------------------------------------ pestaña 3
if pagina == "Laboratorio":
    st.subheader("Pruebas del agente")
    st.caption("Se ejecutan en vivo con el mismo código del repositorio; nada es un resultado guardado. "
               "Las pruebas de desempeño escriben sus archivos en una carpeta temporal (no sobrescriben `logs/`).")
    p1, p2, p3 = st.columns(3)
    if p1.button("Pruebas unitarias (20)"):
        with st.spinner("Ejecutando..."):
            flujo = io.StringIO()
            suite = unittest.defaultTestLoader.discover(str(RAIZ / "tests"), top_level_dir=str(RAIZ))
            res = unittest.TextTestRunner(stream=flujo, verbosity=2).run(suite)
        (st.success if res.wasSuccessful() else st.error)(
            f"{res.testsRun} pruebas ejecutadas · fallos: {len(res.failures)} · errores: {len(res.errors)}")
        st.code(flujo.getvalue())
    if p2.button("17 escenarios deterministas"):
        with st.spinner("Ejecutando..."):
            filas = correr_escenarios()
        df = pd.DataFrame(filas)
        df["cumple"] = df["cumple"].map({True: "Sí", False: "NO"})
        st.success(f"{(df['cumple'] == 'Sí').sum()}/{len(df)} escenarios cumplen lo esperado")
        st.dataframe(df, width="stretch", hide_index=True)
    if p3.button("Pruebas de desempeño M1–M7 (≈ 10–40 s)"):
        with st.spinner("Ejecutando más de 7.500 evaluaciones con 5 semillas..."):
            with tempfile.TemporaryDirectory() as tmp:
                filas, _ = ejecutar(tmp)
        cab = ["Medida de desempeño", "Fórmula", "Umbral", "Casos ejecutados", "Resultado obtenido", "¿Cumple?", "Evidencia"]
        df = pd.DataFrame([[*f[:5], "PENDIENTE" if f[5] is None else ("Sí" if f[5] else "No"), f[6]] for f in filas],
                          columns=cab)
        st.dataframe(df, width="stretch", hide_index=True)
        if any(f[5] is None for f in filas):
            st.caption("M2b queda PENDIENTE hasta medir la línea base manual (scripts/medir_linea_base_manual.py).")
        st.download_button("Descargar tabla (CSV)", df.to_csv(index=False, sep=";").encode("utf-8-sig"),
                           file_name="tabla_resultados.csv")

# ------------------------------------------------------------------ pestaña 4
if pagina == "Arquitectura":
    st.markdown("""
**Ciclo del agente** (`src/creditscore/agente.py`): `percibir` (formulario + buró, validación) → `decidir`
(utilidad esperada, memoria de casos similares, reglas) → `actuar` (originación, bandeja del analista, expediente, auditoría).

**Reglas principales** (en este orden)
- **R1:** si los datos son inválidos, incompletos o están fuera de dominio, el agente se abstiene y remite a revisión humana.
- **R4:** si el DTI (obligaciones / ingresos) supera 0,80, remite a revisión por política crediticia.
- **R3:** si el modelo y la memoria de casos similares discrepan demasiado (incertidumbre), remite a revisión.
- **R2:** en los demás casos, compara el costo esperado de aprobar, rechazar y remitir, y elige el menor (utilidad).
- **Fallas:** si el buró no responde reintenta 3 veces; si la originación cae, la recomendación queda en el *outbox* (DIFERIDA).

**Aprendizaje:** con resultados observados llegados de cartera, detecta deriva (PSI y brecha de calibración) y recalibra el modelo.

**Datos:** sintéticos (`src/creditscore/simulador.py`). Los resultados demuestran el funcionamiento del agente, no su
desempeño en una entidad financiera real.
""")

if pagina == "Comparación de modelos":
    st.subheader("Experimento independiente de clasificación")
    st.caption("5.000 casos sintéticos: 70 % entrenamiento, 15 % validación, 15 % prueba. Selección por AUC de validación; umbral F1 fijo de 0,5. No cambia el agente operativo.")
    if st.button("Comparar modelos",type="primary"):
        from creditscore.comparacion import comparar
        with st.spinner("Entrenando y evaluando modelos..."):
            st.session_state.comparacion = comparar(int(st.session_state.semilla_activa))
    if "comparacion" in st.session_state:
        filas, errores = st.session_state.comparacion
        df=pd.DataFrame(filas)
        st.dataframe(df,hide_index=True)
        st.bar_chart(df.set_index("Modelo")["AUC prueba"])
        st.caption("AUC y F1: mayor es mejor. Brier: menor es mejor.")
        st.download_button("Descargar métricas",df.to_csv(index=False),"comparacion.csv")
        st.subheader("Errores de clasificación")
        st.dataframe(pd.DataFrame(errores),hide_index=True)
        st.download_button("Descargar errores",pd.DataFrame(errores).to_csv(index=False),"errores.csv")

if pagina == "Aprendizaje":
    st.subheader("Adaptación ante cambios simulados")
    st.caption("Experimento aislado: no altera el modelo de la sesión. Se generan resultados observados sintéticos.")
    if st.button("Simular cambio de distribución",type="primary"):
        cl=construir(int(st.session_state.semilla_activa))
        ag,en=cl["agente"],cl["entorno"]
        d=generar_solicitudes(1000,np.random.default_rng(int(st.session_state.semilla_activa)+1),prefijo="DERIVA",deriva=1.0)
        antes=cl["modelo"].version
        for t in d:
            en.registrar_solicitud(t)
            ag.evaluar(t["id"])
            ag.registrar_resultado_observado(t["id"])
        resultado=ag.revisar_aprendizaje()
        st.session_state.aprendizaje=(antes,cl["modelo"].version,resultado)
        cl["registro"].cerrar()
    if "aprendizaje" in st.session_state:
        antes,despues,resultado=st.session_state.aprendizaje
        x,y=st.columns(2)
        x.metric("Versión inicial",antes)
        y.metric("Versión posterior",despues)
        st.write("Se recalibró el modelo." if antes!=despues else "No se activó la recalibración.")
        st.write(resultado)

if pagina == "Memoria inteligente":
    st.subheader("Memoria histórica sintética")
    mem, mod = c["memoria"], c["modelo"]
    X, y, ids = mem.datos_con_resultado()
    a,b = st.columns(2)
    a.metric("Casos con resultado conocido",len(y))
    b.metric("Incumplimiento observado",f"{y.mean():.1%}" if len(y) else "N/D")
    u = st.session_state.ultimo
    if u and u["res"]["p_default"] is not None:
        from creditscore.fabrica import features_de
        x = features_de(u["entrada"])
        dist = np.linalg.norm((X-x)/mod.sigma,axis=1)
        idx = np.argsort(dist)[:25]
        st.caption("Consulta de los 25 vecinos actuales con resultado conocido, usando distancia estandarizada.")
        st.dataframe(pd.DataFrame({"Caso sintético":[ids[i] for i in idx],"Distancia":dist[idx],"Incumplió":y[idx].astype(int)}),hide_index=True)
    else:
        st.info("Ejecuta una evaluación válida para consultar sus vecinos.")

if pagina == "Monitoreo":
    st.subheader("Eventos reales de la sesión")
    eventos = c["registro"].eventos
    if eventos:
        df = tabla_eventos(eventos)
        st.bar_chart(df["evento"].value_counts())
        filtro = st.multiselect("Tipos de evento",sorted(df["evento"].unique()),default=sorted(df["evento"].unique()))
        vista = df[df["evento"].isin(filtro)]
        st.dataframe(vista,hide_index=True)
        st.download_button("Exportar eventos",vista.to_csv(index=False),"eventos.csv")
    else:
        st.info("Todavía no hay eventos.")

if pagina == "Laboratorio de proyectos":
    import plotly.graph_objects as go
    import numpy_financial as nf
    st.subheader("Laboratorio de proyectos sintéticos")
    st.caption("Escenarios educativos independientes del modelo crediticio. No introduzcas datos personales ni utilices los resultados para contratar créditos.")
    defaults = {"monto":20000000., "ingresos":8000000., "costos":5000000., "plazo":24, "tasa":18., "gracia":0}
    for k,v in defaults.items():
        st.session_state.setdefault("pr_"+k,v)
    st.session_state.setdefault("pr_chat",[])
    def demo():
        for k,v in defaults.items(): st.session_state["pr_"+k]=v
    st.button("Cargar proyecto demo",on_click=demo)
    archivo=st.file_uploader("Importar escenario sintético",type=["csv","xlsx","pdf"])
    if archivo and st.button("Extraer datos"):
        try:
            if archivo.name.lower().endswith(".pdf"):
                from pypdf import PdfReader
                import re
                texto=" ".join(p.extract_text() or "" for p in PdfReader(archivo).pages)
                datos={}
                for k in defaults:
                    m=re.search(r"\\b"+k+r"\\s*[:=]\\s*(\\d+(?:\\.\\d+)?)",texto,re.I)
                    if m: datos[k]=float(m.group(1))
            else:
                df=pd.read_csv(archivo) if archivo.name.lower().endswith(".csv") else pd.read_excel(archivo)
                datos=df.iloc[0].to_dict()
            nuevos={}
            for k,v in defaults.items():
                if k in datos:
                    x=float(datos[k])
                    if not np.isfinite(x) or x<0 or (k in ("monto","plazo") and x<=0): raise ValueError(k)
                    if k=="plazo" and x>120 or k=="gracia" and x>119 or k=="tasa" and x>100: raise ValueError(k)
                    nuevos["pr_"+k]=int(x) if isinstance(v,int) else x
            if not nuevos: raise ValueError("No se encontraron campos compatibles")
            st.session_state.update(nuevos)
            st.success("Campos importados: "+", ".join(nuevos))
        except Exception as e: st.error("No se pudo importar. Usa la plantilla de ejemplo: "+str(e))
    st.download_button("Plantilla CSV",pd.DataFrame([defaults]).to_csv(index=False),"proyecto_demo.csv")
    a,b,c1=st.columns(3)
    a.number_input("Monto sintético (COP)",min_value=1.,key="pr_monto")
    b.number_input("Ingresos mensuales (COP)",min_value=0.,key="pr_ingresos")
    c1.number_input("Costos mensuales (COP)",min_value=0.,key="pr_costos")
    a.number_input("Plazo (meses)",1,120,key="pr_plazo")
    b.number_input("Tasa anual efectiva (%)",0.,100.,key="pr_tasa")
    c1.number_input("Gracia de capital (meses)",0,119,key="pr_gracia")
    with st.sidebar:
        st.subheader("Modo crisis")
        caida=st.slider("Caída de ventas (%)",0,90,0,key="pr_caida")
        retraso=st.slider("Retraso operativo (meses)",0,24,0,key="pr_retraso")
        shock=st.slider("Variación tasa (puntos porcentuales)",-10,30,0,key="pr_shock")
    p={k:st.session_state["pr_"+k] for k in defaults}
    n=p["plazo"]; g=min(p["gracia"],n-1)
    tasa=max(0,p["tasa"]+shock); r=(1+tasa/100)**(1/12)-1
    cuota=float(-nf.pmt(r,n-g,p["monto"]))
    meses=np.arange(1,n+1)
    flujo=np.where(meses>retraso,p["ingresos"]*(1-caida/100),0)-p["costos"]
    pagos=np.where(meses<=g,p["monto"]*r,cuota)
    dscr=float(flujo.sum()/pagos.sum())
    van=float(nf.npv(r, np.r_[-p["monto"],flujo]))
    tir=float(nf.irr(np.r_[-p["monto"],flujo]))
    a,b,c1=st.columns(3)
    a.metric("VAN ilustrativo",f"$ {van:,.0f}")
    b.metric("TIR mensual",f"{tir:.2%}" if np.isfinite(tir) else "N/D")
    c1.metric("DSCR agregado",f"{dscr:.2f}x")
    st.caption("Supuestos: inversión inicial igual al monto, costos constantes, gracia solo de capital, descuento igual a tasa del escenario; sin impuestos ni valor residual.")
    fig=go.Figure([go.Bar(x=meses,y=flujo,name="Flujo operativo",marker_color="#820AD1"),go.Scatter(x=meses,y=pagos,name="Cuota simulada",line=dict(color="#DA0081",width=3))])
    if g: fig.add_vrect(x0=.5,x1=g+.5,fillcolor="#ffffff",opacity=.1,line_width=0)
    fig.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",xaxis_title="Mes",yaxis_title="COP")
    st.plotly_chart(fig,use_container_width=True)
    if st.button("Ejecutar comité académico",type="primary"):
        with st.status("Comité de análisis",expanded=True) as estado:
            st.write(f"Auditor: margen operativo acumulado {flujo.sum():,.0f} COP.")
            st.write(f"Riesgo: caída {caida} %, retraso {retraso} meses; DSCR {dscr:.2f}.")
            st.write(f"Estructurador: VAN {van:,.0f}; cuota {cuota:,.0f} COP.")
            estado.update(label="Análisis registrado",state="complete")
        st.session_state.setdefault("pr_hist",[]).append({**p,"caida":caida,"retraso":retraso,"shock":shock,"VAN":van,"DSCR":dscr})
    st.caption("Los tres roles son etapas de cálculo deterministas, no modelos autónomos independientes.")
    with st.expander("Historial de escenarios"):
        st.dataframe(pd.DataFrame(st.session_state.get("pr_hist",[])),hide_index=True)
    st.subheader("Asistente de escenarios")
    for msg in st.session_state.pr_chat:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    pregunta=st.chat_input("Ejemplo: plazo 36, tasa 15 o gracia 3")
    if pregunta:
        import re
        cambios={}
        for k,lim in [("plazo",120),("tasa",100),("gracia",119)]:
            m=re.search(r"\\b"+k+r"\\s*(?:a|de|=|:)?\\s*(\\d+(?:[.,]\\d+)?)",pregunta.lower())
            if m:
                v=float(m.group(1).replace(",","."))
                if 0<=v<=lim and (k!="plazo" or v>=1): cambios[k]=v if k=="tasa" else int(v)
        respuesta="Escenario solicitado: "+str(cambios) if cambios else "Prueba con plazo 36, tasa 15 o gracia 3. Las garantías no forman parte de este modelo."
        st.session_state.pr_chat.extend([{"role":"user","content":pregunta},{"role":"assistant","content":respuesta}])
        st.session_state["pr_pending"]=cambios
        st.rerun()
    def aplicar():
        for k,v in st.session_state.pop("pr_pending",{}).items(): st.session_state["pr_"+k]=v
    if st.session_state.get("pr_pending"): st.button("Aplicar escenario solicitado",on_click=aplicar)
    informe=f"KREDIA · UTB\\nSIMULACIÓN ACADÉMICA — NO ES UNA OFERTA DE CRÉDITO\\nMonto: {p['monto']:,.0f} COP\\nPlazo: {n} meses\\nTasa simulada: {tasa:.2f}% EA\\nCuota: {cuota:,.0f} COP\\nVAN: {van:,.0f} COP\\nDSCR: {dscr:.2f}"
    st.download_button("Descargar ficha de escenario",informe,"kredia_escenario.txt")
