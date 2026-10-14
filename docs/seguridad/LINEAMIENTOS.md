# Lineamientos de seguridad (FNC-036)

Son reglas obligatorias para toda tarea y sirven de criterio de revisión para `revisor` y `auditor-seguridad`. Las reglas generales (sin secretos ni IPs, protección explícita, errores genéricos, variables registradas, pruebas mínimas) están en `~/.claude/agentes/LINEAMIENTOS.md` y no se repiten aquí. Una tarea que toque un módulo de la §11 corrige de paso sus hallazgos, con una prueba de regresión; si no, la corrección queda para la fase 5. El portal no se expone antes de cerrar la fase 5. *Por confirmar* remite a la §12. Origen: [auditoría inicial](auditorias/2026-10-13-auditoria-inicial.md).

## 1. Autenticación

| ID | Regla | Verificación | Origen |
|---|---|---|---|
| SEC-AUTH-01 | Aceptar `Remote-*` solo si el origen está en `TRUSTED_PROXIES` **y** llega un secreto compartido (de Vaultwarden, comparado con `hmac.compare_digest`) | Prueba sin secreto, con secreto erróneo y con IP ajena: 401 | SEG-04 |
| SEC-AUTH-02 | nginx borra `Remote-*` y el secreto en **cada** `location` (con `include`), y `/api` y `/auth` en cualquier combinación de mayúsculas nunca llegan a Next.js | Revisión de la plantilla y `curl` local a `/API/...` | SEG-04, 15 |
| SEC-AUTH-03 | Los rewrites de Next.js hacia la API existen solo en desarrollo | Revisión de `next.config.ts` | SEG-04 |
| SEC-AUTH-04 | El login local solo se acepta con `auth_source='local'`; las cuentas `ldap` y `sso` tienen `password_hash` NULL | Prueba y consulta SQL | SEG-02 |
| SEC-AUTH-05 | Sin contraseñas fijas, derivadas ni impresas en código, SQL, `utils/` ni semillas | `grep` y revisión | SEG-02, 03 |
| SEC-AUTH-06 | El primer superadmin se crea solo con un comando CLI interactivo, que falla si ya existe uno; `create_app()` no siembra usuarios | Prueba del comando | SEG-03 |
| SEC-AUTH-07 | Un solo `administrador`: ni SSO, ni LDAP, ni mapeos, ni respaldo, ni API lo asignan | Prueba por cada vía | SEG-10, 06, 17 |
| SEC-AUTH-08 | Un intento de login nunca crea, borra ni modifica cuentas | Prueba con un usuario inexistente | SEG-01 |
| SEC-AUTH-09 | Respuesta de login idéntica en todos los fallos; rechazar la contraseña vacía antes del bind | Prueba que compara las respuestas | SEG-12 |
| SEC-AUTH-10 | Límite de intentos por cuenta e IP, más estricto que el bloqueo de OpenLDAP (umbral *Por confirmar*) | Prueba: N+1 intentos dan 429 | SEG-11 |
| SEC-AUTH-11 | Una cuenta inactiva pierde la sesión en la siguiente petición | Prueba | SEG-14 |
| SEC-AUTH-12 | Contraseña local: hash scrypt o argon2, mínimo 12 caracteres (*Por confirmar*); solo la cambian el propio usuario o el superadmin | Prueba | SEG-05 |
| SEC-AUTH-13 | El logout invalida la sesión y redirige al SLO con URLs de la configuración, nunca con `Host` | Prueba | — |
| SEC-AUTH-14 | MFA de Authelia para el superadmin y los admins (*Por confirmar*) | Configuración documentada | — |

## 2. Autorización

