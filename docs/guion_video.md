# Guion del video (Opción B) — duración total prevista: 18 min (máximo permitido: 20)

**Reglas de la actividad:** cámara y voz de **ambos** integrantes; demostración en vivo (no solo diapositivas); un video de más de 20 min solo se evalúa hasta el minuto 20. Al publicar, coloquen un índice con minutos en la descripción y pegue el enlace en la sección 9.9 del informe.

> Los minutos son **previstos**. Cuando graben, corrijan la columna "Minuto real" y copien esos minutos en la columna «Evidencia» de la tabla de resultados.

**Integrante 1 (I1): Steven David Contreras.  Integrante 2 (I2): Andres Camilo Castaño.** (Pueden intercambiar tareas; ambos deben hablar y aparecer en cámara.)

## Preparación antes de grabar
1. Carpeta nueva y terminal abierta en blanco (para mostrar «desde cero»). Cámara y micrófono encendidos para los dos.
2. Tengan abiertos: el PDF del informe, el editor con la carpeta `src/creditscore`, `docs/diagramas/*.png` y la terminal.
3. No usen resultados previos: ejecuten los comandos en pantalla.

## Índice y guion

| Minuto previsto | Minuto real | Segmento | En pantalla | Quién habla y qué dice | Evidencia que cubre |
|---|---|---|---|---|---|
| 00:00–01:30 | | **Introducción** | Cámara de ambos + portada del informe | I1 y I2 se presentan. I1: problema (riesgo crediticio) y tipo de agente (aprendizaje + utilidad). I2: por qué se eligió este agente (matriz: S = 4,05 vs 3,55 estimado) y que los puntajes del otro agente son estimaciones. | Matriz, participación de ambos |
| 01:30–04:00 | | **Instalación desde cero** | Terminal: `python -m venv .venv`, activar, `pip install numpy`, `dir` de la carpeta | I2 ejecuta y explica cada comando; muestra que `logs/` aún no tiene ejecuciones propias (borre antes `logs/ejecucion_*`). | Inicio desde cero |
| 04:00–07:30 | | **Arquitectura** | `docs/diagramas/arquitectura.png`; luego `agente.py` (método `evaluar`) | I1 explica el diagrama de componentes y los siete componentes IBM; señala en el código `percibir` → `decidir` → `actuar` (ciclo Percepción → Decisión → Acción). | Arquitectura, ciclo P→D→A |
| 07:30–10:30 | | **Escenario típico** | `python scripts\run_agente.py --n 15 --escenario normal` y apertura del `.jsonl` generado | I2 ejecuta; I1 comenta una aprobación, un rechazo y una remisión (p_default, calificación, razón); se muestra el log con marca de tiempo (`PERCEPCION`, `DECISION`, `ACCION`). | Escenario típico |
| 10:30–13:00 | | **Escenarios de fallo esperado** | `run_agente.py --escenario invalidas`, `--escenario fallo_buro`, `--escenario fallo_originacion` | I1 explica que ante datos inválidos o buró caído el agente se abstiene (regla R1); I2 muestra `DIFERIDA` y el outbox cuando cae la originación. Relacionan con las Figuras 3 y 4 (UML de excepción). | Fallo esperado, UML |
| 13:00–16:00 | | **Pruebas y obtención de la tabla** | `python -m unittest discover -s tests -t . -v`, `python scripts\run_escenarios.py`, `python scripts\run_pruebas_desempeno.py` (~10 s) y apertura de `logs\resultados_pruebas.csv` | I2 ejecuta las tres pruebas; I1 lee la tabla (M1–M7), señala qué cumple, que M2b está pendiente y compara con la Tabla 10 del informe. | Pruebas, valores de la tabla |
| 16:00–17:15 | | **Análisis y limitaciones** | Sección 9.7 «Análisis de resultados» y 9.8 del informe | I1: por qué estos resultados deben leerse con cautela (datos sintéticos, PSI poco sensible, 50 % a revisión). I2: mejoras priorizadas. | Análisis de fallos |
| 17:15–18:00 | | **Cierre** | Cámara de ambos | I1 y I2: conclusiones y pendientes (línea base manual). | Cierre |

## Lista de verificación al grabar
- [ ] Se ve el inicio desde cero (entorno virtual e instalación).
- [ ] Un escenario típico y al menos un fallo esperado ejecutados en vivo.
- [ ] Las pruebas se ejecutan en pantalla y de ahí salen los valores de la tabla.
- [ ] Ambos integrantes aparecen y hablan.
- [ ] Duración menor a 20:00; índice con minutos en la descripción.
- [ ] Enlace con acceso habilitado (YouTube no listado, OneDrive o Drive).
