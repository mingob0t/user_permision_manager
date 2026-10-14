# FNC-038 — Contratos v1 backend↔web del gestor de accesos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | contratos |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Rama `fnc/FNC-038-contratos-v1` desde `develop` (worktree `pokemon-wt-038`) |
| **Rama** | `fnc/FNC-038-contratos-v1` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- No existe `docs/contratos/`
- La fase 3 agrega unos 25 endpoints que consumirá el frontend Next.js y, por el método, el acuerdo de interfaz se integra a `develop` antes de implementar para que backend y web trabajen sobre lo mismo
- Hoy los tipos viven solo del lado web (`frontend/src/lib/types.ts`)
- Requerimientos: todas las F-* de la fase 3

## Objetivo
- Redactar e integrar los contratos versionados, con permisos por rol, validaciones, errores, estados y datos simulados, a partir de la plantilla `~/.claude/plantillas/coordinacion/CONTRATO.md`

## Alcance
- **Incluye:**
  - `docs/contratos/areas-y-roles.md`: alta de área por el admin, asignación de admins (superadmin), creación y elevación de admins
  - `docs/contratos/plataformas-integracion.md`: campos `integration_type` (`ldap`/`conector`) y grupos por nivel
  - `docs/contratos/solicitudes.md`: catálogo solicitable, crear, mis solicitudes, bandeja, aprobar, rechazar con motivo; estados `pendiente`, `aprobada`, `rechazada`
  - `docs/contratos/accesos.md`: accesos por usuario, mis accesos, revocar, inventario; estados del acceso (`en_proceso`, `activo`, `fallido`, `revocando`, `revocado`, `fallo_revocacion`) y origen (`solicitud`, `admin_de_area`, `heredado` si se aprueba FNC-065)
  - `docs/contratos/auditoria.md`: consulta con filtros y paginación, historial por usuario y por plataforma, visibilidad por rol
  - `docs/contratos/conectores-y-ejecuciones.md`: configuración de conectores, bitácora de ejecuciones y reintento
  - `docs/contratos/usuarios-directorio.md`: alta de cuentas en OpenLDAP
  - `docs/contratos/inicio.md`: resumen por rol
  - `docs/contratos/README.md` con el índice y la convención de versiones
  - Mecanismo de actualización de cada pantalla según ADR-006
- **No incluye:**
  - Implementación de endpoints o pantallas
  - Endpoints existentes que la fase 3 no cambia

## Archivos previstos
- `docs/contratos/*.md` (nuevos)

## Reutilización
- Forma de error existente `{"status": "error", "message": ...}` (`app/modules/api/crud.py` `_error`)
- Tipos y nombres actuales de `frontend/src/lib/types.ts` para no renombrar lo existente

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| Forma de error de `/api/v1`: campos nuevos opcionales `code` y `correlation_id` (aditivos; `status` y `message` igual) | Convención de API (solo documentada) | Todo el frontend (`lib/api.ts` lee `message`); backend `_error` de `crud.py` y `admin.py` al implementar | Pendiente (dueño) |
| Lista paginada `{items, page, per_page, total}` para endpoints nuevos | Convención de API (solo documentada) | Endpoints nuevos de la fase 3 | Pendiente (dueño) |
| `GET /audit`: sin `page` devuelve el arreglo actual; con `page`, paginado | Endpoint existente | `lib/api.ts:74` (`api.audit`), `components/audit-log.tsx:19` (pantalla Auditoría): sin cambio mientras no envíen `page` | Pendiente (dueño) |
| `managed_area_ids` en `POST/PUT /users` → 400; `POST /users` con `admin_area` ya no copia áreas | Endpoint existente | `components/users-list.tsx:115,124` (pantalla Usuarios) | Pendiente (dueño); lo adapta FNC-069/DIS-019 |
| Retirados `PUT /platforms/<id>/users` y `PUT /users/<id>/platforms` (FNC-065) | Endpoints existentes | `lib/api.ts:123` (`setPlatformUsers`, sin uso en componentes), `lib/api.ts:136` (`setUserPlatforms`) y `components/users-list.tsx` | Pendiente (dueño) |
| Anexo A de `docs/seguridad/LINEAMIENTOS.md`: baja de áreas para admin (sus áreas); §12 sin la pregunta 17 | Lineamiento compartido | Revisor, auditor-seguridad y pruebas de matriz (`tests/matriz_proteccion.py` al implementar FNC-045) | Pendiente (dueño) |

`impacto.py` (2026-10-14, tras las correcciones, contra `develop`): **Impacto en elementos compartidos:** ninguno detectado (comparado contra `develop`; 14 archivos cambiados). Detecta solo código; las filas de arriba son de contrato y se listan a mano.

## Criterios de aceptación
- [x] Un contrato por sección, con versión 1 y fecha (8 contratos + índice)
- [x] Cada endpoint declara método, ruta, permiso por rol, entrada con límites, salida con ejemplo y errores
- [ ] Revisado por el dueño (decisiones de FNC-037 reflejadas en `docs/contratos/README.md`; pendiente su revisión y las *Por confirmar*)
- [ ] Integrado a `develop` antes de iniciar FNC-044 y FNC-069 (pendiente de aprobación de merge)
- [ ] Criterios comunes backend (FNC-037): no aplican en su mayoría (sin código ni endpoints); sin IPs ni secretos verificado

## Verificación
| Comando | Resultado |
|---|---|
| Extraer y `json.loads` de los bloques JSON de `docs/contratos/*.md` | 18 bloques válidos |
| `grep -rnE` de IPv4 en `docs/contratos/` | Sin coincidencias |
| `python3 ~/.claude/agentes/herramientas/impacto.py` | Ninguno detectado; código 0 |

- No verificado: no hay código que probar; sin pytest ni Vitest (la tarea es solo documentación). Sin revisor (indicación del orquestador).

## Respuestas del dueño (2026-10-14)
- P7: revocar no requiere motivo (`reason` opcional, ≤ 500)
- P8: el portal no maneja contraseñas de cuentas LDAP; la contraseña la maneja Authelia
- P10: aviso a admins del área y superadmin; reintento manual solo superadmin (confirmado)
- P11: baja de áreas también por el admin de esas áreas; 409 con plataformas o accesos vigentes. Anexo A y §12 de `docs/seguridad/LINEAMIENTOS.md` actualizados

## Por confirmar (valor más seguro aplicado)
- P10 (resto): el aviso no depende de `pref_email_notifications`
- P13: no cambia la forma; el contrato exige CSRF (cabecera y token según FNC-008)
- P6 (resto): nivel `admin` del acceso automático del creador; otros admins y retiro del área en FNC-055
- Seguridad §12.11: lista blanca de hosts fijada por el despliegue
- Superadmin en grupos LDAP: sin registros de acceso; FNC-055 decide

## Impacto cruzado
- Genera → FNC-069 (consumidor web)
- Origen ← FNC-037
- Depende de → FNC-036 (lineamientos de seguridad), Respuestas del dueño a las preguntas P1 a P14 de FNC-037, ADR-006

## Riesgos y reversión
- Un contrato cerrado demasiado pronto obliga a nuevas versiones; se mitiga esperando las respuestas del dueño.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-14 | Aprobada por el dueño (vía orquestador); En curso en `fnc/FNC-038-contratos-v1` |
| 2026-10-14 | 8 contratos v1 + `docs/contratos/README.md`; commit local `e092ee9` sin push |
| 2026-10-14 | Respuestas P7, P8, P10, P11 y 9 hallazgos del revisor corregidos; En revisión hasta el merge |
