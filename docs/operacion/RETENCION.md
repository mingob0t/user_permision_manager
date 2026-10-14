# Retención de datos

| Dato | Ejemplo | ¿Es dato personal? | Dónde se guarda | Retención | Cómo se elimina | Base legal / motivo |
|---|---|---|---|---|---|---|
| Logs de aplicación | | | `logs/` | | rotación | |
| Auditoría | correo e id del actor y del usuario afectado, IP, acción, área, plataforma, antes/después (JSON) | Sí | BD (`audit_logs`) | Por definir (FNC-018, §12 P3 de seguridad) | Solo por el proceso auditado de FNC-018; la app no borra ni edita (FNC-047) | No repudio (SEC-AUD-02, 03) |
| Cuentas de usuario | correo, nombre | Sí | BD | | | |

## Notas de la auditoría (FNC-047)
- Antes/después guarda datos personales (correo, nombre, rol, áreas); nunca contraseñas, hashes, tokens ni secretos (SEC-AUD-05).
- Borrar un usuario, área o plataforma no borra sus eventos: la referencia queda en NULL y el correo o nombre sigue en `user`/`target`.
- Índices por fecha, actor, usuario afectado, área y plataforma: la tabla crece sin tope hasta que FNC-018 defina la retención.
- Permisos de BD de solo INSERT/SELECT sobre `audit_logs` para el usuario de la app: pendiente de aprobación del dueño.

## Marco aplicable

Indicar la ley que aplica (en México, LFPDPPP), el aviso de privacidad y cómo se atienden las solicitudes de acceso, rectificación, cancelación u oposición (derechos ARCO).
