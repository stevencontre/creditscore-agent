# Opción A — Plataforma de despliegue (Streamlit Community Cloud)

**Enlace público de la app:** https://creditscore-agent-7pyg7dzx7yiykdggfwoinw.streamlit.app/
La app debe estar disponible hasta la fecha de calificación (ábranla antes de entregar: si una app gratuita se duerme por inactividad, hay que despertarla y comprobar que carga).

## Cómo desplegar (una sola vez)
1. Suban el repositorio a GitHub como **público**, con `app.py` y `requirements.txt` en la raíz (`git add .`, `git commit`, `git push`).
2. Entren a https://share.streamlit.io e inicien sesión con GitHub.
3. Pulsen **Create app** y completen: repositorio, rama `main`, archivo principal `app.py`. Opcional: elijan un subdominio.
4. Pulsen **Deploy**. Tarda unos minutos. Copien la URL final y péguenla en la sección 9.9 del informe y en el README.

## Cómo ejecutarla en local (alternativa para probar)
```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Instrucciones de uso
1. En la pestaña **1. Evaluar una solicitud** pulsen un caso sugerido (carga los datos), luego **Evaluar solicitud**. También pueden escribir sus propios valores.
2. El resultado muestra la acción (APROBAR / RECHAZAR / REVISION_HUMANA), la probabilidad de incumplimiento, la calificación, la razón, las acciones ejecutadas en el entorno y el **registro de eventos con marca de tiempo** (Percepción → Decisión → Acción). El log completo de la sesión se descarga desde la barra lateral.
3. **2. Lote simulado:** ejecuta los escenarios `normal`, `invalidas`, `fallo_buro`, `fallo_originacion` y `deriva` sobre solicitudes simuladas.
4. **3. Pruebas:** ejecuta en vivo las 20 pruebas unitarias, los 17 escenarios y las pruebas de desempeño M1–M7 que producen la tabla de resultados del informe.
5. **Reiniciar agente (desde cero)** en la barra lateral reconstruye el simulador, el modelo y el entorno con la semilla indicada.

## Casos de prueba sugeridos (equivalen a los escenarios E01–E16 del informe)
| Caso (botón) | Entrada clave | Resultado esperado |
|---|---|---|
| Típico: bajo riesgo | ingresos 8.000.000, obligaciones 800.000, 0 atrasos | APROBAR; originación REGISTRADA |
| Típico: alto riesgo | ingresos 1.500.000, obligaciones 800.000, 6 atrasos | RECHAZAR; originación REGISTRADA |
| Típico: riesgo intermedio | ingresos 2.800.000, obligaciones 900.000, 1 atraso | REVISION_HUMANA; caso en bandeja del analista |
| Límite: DTI > 0,80 | ingresos 3.000.000, obligaciones 2.400.300 | REVISION_HUMANA por R4 |
| Falla: ingreso faltante | campo de ingresos vacío | REVISION_HUMANA; percepción INCOMPLETA; sin llamada a originación |
| Falla: valor no numérico | obligaciones = `abc` | REVISION_HUMANA; percepción INVALIDA |
| Falla: pagos atrasados fuera de rango | 25 pagos atrasados | REVISION_HUMANA; percepción FUERA_DOMINIO |
| Falla: buró caído | casilla «Buró de crédito caído» | 3 reintentos registrados (`SENSOR_FALLO`); REVISION_HUMANA |
| Falla: originación caída | casilla «Sistema de originación caído» | APROBAR con originación DIFERIDA y recomendación en outbox |

## Nota sobre los datos
Todo es sintético: no hay solicitudes ni datos personales reales. Los resultados demuestran el funcionamiento del agente, no su desempeño en una entidad financiera.
