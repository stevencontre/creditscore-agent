# Bitácora de uso de inteligencia artificial

**Herramienta:** Claude (modelo Claude Sonnet 5.5, de Anthropic) en la interfaz de chat con ejecución de código.  
**Fecha de la sesión registrada:** 17/10/2026 (fecha de la conversación; las horas exactas no se registraron).  
**Alcance de esta bitácora:** solo la sesión de esta entrega. El uso de IA en la entrega anterior (el documento «Diseño inicial» contenía marcas de herramientas de citación) **no tiene registro disponible**; los integrantes deben completarlo si corresponde.

Las casillas ☐ de los campos «Cambios aceptados / rechazados» y «Verificación» las completan los integrantes: marquen (☑) solo lo que realmente hicieron y borren el resto.

## Consulta 1

- **Objetivo de la consulta:** Inventariar el ZIP de la entrega anterior y verificar si contenía diseños de agentes
- **Apartados del proyecto:** Fase 1 (diagnóstico)
- **Tipo de ayuda:** Análisis de archivos
- **Código o documentación generados o corregidos:** Diagnóstico: el ZIP contenía solo un taller de n-gramas (PDF manuscrito, `.py`, notebook, log); no incluía diseños de agentes
- **Cambios aceptados / rechazados:** ☑ Aceptado tal como se generó ☐ Modificado: ______ ☐ Rechazado: ______
- **Verificación realizada por los integrantes:** ☑ Abrieron el ZIP anterior y confirmaron que solo traía el taller de n-gramas
- **Errores o limitaciones identificados:** El PDF era un escaneo manuscrito leído visualmente; falta el corpus `data/matilda/`

## Consulta 2

- **Objetivo de la consulta:** Leer el diseño de CREDITSCORE-AGENT y la retroalimentación del docente
- **Apartados del proyecto:** Fase 4, tabla de cambios
- **Tipo de ayuda:** Análisis y resumen
- **Código o documentación generados o corregidos:** Lista de correcciones: artefactos de citación, encabezados desordenados, un solo integrante, referencia duplicada
- **Cambios aceptados / rechazados:** ☑ Aceptado tal como se generó ☐ Modificado: ______ ☐ Rechazado
- **Verificación realizada por los integrantes:** ☑ Compararon la lista de correcciones con la retroalimentación original del docente ☐ Faltó alguna: ______
- **Errores o limitaciones identificados:** No se recibió el diseño de Cartrescue-agent

## Consulta 3

- **Objetivo de la consulta:** Seleccionar el agente (matriz ponderada y sensibilidad)
- **Apartados del proyecto:** Sección A del informe
- **Tipo de ayuda:** Cálculo y redacción
- **Código o documentación generados o corregidos:** `docs/matriz_decision.json`, `scripts/matriz_decision.py`, resultados
- **Cambios aceptados / rechazados:** ☑ Aceptado tal como se generó ☐ Modificado: ______ ☐ Rechazado: ______
- **Verificación realizada por los integrantes:** ☑ Revisaron los puntajes y la evidencia de cada criterio ☑ Contrastaron los puntajes de Cartrescue con la descripción del caso (Use Cases, p. 3)
- **Errores o limitaciones identificados:** Los puntajes del agente B se basan en la descripción del caso (Use Cases, p. 3) y no en su diseño completo; la decisión depende de ellos.

## Consulta 4

- **Objetivo de la consulta:** Implementar el agente
- **Apartados del proyecto:** Fase 3; `src/creditscore/*`, `config/*`
- **Tipo de ayuda:** Generación de código
- **Código o documentación generados o corregidos:** Módulos de percepción, decisión, acciones, memoria, modelo, agente, entorno, simulador, registro
- **Cambios aceptados / rechazados:** ☑ Aceptado tal como se generó ☐ Modificado: ______ ☐ Rechazado: ______
- **Verificación realizada por los integrantes:** ☑ Ejecutaron `python -m unittest discover -s tests -t . -v` ☑ Leyeron `agente.py` (percibir → decidir → actuar) ☐ Pueden explicar el modelo y las reglas R1 a R4
- **Errores o limitaciones identificados:** Datos sintéticos; sin integración real; `pytest` no disponible sin red, se usó `unittest`

## Consulta 5

- **Objetivo de la consulta:** Definir y ejecutar pruebas de desempeño
- **Apartados del proyecto:** Fase 5; `config/umbrales.json`, `evaluacion.py`, `escenarios.py`, `tests/`
- **Tipo de ayuda:** Generación de pruebas y ejecución
- **Código o documentación generados o corregidos:** Umbrales fijados antes de ejecutar; 20 pruebas unitarias; 17 escenarios; medidas M1–M7; logs en `logs/`
- **Cambios aceptados / rechazados:** ☑ Aceptado tal como se generó ☐ Modificado: ______ ☐ Rechazado: ______
- **Verificación realizada por los integrantes:** ☑ Repitieron `python scripts/run_pruebas_desempeno.py` y obtuvieron los mismos valores ☑ Ejecutaron `python scripts/run_escenarios.py` (17/17) ☑ Ejecutaron las pruebas desde la pestaña «3. Pruebas» de la app
- **Errores o limitaciones identificados:** Un reemplazo de texto automático dañó dos claves del código; se detectó por error de ejecución y se corrigió antes de la ejecución oficial final

## Consulta 6

