# pokemon: requerimientos y descripción

> Origen: `git clone` de NEXUS (`MI_NUEVO_PROYECTO`, commit `0bf71e8`, 2026-10-13). La columna **Estado** indica lo que ya existe en el código heredado. Requerimientos acordados con el dueño el 2026-10-13.

## 1. Descripción general
Portal para gestionar el acceso a plataformas internas agrupadas por **áreas**. Los usuarios solicitan acceso a una plataforma con un nivel, y los administradores del área lo aprueban o lo rechazan. Para otorgar el acceso, el portal agrega al usuario a un grupo de OpenLDAP. Si la plataforma no usa Authelia ni OpenLDAP, se ejecuta un conector que crea la cuenta. Todo queda auditado.

## 2. Usuarios y roles
| Rol | Nombre en el código | Puede |
|---|---|---|
| Superadmin | `administrador` | Una sola persona (el dueño). Ve y gestiona todas las áreas sin límite. Es el **único** que crea admins o eleva un usuario a admin. Configura SMTP, LDAP y conectores. |
| Admin | `admin_area` | Gestiona varias áreas: da de alta sus áreas y plataformas y tiene acceso automático a ellas. Aprueba o rechaza las solicitudes y revoca accesos de sus áreas. Para un área ajena, solicita acceso como usuario. |
| Usuario | `usuario` | Consulta el catálogo, solicita acceso a una plataforma con nivel **usuario** o **admin** de la plataforma, y ve sus solicitudes, sus accesos y sus propios registros de auditoría. |

## 3. Funcionalidades
### 3.0 Funcionalidades obligatorias
| ID | Funcionalidad | Estado | Detalle |
|---|---|---|---|
| OB-01 | Autenticación con Authelia (cabeceras `Remote-*` desde proxy de confianza) sobre OpenLDAP | Parcial | Existe en `app/modules/api/auth.py`; el bloque `auth_request` de nginx está comentado |
| OB-02 | Notificaciones por correo (SMTP con plantillas por evento) | Parcial | Motor con escape (SEG-23) y avisos del gestor listos (FNC-048); faltan los llamadores FNC-049/056/057 |
| OB-03 | Tema claro y oscuro, tokens, sin estilos inline, responsive, AA | Por verificar | Diagnóstico de accesibilidad en FNC-001 |
| OB-04 | Sin IPs en código ni configuración; secretos fuera del repo | Por verificar | Diagnóstico de seguridad en FNC-001 |

### 3.1 Funcionalidades por módulo
| ID | Módulo | Funcionalidad | Estado |
|---|---|---|---|
| F-AREA-01 | Áreas | Alta, edición y baja de áreas; el admin da de alta las suyas | Parcial: hoy solo el superadmin crea áreas |
| F-AREA-02 | Áreas | Asignar admins a un área (solo superadmin) | Parcial: un `admin_area` puede asignar el rol `admin_area` |
| F-PLAT-01 | Plataformas | Alta y edición: área (una sola), URL, descripción, **tipo de integración** (`ldap` o `conector`), grupos LDAP por nivel | Parcial: sin tipo de integración ni grupos |
| F-USR-01 | Usuarios | Usar cuentas existentes de OpenLDAP | Parcial: login e importación de solo lectura |
| F-USR-02 | Usuarios | Crear cuentas desde el portal **en OpenLDAP** | Falta: hoy se crean solo en la BD local |
| F-USR-03 | Usuarios | Elevar a admin (solo superadmin) | Parcial (ver F-AREA-02) |
| F-SOL-01 | Solicitudes | Catálogo de plataformas por área para solicitar | Parcial: el catálogo existe, pero no se puede solicitar |
| F-SOL-02 | Solicitudes | Solicitar nivel `usuario` o `admin` con justificación; ver mis solicitudes | Falta (se retiró; referencia: `nexus_master/app/modules/requests`) |
| F-SOL-03 | Solicitudes | Bandeja de aprobación por área; rechazo con motivo obligatorio | Falta |
| F-ACC-01 | Accesos | Otorgar = agregar el usuario al grupo LDAP de la plataforma y del nivel | Falta: ninguna escritura en LDAP |
| F-ACC-02 | Accesos | Revocar manualmente desde el portal = sacarlo del grupo o ejecutar el conector | Falta |
| F-CON-01 | Conectores | Conector por plataforma (API, SSH o BD) que crea o quita la cuenta; ejecución en segundo plano con reintentos y bitácora; credenciales en Vaultwarden | Falta |
| F-AUD-01 | Auditoría | Bitácora inmutable con detalle del cambio (antes/después, a quién, qué plataforma y área) | Parcial: `AuditLog` sin detalle ni FK |
| F-AUD-02 | Auditoría | Inventario de permisos: quién tiene qué plataforma, nivel, desde cuándo, quién aprobó | Falta |
| F-AUD-03 | Auditoría | Historial por usuario y por plataforma | Falta |
| F-AUD-04 | Auditoría | Visibilidad: superadmin todo, admin sus áreas, usuario sus registros | Parcial: el admin filtra por actor, no por área |
| F-NOT-01 | Notificaciones | Correos: nueva solicitud (admins del área), aprobada o rechazada (usuario), fallo de conector (admin) | Parcial: plantillas y avisos listos (FNC-048); faltan los llamadores FNC-049/056/057 |

