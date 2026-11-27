# DIS-153 — DonaKpi: prueba automática de contraste y tooltip con tokens

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Estatus** | Propuesta |
| **Creada** | 2026-11-27 (hallazgo menor de auditor-accesibilidad, previo a DIS-146) |

## Alcance propuesto
- Prueba que mida los 5 tokens `--color-indicador-*` contra `--color-superficie` en claro y oscuro (≥ 3:1) y los pares contiguos de cada dona.
- `dona-kpi.tsx:78-85`: `fontSize`, `borderRadius` y `padding` literales del tooltip a tokens.
