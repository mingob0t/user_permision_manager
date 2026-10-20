# FNC-090 — Cliente web: `justification` opcional (contrato solicitudes 1.1)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | lib/access |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Creada** | 2026-10-20 |

## Contexto
- Contrato `solicitudes.md` 1.1 (FNC-056): `justification` es opcional y puede venir `null`; `frontend/src/lib/access/types.ts:71,87` la declara `string` obligatoria.
- Nuevo `409 estado_invalido` posible en `POST /access-requests`.
- Origen: FNC-056.

## Criterios de aceptación
- [x] Tipos `justification?: string | null` en la creación y `string | null` en `AccessRequest`; mocks y pruebas alineados
- [x] typecheck, lint y pruebas en verde

## Impacto cruzado
- Origen ← FNC-056; afecta DIS-013 y DIS-014

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | Creada como Propuesta (FNC-056) |
| 2026-10-20 | Hecha: resuelta en DIS-013 (`types.ts`; caso sin justificación en `peticiones.test.ts`; mocks sin cambio: ya eran válidos). `estado_invalido` con mensaje en `components/access/request-errors.ts` |
