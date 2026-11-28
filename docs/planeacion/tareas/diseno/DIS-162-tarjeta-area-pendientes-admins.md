# DIS-162 — Tarjeta de área: Solicitudes pendientes y administradores

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-28 (pedido del dueño, captura de Plataformas > Áreas) |

## Cambios
- `areas/tarjeta-area.tsx` (variante estándar): fila de KPI «Personas», «Plataformas» y «Solicitudes pendientes» (3 columnas); esta última es `Cifra` con `enlace` a `/approvals?status=pendiente&area_id=<id>`, `min-h-12`, `foco-visible`, nombre accesible «N solicitudes pendientes en <área>. Abrir Historial.».
- Debajo, `AdministradoresArea`: recuadro `.nx-area-card__cifra` de ancho completo (`col-span-full`) con los nombres de `area.admins` (truncados, `title` con la lista) o «Sin administrador».
- Se retira el badge «N por aprobar» del encabezado (DIS-137); el KPI lo sustituye. `rutaPendientesArea` se conserva.
- `pendientes` ahora es opcional sin valor por omisión: sin dato (consulta fallida) no hay KPI; con dato y sin pendientes, 0.
- `platform-admin.tsx`: solo pasa `undefined` si `inboxStats` no tiene datos.
- Sin CSS ni tokens nuevos: reutiliza `.nx-area-card__*`.
- Pruebas: `tarjeta-area.test.tsx` (3 nuevas, fallaban antes), `platform-admin.test.tsx` y `area-tactil.excepciones.ts` ajustadas.

## Impacto en elementos compartidos
- `TarjetaArea` y `Cifra` (privada): usadas por Plataformas > Áreas (`platform-admin.tsx`); las demás variantes no cambian. `Cifra` conserva su aspecto.
- Otros importadores de `TarjetaArea` (vistas previas de diseño) no pasan `pendientes`: no muestran el KPI.

## Verificación
- `npm run typecheck` 0, `npm run lint` 0, `npx vitest run` 0 (3717 pruebas).
- Visual en claro/oscuro, móvil y escritorio: no realizada (sin app levantada); contraste cubierto por los tokens ya medidos de `.nx-area-card__*`.