- **Objetivo de la consulta:** Crear diagramas
- **Apartados del proyecto:** Sección 9.1 y 9.5
- **Tipo de ayuda:** Generación de diagramas
- **Código o documentación generados o corregidos:** `arquitectura.dot`, tres `.mmd`, `render_secuencia.py`
- **Cambios aceptados / rechazados:** ☑ Aceptado tal como se generó ☐ Modificado: ______ ☐ Rechazado: ______
- **Verificación realizada por los integrantes:** ☑ Compararon los diagramas de secuencia con el código
- **Errores o limitaciones identificados:** `mermaid-cli` no pudo ejecutarse (sin navegador); se escribió un renderizador propio; la letra se hizo pequeña y se pasaron los diagramas a páginas horizontales

## Consulta 7

- **Objetivo de la consulta:** Redactar el documento ajustado
- **Apartados del proyecto:** Fase 7; `docs/construir_informe.py`
- **Tipo de ayuda:** Redacción y maquetación
- **Código o documentación generados o corregidos:** `Documento_Diseno_Ajustado.docx` y `.pdf`
- **Cambios aceptados / rechazados:** ☐ Aceptado tal como se generó ☑ Modificado: ______ ☐ Rechazado: ______
- **Verificación realizada por los integrantes:** ☑ Leyeron el documento completo ☐ Corrigieron: ______ ☐ Verificaron los enlaces de IBM y arXiv
- **Errores o limitaciones identificados:** Se normalizaron y luego se restauraron los enlaces de referencia; no se pudieron verificar (sin acceso a Internet): IBM, arXiv:2603.18927

## Consulta 8

- **Objetivo de la consulta:** Guion de video, README y lista de verificación
- **Apartados del proyecto:** Fases 6, 8, 11
- **Tipo de ayuda:** Redacción
- **Código o documentación generados o corregidos:** `guion_video.md`, `README.md`, `lista_verificacion_rubrica.md`
- **Cambios aceptados / rechazados:** Se actualizaron README y lista de verificación para la Opción A; el guion de video no se usó (se eligió la Opción A)
- **Verificación realizada por los integrantes:** No aplica: no se grabó video
- **Errores o limitaciones identificados:** El video no se grabó; los minutos del guion son previstos

## Consulta 9

- **Objetivo de la consulta:** Cambiar la evidencia de video a plataforma de despliegue (Opción A)
- **Apartados del proyecto:** Fase 3, sección 9.2, 9.6, 9.9; `app.py`, `docs/guia_despliegue.md`
- **Tipo de ayuda:** Generación de código y redacción
- **Código o documentación generados o corregidos:** Interfaz Streamlit que llama a `AgenteCreditScore.evaluar()` sin cambiar su lógica; guía de despliegue y casos de prueba; ajuste de `construir_informe.py` y regeneración del informe
- **Cambios aceptados / rechazados:** `app.py`, `docs/guia_despliegue.md` y los cambios al informe se incorporaron al repositorio (commit 7863c77). ☑ Sin modificaciones ☐ Modificaron: ______
- **Verificación realizada por los integrantes:** Ejecutaron `streamlit run app.py` en local y probaron «Típico: bajo riesgo» (APROBAR) e «ingreso faltante» (REVISION_HUMANA), con capturas; desplegaron la app en Streamlit Community Cloud. ☑ Probaron la URL pública en ventana de incógnito el día de la entrega
- **Errores o limitaciones identificados:** Probada solo en local y con pruebas automáticas de Streamlit; el despliegue real en Streamlit Community Cloud se pudo ejecutar

## Consulta 10

- **Objetivo de la consulta:** Guiar la extracción de archivos, la prueba local, Git y el despliegue en Streamlit Community Cloud
- **Apartados del proyecto:** Fase 3; repositorio y enlaces (9.9)
- **Tipo de ayuda:** Explicación paso a paso y revisión de capturas de pantalla
- **Código o documentación generados o corregidos:** Actualización de la URL de la app en el informe, README, guía y lista de verificación; indicaciones para quitar archivos zip y `docs/.Rhistory` del repositorio
- **Cambios aceptados / rechazados:** Aceptado: los integrantes siguieron los pasos y subieron los cambios (commits 62a3f0d y bf1babf)
- **Verificación realizada por los integrantes:** Comprobaron en pantalla el resultado de cada comando (commit y push sin errores) y que el repositorio abre sin iniciar sesión. ☑ Probar la app pública en incógnito antes de entregar
- **Errores o limitaciones identificados:** La IA no pudo abrir la URL pública (el sitio bloquea accesos automáticos), así que la verificación pública depende de los integrantes; un zip de actualización se subió por error al repositorio y se retiró en un commit posterior

## Declaración

El código, los diagramas, las pruebas y los textos de esta entrega fueron generados por una herramienta de IA (Claude) a partir de las indicaciones de los integrantes. Los integrantes los ejecutaron, los revisaron y los subieron al repositorio. Las cifras de resultados provienen de ejecuciones reales del código incluido (carpeta `logs/`). **Los integrantes son responsables de revisar, comprender y poder explicar** todo el contenido antes de entregarlo.

## Contribución de los integrantes

Marquen (☑) solo lo que realmente hicieron y escriban el detalle. Borren las líneas que no apliquen. No marquen nada que no puedan mostrar o explicar.

- ☐ Escribieron o modificaron código por su cuenta. Archivos y qué cambiaron: ______
- ☐ Cambiaron parámetros o reglas (por ejemplo costos, umbrales o puntajes de la matriz). Cuáles y por qué: ______
- ☐ Corrigieron errores del código o del informe. Cuáles: ______
- ☐ Escribieron o reescribieron partes del informe con sus propias palabras. Secciones: ______
- ☐ Ejecutaron el agente y las pruebas en su equipo y compararon los resultados con los logs.
- ☐ Pueden explicar con sus palabras el ciclo Percepción → Decisión → Acción y la matriz de decisión.

Integrantes: Steven David Contreras (T00077010) · Andres Camilo Castaño (T00077278) — firma/fecha de revisión: 17/10/2026
