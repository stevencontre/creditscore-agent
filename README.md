# Kredia 

**Banca de Proyectos & Crédito Inteligente · Laboratorio de IA UTB**

Universidad Tecnológica de Bolívar — Proyecto académico de inteligencia artificial.

Integrantes: Steven David Contreras y Andres Camilo Castaño.

**Repositorio oficial:** https://github.com/stevencontre/kredia-utb

[![Abrir Kredia](https://img.shields.io/badge/Abrir-Kredia-820AD1?style=for-the-badge)](https://kredia-utb.streamlit.app/)

**Aplicación pública:** https://kredia-utb.streamlit.app/

## Descripción y alcance

Kredia es la evolución de CREDITSCORE-AGENT, un agente de simulación crediticia basado en aprendizaje automático y reglas de decisión. Su propósito es estudiar la estimación de riesgo, la trazabilidad y la gestión de incertidumbre en un entorno sintético. No es un servicio financiero real ni debe emplearse para decidir créditos de personas o empresas.

## Arquitectura y funcionalidades

El ciclo Percepción → Decisión → Acción valida las entradas, estima `p_default`, asigna una calificación A–E cuando corresponde y ejecuta una acción simulada o remite a revisión humana. La memoria y el registro permiten consultar casos y auditar eventos. El núcleo se mantiene separado de la interfaz.

- Panel principal, evaluación individual, procesamiento por lotes e historial.
- Comparación de modelos, aprendizaje, memoria histórica, monitoreo y laboratorio de pruebas.
- Navegación horizontal, formularios numéricos vacíos y gráficos Plotly.
- Laboratorio de proyectos: carga de escenario demo o importación CSV/XLSX/PDF textual con campos identificables (`monto`, `ingresos`, `costos`, `plazo`, `tasa`, `gracia`).
- Simulación de caída de ventas, retraso operativo y variación de tasa; cálculo ilustrativo de VAN, TIR mensual, DSCR agregado y cuotas.
- Comité de análisis determinista (auditor, riesgo y estructurador), asistente de comandos para plazo, tasa y gracia, y descarga de ficha de escenario.

El laboratorio de proyectos es independiente del modelo crediticio original. El comité no contiene tres modelos autónomos y el chat no utiliza un LLM. La ficha descargable no constituye una oferta de crédito.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `app.py` | Interfaz Streamlit de Kredia V6.3 |
| `src/creditscore/` | Percepción, decisión, acciones, memoria, modelo, agente, entorno, simulador, fábrica, registro, evaluación, escenarios, métricas y comparación de modelos |
| `config/` | Parámetros, umbrales preestablecidos y medición manual |
| `scripts/` | Ejecución, escenarios, desempeño, medición manual y matriz de decisión |
| `experiments/` | Resultados de comparación de modelos (`comparacion_2026.json`) |
| `tests/` | Pruebas unitarias |
| `logs/` | Evidencias experimentales archivadas en CSV, JSON, JSONL y TXT |
| `docs/` | Documentación histórica, diagramas, bitácora de IA y guías |
| `entrega_anterior_taller_ngramas/` | Evidencias de una entrega anterior |
| `requirements.txt` | Dependencias de ejecución |
| `requirements-docs.txt` | Dependencias para regenerar documentación histórica |

## Instalación

Se recomienda Python 3.12 o un entorno compatible con las dependencias declaradas.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

En Linux/macOS, activar con `source .venv/bin/activate`.

Dependencias: NumPy, pandas, Streamlit, scikit-learn 1.8.0, Plotly, numpy-financial, pypdf y openpyxl. Para regenerar la documentación histórica, consultar `requirements-docs.txt`; también puede requerir Graphviz y LibreOffice.

## Ejecución

```powershell
# 1) Demostración del agente (escenarios: normal, fallo_buro, fallo_originacion, invalidas, deriva)
python scripts\run_agente.py --n 15 --escenario normal
python scripts\run_agente.py --n 15 --escenario invalidas
python scripts\run_agente.py --n 15 --escenario fallo_buro
python scripts\run_agente.py --escenario deriva

# 2) Escenarios deterministas (17 casos) -> logs\escenarios.csv / .json / _eventos.jsonl
python scripts\run_escenarios.py

# 3) Pruebas de desempeño M1-M7 -> logs\resultados_pruebas.csv / .json, tabla_resultados.md, pruebas_eventos.jsonl (~10 s)
python scripts\run_pruebas_desempeno.py

# 4) Pruebas unitarias
python -m unittest discover -s tests -t . -v

# 5) Matriz de decisión ponderada y sensibilidad
python scripts\matriz_decision.py

# 6) Regenerar diagramas e informe (opcional)
python docs\diagramas\render_secuencia.py
python docs\construir_informe.py
```
Cada ejecución del agente escribe un log JSONL con marca de tiempo (`logs/ejecucion_AAAAMMDD_HHMMSS.jsonl`) con los eventos `PERCEPCION`, `DECISION`, `ACCION`, `AUDITORIA`, `SENSOR_FALLO`, etc.

## Comparación experimental

Experimento sintético de 5.000 solicitudes, semilla 2026, partición estratificada 70/15/15 para entrenamiento, validación y prueba. Selección de hiperparámetros por AUC de validación.

| Modelo | AUC prueba | F1 (umbral 0,5) | Brier |
|---|---:|---:|---:|
| Frecuencia histórica | 0,5000 | 0,0000 | 0,1746 |
| Regresión logística | 0,7786 | 0,2857 | 0,1436 |
| Random Forest | 0,7718 | 0,1910 | 0,1473 |

La regresión logística obtuvo el mejor resultado de esta comparación, aunque su F1 bajo indica limitaciones en la clasificación de incumplimientos al umbral evaluado. Los resultados no validan el uso en poblaciones reales.

Fuente: `experiments/comparacion_2026.json`. Para repetir la comparación, usar la vista Comparación de modelos.

## Pruebas y reproducibilidad

Resultados históricos archivados (no son una nueva ejecución de V6.3):

| Indicador | Resultado |
|---|---|
| AUC promedio, cinco semillas | 0,7793 ± 0,0101 |
| Latencia p95 del núcleo simulado | 0,701 ms |
| ECE promedio | 0,0237 |
| Remisión de entradas inválidas | 1.000/1.000 |
| Trazabilidad | 9.000/9.000 |
| Reproducibilidad de decisiones | 1.500/1.500 |
| Detección de deriva y mejora de Brier tras recalibración | 5/5 semillas en cada indicador |
| Pruebas unitarias archivadas | 20, todas correctas |

La medición manual archivada incluye diez solicitudes y un promedio de 3,6 segundos; no incluye digitación ni consulta real al buró. No es una comparación de procesos bancarios completos.

Fuentes: `logs/tabla_resultados.md`, `logs/resultados_pruebas.json`, `logs/unittest.txt` y `config/linea_base_manual.json`.

No modificar `config/umbrales.json` antes de repetir las pruebas. Las semillas permiten reproducir los resultados en condiciones equivalentes; las latencias dependen del equipo.

## IA responsable y limitaciones

Utilizar exclusivamente datos sintéticos. No introducir información personal ni documentos financieros reales. La revisión humana y la auditoría son mecanismos del entorno simulado; no garantizan equidad ni validez externa. Los indicadores de proyectos suponen costos constantes, inversión inicial igual al monto, gracia de capital y descuento igual a la tasa simulada, sin impuestos ni valor residual.

## Documentación y cierre académico

Los archivos de `docs/` conservan la evidencia de las entregas anteriores. El informe final, la presentación y el guion definitivo deben incorporarse cuando estén terminados y revisados por los integrantes. Revisar la bitácora de IA y las contribuciones individuales; los puntajes históricos de Cartrescue deben interpretarse considerando que se basaron en la descripción del caso.

## Actualización del repositorio

Conservar el historial Git y revisar `git status` antes de confirmar cambios. No publicar credenciales ni datos personales. El enlace público vigente comunicado por los integrantes es https://kredia-utb.streamlit.app/.