| ID | Regla | Verificación | Origen |
|---|---|---|---|
| SEC-AUTHZ-01 | Toda ruta tiene un decorador de `authz.py` o figura en la lista de rutas públicas | Prueba de guardia sobre `url_map` | RNF-05 |
| SEC-AUTHZ-02 | La matriz del Anexo A tiene una prueba parametrizada por rol; un endpoint nuevo agrega su fila y su prueba | Prueba por matriz | RNF-05 |
| SEC-AUTHZ-03 | Los recursos con área se cargan con `scoped_*` o `can_*`, y el área se lee de la BD, nunca de la petición | Prueba: admin de X sobre Y da 404 | SEG-16 |
| SEC-AUTHZ-04 | Un recurso fuera de alcance responde 404; un rol insuficiente responde 403 | Prueba | — |
| SEC-AUTHZ-05 | Solo el superadmin crea, eleva o degrada admins y les asigna áreas | Prueba | SEG-09 |
| SEC-AUTHZ-06 | Un admin no gestiona a otros admins ni al superadmin, ni toca la contraseña de cuentas `ldap` o `sso` | Prueba con dos admins de áreas solapadas | SEG-05 |
| SEC-AUTHZ-07 | Un admin aprueba, rechaza y revoca solo en sus áreas | Prueba | RF-03 |
| SEC-AUTHZ-08 | Nadie aprueba su propia solicitud ni modifica sus propios accesos o rol | Prueba | — |
| SEC-AUTHZ-09 | El actor sale de la sesión; cada endpoint tiene una lista blanca de campos y rechaza `role`, `is_active`, `auth_source` y `password_hash` | Prueba de *mass assignment* | SEG-09 |
| SEC-AUTHZ-10 | Las solicitudes siguen una máquina de estados con control de concurrencia; el rechazo exige motivo | Prueba de doble aprobación | RF-06 |
| SEC-AUTHZ-11 | Purga, importación y bajas masivas: solo el superadmin, con confirmación explícita; la importación nunca da roles admin | Prueba | SEG-06, 17 |

## 3. OpenLDAP

