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

st.set_page_config(page_title="CREDITSCORE-AGENT", page_icon="💳", layout="wide")

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
    st.session_state.update(c=c, ruta=ruta, n=0, historial=[], ultimo=None, semilla_activa=semilla)


def cargar(nombre):
    for k, x in zip(CLAVES, PRESETS[nombre]):
        st.session_state[k] = x


def evaluar_manual():
    c = st.session_state.c
    ent, ag, reg = c["entorno"], c["agente"], c["registro"]
    st.session_state.n += 1
    id_ = f"WEB-{st.session_state.n:04d}"
    sol = {"id": id_, "formulario": {}, "buro": {}}
    for clave, _, grupo, campo, _ in CAMPOS:
        v = valor(st.session_state[clave])
        if v is not None:
            sol[grupo][campo] = v
    ent.registrar_solicitud(sol)
    ent.buro_caido = bool(st.session_state.t_buro)
    ent.originacion_caida = bool(st.session_state.t_orig)
    n0 = len(reg.eventos)
    res = ag.evaluar(id_)
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
        st.session_state.setdefault(k, x)
    iniciar(cargar_config()["simulador"]["semilla_base"])

c = st.session_state.c

# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    st.header("Agente")
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

st.title("💳 CREDITSCORE-AGENT")
st.markdown("Agente de **aprendizaje con decisión basada en utilidad**: estima la probabilidad de incumplimiento de una "
            "solicitud de crédito y recomienda **aprobar, rechazar o remitir a revisión humana**. "
            "El entorno (formulario, buró, originación y cartera) es un **simulador**.")

tab1, tab2, tab3, tab4 = st.tabs(["1. Evaluar una solicitud", "2. Lote simulado", "3. Pruebas", "4. Acerca del agente"])

# ------------------------------------------------------------------ pestaña 1
with tab1:
    st.subheader("Casos de prueba sugeridos")
    st.caption("Pulsa un caso para cargar sus datos y luego «Evaluar solicitud».")
    cols = st.columns(3)
    for i, nombre in enumerate(PRESETS):
        cols[i % 3].button(nombre, key=f"p{i}", on_click=cargar, args=(nombre,), width="stretch")

    st.subheader("Solicitud")
    izq, der = st.columns([3, 2])
    with izq:
        for clave, etiqueta, _, _, ayuda in CAMPOS:
            st.text_input(etiqueta, key=clave, help=ayuda + ". Vacío = dato faltante; sin puntos ni comas.")
    with der:
        st.markdown("**Estado del entorno (para probar fallas)**")
        st.checkbox("Buró de crédito caído (sensor sin dato)", key="t_buro")
        st.checkbox("Sistema de originación caído (actuador falla)", key="t_orig")
        st.button("Evaluar solicitud", type="primary", on_click=evaluar_manual, width="stretch")

    u = st.session_state.ultimo
    if u:
        r = u["res"]
        st.divider()
        st.subheader(f"Resultado de {r['id']}")
        getattr(st, COLORES[r["accion"]])(f"**{r['accion']}** — {r['razon']}")
        m = st.columns(4)
        m[0].metric("p(incumplimiento)", "n/d" if r["p_default"] is None else f"{r['p_default']:.3f}")
        m[1].metric("Calificación", r["calificacion"])
        m[2].metric("Percepción", r["estado_percepcion"])
        m[3].metric("Latencia", f"{r['latencia_ms']:.2f} ms")
        a, b = st.columns(2)
        a.markdown("**Acciones ejecutadas en el entorno**")
        a.json(r["estado_acciones"])
        b.markdown("**Reglas activadas**")
        b.write(", ".join(r["reglas"]) if r["reglas"] else "ninguna")
        dec = next((e for e in u["eventos"] if e["evento"] == "DECISION"), None)
        if dec and dec.get("costos"):
            with st.expander("Cómo decidió (costo esperado de cada acción)"):
                st.json({"costos": dec["costos"], "p_vecinos (memoria)": dec.get("p_vecinos"),
                         "desacuerdo": dec.get("desacuerdo")})
        with st.expander("Registro de eventos con marca de tiempo (Percepción → Decisión → Acción)", expanded=True):
            st.dataframe(tabla_eventos(u["eventos"]), width="stretch", hide_index=True)
    if st.session_state.historial:
        st.divider()
        st.subheader("Historial de esta sesión")
        st.dataframe(pd.DataFrame(st.session_state.historial), width="stretch", hide_index=True)

# ------------------------------------------------------------------ pestaña 2
with tab2:
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
        if extra is not None:
            st.markdown("**Revisión de aprendizaje tras la deriva económica simulada (1.000 casos con resultado observado):**")
            st.json(extra)
        if filas:
            df = pd.DataFrame(filas)
            st.dataframe(df, width="stretch", hide_index=True)
            st.write("Resumen de acciones:", df["acción"].value_counts().to_dict())
        st.write(f"Bandeja de analistas: **{len(en.bandeja)}** · Originación: **{len(en.originacion)}** · "
                 f"Pendientes (outbox): **{len(ag.actuadores.pendientes)}**")
        if ruta and Path(ruta).exists():
            cl["registro"].cerrar()
            st.download_button("Descargar log del lote (JSONL)", Path(ruta).read_bytes(), file_name=Path(ruta).name)

# ------------------------------------------------------------------ pestaña 3
with tab3:
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
with tab4:
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
