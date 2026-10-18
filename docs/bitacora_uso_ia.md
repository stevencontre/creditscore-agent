# Bitácora de uso de inteligencia artificial

**Herramienta:** Claude (modelo Claude Sonnet 5.5, de Anthropic) en la interfaz de chat con ejecución de código.
**Fecha de la sesión registrada:** 17/10/2026 (fecha de la conversación; las horas exactas no se registraron).
**Alcance de esta bitácora:** solo la sesión de esta entrega. El uso de IA en la entrega anterior (el documento «Diseño inicial» contenía marcas de herramientas de citación) **no tiene registro disponible**; los integrantes deben completarlo si corresponde.

Los campos marcados **[PENDIENTE]** solo pueden completarlos los integrantes.

| N.º | Objetivo de la consulta | Apartados del proyecto | Tipo de ayuda | Código o documentación generados o corregidos | Cambios aceptados / rechazados | Verificación realizada por los integrantes | Errores o limitaciones identificados |
|---|---|---|---|---|---|---|---|
| 1 | Inventariar el ZIP de la entrega anterior y verificar si contenía diseños de agentes | Fase 1 (diagnóstico) | Análisis de archivos | Diagnóstico: el ZIP contenía solo un taller de n-gramas (PDF manuscrito, `.py`, notebook, log); no incluía diseños de agentes | [PENDIENTE] | [PENDIENTE] | El PDF era un escaneo manuscrito leído visualmente; falta el corpus `data/matilda/` |
| 2 | Leer el diseño de CREDITSCORE-AGENT y la retroalimentación del docente | Fase 4, tabla de cambios | Análisis y resumen | Lista de correcciones: artefactos de citación, encabezados desordenados, un solo integrante, referencia duplicada | [PENDIENTE] | [PENDIENTE] | No se recibió el diseño de Cartrescue-agent |
| 3 | Seleccionar el agente (matriz ponderada y sensibilidad) | Sección A del informe | Cálculo y redacción | `docs/matriz_decision.json`, `scripts/matriz_decision.py`, resultados | [PENDIENTE] | [PENDIENTE] | Puntajes del agente B son **estimaciones** de la IA sin su diseño; la decisión cambiaría si B sube 1 punto en lo estimado |
| 4 | Implementar el agente | Fase 3; `src/creditscore/*`, `config/*` | Generación de código | Módulos de percepción, decisión, acciones, memoria, modelo, agente, entorno, simulador, registro | [PENDIENTE] | [PENDIENTE: leer y ejecutar el código, poder explicarlo] | Datos sintéticos; sin integración real; `pytest` no disponible sin red, se usó `unittest` |
| 5 | Definir y ejecutar pruebas de desempeño | Fase 5; `config/umbrales.json`, `evaluacion.py`, `escenarios.py`, `tests/` | Generación de pruebas y ejecución | Umbrales fijados antes de ejecutar; 20 pruebas unitarias; 17 escenarios; medidas M1–M7; logs en `logs/` | [PENDIENTE] | [PENDIENTE: repetir `run_pruebas_desempeno.py` en su equipo] | Un reemplazo de texto automático dañó dos claves del código; se detectó por error de ejecución y se corrigió antes de la ejecución oficial final |
| 6 | Crear diagramas | Sección 9.1 y 9.5 | Generación de diagramas | `arquitectura.dot`, tres `.mmd`, `render_secuencia.py` | [PENDIENTE] | [PENDIENTE: comparar los diagramas con el código] | `mermaid-cli` no pudo ejecutarse (sin navegador); se escribió un renderizador propio; la letra se hizo pequeña y se pasaron los diagramas a páginas horizontales |
| 7 | Redactar el documento ajustado | Fase 7; `docs/construir_informe.py` | Redacción y maquetación | `Documento_Diseno_Ajustado.docx` y `.pdf` | [PENDIENTE] | [PENDIENTE: leer el documento completo y corregirlo] | Se normalizaron y luego se restauraron los enlaces de referencia; no se pudieron verificar (sin acceso a Internet): IBM, arXiv:2603.18927 |
| 8 | Guion de video, README y lista de verificación | Fases 6, 8, 11 | Redacción | `guion_video.md`, `README.md`, `lista_verificacion_rubrica.md` | [PENDIENTE] | [PENDIENTE] | El video no se grabó; los minutos del guion son previstos |
| 9 | Cambiar la evidencia de video a plataforma de despliegue (Opción A) | Fase 3, sección 9.2, 9.6, 9.9; `app.py`, `docs/guia_despliegue.md` | Generación de código y redacción | Interfaz Streamlit que llama a `AgenteCreditScore.evaluar()` sin cambiar su lógica; guía de despliegue y casos de prueba; ajuste de `construir_informe.py` y regeneración del informe | [PENDIENTE] | [PENDIENTE: ejecutar `streamlit run app.py`, probar los casos y verificar la URL pública tras desplegar] | Probada solo en local y con pruebas automáticas de Streamlit; el despliegue real en Streamlit Community Cloud no se pudo ejecutar desde el entorno de la IA |

## Declaración
El código y los textos fueron generados con asistencia de IA. Las cifras de resultados provienen de ejecuciones reales del código incluido (carpeta `logs/`). **Los integrantes son responsables de revisar, comprender y poder explicar** todo el contenido antes de entregarlo.

Integrantes: Steven David Contreras (T00077010) · Andres Camilo Castaño (T00077278) — firma/fecha de revisión: **[PENDIENTE]**
