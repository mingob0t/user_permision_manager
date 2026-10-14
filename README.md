# 🧠 NEXUS - UNIFIED SYSTEM TERMINAL

NEXUS es una plataforma de gestión centralizada diseñada para el monitoreo y administración de identidades, áreas operativas y plataformas de servicios.

## 🚀 Características Principales

*   **Gestión de Áreas y Plataformas**: Control centralizado de departamentos y los sistemas vinculados a ellos.
*   **Portal de Catálogo**: Vista unificada para que los usuarios finales exploren y marquen sus sistemas favoritos.
*   **Sistema de Solicitudes**: Flujo de aprobación para el acceso a plataformas restringidas.
*   **Seguridad de Grado Empresarial**: Sistema de autenticación con soporte LDAP y control de acceso basado en roles (RBAC).
*   **Sistema de Notificaciones**: Motor de plantillas configurable para alertas por correo electrónico y notificaciones in-app.
*   **Auditoría Integral**: Registro detallado de cada acción realizada en el sistema.

## 🛠️ Stack Tecnológico

*   **Backend**: Python 3.x, Flask como API JSON (`/api/v1`), modular con Blueprints.
*   **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS.
*   **Base de Datos**: SQLAlchemy (Soporte para SQLite y MySQL).
*   **Autenticación**: Flask-Login, con soporte para LDAP y SSO vía Authelia.
*   **Entorno**: Soporte nativo para variables `.env`.

Son **dos servicios** tras un reverse proxy: Flask no sirve interfaz, solo
datos; Next.js no accede a la base de datos, solo consume la API. Ver
[deploy/README.md](deploy/README.md).

## 📂 Estructura del Proyecto

```text
/
├── app/                  # Backend Flask (solo API)
│   ├── authz.py          # Autorización y alcance multitenant
│   ├── modules/
│   │   ├── api/          # API v1: lectura, escritura, admin y auth
│   │   ├── auth/         # Sesión, LDAP y SSO
│   │   ├── areas/        # Áreas (tenants)
│   │   ├── notifications/# SMTP y plantillas
│   │   ├── audit/        # Auditoría
│   │   └── settings/     # Configuración del sistema
│   └── utils/            # Utilidades compartidas
├── frontend/             # Frontend Next.js
│   └── src/
│       ├── app/          # Rutas (App Router)
│       ├── components/   # Componentes
│       └── lib/          # Cliente de API y tipos
├── assets/img/           # Imágenes subidas desde los ajustes
├── templates/errors/     # Páginas de error de Flask
├── deploy/               # systemd y Nginx
└── run.py                # Punto de entrada del backend
```

## ⚙️ Iniciar los servicios

Son dos procesos independientes: el **backend** (Flask, puerto 5001) y el
**frontend** (Next.js, puerto 3000). El navegador entra siempre por el
frontend, que reenvía `/api` y `/auth` al backend.

### Requisitos

*   Python 3.11 o superior, Node 18.18 o superior (se recomienda 22 LTS).
*   MySQL accesible por nombre de host (si `DB_ENGINE` no es `mysql`, la app usa SQLite local `nexus.db`).
*   Redis es opcional: si no responde, la app arranca igual.

### 1. Configuración (una sola vez)

```bash
cp .env.example .env    # completar los valores; .env nunca se versiona
```

Las variables y su significado están en [docs/configuracion/VARIABLES.md](docs/configuracion/VARIABLES.md).

### 2. Backend (terminal 1)

```bash
# instalación (una sola vez)
python3.11 -m venv venv
venv/bin/pip install -r requirements.txt

# iniciar en desarrollo
venv/bin/python run.py                     # API en http://localhost:5001

# o iniciar como en producción (sin modo debug)
venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5001 "run:app"
```

Comprobar que responde:

```bash
curl -s localhost:5001/api/v1/auth/context
```

> ⚠️ `run.py` arranca con `debug=True` y escucha en todas las interfaces. Úsalo
> solo en tu equipo; en cualquier servidor usa gunicorn (corrección pendiente
> en la tarea FNC-009).

### 3. Frontend (terminal 2)

```bash
cd frontend

# instalación (una sola vez)
npm ci

# iniciar en desarrollo (recarga en caliente)
npm run dev                                # interfaz en http://localhost:3000

# o compilar e iniciar como en producción
npm run build
npm run start
```

Comprobar que responde:

```bash
curl -s -o /dev/null -w '%{http_code}\n' localhost:3000/login   # espera 200
```

Abre `http://localhost:3000` en el navegador. El backend debe estar arriba
antes de iniciar sesión.

### 4. En el servidor (systemd)

Tras `deploy/install.sh` (ver abajo), los dos servicios quedan como unidades
systemd llamadas `NOMBRE-backend` y `NOMBRE-frontend` (`NOMBRE` es el valor de
`--name`, por defecto `nexus`):

```bash
sudo systemctl start   nexus-backend nexus-frontend    # iniciar
sudo systemctl stop    nexus-backend nexus-frontend    # detener
sudo systemctl restart nexus-backend nexus-frontend    # reiniciar
systemctl status       nexus-backend nexus-frontend    # estado
journalctl -u nexus-backend -f                          # logs del backend
journalctl -u nexus-frontend -f                         # logs del frontend
```

El frontend depende del backend: systemd arranca primero `nexus-backend`.

## 🚀 Instalación en servidor (Rocky Linux 8)

```bash
./deploy/preflight.sh          # evalúa el sistema, no modifica nada
sudo ./deploy/install.sh --domain nexus.example.com
```

`preflight.sh` comprueba distribución, recursos, Python, Node, cabeceras de
compilación, conectividad con la base de datos y Redis, puertos libres, nginx,
SELinux y firewalld. Sale con código 1 si hay algo que resolver antes.

`install.sh` instala los paquetes, crea el usuario de servicio, copia el
proyecto, monta el venv, construye el frontend, registra las dos unidades
systemd y configura nginx. Es idempotente. Opciones: `--prefix`, `--user`,
`--domain`, `--skip-packages`.

Detalles y notas de seguridad en [deploy/README.md](deploy/README.md).

## 📚 Documentación Adicional

*   [Reglas de Negocio](docs/business_rules.md): Lineamientos operativos y de diseño.
*   [Arquitectura Técnica](docs/ARCHITECTURE.md): Detalles sobre el flujo de datos y base de datos.
*   [Despliegue](deploy/README.md): Servicios systemd y reverse proxy.

## 🚧 Desarrollos Pendientes (Roadmap)

*   [ ] **Activación del Centro de Ayuda**: Habilitación visual de la documentación integrada para usuarios y administradores.