| ID | Regla | Verificación | Origen |
|---|---|---|---|
| SEC-LDAP-01 | Un solo módulo usa `ldap3` | `grep ldap3 app/` | SEG-13 |
| SEC-LDAP-02 | LDAPS o StartTLS con `CERT_REQUIRED`, CA configurable y verificación del host; sin TLS válido la app no arranca | `grep CERT_NONE` da 0; prueba de arranque | SEG-13 |
| SEC-LDAP-03 | La cuenta de servicio de escritura solo puede cambiar la membresía bajo la OU de grupos de plataforma y crear entradas en la OU de personas (con ACL) | ACL documentada | SEG-08 |
| SEC-LDAP-04 | Antes de escribir, el código valida que el DN está bajo la OU (comparando RDN normalizados) y registrado en una plataforma | Prueba con DN fuera de la OU | — |
| SEC-LDAP-05 | Cambiar el DN de grupo de una plataforma: solo el superadmin (*Por confirmar*), con validación y auditoría | Prueba | — |
| SEC-LDAP-06 | Escapar filtros (`escape_filter_chars`) y DN (`escape_rdn`); nunca concatenar | Prueba con `*`, `)(`, `,`, `\` | SEG-12 |
| SEC-LDAP-07 | Solo se usa `MODIFY_ADD` o `MODIFY_DELETE` de un valor del atributo de membresía; nunca `REPLACE` ni atributos operativos | Doble que registra las operaciones | — |
| SEC-LDAP-08 | Escritura idempotente: un miembro existente o ausente cuenta como "sin cambios" | Prueba de doble ejecución | — |
| SEC-LDAP-09 | La contraseña inicial de una cuenta nueva nunca es fija, no se guarda y no se envía por correo (mecanismo *Por confirmar*) | Revisión | SEG-02 |
| SEC-LDAP-10 | El rol se deriva por DN exacto normalizado; el directorio nunca otorga `administrador` | Prueba con DN parecidos | SEG-10 |
| SEC-LDAP-11 | El bind sale del entorno o de Vaultwarden, nunca de la BD; la prueba de conexión usa solo el host configurado | `grep ldap_pass`; prueba | SEG-08, 22 |
| SEC-LDAP-12 | Tiempos de espera registrados; los errores van al log | Revisión | SEG-21 |

## 4. Conectores (API, SSH y BD)

| ID | Regla | Verificación | Origen |
|---|---|---|---|
| SEC-CON-01 | Todo conector implementa `otorgar`, `revocar` y `consultar` con un `id_operacion` y un resultado tipado | Prueba de contrato | — |
| SEC-CON-02 | La credencial sale solo de Vaultwarden y la BD guarda solo la referencia (mecanismo *Por confirmar*) | `grep` en los modelos | SEG-08 |
| SEC-CON-03 | El conector recibe solo datos del servidor (uid del directorio y nivel enumerado); nunca texto del usuario | Revisión de la firma | — |
| SEC-CON-04 | SSH: comandos fijos, parámetros validados con lista blanca y `shlex.quote`; sin `shell=True` ni `AutoAddPolicy`; `known_hosts` fijo | `grep`; prueba con `;` y `$()` | — |
| SEC-CON-05 | BD: consultas parametrizadas e identificadores validados con lista blanca; cuenta con mínimo privilegio y TLS | Prueba | — |
| SEC-CON-06 | API: TLS validado, sin `verify=False`, cuerpo en JSON y sin redirecciones a otros hosts | `grep verify=False` | — |
| SEC-CON-07 | Destino solo de una lista blanca de nombres de host definida en el despliegue; cambiar el host invalida la credencial | Prueba con un host ajeno | SEG-22 |
| SEC-CON-08 | Tiempos de espera; reintentos con *backoff* y *jitter* y un máximo registrado; sin reintentos en errores permanentes | Prueba con un doble | — |
| SEC-CON-09 | El acceso se marca otorgado o revocado solo tras confirmar el éxito; si falla, estado *fallido*, auditoría y correo | Prueba | — |
| SEC-CON-10 | Bitácora de ejecución sin secretos y con la salida truncada y filtrada | Prueba con un secreto ficticio | — |
| SEC-CON-11 | Solo el superadmin crea o modifica conectores | Matriz | — |

## 5. Sesión, CSRF, cabeceras y TLS

| ID | Regla | Verificación | Origen |
|---|---|---|---|
| SEC-SES-01 | La cookie lleva `Secure`, `HttpOnly` y `SameSite=Lax` explícitos | Prueba de `Set-Cookie` | SEG-06, 14 |
| SEC-SES-02 | Inactividad y duración absoluta registradas (30 min y 8 h provisionales), sin *remember* largo | Configuración | SEG-14 |
| SEC-SES-03 | `session.clear()` al iniciar sesión; `session_version` revoca las sesiones al cambiar rol, contraseña o estado | Prueba | SEG-14 |
| SEC-SES-04 | Todo método que cambia estado exige un token CSRF en cabecera y un `Origin` del mismo sitio; la API no queda exenta | Prueba sin token: 403 | SEG-06 |
| SEC-SES-05 | Los endpoints JSON solo aceptan `application/json` | Prueba: 415 | SEG-06 |
| SEC-SES-06 | Sin CORS; nunca `*` con credenciales | `grep` | — |
| SEC-SES-07 | nginx envía CSP con `frame-ancestors 'none'`, `nosniff`, `X-Frame-Options`, `Referrer-Policy` y HSTS | `curl -I` local | SEG-15 |
| SEC-SES-08 | Solo TLS 1.2 o 1.3; redirección de 80 a 443; servicios solo en loopback | Revisión | SEG-15 |
| SEC-SES-09 | Límites de cuerpo alineados en Flask y nginx; ZIP limitado por tamaño descomprimido | Prueba: 413 | SEG-29 |
| SEC-SES-10 | Las URL de plataformas aceptan solo `https://` | Prueba con `javascript:` | SEG-24 |

