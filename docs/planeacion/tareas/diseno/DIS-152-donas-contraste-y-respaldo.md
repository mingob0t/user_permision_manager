# DIS-152 — Donas Conectores y Usuarios: colores distinguibles y respaldo sin desglose

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-27 (hallazgos de auditor-accesibilidad sobre DIS-146; el dueño pidió corregir tras DIS-147) |
| **Origen** | DIS-146 |

## Hallazgos que corrige
| Severidad | Hallazgo | Corrección |
|---|---|---|
| Media | Series contiguas casi iguales en luminancia: Usuarios 1.03, Conectores 1.16 | Par `PAR_DOS_SERIES` (plataformas + solicitudes, 1.62; único par ≥ 1.5 entre los tokens existentes) en ambas donas |
| Menor | Sin `desglose` la tarjeta desaparecía (antes mostraba el valor) | Una fila «Total» con el valor de `GET /stats` |

## Cambios
- `dashboard/dona-kpi.tsx`: exporta `PAR_DOS_SERIES`.
- `access/dona-conectores.tsx`, `access/dona-usuarios.tsx`: `valor` + `desglose?`, funciones `filasConectores`/`filasUsuarios`.
- `access/approvals-resumen.tsx`: muestra las donas con solo el valor.
- Pruebas DIS-152 en `approvals-resumen.test.tsx`.

## Impacto en elementos compartidos
- `DonaKpi`: solo se agrega una constante exportada; usos: las 4 KPI del Resumen de `/approvals`.

## Verificación
- tsc 0, eslint 0, vitest completo 121 archivos / 3677 pruebas, salida 0.
