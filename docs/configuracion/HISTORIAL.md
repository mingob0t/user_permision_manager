# Historial de cambios de variables y configuración

> Una fila por cambio de valor, de valor por defecto, de significado, de alta o de baja. **El motivo es obligatorio.** En los secretos no se escriben valores: solo "rotado". El mensaje de commit no reemplaza esta entrada.

| Fecha | Variable | Entorno | Antes | Después | Motivo | Tarea / ADR | Autor |
|---|---|---|---|---|---|---|---|
| 2026-10-13 | (todas las de VARIABLES.md) | todos | — | alta | Estructura inicial del proyecto | FNC-001 | — |
| 2026-10-13 | (todas las variables de entorno y constantes de VARIABLES.md) | todos | — | alta | Registro inicial de variables heredadas de NEXUS. Motivo: incorporación FNC-001 | FNC-001 | agente de documentación |
| 2026-10-13 | `APP_ENV`, `LOG_DIR`, `LOG_LEVEL`, `DB_PASSWORD`, `NEXT_PUBLIC_API_URL` | todos | alta (plantilla) | baja | Venían de la plantilla genérica y el código no las lee (la contraseña de BD es `DB_PASS`). Motivo: incorporación FNC-001 | FNC-001 | agente de documentación |