## 6. Secretos y configuración

| ID | Regla | Verificación | Origen |
|---|---|---|---|
| SEC-CFG-01 | La app no arranca sin `SECRET_KEY` fuerte, sin la BD, sin el secreto del proxy (con SSO) ni sin TLS de LDAP y SMTP fuera de dev | Prueba de arranque | SEG-07 |
| SEC-CFG-02 | Ningún secreto con valor por defecto en `getenv` | `grep` | SEG-07 |
| SEC-CFG-03 | En la BD no hay credenciales de servicio; las contraseñas de usuario se guardan solo como hash | Revisión de modelos | SEG-08 |
| SEC-CFG-04 | Exportaciones y respaldos sin hashes ni secretos | Prueba | SEG-17 |
| SEC-CFG-05 | Sin `debug` y con escucha en loopback por defecto; fuera de dev, debug impide arrancar | `grep debug=True` | SEG-18 |
| SEC-CFG-06 | Al cliente, un mensaje genérico con un id de correlación; `str(e)` solo va al log | `grep str(e` | SEG-12, 21 |
| SEC-CFG-07 | Los cambios a variables de seguridad (claves, proxies, TLS, hosts de conectores, sesión, límites) se registran en `HISTORIAL.md` con su motivo | Revisión | SEG-26 |
| SEC-CFG-08 | Redis con contraseña y en loopback | Prueba de arranque | SEG-29 |
| SEC-CFG-09 | La cuenta MySQL de la app tiene el mínimo privilegio; las migraciones usan otra cuenta | Script de permisos | — |

## 7. Auditoría

| ID | Regla | Verificación | Origen |
|---|---|---|---|
| SEC-AUD-01 | Se auditan: logins y fallos, bloqueos, cambios de usuario, rol o áreas, solicitudes, otorgar y revocar, conectores fallidos, configuración, DN de grupos, respaldo, purga, alta del superadmin y 403 de administración | Prueba por evento | — |
| SEC-AUD-02 | Cada registro guarda: fecha en UTC, id y correo del actor, acción enumerada, área y plataforma (columnas), antes y después, resultado e IP | Revisión del modelo | SEG-16, 25 |
| SEC-AUD-03 | Inmutable: sin rutas de edición ni borrado, la app sin `UPDATE`/`DELETE` en la tabla y sin cascada al borrar usuarios | Prueba y permisos de BD | — |
| SEC-AUD-04 | IP real con `ProxyFix` solo para el proxy de confianza; nginx sobrescribe `X-Forwarded-For` | Prueba con un XFF falso | SEG-25 |
| SEC-AUD-05 | Nunca se registran contraseñas, tokens, cookies, cabeceras completas ni secretos | Prueba | — |
| SEC-AUD-06 | Otorgar, revocar, aprobar o cambiar el rol se auditan en la misma transacción | Prueba de *rollback* | — |

## 8. Correo

| ID | Regla | Verificación | Origen |
|---|---|---|---|
| SEC-MAIL-01 | Los valores se escapan con `html.escape` en HTML y sin CR/LF en el asunto | Prueba con `<a>` y `\r\n` | SEG-23 |
| SEC-MAIL-02 | Sustitución con una lista blanca de claves; nunca `render_template_string` | `grep` | — |
| SEC-MAIL-03 | Los destinatarios salen del servidor, nunca de la petición | Revisión | — |
| SEC-MAIL-04 | La misma respuesta exista o no la cuenta (sin enumeración) | Prueba | SEG-12 |
| SEC-MAIL-05 | Los enlaces se construyen con `BASE_URL`; el correo no lleva contraseñas ni tokens largos | Prueba con un `Host` falso | SEG-26 |
| SEC-MAIL-06 | SMTP con TLS validado; `none` está prohibido fuera de dev | Configuración | — |

## 9. Datos personales y retención

