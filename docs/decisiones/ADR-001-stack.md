# ADR-001 — Stack y plataformas

- **Estatus:** Aceptada
- **Fecha:** 2026-10-13
- **Tarea:** FNC-001 (incorporación al método)

## Contexto

El proyecto es un clon de NEXUS (portal de catálogo de plataformas por área, multitenant). Se incorpora al método con su código existente; este ADR registra el stack **real** del repositorio y las decisiones del dueño sobre la base de datos y la autenticación. Plataformas: backend, web e infra.

## Decisión

### Backend (`app/`, `run.py`) — versiones de `requirements.txt`

| Paquete | Versión | Uso |
|---|---|---|
| Python | ≥ 3.11 (lo exige `deploy/preflight.sh`) | Intérprete |
| Flask | 3.0.3 | API JSON `/api/v1` (sin plantillas ni estáticos) |
| Flask-SQLAlchemy | 3.1.1 | ORM |
| PyMySQL | 1.1.0 | Controlador MySQL/MariaDB |
| Flask-Login | 0.6.3 | Sesión por cookie |
| Flask-WTF | 1.2.1 | CSRF (hoy exento en todos los blueprints) |
| Flask-Compress | 1.15 | Compresión de respuestas |
| python-dotenv | 1.0.1 | Carga de `.env` |
| ldap3 | sin fijar | Autenticación y búsqueda en el directorio (solo lectura) |
| cryptography | sin fijar | Dependencia de TLS |
| redis | sin fijar | Cliente Redis (conectado, sin uso funcional) |
| gunicorn | sin fijar | Servidor WSGI en producción |
| Flask-Mail, psycopg2-binary, pexpect, openpyxl, xlrd, pandas | sin fijar | Sin uso aparente en el código actual |

### Frontend (`frontend/`) — versiones de `package.json`

| Paquete | Versión |
|---|---|
| Node.js | 22 LTS recomendado, mínimo 18.18 |
| next | 15.5.7 (App Router, `output: standalone`) |
| react / react-dom | 19.2.0 |
| typescript | 5.7.3 (strict) |
| tailwindcss | 3.4.17 (+ postcss 8.5.1, autoprefixer 10.4.20) |
| recharts | 2.15.4 |
| @types/node / @types/react / @types/react-dom | 22.10.5 / 19.0.7 / 19.0.3 |

### Base de datos

- **MySQL es la BD objetivo** (decisión del dueño). El código ya la soporta con `DB_ENGINE=mysql` (PyMySQL) y las migraciones de `utils/migrations/` están escritas en SQL de MySQL.
- SQLite queda solo como respaldo implícito del código cuando `DB_ENGINE` no es `mysql`; no se usa en staging ni producción.
- PostgreSQL **no** se adopta: no hay rama en `create_app()`, aunque `psycopg2-binary` siga en dependencias.

### Autenticación

- **Authelia + OpenLDAP existentes** son la autoridad de identidad (decisión del dueño). No se instalan ni se administran desde este proyecto.
- Authelia: SSO por cabeceras `Remote-*` inyectadas por nginx y aceptadas solo desde `TRUSTED_PROXIES`.
- OpenLDAP: solo lectura (bind y búsqueda) para login por directorio, mapeo de grupos a roles y búsqueda de usuarios.
- La sesión de la aplicación la emite Flask-Login (cookie `nexus_session`).

### Infraestructura

- Rocky Linux 8 (familia RHEL 8), dos unidades systemd (`<nombre>-backend` con Gunicorn, `<nombre>-frontend` con `node server.js`), nginx como reverse proxy en el mismo dominio. Redis opcional. Ver `docs/operacion/ENTORNOS.md`.

## Consecuencias

- Las tareas nuevas deben respetar Next.js 15 + Flask API + MySQL; cambiar de stack requiere un ADR nuevo.
- Hay que fijar versiones de las dependencias Python sin versión y retirar las que no se usan (registrar como tarea Propuesta).
- La convención de atributos LDAP del código es de Active Directory (`sAMAccountName`, `memberOf`); con OpenLDAP se configura `ldap_user_attr` desde la interfaz y se verifica el overlay `memberOf` (punto abierto en `docs/REQUERIMIENTOS.md`).
- Documentos previos que contradicen este stack (Docker obligatorio, MariaDB en contenedor, "prohibido `/api/v1`") quedan obsoletos: ver la nota en `docs/business_rules.md` y `docs/ARCHITECTURE.md`.
