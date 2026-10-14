> **OBSOLETO PARCIALMENTE (FNC-001, 2026-10-13).** Se conserva como referencia histórica; las reglas vigentes están en `docs/REQUERIMIENTOS.md` y el comportamiento real en `docs/backend/README.md`. Contradicciones con el código:
> - **"Desacoplamiento de componentes legados"** prohíbe crear rutas `/api/v1`: **ya no aplica**; toda la API actual vive en `/api/v1` (ADR-001).
> - **"Estandarización de contenedores"** (Docker obligatorio, MariaDB/Redis orquestados, `docker-compose.yml`): **no aplica**; no hay Docker en el repositorio y el despliegue es Rocky Linux 8 con systemd + nginx (`deploy/`), con MySQL como BD objetivo.
> - **"Gestión de contraseñas locales"**: el backend no exige contraseña en el alta; si no llega, asigna una por defecto (`POST /api/v1/users`).
> - **"Paginación maestra"** estilo DataTables: el frontend Next.js no implementa paginación en Usuarios, Áreas ni Plataformas (solo quedan las clases `.dt-*` en los estilos).
> - **"Integridad referencial"**: vigente, pero el mensaje real es "El área tiene N plataforma(s). Reasígnalas o elimínalas primero." (`409`), sin borrado múltiple.
> - **"Segregación de gestión de accesos"**: vigente (`PUT /api/v1/areas/<id>/users` separado de la edición del área).

# 📚 MOTOR DE REGLAS DE NEGOCIO — NEXUS PLATFORM

## Áreas y Plataformas

### Regla: Integridad Referencial
No se permite la eliminación de un área si existen plataformas o sistemas vinculados a ella. El sistema debe bloquear la operación y mostrar un error detallado.

### Ejemplo
Si el área "Infraestructura" tiene vinculada la plataforma "AWS", el administrador recibirá un mensaje: "No se pueden eliminar las siguientes áreas porque tienen plataformas vinculadas: Infraestructura".

### Impacto
Backend (API de Áreas), UI (Módulo de Áreas).

---

## Seguridad y Autenticación

### Regla: Gestión de Contraseñas Locales
Los usuarios creados mediante el flujo Local DEBEN tener una contraseña establecida en el momento del registro. Los usuarios LDAP no requieren este campo ya que la autenticación es externa.

### Ejemplo
Al registrar un usuario local, los campos "Password" y "Confirm Password" son obligatorios y deben coincidir. Al importar de LDAP, estos campos se ocultan automáticamente.

### Impacto
Frontend (Registration Modal), Backend (User Model).

---

## Interfaz de Usuario (UI)

### Regla: Paginación Maestra
La paginación en todos los módulos de gestión debe seguir el estándar de Auditoría (DataTables style), mostrando "Mostrando X-Y de Z registros" y controles simplificados.

### Ejemplo
El módulo de Áreas utiliza `dt-layout-row` para su footer de paginación, logrando paridad 1:1 con Auditoría.

### Impacto
Módulos de Usuarios, Áreas y Plataformas.
---

## Gestión de Ciclo de Vida del Sistema

### Regla: Desacoplamiento de Componentes Legados
Queda terminantemente prohibida la reintroducción de módulos relacionados con PSX5K, Worker Daemons o APIs tácticas v1. El sistema debe operar exclusivamente bajo la arquitectura de portal de gestión de identidades y accesos.

### Ejemplo
Cualquier intento de crear una ruta `/api/v1` o de importar servicios de ejecución de comandos remotos (SSH/Task Engines) será rechazado en la revisión arquitectónica.

### Impacto
Arquitectura Global, Documentación Técnica, Estructura de Base de Datos.

---

## Gestión Organizacional

### Regla: Segregación de Gestión de Accesos
La gestión de usuarios vinculados a un área debe realizarse de forma independiente a la modificación de los datos básicos del área (nombre, descripción, imagen). Esto garantiza que los cambios en la identidad visual o funcional no afecten accidentalmente los permisos de acceso.

### Ejemplo
Al modificar un área, el paso de selección de usuarios ya no está presente. Para gestionar quién tiene acceso, se utiliza el botón "Accesos" que abre un modal dedicado con una picklist de usuarios.

### Impacto
UI (Módulo de Áreas), Backend (API de Accesos).

---

## Infraestructura y Despliegue

### Regla: Estandarización de Contenedores
El despliegue de la plataforma debe realizarse obligatoriamente mediante Docker. El entorno productivo debe utilizar Gunicorn como servidor de aplicaciones y MariaDB/Redis como servicios externos orquestados.

### Ejemplo
El archivo `docker-compose.yml` define los servicios `app`, `db` y `redis`, asegurando que la aplicación sea portable y fácil de escalar.

### Impacto
DevOps, Proceso de Despliegue, CI/CD.