| ID | Regla | Verificación | Origen |
|---|---|---|---|
| SEC-PRIV-01 | `RETENCION.md` se completa antes de exponer el portal y se actualiza con cada dato personal nuevo | Revisión | SEG-28 |
| SEC-PRIV-02 | Del directorio solo se guardan uid, correo, nombre y membresía | Revisión del mapeo | — |
| SEC-PRIV-03 | La retención de auditoría, logs y cuentas (*Por confirmar*) se aplica con un proceso auditado | Prueba | SEG-28 |
| SEC-PRIV-04 | La seudonimización está activa antes de usar datos reales; las pruebas usan solo datos ficticios | `validar_proyecto.py` | SEG-28 |

## 10. Dependencias

| ID | Regla | Verificación | Origen |
|---|---|---|---|
| SEC-DEP-01 | Versiones fijadas (`==` y `package-lock.json` con `npm ci`); sin paquetes sin uso | `grep` | SEG-27 |
| SEC-DEP-02 | Una dependencia nueva se justifica en la ficha y pasa por `auditor-seguridad` | Revisión | — |
| SEC-DEP-03 | `pip-audit` y `npm audit` en CI; un aviso Crítico o Alto bloquea el release | Salida de CI | SEG-19 |
| SEC-DEP-04 | Sin CDN; si se usa una, con versión fija y SRI | `grep` | — |

### Cierre de cada tarea
- [ ] Corregí de paso los hallazgos de la §11 en los módulos que toqué, con prueba de regresión.
- [ ] Cada endpoint nuevo o modificado tiene protección y su fila de la matriz con prueba por rol.
- [ ] El alcance por área y el actor salen del servidor; los campos van en lista blanca.
- [ ] Las escrituras exigen CSRF y `Origin`.
- [ ] Sin credenciales por defecto, secretos en la BD, `debug` ni `str(e)` al cliente.
- [ ] LDAP y conectores: TLS validado, escape, lista blanca de hosts e idempotencia.
- [ ] Los eventos quedan auditados sin datos sensibles y con la IP real.
- [ ] Correos escapados y con enlaces de `BASE_URL`.
- [ ] Variables de seguridad registradas, con su motivo en `HISTORIAL.md`.
- [ ] Veredicto de `auditor-seguridad` en modo cambio, si aplica.

## 11. Hallazgos abiertos por módulo

La fase 3 tocará casi todo el backend de esta tabla: es probable que FNC-002, 007, 008, 010, 012, 013 y 015 se adelanten.

| Módulo | SEG | FNC |
|---|---|---|
| `app/modules/auth/services.py` | 01, 12 / 13 / 10 / 21, 26 | 002 / 012 / 013 / 017 |
| `app/modules/api/auth.py` | 01, 12 / 02 / 04 / 10 / 11 / 14 | 002 / 003 / 006 / 013 / 014 / 008 |
| `app/__init__.py` | 03 / 06, 14 / 07 / 29 | 003 / 008 / 009 / 017 |
| `app/authz.py` | 05 | 007 |
| `app/modules/api/crud.py` | 02 / 05, 09 / 06 / 24 | 003 / 007 / 008 / 017 |
| `app/modules/api/admin.py` | 06 / 08, 17, 22 / 13 / 21, 29 | 008 / 010 / 012 / 017 |
| `auth/models.py`, `notifications/models.py` | 08 | 010 |
| `notifications/services.py` | 23 | 017 |
| `api/routes.py` (`/audit`), `audit/` | 16 (25 cerrado por FNC-047) | 060 (015 parcial) |
| `run.py` | 18 | 009 |
| `deploy/nginx.conf.tmpl` | 04, 15 / 29 | 004 / 017 |
| `frontend/next.config.ts` | 04 | 005 |
| `frontend/.../platform-card.tsx` | 24 | 017 |
| `requirements.txt`, `frontend/package.json` | 19, 27 | 016 |
| `utils/` (SQL, `emergency_reset`, `seed_users`) | 03 | 003 |
| `.env.example` | 10 / 26 | 013 / 017 |
| Historial de git (`24b12b5`) | 20 | 011 |
| `RETENCION.md`, `.claude/seudonimizacion.json` | 28 | 018 |

