# Lista de comprobación frente a la rúbrica (100 puntos)

No se calcula una nota: hay elementos que solo los integrantes pueden completar (video, enlaces, línea base).

| # | Criterio (pts) | Estado | Evidencia disponible | Acciones antes de entregar |
|---|---|---|---|---|
| 1 | Matriz de decisión y justificación (15) | **Parcial** | 6 criterios con pesos, evidencia por puntaje, sensibilidad ±10 pp y pesos iguales (`docs/resultados_matriz.*`, sección A del PDF) | Revisar y corregir los puntajes de Cartrescue con su diseño real y volver a ejecutar `scripts/matriz_decision.py`; la decisión es sensible a esos puntajes |
| 2 | Documento ajustado (10) | **Cumplido en lo verificable** | Tabla de cambios al inicio; corrección de artefactos de citación y de encabezados (`docs/Documento_Diseno_Ajustado.pdf`) | Confirmar datos del segundo integrante; verificar que existan los enlaces de las referencias (IBM, arXiv) |
| 3 | Implementación del agente (25) | **Cumplido** | Ciclo P→D→A en `agente.py`; 20 pruebas unitarias y 17 escenarios aprobados; reproducible con README | Ejecutar todo en su equipo; leer el código para poder explicarlo |
| 4 | Tecnologías, entradas y arquitectura (10) | **Cumplido** | Secciones 9.1 a 9.4 del PDF (tablas 3 a 7, diagrama de componentes, correspondencia con los 7 componentes IBM) | Revisar |
| 5 | Diagrama de secuencia (10) | **Cumplido** | 3 diagramas con loop y alt (típico y dos excepciones) y fragmentos de código real (9.5) | Comprobar que coinciden con el código |
| 6 | Pruebas de desempeño (20) | **Parcial** | 10 medidas con fórmula, umbral previo (SHA-256 en el log), 7.500+ casos, 5 semillas, logs, análisis de resultados; todas las ejecutables cumplen | Cerrar M2b con la línea base manual; el AUC se midió con datos sintéticos |
| 7 | Evidencia de funcionamiento (10) | **Pendiente (Opción A elegida)** | `app.py` (Streamlit) probada en local: 9 casos sugeridos, lote, pruebas unitarias, 17 escenarios y M1–M7 en vivo; guía en `docs/guia_despliegue.md` | Desplegar en Streamlit Community Cloud, probar la URL pública y pegarla en README y sección 9.9 |

## Pendientes críticos
1. Desplegar la app y pegar la URL pública en el README y en la sección 9.9.
2. Línea base manual (`config/linea_base_manual.json`).
3. Diseño real de Cartrescue-agent y revisión de la matriz.
4. Bitácora de IA: completar campos [PENDIENTE].
5. Confirmar el nombre y código del segundo integrante.
