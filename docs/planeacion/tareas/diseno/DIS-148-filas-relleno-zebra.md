# DIS-148 — Tabla de pendientes: filas de relleno vacías con zebra

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-27 (aprobada por pedido directo del dueño) |

## Motivo
- Las filas fantasma del panel «Solicitudes – Pendientes por aprobar» tenían barras y un círculo de esqueleto: parecían registros pendientes de más (pedido del dueño con captura).

## Cambios
- `components/panel-tabla.tsx` (`FilasFantasma`): filas vacías, sin esqueleto ni `opacity-20`; conservan zebra (`claseFilaPanel`), borde, `aria-hidden` y solo escritorio. Se retira la prop `columnas` (ya no se usa).
- `access/solicitudes-panel.tsx`: deja de pasar `columnas`.
- Prueba nueva `tests/components/panel-tabla.test.tsx` (falla con el código anterior: atenuación y zebra).

## Impacto en elementos compartidos
- `FilasFantasma` (panel-tabla): único uso en `SolicitudesPanel` → Resumen de `/approvals`.

## Verificación
- tsc 0, eslint 0, vitest completo 121 archivos / 3671 pruebas, salida 0. Sin captura visual en claro/oscuro (no verificada).