## 12. Preguntas para el dueño
No bloquean: cada una se decide en la fase indicada, al llegar la tarea que la necesita (decisión del dueño, 2026-10-13).
1. **[Fase 5]** ¿MFA para el superadmin y los admins? ¿Y para los usuarios?
2. **[Fase 5]** ¿Duración de la sesión (inactividad y absoluta)? ¿Se permite "recordarme"?
3. **[Fase 5]** ¿Retención de auditoría, logs, bitácora de conectores y cuentas? ¿Quién responde por el aviso de privacidad y los derechos ARCO?
4. **[Fase 5]** ¿Se conservan cuentas locales (solo la de emergencia del superadmin)? ¿Longitud mínima de contraseña?
5. **[Fase 5]** ¿Cómo se transfiere el superadmin o se recupera el acceso de emergencia?
6. **[Fase 3]** ¿Cómo se entrega la contraseña inicial de las cuentas creadas en OpenLDAP? ¿Hay `ppolicy`?
7. **[Fase 3]** ¿Qué convención de OpenLDAP se usa: OUs, atributo de membresía y atributos de las cuentas nuevas?
8. **[Fase 3]** ¿Quién define el DN de grupo de una plataforma? ¿Lo crea el portal?
9. **[Fase 3]** ¿Cuántas cuentas de servicio (lectura y escritura)? ¿Quién configura las ACL?
10. **[Fase 3]** ¿Las credenciales de conectores se cargan al desplegar o se consultan a Vaultwarden en tiempo de ejecución?
11. **[Fase 3]** ¿La lista blanca de hosts de conectores la fija el despliegue o la edita el superadmin?
12. **[Fase 3]** ¿Quién aprueba la solicitud del único admin de un área? ¿El superadmin se otorga accesos sin aprobación?
13. **[Fase 5]** ¿Umbral del límite de intentos y política de bloqueo actual de OpenLDAP?
14. **[Fase 5]** ¿HSTS con `includeSubDomains`?
15. **[Fase 5]** ¿La auditoría basta con permisos de BD, o se requiere cadena de hash o envío a un SIEM?
16. **[Fase 3]** ¿Qué cola de trabajos se usa para los conectores (se decide en un ADR)?

Resuelta y retirada: la 17 (baja de áreas por el admin): sí, sus áreas (dueño, 2026-10-14; P11 de FNC-037).

## Anexo A. Matriz de permisos
Los casos "sin sesión" siempre dan 401. "Ajena" significa un área que el admin no gestiona y responde 404.

| Acción | Usuario | Admin (sus áreas) | Admin (ajena) | Superadmin |
|---|---|---|---|---|
| Ver el catálogo y solicitar acceso | Sí | Ver | Sí | Ver |
| Aprobar, rechazar o revocar | No | Sí, salvo lo propio | No | Sí, salvo lo propio |
| Alta y edición de áreas y plataformas | No | Sí | No | Sí |
| Baja de áreas (409 con plataformas o accesos vigentes) | No | Sí | No | Sí |
| DN de grupos; conectores | No | No | No | Sí |
| Crear cuentas en OpenLDAP | No | Sí (para sus áreas) | No | Sí |
| Elevar o gestionar admins | No | No | No | Sí |
| Gestionar usuarios no admin | No | Sí (sin contraseña `ldap`/`sso`) | No | Sí |
| Ver usuarios e inventario | Los propios | Sí | No | Todo |
| Ver la auditoría | La propia | Área afectada | No | Todo |
| Configuración, respaldo y purga | No | No | No | Sí |
