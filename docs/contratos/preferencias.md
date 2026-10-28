# Contrato — Preferencias de la cuenta (tema)

| Campo | Valor |
|---|---|
| Versión | 1 (2026-10-27) — Aprobado por el dueño |
| Proveedor | backend (FNC-122; cambio en FNC-132) |
| Consumidores | web (FNC-123; cambio en DIS-054) |
| Solicitudes | — (origen: PLAN-FASE-7) |

Convenciones comunes: [README.md](README.md). Hasta hoy la forma estaba solo en `docs/backend/README.md`.

## API
- **`GET /me`** · sesión: `preferences.theme`: texto, uno de los valores válidos.
- **`PUT /me/preferences`** · sesión · solo la cuenta propia: acepta `theme` (opcional).
- **Valores válidos de `theme`:** `sistema` (por defecto), `claro`, `oscuro`.
  - Se retiran: `esmeralda`, `obsidiana`, `rosa`, `violeta`.
- **Errores:** valor fuera de la lista o que no es texto → `422 validacion` con `fields.theme` = «Elige un tema de la lista.»; nada se guarda.
- **Integración:** lectura al cargar la sesión y escritura al elegir; sin polling propio.

## Datos existentes
| Valor guardado | Pasa a |
|---|---|
| `esmeralda`, `rosa` | `claro` |
| `obsidiana`, `violeta` | `oscuro` |
| Cualquier otro fuera de la lista | `sistema` |

- Migración Alembic 0012 (FNC-132); sin vuelta atrás de datos.
- El cliente traduce igual los valores retirados que encuentre en la cuenta o en `localStorage` (DIS-054).

## Interfaz
- Selector en la cabecera: «Según el sistema», «Claro», «Oscuro».
- Error al guardar: toast de error (FNC-123), sin revertir la vista.

## Despliegue
- Web (DIS-054) antes o junto con el backend (FNC-132).

## Historial
| Versión | Fecha | Cambio |
|---|---|---|
| 1 | 2026-10-27 | Primera versión formal; reduce los temas válidos a 3 (Propuesta) |
