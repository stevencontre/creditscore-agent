# CREDITSCORE-AGENT — Agente inteligente de evaluación de riesgo crediticio

Proyecto de Inteligencia Artificial (Universidad Tecnológica de Bolívar). Agente de **aprendizaje con decisión basada en utilidad** que estima la probabilidad de incumplimiento de una solicitud de crédito y recomienda **aprobar, rechazar o remitir a revisión humana**.

> **Datos sintéticos.** No hay datos reales de solicitudes: el entorno (formulario, buró, originación y cartera) lo genera `src/creditscore/simulador.py` y `entorno.py`. Los resultados demuestran el funcionamiento del agente, no su desempeño en una entidad financiera real.

## Estructura

| Ruta | Contenido |
|---|---|
| `src/creditscore/` | Código del agente: `percepcion.py` (sensores), `decision.py`, `acciones.py` (actuadores), `memoria.py`, `modelo.py`, `agente.py` (ciclo Percepción → Decisión → Acción), `entorno.py`/`simulador.py`/`fabrica.py`, `registro.py`, `evaluacion.py`, `escenarios.py` |
| `config/` | `config.json` (parámetros), `umbrales.json` (umbrales fijados **antes** de las pruebas), `linea_base_manual.json` (pendiente) |
| `scripts/` | `run_agente.py`, `run_escenarios.py`, `run_pruebas_desempeno.py`, `matriz_decision.py` |
| `tests/` | 20 pruebas unitarias (`unittest`) |
| `logs/` | Registros de las ejecuciones reales (JSONL, CSV, JSON, TXT) |
| `docs/` | Informe (PDF y DOCX), matriz de decisión, diagramas, guion del video, bitácora de IA, lista de verificación |

## Instalación (Windows, PowerShell)

Requiere Python 3.10 o superior (se probó con 3.12.3).

```powershell
cd creditscore_agent
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install numpy
```
Para regenerar figuras e informe también: `pip install matplotlib python-docx` (más Graphviz y LibreOffice instalados). El agente solo necesita `numpy`.

En Linux/macOS: `source .venv/bin/activate`.

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

## Reproducibilidad
Todo es determinista dado el valor de semilla (`config/config.json` y `config/umbrales.json`). Las latencias dependen del equipo y varían ligeramente entre ejecuciones; el resto de cifras se reproduce exactamente.
Antes de repetir las pruebas, no modifique `config/umbrales.json`: sus umbrales se fijaron antes de ejecutar (su SHA-256 queda en `logs/resultados_pruebas.json`).

## Pendiente por los integrantes
1. Medir el tiempo del proceso manual (≥ 10 solicitudes) y escribirlo en `config/linea_base_manual.json` (medida M2b).
2. Revisar `docs/matriz_decision.json`: los puntajes del agente B (Cartrescue) son **estimaciones** hechas sin su diseño.
3. Grabar el video (`docs/guion_video.md`), publicar el repositorio y pegar los enlaces en la sección 9.9 del informe (`docs/construir_informe.py` o el DOCX).
4. Completar las verificaciones humanas de `docs/bitacora_uso_ia.md`.

## Git (publicación segura)
```powershell
git init
git add .
git status          # revise que no haya credenciales ni archivos temporales
git commit -m "Entrega 2: CREDITSCORE-AGENT, pruebas y documento ajustado"
git remote add origin <URL-DE-SU-REPOSITORIO>
git push -u origin main
```
Si ya tienen un repositorio de la entrega anterior, clónenlo, copien estas carpetas dentro y hagan `git add`/`commit` sin borrar los archivos originales.
