# Reglas de Negocio

## Preferencias y Temas de Interfaz

### Regla
El sistema solo acepta tres temas de interfaz: `sistema` (por defecto), `claro` y `oscuro`. Cualquier intento de guardar un valor retirado o desconocido es rechazado con error 422.

### Ejemplo
Si un usuario envía `theme: "rosa"` en `PUT /api/v1/me/preferences`, la API devuelve un código de error 422 indicando que debe elegir un tema válido de la lista.

### Impacto
Afecta a la API de preferencias de usuario (`/api/v1/me/preferences`), migración de base de datos `pref_theme` y selector de tema en la interfaz web.