## 4. Requerimientos funcionales
| ID | Requerimiento |
|---|---|
| RF-01 | Cada plataforma pertenece a una sola área; un admin puede gestionar varias áreas. |
| RF-02 | Cada plataforma tiene dos grupos en OpenLDAP: nivel usuario y nivel admin. OpenLDAP es la fuente de verdad del acceso. |
| RF-03 | Un admin no aprueba solicitudes de áreas que no gestiona; las solicita como usuario. |
| RF-04 | Solo el superadmin crea o eleva admins. |
| RF-05 | La auditoría se basa en lo registrado en el portal (no se concilia contra LDAP ni contra las plataformas). |
| RF-06 | El rechazo de una solicitud exige motivo. |

### Pantallas por rol
| Pantalla | Usuario | Admin | Superadmin |
|---|---|---|---|
| Inicio | Mis accesos y mis solicitudes | Pendientes y resumen de sus áreas | Pendientes y resumen global |
| Catálogo (solicitar) | Sí | Sí, áreas ajenas | — |
| Mis solicitudes | Sí | Sí | — |
| Aprobaciones | — | Sus áreas | Todas |
| Áreas | — | Las suyas | Todas y asignar admins |
| Plataformas | — | Las de sus áreas | Todas |
| Usuarios y accesos | — | Con acceso a sus áreas; revocar | Todos; crear cuentas; elevar a admin |
| Inventario de permisos | — | Sus áreas | Todo |
| Auditoría | Sus registros | Sus áreas | Todo |
| Configuración (SMTP, LDAP, conectores) | — | — | Sí |

### Fuera de la v1
Accesos temporales con vencimiento, baja masiva de un usuario, recertificación periódica, conciliación contra LDAP, recordatorios y escalamiento, suplentes.

## 5. Requerimientos no funcionales
| ID | Requerimiento |
|---|---|
| RNF-01 | Tema claro y oscuro, tokens, sin estilos inline, responsive, accesibilidad AA |
| RNF-02 | Sin direcciones IP: solo nombres de host desde variables |
| RNF-03 | Secretos: `.env` en dev, Vaultwarden en staging/prod; nunca en el repo ni en claro en la BD |
| RNF-04 | Base de datos MySQL |
| RNF-05 | Pruebas automatizadas de permisos por rol en cada endpoint |

## 6. Tecnologías y plataformas
| Plataforma | Código | Documentación |
|---|---|---|
| Backend (Flask, API JSON `/api/v1`) | `app/`, `run.py` | `docs/backend/` |
| Frontend web (Next.js 15, TypeScript, Tailwind) | `frontend/` | `docs/frontend/` |
| Infraestructura (Rocky Linux, systemd, nginx) | `deploy/` | `docs/operacion/` |
| Autenticación | Authelia + OpenLDAP existentes | `docs/decisiones/` |

## 7. Requerimientos mínimos de entorno
Levantados del código y de `deploy/preflight.sh` en FNC-001.

| Componente | Mínimo | Recomendado / notas |
|---|---|---|
| Sistema operativo (servidor) | Rocky Linux 8 o familia RHEL 8 (x86_64 o aarch64) | RHEL 9 funciona con avisos; el instalador asume `dnf` |
| Python | 3.11 con módulo `venv` | 3.11 o 3.12; Rocky 8 trae 3.6, se instala `python311` de AppStream si no hay otro |
| Node.js / npm | 18.18 | 22 LTS (Next.js 15) |
| Base de datos | MySQL (BD objetivo, ADR-001) accesible por nombre de host | El código usa PyMySQL; SQLite solo como respaldo en dev |
| Cliente `mysql` | — | Útil para respaldar la base antes de migrar |
| Redis | Opcional | La app arranca sin él; hoy no tiene uso funcional |
| Reverse proxy | nginx con TLS en el mismo dominio para API y frontend | SELinux `httpd_can_network_connect` activo; firewalld con `http`/`https` |
| Autenticación | Authelia y OpenLDAP existentes, accesibles por nombre de host | Authelia vía `auth_request` en nginx; LDAP solo lectura |
| Correo | Servidor SMTP (nombre de host) | Configurable por interfaz o por `.env` |
| Paquetes de compilación | `gcc`, `make`, `openssl-devel`, `libffi-devel`, `openldap-devel` | Para `cryptography` y `ldap3` sin rueda binaria |
| Recursos | 2 GB de disco libres; 1 GB de RAM | Más RAM o swap para `next build` |
| Puertos locales | 5001 (backend) y 3000 (frontend) libres, solo en loopback | Solo nginx expone 443 |
| Salida a Internet | Directa o vía proxy corporativo | Necesaria para `dnf`, `pip` y `npm` durante la instalación |

## 8. Puntos abiertos
- Servidor SMTP (nombre de host en configuración).
- Convención de nombres de grupos y OUs en OpenLDAP.
- MFA en Authelia para admins.
- Entorno de despliegue.
