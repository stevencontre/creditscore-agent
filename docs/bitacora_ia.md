# Bitácora humano–IA — Kredia

El registro histórico de octubre se conserva en [bitacora_uso_ia.md](bitacora_uso_ia.md). Las siguientes entradas complementan ese registro. La identidad del interlocutor de noviembre debe ser confirmada por el equipo.

| Fecha | Integrante | Herramienta | Para qué se usó | Qué se aceptó, modificó o descartó | Cómo se verificó |
|---|---|---|---|---|---|
| 24/11/2026 | Por confirmar | ChatGPT | Actualización de interfaz y README | Identidad Kredia y enlace actualizado | Usuario confirmó funcionamiento y publicación del README |
| 24/11/2026 | Por confirmar | ChatGPT | Informe IEEE | Se rechazaron versiones con primera página casi vacía y notas internas; se solicitó corrección | Usuario aportó capturas del defecto |
| 24/11/2026 | Por confirmar | ChatGPT | Evidencias del prototipo | Se aportaron seis capturas reales y contribuciones individuales | Capturas compartidas por el usuario; aprobación final pendiente |
| 24/11/2026 | Por confirmar | ChatGPT | Reproducibilidad | Script de datos y notebook exploratorio | Script y 20 pruebas unitarias ejecutados por el asistente; comparación reproducida; revisión humana pendiente |

## Reflexión
La generación automática del informe produjo repetidamente una primera página casi vacía. El equipo detectó el defecto al abrir el PDF y solicitó correcciones. El caso evidencia que generar un archivo no equivale a verificar su maquetación: deben revisarse las páginas renderizadas y la distribución del contenido. El registro de octubre también documenta un reemplazo automático que dañó dos claves del código y fue detectado mediante ejecución. Ambos casos justifican combinar revisión humana, pruebas automatizadas y comprobación de los artefactos finales. No se debe atribuir a los integrantes una verificación que todavía no hayan realizado.
