# Reglas de Negocio

## Preferencias y Temas de Interfaz

### Regla

El sistema solo acepta tres temas de interfaz: `sistema` (por defecto), `claro` y `oscuro`. Cualquier intento de guardar un valor retirado o desconocido es rechazado con error 422.

### Ejemplo

Si un usuario envía `theme: "rosa"` en `PUT /api/v1/me/preferences`, la API devuelve un código de error 422 indicando que debe elegir un tema válido de la lista.

### Impacto

Afecta a la API de preferencias de usuario (`/api/v1/me/preferences`), migración de base de datos `pref_theme` y selector de tema en la interfaz web.

## Identidad y Marca del Portal

### Regla

La identidad visual y nomenclatura del sistema debe utilizar la denominación "Portal" o "Portal de accesos", prescindiendo por completo de la denominación anterior "Nexus" en títulos, valores por defecto de configuración, componentes de marca y correos de notificación.

### Ejemplo

Al acceder al sistema sin configuración previa guardada en `system_config`, el nombre por defecto retornado por `/api/v1/settings` y mostrado en la interfaz es "Portal de accesos" (no "Nexus Core AI"), la pantalla de inicio de sesión titula "Portal de accesos", y las notificaciones por correo salen firmadas como "Portal".

### Impacto

Afecta a `app/modules/settings/valores_por_defecto.py`, `app/modules/notifications/services.py`, encabezados en `frontend/src/app/layout.tsx`, componente `Brand`, pantalla de login y descargas de respaldo.

## Plataformas y Áreas

### Regla

En la vista detallada de plataformas de un área (`/admin/platforms`), la barra de herramientas ubica el indicador del área activa inmediatamente después del buscador de plataformas (orden: Botón Volver -> Buscador -> Insignia del Área). Asimismo, a la derecha de la barra de herramientas se integran las acciones contextuales de administración del área activa: botón "Accesos" (disponible para superadministradores para gestionar los administradores delegados mediante modal), botón "Editar" (para editar los datos del área) y botón "Eliminar" (con diálogo de confirmación y retorno automático al catálogo general tras eliminar), finalizando con un separador vertical y el botón "Nuevo" para la creación de plataformas en dicha área.

### Ejemplo

Al hacer click en la tarjeta del área "Demo Finanzas", la barra superior muestra a la izquierda el botón de retorno "Áreas", el campo de búsqueda de plataformas y a su derecha la insignia de "Demo Finanzas". A la derecha de la barra se muestran los botones "Accesos", "Editar", "Eliminar", un separador y el botón "Nuevo".

### Impacto

Afecta a [frontend/src/components/platform-admin.tsx](../frontend/src/components/platform-admin.tsx) y a la suite de pruebas en [frontend/tests/components/platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Botones de Barra de Herramientas en Plataformas

### Regla

Los botones de acción en la barra de herramientas de la vista de plataformas siguen estrictamente la nomenclatura, diseño y orden estándar del sistema: `ADMINS` (icono usuarios), `EDITAR` (icono editar), `ELIMINAR` (icono eliminar, en variante neutra `fila` para simetría visual con los demás botones de acción secundaria), seguidos del separador vertical `|` y el botón primario `+ NUEVO` (icono más, variante `fila-primario`).

### Ejemplo

En la vista de plataformas del área seleccionada, el bloque de botones a la derecha muestra en orden y con tipografía en mayúsculas: `ADMINS`, `EDITAR`, `ELIMINAR`, la línea divisoria vertical y `+ NUEVO`.

### Impacto

Afecta a [frontend/src/components/platform-admin.tsx](../frontend/src/components/platform-admin.tsx) y pruebas en [frontend/tests/components/platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Formulario Asistido de Creación y Edición de Áreas

### Regla

El modal de creación y edición de áreas (`AreaForm`) opera como un asistente estructurado de 2 pasos secuenciales:

- **Paso 1 (Descripción)**: Captura y valida el nombre obligatorio del área y su descripción funcional. Contiene las acciones de pie "Cancelar" y "Siguiente".
- **Paso 2 (Estilo visual)**: Permite configurar el color del área mediante selector, ofrece una vista previa interactiva en tiempo real (mostrando el chip con las iniciales teñidas dinámicamente, nombre, descripción y badge de estado) y el control de activación ("Activa"). Contiene las acciones de pie "Atrás" y "Guardar".

### Ejemplo

Al hacer click en "Nuevo" o "Editar área", el modal inicia en el paso 1 "Descripción". El usuario ingresa el nombre "Marketing" y descripción; al pulsar "Siguiente", avanza al paso 2 "Estilo visual" donde visualiza en vivo la tarjeta previa con el chip "MA" y puede ajustar el color o estado antes de presionar "Guardar".

### Impacto

Afecta a [frontend/src/components/areas/area-form.tsx](../frontend/src/components/areas/area-form.tsx), [frontend/src/components/areas-list.tsx](../frontend/src/components/areas-list.tsx) y pruebas en [frontend/tests/components/areas-list.test.tsx](../frontend/tests/components/areas-list.test.tsx).

## Estandarización de Radio de Borde en Modales y Botones

### Regla

Para garantizar consistencia visual y armonía en la jerarquía geométrica del sistema:

1. **Modales y Diálogos**: El panel contenedor de los modales (`Modal`) y diálogos de alerta (`AlertDialog`) adopta un radio de borde idéntico al de los contenedores estándar del sistema (`rounded-xl` / 12px / 0.75rem), eliminando el exceso de curvatura (`rounded-3xl` / 24px).
2. **Botones de Modales y Sistema**: Los botones de acción (`Button`, `.nexus-btn`) estandarizan su radio de borde en base al design token de radio de control `var(--radius-base, 8px)` (8px), evitando apariencias de cápsula o redondeo excesivo (`border-radius: 1rem` / 16px) y alineándose con los botones de fila, tarjetas y barras de herramientas.
3. **Contenedores Internos**: Componentes internos a los modales (steppers, indicadores de progreso, cajas de aviso) limitan su radio a `rounded-xl` o `rounded-lg` para respetar la jerarquía contenida respecto al panel principal.

### Ejemplo

Al abrir el modal de "Nueva área" o un diálogo de confirmación, la ventana modal presenta esquinas con radio uniforme de 12px (`rounded-xl`), igual al de las tarjetas del catálogo. Los botones inferiores "Cancelar", "Atrás", "Siguiente" o "Guardar" lucen esquinas de 8px (`var(--radius-base)`), consistentes y simétricas, sin deformación tipo píldora.

### Impacto

Afecta a [frontend/src/components/form.tsx](../frontend/src/components/form.tsx), [frontend/src/components/alert-dialog.tsx](../frontend/src/components/alert-dialog.tsx), [frontend/src/styles/components.css](../frontend/src/styles/components.css), [frontend/src/components/areas/area-form.tsx](../frontend/src/components/areas/area-form.tsx) y [frontend/src/components/users/directory-account-form.tsx](../frontend/src/components/users/directory-account-form.tsx).

## Asistente de 2 Pasos en Modales de Creación y Edición (Plataforma y Área)

### Regla

Los modales de creación y edición tanto de **Área** (`AreaForm`) como de **Plataforma** (`PlatformForm`) operan bajo un flujo unificado y secuencial de dos pasos claros y delimitados:

1. **Paso 1 (1. Descripción)**:
   - Captura la información funcional obligatoria y de configuración:
     - En Áreas: Nombre (obligatorio) y Descripción (opcional).
     - En Plataformas: Nombre (obligatorio), Descripción (obligatoria), Enlace directo https:// (opcional), Área asignada (obligatoria) y Configuración de Integración (manual o LDAP/AD con grupos de nivel usuario y admin según el rol del usuario).
   - Botones de pie: "Cancelar" (a la izquierda) y "Siguiente" (a la derecha).
   - Al pulsar "Siguiente" o presionar Enter, se validan los campos de este paso antes de avanzar.
2. **Paso 2 (2. Estilo)**:
   - Permite personalizar la apariencia visual y estado operativo:
     - En Áreas: Color personalizado del área, Vista previa en vivo con chip de iniciales dinámicas y estado Activa/Inactiva.
     - En Plataformas: Color de fondo y Color de texto (mediante `ColorInput` con altura táctil accesible de 48px), Vista previa en vivo de la tarjeta con chip sólido, nombre, descripción, área y badge de estado, y checkbox de activación ("Activa").
   - Botones de pie: "Atrás" (a la izquierda, para regresar al Paso 1 conservando datos) y "Guardar" (a la derecha, para persistir los cambios).

### Ejemplo

Al pulsar "+ Nuevo" en la sección de plataformas, se abre el modal "Nueva plataforma" posicionado en el paso "1. Descripción". El usuario introduce nombre, descripción y tipo de integración. Al pulsar "Siguiente", el modal transiciona al paso "2. Estilo", donde visualiza una tarjeta simulada interactiva que reacciona a los colores de fondo y texto elegidos antes de presionar "Guardar".

### Impacto

Afecta a [frontend/src/components/platforms/platform-form.tsx](../frontend/src/components/platforms/platform-form.tsx), [frontend/src/components/areas/area-form.tsx](../frontend/src/components/areas/area-form.tsx), [frontend/tests/components/platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx) y [frontend/tests/components/areas-list.test.tsx](../frontend/tests/components/areas-list.test.tsx).

Simplificación del Modal de Nueva Plataforma (Omisión de Área y Conector)

## Plataformas

### Regla

En el modal de creación de una nueva plataforma (`PlatformForm`, modo alta `!isEdit`), se omiten del formulario los campos y selectores de **Área** y de **Integración/Conector**:

1. **Área**: Dado que la creación de plataformas ocurre de forma contextual dentro del área seleccionada actualmente (`defaultAreaId`), el formulario asocia automáticamente la plataforma a dicha área sin necesidad de mostrar un selector redundante en pantalla. El nombre del área se refleja en la vista previa del Paso 2.
2. **Integración/Conector**: En el alta de nueva plataforma no se solicitan campos de conector ni configuración de grupos del directorio (LDAP), estableciendo por omisión el tipo de integración `conector` en el payload (`POST /platforms`) para permitir el alta limpia sin dependencias de infraestructura ni configuraciones previas de directorio. La configuración avanzada de conectores e integraciones se administra posteriormente o en la edición por administradores autorizados.
3. El Paso 1 del modal "Nueva plataforma" queda enfocado exclusivamente en la identidad funcional esencial: Nombre, Descripción y Enlace https:// opcional.

### Ejemplo

Al acceder al área "Demo Finanzas" y pulsar "+ NUEVO", el modal "Nueva plataforma" muestra en el Paso 1 únicamente los campos "Nombre", "Descripción" y "Enlace". No se muestra el selector de área ni la sección de integración/conector. Al pulsar "Siguiente", el Paso 2 muestra los colores y la tarjeta de vista previa con la insignia del área "Demo Finanzas". Al guardar, la plataforma se registra exitosamente asignada a "Demo Finanzas" con `integration_type: 'conector'`.

### Impacto

Afecta a [platform-form.tsx](../frontend/src/components/platforms/platform-form.tsx), [platform-payload.ts](../frontend/src/components/platforms/platform-payload.ts) y [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Selección por Checkbox y Notificaciones Toast en Tabla de Plataformas

### Regla

1. **Eliminación de Botones de Fila**: En la tabla de plataformas de un área (`/admin/platforms`), se suprimen los botones de acción por fila (anterior columna "Acciones" con botones de historial, edición y eliminación).
2. **Selección por Checkbox al Inicio**: En su lugar, la tabla inicia con una columna de selección por casilla de verificación (`nexus-checkbox`), permitiendo seleccionar una o todas las plataformas visibles mediante el checkbox maestro del encabezado (`aria-label="Seleccionar todas las plataformas"`) o la casilla de cada fila (`aria-label="Seleccionar {nombre}"`), así como mediante el clic directo sobre cualquier punto de la fila.
3. **Acciones Contextuales en Barra de Herramientas**:
   - Cuando no hay plataformas seleccionadas, los botones `EDITAR` y `ELIMINAR` de la barra de herramientas actúan sobre el área activa.
   - Cuando se selecciona exactamente una plataforma, los botones `EDITAR` y `ELIMINAR` de la barra de herramientas se vinculan a dicha plataforma para permitir su edición o eliminación.
   - Si se seleccionan múltiples plataformas, se muestra un contador badge (`{n} plataformas seleccionadas`) y los botones de edición/eliminación se deshabilitan preventivamente.
4. **Notificaciones Flotantes (Toast)**: Se suprimen de manera definitiva los banners informativos fijos en la parte superior del contenedor (`PlatformSaveNotice`, `<ErrorNote>` superior). Toda confirmación de guardado, retiro o advertencia operativa se emite exclusivamente a través del sistema de notificaciones flotantes `useToast` (`avisar(tono, mensaje, titulo)`), garantizando una interfaz despejada y accesible con regiones vivas WCAG (`role="status"` y `role="alert"`).

### Ejemplo

Al visualizar las plataformas de "Demo Finanzas", cada fila inicia con un checkbox y ya no existe la columna "Acciones" al final. Al marcar el checkbox de la plataforma "asd", los botones "EDITAR" y "ELIMINAR" de la barra superior cambian su foco a "asd". Al editar y guardar, no aparece ninguna barra superior en la página, sino un toast flotante en la esquina inferior derecha confirmando "Se guardó «asd»".

### Impacto

Afecta a [platform-columns.tsx](../frontend/src/components/platforms/platform-columns.tsx), [platform-admin.tsx](../frontend/src/components/platform-admin.tsx) y la suite de pruebas [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Normalización Automática del Protocolo en Enlaces de Plataformas

### Regla

En los formularios de creación y edición de plataformas (`PlatformForm`), el campo de enlace directo no obliga al usuario a escribir manualmente el prefijo `https://`:

1. **Normalización Inteligente**: Si el usuario introduce un dominio, dirección o ruta omitiendo el protocolo (por ejemplo `google.com`, `localhost:3000`, `sistema.empresa.local/panel`), el sistema le antepone automáticamente `https://` al desenfocar el campo (`onBlur`), al avanzar de paso y al guardar.
2. **Prevención de Errores Innecesarios**: La validación previa en cliente (`validate`) y la construcción del payload (`buildPayload`) normalizan la entrada antes de evaluar la seguridad del enlace (`enlaceSeguro`), evitando que se arroje el error `"Usa una dirección https://."` por el simple hecho de haber omitido el protocolo.
3. **Seguridad Preservada**: Esquemas explícitamente inseguros o no autorizados (como `http://`, `javascript:`, `mailto:`, `data:`, `file:`) no se transforman silenciosamente, manteniéndose la protección para que sean rechazados conforme a las políticas de seguridad.
4. **Claridad en la Interfaz**: El marcador de posición se actualiza a `ejemplo.com o https://ejemplo.com` y la pista textual especifica que `https://` se añade automáticamente si se omite.

### Ejemplo

Al crear una plataforma llamada "ERP" y escribir simplemente `erp.empresa.local` en el campo Enlace, el usuario puede presionar directamente "Siguiente" o "Guardar" sin recibir ningún mensaje de error. El enlace se almacena y se envía al backend como `https://erp.empresa.local`.

### Impacto

Afecta a [platform-payload.ts](../frontend/src/components/platforms/platform-payload.ts), [platform-form.tsx](../frontend/src/components/platforms/platform-form.tsx) y pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Reglas de Activación y Desactivación de Botones en la Tabla de Plataformas

### Regla

1. **Regla de Selección Estricta en Toolbar**: En la vista de tabla de plataformas de un área (`/admin/platforms`), los botones de acción situados en la barra de herramientas a la izquierda del separador vertical (`ADMINS`, `EDITAR`, `ELIMINAR`) deben obedecer de forma uniforme las mismas reglas de activación y desactivación vigentes en los módulos de Usuarios (`users-list.tsx`) y Áreas (`areas-list.tsx`):
   - **0 filas seleccionadas**: Los botones `ADMINS`, `EDITAR` y `ELIMINAR` permanecen inactivos/deshabilitados (`disabled={true}`, con clases visuales de estado deshabilitado en gris tenue). Sus tooltips y atributos `title` indican claramente al usuario la acción requerida: `"Selecciona 1 plataforma para ver administradores"`, `"Selecciona 1 plataforma para editar"` y `"Selecciona 1 plataforma para eliminar"`.
   - **1 fila seleccionada**: Los botones se habilitan automáticamente (`disabled={false}`). `EDITAR` y `ELIMINAR` operan sobre la plataforma seleccionada (con `aria-label` y `title` contextuales: `"Editar {nombre}"`, `"Eliminar {nombre}"`). `ADMINS` permite abrir el panel de administradores del área activa. `ELIMINAR` utiliza la variante visual destructiva estándar `variant="fila-peligro"`.
   - **Más de 1 fila seleccionada**: `ADMINS` y `EDITAR` se deshabilitan (`"Solo se puede editar 1 plataforma a la vez"`); `ELIMINAR` sigue activo para el borrado en lote (ver "Eliminación en Lote para Selección Múltiple de Áreas y Plataformas").
2. **Consistencia Visual con el Botón Nuevo**: El botón `+ NUEVO` permanece ubicado a la derecha del separador vertical `|` como acción de creación primaria independiente de la selección (`variant="fila-primario"`), siempre disponible salvo durante la carga inicial o si no existen áreas disponibles.

### Ejemplo

Al acceder a "Demo Finanzas" con 0 plataformas marcadas, los botones `ADMINS`, `EDITAR` y `ELIMINAR` se muestran en gris tenue y no permiten clic (deshabilitados), mientras que `+ NUEVO` permanece activo en azul primario. Al marcar la casilla de la plataforma "Contabilidad", los tres botones se iluminan y se vuelven interactivos, mostrando "Editar Contabilidad" y "Eliminar Contabilidad". Al desmarcarla o marcar más de una, los botones regresan inmediatamente a su estado deshabilitado.

### Impacto

Afecta a [platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [areas-list.tsx](../frontend/src/components/areas-list.tsx), [users-list.tsx](../frontend/src/components/users-list.tsx) y a las pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Simplificación de los Asistentes de Plataformas (Eliminación de Área e Integración en Alta y Edición)

### Regla

1. **Flujo de 2 Pasos Estricto y Simplificado**: Tanto el modal de creación ("Nueva plataforma") como el de edición ("Editar plataforma") operan bajo un flujo unificado y conciso de exactamente dos pasos:
   - **Paso 1: Descripción**: Contiene exclusivamente los campos esenciales de la plataforma: Nombre (`name`), Descripción (`description`) y Enlace directo (`direct_link`). Se eliminan por completo los selectores y configuraciones de "Área" y de "Integración" (conector o LDAP).
   - **Paso 2: Estilo**: Permite configurar el Color de fondo (`bg_color`), Color de texto (`text_color`), visualización de la tarjeta en la Vista previa en tiempo real (mostrando el badge del área activa a la que pertenece) y el interruptor de Estado Activo/Inactivo (`status`).
2. **Contexto Automático del Área**:
   - En el alta, la plataforma se vincula de manera automática al área seleccionada en la vista (`selectedArea.id`), aplicando el tipo de integración por omisión (`conector`).
   - En la edición, la plataforma conserva inmutable su `area_id` y su `integration_type` original, actualizando únicamente su identidad descriptiva, enlace y atributos de estilo visual.

### Ejemplo

Al seleccionar una plataforma en la tabla y presionar el botón "EDITAR", se abre el diálogo "Editar plataforma" mostrando en el Paso 1 únicamente los campos Nombre, Descripción y Enlace (sin el selector desplegable de Área ni la sección de Integración). El usuario puede modificar el nombre o enlace, presionar "Siguiente" para ajustar los colores o estado en el Paso 2, y guardar de inmediato sin fricción ni validaciones accesorias de directorio o conector.

### Impacto

Afecta a [platform-form.tsx](../frontend/src/components/platforms/platform-form.tsx), [platform-admin.tsx](../frontend/src/components/platform-admin.tsx) y la suite de pruebas [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Botón de Accesos en la Tabla de Plataformas (Gestión de Accesos por Plataforma)

### Regla

1. **Sustitución de Botón Admins por Accesos**: En la vista de tabla de plataformas de un área (`/admin/platforms`), el botón de acción anteriormente denominado `ADMINS` se sustituye de forma permanente por `ACCESOS` (`Icono nombre="solicitudes"`), disponible para administradores de área y superadministradores (`canManage`).
2. **Reglas de Selección y Activación**:
   - **0 plataformas seleccionadas**: El botón permanece deshabilitado (`disabled={true}`), con `title="Selecciona 1 plataforma para gestionar accesos"` y `aria-label="Accesos"`.
   - **1 plataforma seleccionada**: Se habilita (`disabled={false}`), con `title="Accesos de {nombre_plataforma}"` y `aria-label="Accesos de {nombre_plataforma}"`.
   - **Más de 1 plataforma seleccionada**: Se deshabilita preventivamente (`disabled={true}`), con `title="Solo se pueden gestionar accesos de 1 plataforma a la vez"`.
3. **Panel Modal de Gestión de Accesos (`PlatformAccessPanel`)**:
   - Al pulsar el botón `ACCESOS` con una plataforma seleccionada, se abre el diálogo modal "Accesos — {nombre_plataforma}".
   - Lista los usuarios pertenecientes al área de la plataforma, indicando mediante casillas de verificación interactivas (`Checkbox`) quiénes cuentan con acceso vigente y su estado (`Activo`).
   - **Dar acceso**: Marcar la casilla de un usuario sin acceso programa el alta; al guardar, se invoca `POST /api/v1/platforms/{id}/access`, encolando el aprovisionamiento correspondiente y registrando la auditoría.
   - **Quitar acceso**: Desmarcar la casilla de un usuario con acceso vigente programa su revocación; antes de aplicar el cambio, el sistema solicita confirmación mediante un diálogo explicativo (`ConfirmDialog`) y, al confirmar, se invoca `POST /api/v1/access/{id}/revoke`.
   - Incluye buscador rápido por nombre o correo, región viva WCAG (`role="status"`) y notificación Toast al completar los cambios.

### Ejemplo

Al seleccionar la plataforma "Contabilidad" dentro del área "Finanzas" y hacer clic en el botón "ACCESOS" de la barra de herramientas, se abre el panel modal "Accesos — Contabilidad". Si la usuaria "Ana López" no tiene acceso, el administrador marca su casilla y presiona "Guardar", otorgándole acceso inmediatamente. Si el usuario "Carlos Ruiz" ya tiene acceso y se desmarca su casilla, el sistema solicita confirmación ("¿Deseas retirar el acceso?") y al confirmar ejecuta la revocación formal.

### Impacto

Afecta a [platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [platform-access-panel.tsx](../frontend/src/components/platforms/platform-access-panel.tsx), [api.ts](../frontend/src/lib/api.ts), [api.py](../app/modules/access/api.py) y las suites de pruebas [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx) y [platform-access-panel.test.tsx](../frontend/tests/components/platform-access-panel.test.tsx).

## Dual Picklist en la Gestión de Accesos por Plataforma

### Regla

1. **Estructura de Doble Columna (Dual Picklist - DIS-019)**:
   - El modal de gestión de accesos por plataforma (`PlatformAccessPanel`) organiza a los usuarios del área en dos listas interactivas claramente diferenciadas:
     - **Columna Izquierda ("Sin acceso")**: Contiene a los miembros del área que no tienen acceso otorgado a la plataforma seleccionada. Cuenta con buscador propio, contador de usuarios disponibles y acción rápida "Todos +".
     - **Columna Derecha ("Con acceso")**: Contiene a los miembros del área autorizados con acceso activo a la plataforma. Cuenta con buscador propio, contador de usuarios asignados y acción rápida "Todos ✕".
2. **Interacción y Transferencia**:
   - Transferencia ágil con un solo clic: al pulsar sobre un usuario en la columna "Sin acceso", este se transfiere de inmediato a la columna "Con acceso" con la insignia visual `Nuevo`.
   - Al pulsar sobre un usuario en la columna "Con acceso", este se transfiere de vuelta a la columna "Sin acceso".
3. **Persistencia y Confirmación de Seguridad**:
   - Los cambios permanecen en estado pendiente hasta presionar el botón "Guardar".
   - Si se detectan revocaciones de accesos previamente vigentes (`aRevocar > 0`), se despliega un diálogo de confirmación de seguridad (`ConfirmDialog`) antes de ejecutar las revocaciones mediante `POST /api/v1/access/{id}/revoke`.
   - Las nuevas asignaciones se procesan vía `POST /api/v1/platforms/{id}/access`, notificando mediante Toast reactivo.

### Ejemplo

Al abrir el modal "Accesos — Contabilidad", en el lado izquierdo aparecen los usuarios de Finanzas que no cuentan con cuenta o permisos en Contabilidad, y en el lado derecho aquellos que ya están autorizados. El administrador puede hacer clic sobre "Ana López" en la izquierda para moverla a la derecha ("Con acceso"). Luego pulsa "Guardar" para consolidar el otorgamiento. Si traslada a "Carlos Ruiz" de la derecha a la izquierda y presiona "Guardar", el sistema despliega el diálogo "Revocar accesos" solicitando confirmación explícita para evitar revocaciones accidentales.

### Impacto

Afecta a [platform-access-panel.tsx](../frontend/src/components/platforms/platform-access-panel.tsx), [form.tsx](../frontend/src/components/form.tsx) y la suite de pruebas [platform-access-panel.test.tsx](../frontend/tests/components/platform-access-panel.test.tsx).

## Cierre Automático del Modal de Accesos tras Guardar

### Regla

Al completar exitosamente el guardado de los cambios en el modal de accesos por plataforma (`PlatformAccessPanel`), el sistema debe emitir la notificación Toast reactiva y cerrar de inmediato el diálogo modal invocando `onClose()`, devolviendo el foco de forma accesible al disparador en la barra de herramientas y evitando que el usuario deba presionar manualmente el botón "Cerrar".

### Ejemplo

El administrador transfiere a "Ana López" a la columna "Con acceso" y presiona "Guardar". Una vez que la API confirma el otorgamiento del acceso, se muestra el Toast de éxito y el modal se cierra automáticamente, regresando a la tabla de plataformas.

### Impacto

Afecta a [platform-access-panel.tsx](../frontend/src/components/platforms/platform-access-panel.tsx) y [platform-access-panel.test.tsx](../frontend/tests/components/platform-access-panel.test.tsx).

## Guardado Directo Sin Diálogo de Confirmación en Dual Picklist de Accesos

### Regla

En el modal de gestión de accesos por plataforma (`PlatformAccessPanel`), la transferencia de un usuario hacia la columna "Sin acceso" (quitar acceso) no debe requerir un diálogo secundario de confirmación (`ConfirmDialog`). Al presionar el botón "Guardar", todas las modificaciones (tanto otorgamientos como revocaciones) se ejecutan de manera directa y atómica, emitiendo de inmediato la notificación Toast de confirmación correspondiente y cerrando el modal.

### Ejemplo

El administrador traslada a un usuario de la columna "Con acceso" a "Sin acceso" y hace clic en "Guardar". El sistema procesa la revocación inmediatamente sin mostrar ninguna ventana emergente adicional, muestra la notificación Toast "Acceso retirado para «Contabilidad»." y cierra el modal devolviendo el foco a la tabla.

### Impacto

Afecta a [platform-access-panel.tsx](../frontend/src/components/platforms/platform-access-panel.tsx) y [platform-access-panel.test.tsx](../frontend/tests/components/platform-access-panel.test.tsx).

## Notificaciones Exclusivas vía Toast en Gestión de Accesos

### Regla

En el modal de administración de accesos por plataforma (`PlatformAccessPanel`), todos los mensajes informativos, de confirmación y de error derivados de las operaciones de otorgar o revocar accesos deben comunicarse exclusivamente mediante el sistema global de notificaciones Toast (`useToast`). Queda prohibido renderizar notas de error o badges de confirmación como elementos de contenido inline dentro del cuerpo del modal, garantizando que el diseño del modal permanezca limpio, estable y sin desplazamientos de layout.

### Ejemplo

Cuando ocurre un error o se completa exitosamente el guardado de accesos, el sistema despacha `avisar('error', ...)` o `avisar('success', ...)`. Ningún bloque `<ErrorNote>` o `<Badge>` aparece dentro del modal.

### Impacto

Afecta a [platform-access-panel.tsx](../frontend/src/components/platforms/platform-access-panel.tsx) y [platform-access-panel.test.tsx](../frontend/tests/components/platform-access-panel.test.tsx).

## Auto-cierre Universal de Notificaciones Toast

### Regla

Todos los avisos y notificaciones mostrados a través del proveedor Toast (`ToastProvider`), incluidos los de tono error, advertencia, éxito e información, deben cerrarse automáticamente al transcurrir el tiempo definido (`TOAST_MS`). Cada notificación incorpora una barra de progreso regresivo y soporta pausa interactiva mientras el cursor (ratón) o el foco por teclado se encuentren sobre la tarjeta (WCAG 2.2.1), reanudando el temporizador al salir.

### Ejemplo

Al producirse un error en una operación, se despliega una tarjeta Toast roja en la esquina inferior derecha con su barra de progreso. El usuario puede leerla y, si no interactúa con ella, se disipa automáticamente tras 6 segundos sin requerir que haga clic en el botón de cerrar.

### Impacto

Afecta a [toast.tsx](../frontend/src/components/toast.tsx) y [componentes-comunes.test.tsx](../frontend/tests/components/componentes-comunes.test.tsx).

## Gestión Directa de Accesos en Plataformas sin Conector Automatizado

### Regla

En plataformas que no cuentan con un conector externo activo ni integración LDAP (`sin_conector`), las operaciones de asignación y revocación directa ejecutadas por administradores deben resolverse de forma síncrona e inmediata. Al otorgar acceso, el registro se establece directamente en estado `activo` (sin quedar bloqueado en `en_proceso`); al revocar acceso, el registro pasa directamente a `revocado` (liberando de inmediato el slot vigente sin requerir un worker de aprovisionamiento en segundo plano ni arrojar 409 por estados no sincronizados).

### Ejemplo

Un administrador ingresa a los accesos de la plataforma "qw" (sin conector), mueve a "Usuario Demo 2" a la columna "Con acceso" y guarda: el acceso queda inmediatamente en estado "activo". Al retirarlo y guardar, el acceso se revoca de inmediato sin error de "Solo se revoca un acceso activo".

### Impacto

Afecta a [api.py](../app/modules/access/api.py) y [test_platform_access_api.py](../tests/access/test_platform_access_api.py).

## Configuración de Duración a 8 Segundos en Auto-cierre Toast

### Regla

El temporizador global de auto-cierre para todas las notificaciones Toast (`TOAST_MS`) queda establecido en 8 segundos (8000 ms), sincronizando la animación CSS de la barra regresiva (`.nx-toast-progress`) a 8 segundos. Toda notificación (éxito, error, advertencia e información) permanece visible durante este intervalo completo, manteniendo el soporte de pausa al recibir cursor o foco accesible y reanudando al perderlos.

### Ejemplo

Al guardar o retirar un acceso, el aviso Toast generado se muestra durante 8 segundos completos mientras su barra de progreso disminuye suavemente, desapareciendo de forma automática si el usuario no interactúa con él.

### Impacto

Afecta a [toast.tsx](../frontend/src/components/toast.tsx), [components.css](../frontend/src/styles/components.css) y [componentes-comunes.test.tsx](../frontend/tests/components/componentes-comunes.test.tsx).

## Optimización de Navegación: Caché en Memoria y Stale-While-Revalidate

### Regla

Para eliminar bloqueos y destellos de "Cargando…" en las transiciones de página:

1. `SessionProvider` debe mantener la sesión en memoria (`cachedSession`) una vez autenticada. En navegaciones subsecuentes, la sesión se sirve de forma inmediata (`loading: false`) mientras se valida en segundo plano sin desmontar el marco general de la interfaz.
2. El hook `useAsync` soporta el patrón Stale-While-Revalidate mediante una clave opcional `cacheKey`. Al revisitar vistas con clave de caché, los datos previos se despliegan instantáneamente en el primer render (`loading: false`), sincronizando silenciosamente en segundo plano sin provocar parpadeos de esqueletos o spinners.

### Ejemplo

Al navegar entre "Áreas", "Plataformas" y otras secciones del sistema, la barra superior, la barra lateral y los listados principales se muestran de inmediato sin el spinner de pantalla completa ni recargas vacías.

### Impacto

Afecta a [session-provider.tsx](../frontend/src/components/session-provider.tsx), [use-async.ts](../frontend/src/lib/use-async.ts) y [platform-admin.tsx](../frontend/src/components/platform-admin.tsx).

## Configuración de Icono en Áreas y Columnas Estandarizadas en Tabla de Usuarios

### Regla

1. **Configuración de Icono en Áreas**: En el modal de creación y edición de áreas (`AreaForm`), dentro del Paso 2 (Estilo visual), se proporciona un selector accesible de iconos (`ICONOS_AREA`) que permite configurar el icono identificativo del área. El icono elegido se refleja en la vista previa del área y se persiste en base de datos.
2. **Columnas en Tabla de Usuarios**: La tabla principal de usuarios (`UsersList`) estructura sus columnas exactamente en:
   - `Nombre`: Muestra el avatar con iniciales y el nombre completo del usuario.
   - `Correo`: Muestra la dirección de correo electrónico del usuario.
   - `Rol`: Muestra la insignia correspondiente a su rol en el sistema.
   - `Estado`: Muestra las insignias de estatus de actividad (Activo/Inactivo) y tipo de autenticación.
   - `Áreas asignadas`: Despliega **únicamente** los iconos representativos de cada área asignada al usuario dentro de contenedores compactos y accesibles (incluyendo `title` y `aria-label` con el nombre del área), sin texto plano visible del nombre del área.
3. **Serialización Backend**: El backend serializa `icon` y `color` en las áreas asignadas del usuario (`app/modules/users/serializacion.py`).

### Ejemplo

En la tabla de usuarios, las columnas visibles son "Nombre", "Correo", "Rol", "Estado" y "Áreas asignadas". En la columna "Áreas asignadas", en lugar de etiquetas de texto como "Finanzas", se observan exclusivamente los iconos distintivos configurados para dichas áreas (por ejemplo el icono de estructura o de plataforma con tooltip de su nombre). Al dar de alta un área, en el paso 2 el administrador puede pulsar el icono deseado dentro de la cuadrícula interactiva.

### Impacto

Afecta a [serializacion.py](../app/modules/users/serializacion.py), [types.ts](../frontend/src/lib/types.ts), [area-form.tsx](../frontend/src/components/areas/area-form.tsx), [platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [users-list.tsx](../frontend/src/components/users-list.tsx) y pruebas en [users-list.test.tsx](../frontend/tests/components/users-list.test.tsx).

## Columnas Estandarizadas en la Tabla de Áreas

### Regla

En la vista de administración de áreas (`/areas`), la tabla principal (`AreasList`) estandariza sus columnas para mostrar exclusivamente:

1. `Casilla de selección`: Control de selección individual y global para acciones en lote.
2. `Área`: Chip de iniciales con color personalizado + nombre del área (incluyendo la insignia `Administras` si el usuario en sesión es administrador delegado de dicha área).
3. `Descripción`: Detalle descriptivo del área o indicador en cursiva si no cuenta con descripción.
4. `Plataformas`: Contador numérico acompañado del icono representativo de plataformas.
5. `Usuarios`: Contador numérico acompañado del icono representativo de usuarios.
6. `Estado`: Insignia de estado operativo (`Activo` / `Inactivo`).

Queda eliminada la columna `Alcance` de la tabla, integrando el indicador de administración delegada de forma contextual y compacta directamente junto al nombre del área.

### Ejemplo

Al acceder a `/areas`, la tabla muestra los encabezados "Área", "Descripción", "Plataformas", "Usuarios" y "Estado". La columna previa "Alcance" no se despliega, optimizando el espacio horizontal y concentrando la información de descripción de cada área en su propia columna dedicada.

### Impacto

Afecta a [areas-list.tsx](../frontend/src/components/areas-list.tsx) y a la suite de pruebas en [areas-list.test.tsx](../frontend/tests/components/areas-list.test.tsx).

## Gestión de Usuarios y Accesos

### Regla

En la vista de administración de usuarios (`/users`), al seleccionar un usuario y pulsar la acción "Accesos" (en la barra de herramientas o en las acciones de fila), el sistema abre obligatoriamente un diálogo modal accesible (`Modal` flotante centrado con tamaño `2xl`), sustituyendo cualquier visualización incrustada inline que desplace la tabla.
El modal implementa un componente Dual Picklist estructurado en dos columnas independientes:

1. Columna izquierda ("Sin acceso"): Plataformas disponibles a las que el usuario no tiene acceso concedido actualmente, con buscador reactivo por nombre/código y contador de elementos.
2. Columna derecha ("Con acceso"): Plataformas en las que el usuario posee acceso activo/vigente, con buscador reactivo y contador de elementos.
Cada elemento de plataforma en las columnas cuenta con un objetivo táctil $\ge 48\text{ px}$ y un botón de transferencia inmediata en un solo clic (`+` para asignar, `−` para desasignar). El pie del modal exhibe el botón secundario "Cerrar", un indicador en tiempo real de cambios pendientes y el botón primario "Guardar" (deshabilitado si no hay cambios pendientes).
Al guardar, se realizan las operaciones de otorgamiento (`grantPlatformAccess`) y revocación (`revokeAccess`), notificando el resultado exclusivamente mediante mensajes Toast del sistema (sin alertas ni banners inline dentro del modal). En caso de usuarios con rol `superadmin`, el modal informa de manera accesible que cuentan con acceso universal automático.

### Ejemplo

Al seleccionar al usuario "Ana Ruiz" y presionar "Accesos", se despliega el modal flotante "Accesos — Ana Ruiz". En la columna "Sin acceso" se listan las plataformas disponibles. Al hacer clic en el botón "+" de la plataforma "GitLab", esta se transfiere inmediatamente a la columna "Con acceso" y el pie actualiza a "1 cambio pendiente". Al presionar "Guardar", se aplican las operaciones correspondientes y se muestra un toast de éxito "Accesos actualizados correctamente".

### Impacto

Afecta a [user-access-panel.tsx](../frontend/src/components/users/user-access-panel.tsx), [users-list.tsx](../frontend/src/components/users-list.tsx), [api.ts](../frontend/src/lib/api.ts), [serializacion.py](../app/modules/access/serializacion.py) y las suites de pruebas en [user-access-panel.test.tsx](../frontend/tests/components/users/user-access-panel.test.tsx) y [users-list.test.tsx](../frontend/tests/components/users-list.test.tsx).

## Columnas Estandarizadas en la Tabla de Áreas

### Regla

En la vista de administración de áreas (`/areas`), la tabla principal (`AreasList`) estandariza sus columnas para mostrar exclusivamente:

1. `Casilla de selección`: Control de selección individual y global para acciones en lote.
2. `Área`: Chip de iniciales con color personalizado + nombre del área (incluyendo la insignia `Administras` si el usuario en sesión es administrador delegado de dicha área).
3. `Descripción`: Detalle descriptivo del área o indicador en cursiva si no cuenta con descripción.
4. `Plataformas`: Contador numérico acompañado del icono representativo de plataformas.
5. `Usuarios`: Contador numérico acompañado del icono representativo de usuarios.
6. `Estado`: Insignia de estado operativo (`Activo` / `Inactivo`).

Queda eliminada la columna `Alcance` de la tabla, integrando el indicador de administración delegada de forma contextual y compacta directamente junto al nombre del área.

### Ejemplo

Al acceder a `/areas`, la tabla muestra los encabezados "Área", "Descripción", "Plataformas", "Usuarios" y "Estado". La columna previa "Alcance" no se despliega, optimizando el espacio horizontal y concentrando la información de descripción de cada área en su propia columna dedicada.

### Impacto

Afecta a [areas-list.tsx](../frontend/src/components/areas-list.tsx) y a la suite de pruebas en [areas-list.test.tsx](../frontend/tests/components/areas-list.test.tsx).

## Gestión de Usuarios y Accesos

### Regla

En la vista de administración de usuarios (`/users`), al seleccionar un usuario y pulsar la acción "Accesos" (en la barra de herramientas o en las acciones de fila), el sistema abre obligatoriamente un diálogo modal accesible (`Modal` flotante centrado con tamaño `2xl`), sustituyendo cualquier visualización incrustada inline que desplace la tabla.
El modal implementa un componente Dual Picklist estructurado en dos columnas independientes:

1. Columna izquierda ("Sin acceso"): Plataformas disponibles a las que el usuario no tiene acceso concedido actualmente, con buscador reactivo por nombre/código y contador de elementos.
2. Columna derecha ("Con acceso"): Plataformas en las que el usuario posee acceso activo/vigente, con buscador reactivo y contador de elementos.
Cada elemento de plataforma en las columnas cuenta con un objetivo táctil $\ge 48\text{ px}$ y un botón de transferencia inmediata en un solo clic (`+` para asignar, `−` para desasignar). El pie del modal exhibe el botón secundario "Cerrar", un indicador en tiempo real de cambios pendientes y el botón primario "Guardar" (deshabilitado si no hay cambios pendientes).
Al guardar, se realizan las operaciones de otorgamiento (`grantPlatformAccess`) y revocación (`revokeAccess`), notificando el resultado exclusivamente mediante mensajes Toast del sistema (sin alertas ni banners inline dentro del modal). En caso de usuarios con rol `superadmin`, el modal informa de manera accesible que cuentan con acceso universal automático.

### Ejemplo

Al seleccionar al usuario "Ana Ruiz" y presionar "Accesos", se despliega el modal flotante "Accesos — Ana Ruiz". En la columna "Sin acceso" se listan las plataformas disponibles. Al hacer clic en el botón "+" de la plataforma "GitLab", esta se transfiere inmediatamente a la columna "Con acceso" y el pie actualiza a "1 cambio pendiente". Al presionar "Guardar", se aplican las operaciones correspondientes y se muestra un toast de éxito "Accesos actualizados correctamente".

### Impacto

Afecta a [user-access-panel.tsx](../frontend/src/components/users/user-access-panel.tsx), [users-list.tsx](../frontend/src/components/users-list.tsx), [api.ts](../frontend/src/lib/api.ts), [serializacion.py](../app/modules/access/serializacion.py) y las suites de pruebas en [user-access-panel.test.tsx](../frontend/tests/components/users/user-access-panel.test.tsx) y [users-list.test.tsx](../frontend/tests/components/users-list.test.tsx).

## Persistencia de Dimensiones de Cuadrícula en Plataformas

### Regla

En la vista de administración de plataformas (`/admin/platforms`), las dimensiones de la cuadrícula de tarjetas de áreas (filas de 2 a 4 y columnas de 2 a 4) se persisten en el navegador del usuario utilizando `localStorage` (`portal_grid_filas` y `portal_grid_columnas`). Cada cambio de filas, columnas o combinaciones predefinidas ($2\times 2$, $3\times 3$, $4\times 4$, etc.) se almacena inmediatamente en el almacenamiento local. Al recargar la página o navegar entre distintas vistas del sistema, el componente restaura de forma reactiva las dimensiones configuradas por el usuario, evitando que se restablezcan a los valores iniciales de $2\times 4$.

### Ejemplo

Un administrador ingresa a `General > Plataformas` y en el menú de cuadrícula selecciona la combinación `3×3`. El diseño se adapta de inmediato mostrando 9 ranuras y guardando los valores `3` y `3` en el almacenamiento local. Al navegar hacia otra ruta del sistema o refrescar la pestaña, la vista de plataformas mantiene activa la configuración de 3 filas por 3 columnas.

### Impacto

Afecta a [platform-admin.tsx](../frontend/src/components/platform-admin.tsx) y a la suite de pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Botones Estandarizados en la Barra de Herramientas de Conectores

### Regla

En la vista de administración de conectores (`/admin/connectors`), la barra de herramientas principal estandariza sus acciones contextuales a la derecha, reemplazando el botón aislado de "Recargar":

1. **Botón `EDITAR`**: Variante `fila`, icono de edición y texto "Editar". Se activa únicamente cuando se selecciona una plataforma en la lista (`disabled={!seleccionada}`) y permite abrir o enfocar el panel de edición del conector correspondiente.
2. **Botón `ELIMINAR`**: Variante `fila-peligro`, icono de eliminar y texto "Eliminar". Se habilita exclusivamente cuando la plataforma seleccionada cuenta con un conector configurado (`disabled={!seleccionada || !seleccionada.has_connector}`). Al pulsarlo, abre el diálogo de confirmación `ConnectorDeleteDialog` para eliminar el conector.
3. **Separador vertical**: Divisor visual de 24 px (`w-px bg-panel-border/80`).
4. **Botón `+ NUEVO`**: Variante `fila-primario`, icono de más y texto "Nuevo". Si se tiene seleccionada una plataforma sin conector, abre directamente su panel para configurarla. En caso contrario, despliega un modal accesible para seleccionar cuál de las plataformas pendientes se desea configurar; si todas ya tienen conector, notifica amigablemente mediante Toast.

### Ejemplo

Al ingresar a `Gestión > Conectores`, la barra de herramientas presenta a la derecha los botones `Editar` y `Eliminar` (ambos deshabilitados inicialmente), el separador vertical y `+ Nuevo`. Al seleccionar la plataforma "Contabilidad", los botones `Editar` y `Eliminar` se activan con sus respectivas etiquetas accesibles. Al presionar `Eliminar`, se despliega el diálogo de confirmación para revocar el conector sin necesidad de descender al panel inferior.

### Impacto

Afecta a [connectors-admin.tsx](../frontend/src/components/connectors/connectors-admin.tsx), [connector-list.tsx](../frontend/src/components/connectors/connector-list.tsx) y a la suite de pruebas en [connectors-admin.test.tsx](../frontend/tests/components/connectors/connectors-admin.test.tsx).

## Tolerancia a Entidades Nulas en Bitácora de Ejecuciones

### Regla

En la vista y componentes de bitácora de ejecuciones de aprovisionamiento (`/admin/jobs`, `JobsTable`, `JobDetailModal`, `JobRetryDialog` y `JobsLog`), las referencias a entidades asociadas (`job.platform`, `job.user` y `job.area`) deben consumirse de forma defensiva mediante encadenamiento opcional (`?.`) y textos descriptivos de contingencia (`'Plataforma eliminada'`, `'Usuario eliminado'`, `'Área eliminada'`).
Debido a que el backend retorna intencionalmente `null` cuando una entidad referenciada por un trabajo previo ha sido eliminada del sistema, los componentes frontend deben garantizar la renderización íntegra de la bitácora histórica sin generar excepciones `TypeError` ni páginas de error 500.

### Ejemplo

Si un trabajo de aprovisionamiento histórico referencia una plataforma que posteriormente fue eliminada de la base de datos (como el trabajo n.º 2), la bitácora despliega correctamente la fila identificando al usuario y señalando "Plataforma eliminada · [Nombre del área]" en lugar de interrumpir la renderización.

### Impacto

Afecta a [jobs-table.tsx](../frontend/src/components/connectors/jobs-table.tsx), [job-detail-modal.tsx](../frontend/src/components/connectors/job-detail-modal.tsx), [job-retry-dialog.tsx](../frontend/src/components/connectors/job-retry-dialog.tsx), [jobs-log.tsx](../frontend/src/components/connectors/jobs-log.tsx), [types.ts](../frontend/src/lib/access/types.ts) y a la suite de pruebas en [jobs-page.test.tsx](../frontend/tests/components/connectors/jobs-page.test.tsx).

## Script Unificado de Arranque de Servicios

### Regla

Para facilitar el levantamiento del ecosistema de desarrollo en local, se dispone del script ejecutable `start.sh` en la raíz del proyecto (a la altura de `run.py`). El script orquesta de forma automatizada:

1. Validación de la presencia del entorno virtual Python (`venv`).
2. Comprobación e instalación de dependencias del frontend (`frontend/node_modules`).
3. Aplicación de migraciones pendientes de base de datos (`venv/bin/alembic upgrade head`).
4. Lanzamiento concurrente del Backend Flask (`run.py` en puerto 5001) y del Frontend Next.js (`npm run dev` en puerto 3000).
5. Captura y propagación de señales de terminación (`SIGINT`, `SIGTERM`, `EXIT`) para asegurar el apagado limpio y simultáneo de ambos procesos al pulsar `Ctrl+C`, previniendo puertos bloqueados o procesos huérfanos.

### Ejemplo

Al ejecutar `./start.sh` desde la terminal en la raíz del proyecto, el sistema aplica las migraciones pendientes y levanta de inmediato tanto el backend (`http://localhost:5001`) como el frontend (`http://localhost:3000`). Al presionar `Ctrl+C`, la terminal finaliza ambos subprocesos y libera los puertos de forma segura.

### Impacto

Afecta a [start.sh](../start.sh) y a los procedimientos de desarrollo local.

## Limpieza Visual en Modal de Accesos (Dual Picklist)

### Regla

En el modal de administración de accesos (`PlatformAccessPanel` y paneles análogos con Dual Picklist), se suprime el texto de ayuda explicativo sobre la transferencia de registros entre columnas ("Haz clic sobre cualquier usuario para transferirlo entre columnas..."). La interacción intuitiva mediante botones interactivos, estados visuales y diseño autodirigido sustituye la instrucción redundante, maximizando el espacio vertical y la legibilidad de las listas de transferencia.

### Ejemplo

Al abrir el modal de accesos para una plataforma desde el catálogo, la cabecera muestra inmediatamente los contadores y las dos columnas del Dual Picklist sin párrafos de texto instructivo innecesarios, permitiendo una visión despejada y directa de los usuarios asignados y disponibles.

### Impacto

Afecta a [platform-access-panel.tsx](../frontend/src/components/platforms/platform-access-panel.tsx) y a la experiencia de usuario en la administración de accesos del portal.

## Estandarización Global de Opciones de Selección (Option y nexus-option)

### Regla

Todos los elementos desplegables de selección (`<Select>` y selectores del sistema) deben utilizar el componente reutilizable `<Option>` de [form.tsx](../frontend/src/components/form.tsx) o, en su defecto, portar la clase CSS `.nexus-option` (junto con tokens de fondo, texto y peso tipográfico semibold: `bg-input-bg text-input-text font-semibold`). Queda estrictamente prohibido el uso de etiquetas `<option>` nativas desnudas sin estilizado de clase, asegurando que en todos los navegadores y sistemas operativos las opciones respeten los tokens de superficie, contraste, estados `:checked`, `:hover` y soporte completo de modo oscuro.

### Ejemplo

En los filtros de auditoría, bitácora de ejecuciones, alcance, inventario y solicitudes, cada opción se renderiza como `<Option value="...">Texto</Option>`, inyectando la clase `.nexus-option` y garantizando que el menú desplegable conserve el tema visual de Nexus en lugar de los estilos grises por defecto del navegador.

### Impacto

Afecta a [form.tsx](../frontend/src/components/form.tsx), [select-premium.tsx](../frontend/src/components/select-premium.tsx), [scope-filters.tsx](../frontend/src/components/access/scope-filters.tsx), [inventory-filters.tsx](../frontend/src/components/access/inventory-filters.tsx), [my-access.tsx](../frontend/src/components/access/my-access.tsx), [approvals-inbox.tsx](../frontend/src/components/access/approvals-inbox.tsx), [my-requests.tsx](../frontend/src/components/access/my-requests.tsx), [catalog-filters.tsx](../frontend/src/components/access/catalog-filters.tsx), [theme-selector.tsx](../frontend/src/components/theme-selector.tsx), [platform-integration-fields.tsx](../frontend/src/components/platforms/platform-integration-fields.tsx), [jobs-filters.tsx](../frontend/src/components/connectors/jobs-filters.tsx), [connector-form.tsx](../frontend/src/components/connectors/connector-form.tsx), [connector-param-fields.tsx](../frontend/src/components/connectors/connector-param-fields.tsx), [audit-filters.tsx](../frontend/src/components/audit/audit-filters.tsx), [smtp-tab.tsx](../frontend/src/components/settings/smtp-tab.tsx) y [components.css](../frontend/src/styles/components.css).

## Supresión de Texto Instructivo en Modal de Accesos de Usuarios (UserAccessPanel)

### Regla

En concordancia con la estandarización del modal de accesos de plataformas, en el modal de accesos de usuarios ([user-access-panel.tsx](../frontend/src/components/users/user-access-panel.tsx)) se elimina el texto de instrucción ("Haz clic sobre cualquier plataforma para transferirla entre columnas..."). Las columnas Dual Picklist, los buscadores independientes y los botones interactivos proporcionan una interfaz autodirigida y ergonómica sin necesidad de leyendas explicativas estáticas.

### Ejemplo

Al seleccionar un usuario en la tabla de usuarios y hacer clic en el botón `Accesos`, el modal desplegado muestra de inmediato los contadores y las columnas de plataformas disponibles y asignadas, con máximo aprovechamiento del espacio vertical y sin bloques de texto redundantes.

### Impacto

Afecta a [user-access-panel.tsx](../frontend/src/components/users/user-access-panel.tsx) y a la suite de pruebas en [user-access-panel.test.tsx](../frontend/tests/components/users/user-access-panel.test.tsx).

## Estandarización Global de Opciones de Selección (Option y nexus-option)

### Regla

Todos los elementos desplegables de selección (`<Select>` y selectores del sistema) deben utilizar el componente reutilizable `<Option>` de [form.tsx](../frontend/src/components/form.tsx) o, en su defecto, portar la clase CSS `.nexus-option` (junto con tokens de fondo, texto y peso tipográfico semibold: `bg-input-bg text-input-text font-semibold`). Queda estrictamente prohibido el uso de etiquetas `<option>` nativas desnudas sin estilizado de clase, asegurando que en todos los navegadores y sistemas operativos las opciones respeten los tokens de superficie, contraste, estados `:checked`, `:hover` y soporte completo de modo oscuro.

### Ejemplo

En los filtros de auditoría, bitácora de ejecuciones, alcance, inventario y solicitudes, cada opción se renderiza como `<Option value="...">Texto</Option>`, inyectando la clase `.nexus-option` y garantizando que el menú desplegable conserve el tema visual de Nexus en lugar de los estilos grises por defecto del navegador.

### Impacto

Afecta a [form.tsx](../frontend/src/components/form.tsx), [select-premium.tsx](../frontend/src/components/select-premium.tsx), [scope-filters.tsx](../frontend/src/components/access/scope-filters.tsx), [inventory-filters.tsx](../frontend/src/components/access/inventory-filters.tsx), [my-access.tsx](../frontend/src/components/access/my-access.tsx), [approvals-inbox.tsx](../frontend/src/components/access/approvals-inbox.tsx), [my-requests.tsx](../frontend/src/components/access/my-requests.tsx), [catalog-filters.tsx](../frontend/src/components/access/catalog-filters.tsx), [theme-selector.tsx](../frontend/src/components/theme-selector.tsx), [platform-integration-fields.tsx](../frontend/src/components/platforms/platform-integration-fields.tsx), [jobs-filters.tsx](../frontend/src/components/connectors/jobs-filters.tsx), [connector-form.tsx](../frontend/src/components/connectors/connector-form.tsx), [connector-param-fields.tsx](../frontend/src/components/connectors/connector-param-fields.tsx), [audit-filters.tsx](../frontend/src/components/audit/audit-filters.tsx), [smtp-tab.tsx](../frontend/src/components/settings/smtp-tab.tsx) y [components.css](../frontend/src/styles/components.css).

## Supresión de Texto Instructivo en Modal de Accesos de Usuarios (UserAccessPanel)

### Regla

En concordancia con la estandarización del modal de accesos de plataformas, en el modal de accesos de usuarios ([user-access-panel.tsx](../frontend/src/components/users/user-access-panel.tsx)) se elimina el texto de instrucción ("Haz clic sobre cualquier plataforma para transferirla entre columnas..."). Las columnas Dual Picklist, los buscadores independientes y los botones interactivos proporcionan una interfaz autodirigida y ergonómica sin necesidad de leyendas explicativas estáticas.

### Ejemplo

Al seleccionar un usuario en la tabla de usuarios y hacer clic en el botón `Accesos`, el modal desplegado muestra de inmediato los contadores y las columnas de plataformas disponibles y asignadas, con máximo aprovechamiento del espacio vertical y sin bloques de texto redundantes.

### Impacto

Afecta a [user-access-panel.tsx](../frontend/src/components/users/user-access-panel.tsx) y a la suite de pruebas en [user-access-panel.test.tsx](../frontend/tests/components/users/user-access-panel.test.tsx).

## Estandarización de Dimensiones de Iconos en Tablas (Usuarios y Áreas)

### Regla

Todos los iconos contenedores, badges de estado, contadores numéricos y avatares en las tablas de entidades maestras ([users-list.tsx](../frontend/src/components/users-list.tsx), [areas-list.tsx](../frontend/src/components/areas-list.tsx) y [platform-columns.tsx](../frontend/src/components/platforms/platform-columns.tsx)) deben estar rigurosamente estandarizados bajo el sistema de 8pt con una altura y escala unificada:

- **Contenedores de iconos / Avatares**: Cuadrados de 32x32 px (`size-8`) con radio de curvatura uniforme (`rounded-lg`).
- **Pastillas de contadores y estados**: Altura fija de 32 px (`h-8` / `!h-8`) con esquinas curvadas (`rounded-lg`) y relleno táctil equilibrado.
- **Iconografía interna**: Escala estándar de 16 px (`tamano="sm"`), eliminando iconos reducidos (`tamano="xs"` o contenedores `size-7`) que producían disparidad visual respecto al avatar de la columna de nombre.
- **Representación de Área**: En la columna de área, si el registro cuenta con un icono personalizado configurado (`area.icon`), se renderiza dicho icono dentro del chip de 32 px en lugar de las iniciales alfabéticas.

### Ejemplo

En la tabla de usuarios, las insignias de estado (activo/inactivo y LDAP/local) y los iconos de áreas asignadas miden exactamente 32x32 px (`size-8`), alineándose de manera simétrica y con la misma presencia visual que el avatar del nombre. En la tabla de áreas, los contadores de plataformas y usuarios tienen altura de 32 px con iconos de 16 px (`tamano="sm"`), igualando la escala del chip de nombre de área.

### Impacto

Afecta a [users-list.tsx](../frontend/src/components/users-list.tsx), [areas-list.tsx](../frontend/src/components/areas-list.tsx), [platform-columns.tsx](../frontend/src/components/platforms/platform-columns.tsx) y [ui.tsx](../frontend/src/components/ui.tsx).

## Operaciones de Directorio LDAP en el Backend (CRUD de Usuarios, Contraseñas y Membresías)

### Regla

El backend centraliza y garantiza la gestión integral de cuentas y membresías sobre el servidor de directorio OpenLDAP a través de `EscritorDirectorio` (writer.py), cumpliendo con las siguientes directrices de seguridad y consistencia:

1. **Creación de usuarios (`create_user`)**: Crea la entrada en `LDAP_USERS_BASE_DN` con clases `inetOrgPerson` (y las configuradas en `LDAP_USER_OBJECT_CLASSES`). Valida identificador y correo, escapa caracteres RDN y filtros, y, si se suministra una contraseña inicial, la fija **después del alta con Password Modify (RFC 3062)**: el servidor la guarda cifrada; nunca va `userPassword` en claro en el alta (FNC-138).
2. **Eliminación de usuarios (`delete_user`)**: Permite la baja de cuentas en OpenLDAP identificando al usuario por instancia `UsuarioDirectorio`, identificador (UID) o DN completo. Valida estrictamente que el DN pertenezca a la base de usuarios configurada (`bajo_base(dn, cfg.usuarios_base_dn)`) y rechaza cualquier intento de borrado sobre la base o fuera de ella con `Resultado.ERROR_PERMANENTE` (`motivo='fuera_de_base'`). La baja es idempotente (`Resultado.NO_EXISTE` si el usuario no existe).
3. **Cambio de contraseña (`change_password` / `set_password`)**: Fija la contraseña con Password Modify (RFC 3062), que el servidor cifra; ya no se escribe `userPassword` en claro con `MODIFY_REPLACE` (FNC-138). Valida que la contraseña sea texto no vacío y que la cuenta pertenezca a la base de usuarios. Si se proporciona `old_password`, valida previamente la clave actual antes de efectuar la modificación.
4. **Membresía en grupos (`add_member` y `remove_member`)**: Gestiona la inclusión y exclusión de usuarios en grupos de LDAP (`groupOfNames` o `groupOfUniqueNames`), aceptando tanto instancias de `UsuarioDirectorio` como cadenas de identificador o DN normalizadas. Previene que grupos con miembros obligatorios queden vacíos inyectando el marcador `LDAP_GROUP_PLACEHOLDER_MEMBER` o denegando la operación con `ultimo_miembro`.

### Ejemplo

Al invocar `escritor.create_user(DatosCuenta('carlos', 'Carlos', 'Gomez', 'carlos@dominio.com', password='Password123!'))`, el backend crea la entrada en LDAP y luego fija su contraseña con Password Modify (OpenLDAP la guarda cifrada). Para cambiar su contraseña, `escritor.change_password('carlos', 'NuevaClave456!')` actualiza la clave en OpenLDAP de forma segura y sin exponer credenciales en los logs. Para eliminar la cuenta, `escritor.delete_user('carlos')` verifica que el DN esté bajo la base autorizada y ejecuta la eliminación sin afectar ramas ajenas.

### Impacto

Afecta a [writer.py](../app/modules/directory/writer.py), [directory_accounts.py](../app/modules/users/directory_accounts.py), [ldap_provider.py](../app/modules/provisioning/ldap_provider.py) y las suites de pruebas [test_writer.py](../tests/directory/test_writer.py) y [test_alta_directorio.py](../tests/users/test_alta_directorio.py).

## Eliminación en Lote para Selección Múltiple de Usuarios

### Regla

En la vista de administración de usuarios ([users-list.tsx](../frontend/src/components/users-list.tsx)), el botón de acción "Eliminar" en la barra de herramientas se habilita tanto para selección individual como para selecciones múltiples (`disabled={activeSelectedIds.size === 0}`):

1. **Acción unificada**: Mientras que los botones "Accesos" y "Editar" requieren un alcance singular (`isSingleSelected = activeSelectedIds.size === 1`), el botón "Eliminar" permite la supresión de una o más cuentas de usuarios concurrentemente.
2. **Confirmación contextual**: Al presionar "Eliminar" con múltiples registros seleccionados, el diálogo de confirmación `ConfirmDialog` adapta su título a "Eliminar usuarios" y expone explícitamente el conteo total de cuentas a retirar ("Se eliminarán las cuentas de los X usuarios seleccionados. Esta acción no se puede deshacer.").
3. **Ejecución y notificación**: Tras la confirmación, el sistema ejecuta la baja de cada cuenta invocando `api.deleteUser`, limpia la selección activa, recarga la lista de usuarios y notifica mediante Toast el total de cuentas retiradas.

### Ejemplo

Al marcar la casilla superior para seleccionar todos los usuarios o seleccionar varias filas (por ejemplo, 3 usuarios), los botones "Accesos" y "Editar" permanecen deshabilitados con sus respectivas descripciones explicativas, mientras que el botón "Eliminar" se activa indicando "Eliminar 3 usuarios seleccionados". Al pulsarlo, el modal solicita confirmación para los 3 usuarios y, tras confirmar, retira las cuentas y muestra el aviso "3 cuentas de usuarios retiradas".

### Impacto

Afecta a [users-list.tsx](../frontend/src/components/users-list.tsx) y a la suite de pruebas en [users-list.test.tsx](../frontend/tests/components/users-list.test.tsx).

## Eliminación en Lote para Selección Múltiple de Áreas y Plataformas

### Regla

En las tablas de administración de entidades ([areas-list.tsx](../frontend/src/components/areas-list.tsx) y [platform-admin.tsx](../frontend/src/components/platform-admin.tsx)), el botón de acción "Eliminar" en la barra de herramientas admite tanto selección individual como selección múltiple de 2 o más registros:

1. **Áreas ([areas-list.tsx](../frontend/src/components/areas-list.tsx))**:
   - El botón "Eliminar" se habilita cuando hay al menos 1 área seleccionada y el usuario cuenta con permisos sobre todas las áreas seleccionadas (superadministrador, o administrador de área con todas las áreas seleccionadas dentro de `managedIds`).
   - El diálogo de confirmación `ConfirmDialog` adapta título y mensaje en plural indicando el conteo de áreas ("Se eliminarán las X áreas seleccionadas. Si alguna tiene plataformas asignadas, primero hay que reasignarlas.").
   - La eliminación ejecuta `api.deleteArea` secuencialmente por cada área, limpia la selección, recarga la lista y notifica con Toast el resultado ("X áreas fueron retiradas.").
2. **Plataformas ([platform-admin.tsx](../frontend/src/components/platform-admin.tsx))**:
   - En la tabla de plataformas de un área activa, el botón "Eliminar" se habilita para 1 o más plataformas seleccionadas (`activeSelectedPlatformIds.size > 0`). Los botones "Accesos" y "Editar" se mantienen restringidos a exactamente 1 plataforma (`isSinglePlatformSelected`).
   - El diálogo de confirmación adapta título y mensaje ("Se eliminarán las X plataformas seleccionadas. Esta acción no se puede deshacer.").
   - La eliminación invoca `api.deletePlatform` por cada plataforma en lote, retira los IDs de la selección activa, recarga el listado y reporta mediante Toast el total de plataformas eliminadas.

### Ejemplo

Al marcar varias casillas en la tabla de áreas (por ejemplo, 2 áreas administradas), el botón "Eliminar" se activa como "Eliminar 2 áreas seleccionadas". Al hacer click y confirmar en el modal, se eliminan ambas áreas y se muestra el toast "2 áreas fueron retiradas". De igual forma, en la tabla de plataformas de un área, al seleccionar 3 plataformas el botón "Eliminar" se activa para eliminarlas en lote tras la confirmación respectiva.

### Impacto

Afecta a [areas-list.tsx](../frontend/src/components/areas-list.tsx), [platform-admin.tsx](../frontend/src/components/platform-admin.tsx) y a las suites de pruebas [areas-list.test.tsx](../frontend/tests/components/areas-list.test.tsx) y [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Condiciones de Integridad para la Baja de Áreas (Plataformas y Usuarios)

### Regla

La eliminación de un área en el sistema está sujeta a las siguientes reglas estrictas de integridad referencial:

1. **Plataformas vinculadas (Bloqueo de eliminación)**: Un área no puede eliminarse si contiene una o más plataformas asociadas (`area.platforms` no vacío). La API rechaza la solicitud con código `409 Conflict` (`area_con_plataformas`), requiriendo que las plataformas sean previamente eliminadas o reasignadas a otra área.
2. **Usuarios asignados (Desvinculación automática)**: La existencia de usuarios asignados al área (`user_areas`) o administradores delegados (`area_admins`) no impide la baja del área. Al concretarse la eliminación del área, las asociaciones en las tablas relacionales secundarias se eliminan automáticamente (desvinculando a los usuarios y administradores de dicha área), mientras que las cuentas de usuario (`users`) se conservan intactas en el sistema y en el directorio.

### Ejemplo

Si el área "Finanzas" contiene 2 plataformas y 5 usuarios, al intentar eliminarla el sistema rechaza la operación informando que primero deben reasignarse o eliminarse sus plataformas. Una vez que las plataformas se han movido a otra área (dejando 0 plataformas en Finanzas), el área se elimina exitosamente y los 5 usuarios simplemente dejan de pertenecer a "Finanzas", manteniéndose activos en el catálogo de usuarios.

### Impacto

Afecta a [app/modules/areas/baja.py](../app/modules/areas/baja.py), [app/modules/areas/api.py](../app/modules/areas/api.py), [areas-list.tsx](../frontend/src/components/areas-list.tsx) y los modelos de datos en [app/modules/auth/models.py](../app/modules/auth/models.py).

## Generador de Contraseñas Seguras en el Modal de Nueva Cuenta

### Regla

El modal de creación de nueva cuenta ([directory-account-form.tsx](../frontend/src/components/users/directory-account-form.tsx)) incorpora un generador criptográfico de contraseñas de alta seguridad ([generador-contrasena.ts](../frontend/src/lib/generador-contrasena.ts)):

1. **Composición y Longitud**: Genera contraseñas alfanuméricas con símbolos con una longitud mínima garantizada de 16 caracteres (`LONGITUD_MINIMA_GENERADOR = 16`). La contraseña generada incluye obligatoriamente al menos una letra mayúscula (`A-Z`), una minúscula (`a-z`), un dígito numérico (`0-9`) y un símbolo especial (`!@#$%^&*()_+-=[]{}|;:,.<>?`), distribuidos mediante aleatoriedad criptográfica (`window.crypto.getRandomValues`) y mezclados con el algoritmo Fisher-Yates.
2. **Sincronización Automática de Campos**: Al pulsar el botón "Generar contraseña", el sistema asigna el valor generado simultáneamente a los campos `Contraseña` y `Confirmar contraseña`, eliminando discrepancias o errores de coincidencia, activa la visibilidad del texto para que el operador pueda inspeccionarlo y copia la contraseña al portapapeles del navegador emitiendo una notificación Toast informativa.
3. **Controles de Inspección**: Se habilitan controles contextuales para alternar la visibilidad de la contraseña ("Ver / Ocultar") y para copiarla al portapapeles en cualquier momento ("Copiar").

### Ejemplo

Al crear un nuevo usuario mediante el botón "Nuevo", el administrador hace clic en "Generar contraseña". El sistema genera instantáneamente una clave de 16 caracteres como `k7$M9!wP#2zL&4qX`, la copia al portapapeles, muestra la notificación correspondiente y puebla automáticamente los campos de contraseña y confirmación sin necesidad de digitación manual.

### Impacto

Afecta a [directory-account-form.tsx](../frontend/src/components/users/directory-account-form.tsx), [generador-contrasena.ts](../frontend/src/lib/generador-contrasena.ts) y a las suites de pruebas [directory-account-form.test.tsx](../frontend/tests/components/users/directory-account-form.test.tsx) y [generador-contrasena.test.ts](../frontend/tests/lib/generador-contrasena.test.ts).

## Disposición Inferior del Generador de Contraseñas en el Modal de Nueva Cuenta

### Regla

En el formulario del modal de nueva cuenta ([directory-account-form.tsx](../frontend/src/components/users/directory-account-form.tsx)), la barra de utilidades del generador de contraseñas seguras se posiciona inmediatamente debajo de la cuadrícula de campos de contraseña (`Contraseña` y `Confirmar contraseña`):

- Los campos de entrada de credenciales se presentan de forma limpia y directa al usuario en su cuadrícula de 2 columnas.
- La barra de herramientas ubicada abajo integra la leyenda de asistencia, el botón de acción principal ("Generar contraseña") y los controles secundarios dinámicos ("Ver / Ocultar" y "Copiar") preservando el flujo visual natural de arriba a abajo.

### Ejemplo

Al visualizar el Paso 1 en "Nueva cuenta", el operador observa primero los campos "Nombre completo", "Correo", y a continuación la cuadrícula con "Contraseña" y "Confirmar contraseña". Inmediatamente debajo de ambos campos encuentra el contenedor del generador con el botón "Generar contraseña".

### Impacto

Afecta a [directory-account-form.tsx](../frontend/src/components/users/directory-account-form.tsx) y a la suite de pruebas [directory-account-form.test.tsx](../frontend/tests/components/users/directory-account-form.test.tsx).

## Optimización Dimensional y Prevención de Desbordamiento en Modales

### Regla

Para garantizar que todos los modales con formularios complejos de 2 pasos ([directory-account-form.tsx](../frontend/src/components/users/directory-account-form.tsx)) desplieguen su contenido íntegro sin generar barras de desplazamiento vertical internas (scroll) ni ocultar acciones secundarias:

1. **Altura Base de Modal ([components.css](../frontend/src/styles/components.css))**: La clase `.nx-modal-glass` eleva su altura estándar a `640px` (respetando `max-height: 90vh`), proveyendo el espacio vertical necesario para alojar el encabezado, el indicador de pasos (stepper), los campos del formulario con sus reservas de error de layout (`min-h-5`) y las barras de herramientas auxiliares.
2. **Compactación de Contenedores Auxiliares**: La barra de autogeneración de contraseñas adopta una disposición horizontal ultra compacta (`px-3 py-2`), alineando la leyenda y los botones de acción (`Generar`, `Ver / Ocultar`, `Copiar`) en una sola línea fluida sin generar saltos de línea ni forzar scroll.

### Ejemplo

Al abrir el modal "Nueva cuenta", todo el Paso 1 (stepper, nombre completo, correo, contraseña, confirmar contraseña y la barra del generador) se visualiza completo y despejado sobre los botones "Cancelar" y "Siguiente", sin que aparezca ninguna barra de desplazamiento vertical y sin elementos recortados detrás del pie del modal.

### Impacto

Afecta a [components.css](../frontend/src/styles/components.css), [directory-account-form.tsx](../frontend/src/components/users/directory-account-form.tsx) y a la suite de pruebas [directory-account-form.test.tsx](../frontend/tests/components/users/directory-account-form.test.tsx).

## Asistente de 3 Pasos en la Creación y Edición de Plataformas

## Plataformas

### Regla

El asistente modal de alta y edición de plataformas ([platform-form.tsx](../frontend/src/components/platforms/platform-form.tsx)) adopta un flujo guiado de 3 pasos progresivos:

1. **Paso 1: Descripción**: Recopila los metadatos esenciales de la plataforma: `Nombre` (obligatorio), `Descripción` (obligatoria) y `Enlace directo` (con normalización automática de protocolo `https://`).
2. **Paso 2: Diseño** (Sustituye a "Estilo"):
   - **Personalización de Colores**: Permite seleccionar el `Color de fondo` (`bg_color`) y el `Color del icono` (`text_color`), con soporte de valores por omisión del sistema si no se especifican.
   - **Identidad Visual**: Ofrece un selector interactivo dual entre:
     - **Elegir icono del catálogo**: Cuadrícula accesible de iconos representativos del sistema (`ICONOS_PLATAFORMA`).
     - **Subir imagen / logotipo**: Control de carga de archivos de imagen locales (PNG, JPG, SVG, WebP, máx. 2 MB) con lectura y previsualización instantánea.
3. **Paso 3: Vista previa y activación**:
   - **Vista previa de la plataforma**: Muestra una representación fiel de la tarjeta en vivo con el chip estilizado, icono o imagen subida, nombre, descripción, enlace y badge de estado.
   - **Toggle de activación**: Reemplaza la casilla de verificación tradicional por un control conmutador accesible (`Toggle` / `role="switch"`), permitiendo alternar de forma intuitiva el estado `Activa` / `Inactiva` con retroalimentación visual reactiva inmediata.

### Ejemplo

Al crear una plataforma en el área Finanzas, el operador completa en el Paso 1 el nombre "ERP Central" y la URL. Al avanzar al Paso 2 ("Diseño"), puede seleccionar un color azul distintivo y cargar el archivo `erp-logo.svg` de su equipo o escoger el icono `panel` del catálogo. En el Paso 3 ("Vista previa"), revisa la tarjeta resultante exactamente como la verán los usuarios y conmuta el Toggle a "Activa" antes de pulsar "Guardar".

### Impacto

Afecta a [platform-form.tsx](../frontend/src/components/platforms/platform-form.tsx), [form.tsx](../frontend/src/components/form.tsx), [platform-admin.tsx](../frontend/src/components/platform-admin.tsx) y a la suite de pruebas [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Simetría de Espaciado y Ajuste Natural en Modales

## UI/UX

### Regla

Para garantizar una distribución armónica y simétrica de los elementos dentro de las ventanas modales ([form.tsx](../frontend/src/components/form.tsx), [directory-account-form.tsx](../frontend/src/components/users/directory-account-form.tsx)):

1. **Ajuste Dinámico de Altura**: La clase `.nx-modal-glass` en [components.css](../frontend/src/styles/components.css) prescinde de una altura rígida forzada (`height: 640px`), adoptando un ajuste de altura natural al contenido con límite superior seguro `max-height: 90vh`.
2. **Equidistancia y Simetría Vertical**: El espaciado inferior entre el último elemento interactivo del formulario (la barra compacta de "Clave segura") y el pie de página (`footer`) coincide exactamente con el espaciado superior entre la cabecera del modal y el primer elemento del formulario ("1. Datos de usuario"), ambos fijados de forma consistente en 24 px (`py-6`).

### Ejemplo

Al abrir el modal "Nueva cuenta", la distancia desde el divisor de la cabecera hasta el stepper ("1. Datos de usuario") es de exactamente 24 px, y la distancia desde la barra de "Clave segura" hasta el divisor del pie del modal es igualmente de 24 px, eliminando zonas muertas y evitando la aparición de barras de desplazamiento vertical innecesarias.

### Impacto

Afecta a [components.css](../frontend/src/styles/components.css), [form.tsx](../frontend/src/components/form.tsx), [directory-account-form.tsx](../frontend/src/components/users/directory-account-form.tsx) y a la suite de pruebas [directory-account-form.test.tsx](../frontend/tests/components/users/directory-account-form.test.tsx).

## Ocultamiento de Parámetros de Consulta (Clean URLs) en Navegación de Plataformas

## Navegación

### Regla

Para evitar la exposición de parámetros internos en la barra de direcciones del navegador (`/admin/platforms?area=2&area_name=Demo+Finanzas`), la navegación entre la cuadrícula de áreas y el listado de plataformas gestionadas ([platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [ruta-navegacion.tsx](../frontend/src/components/marco/ruta-navegacion.tsx)) implementa URLs limpias (Clean URLs):

1. **Preservación de Estado sin Query String**: Al seleccionar un área, la información de navegación (`areaId`, `areaName`) se almacena en el estado del historial del navegador (`window.history.pushState({ areaId, areaName }, '', window.location.pathname)`) y en almacenamiento de sesión (`sessionStorage`), manteniendo la barra de direcciones permanentemente en `/admin/platforms` sin parámetros después del signo `?`.
2. **Saneamiento Inmediato de URLs Residuales**: Si un usuario o enlace externo accede mediante una URL con parámetros de consulta (`?area=...&area_name=...`), el sistema extrae de forma transparente los identificadores necesarios para cargar el área e inmediatamente limpia la barra de direcciones mediante `window.history.replaceState`.
3. **Migas de Pan y Navegación Histórica**: La ruta de migas de pan (`RutaNavegacion`) y los botones de retroceso/avance del navegador recuperan fluidamente el contexto del área seleccionada mediante los eventos `popstate` y el estado en memoria, sin requerir exponer cadenas de consulta en la URL visible.

### Ejemplo

Cuando un administrador hace clic sobre el área "Demo Finanzas" dentro de `/admin/platforms`, el sistema muestra la tabla y plataformas de "Demo Finanzas", actualiza las migas de pan a `Administración › Plataformas › Demo Finanzas`, y la barra de direcciones del navegador permanece limpia como `https://portal.empresa.local/admin/platforms`, sin mostrar `?area=2&area_name=Demo+Finanzas`.

### Impacto

Afecta a [platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [ruta-navegacion.tsx](../frontend/src/components/marco/ruta-navegacion.tsx) y a la suite de pruebas [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Supresión de Prefijos Numéricos Redundantes en Indicadores de Pasos (Wizards/Steppers)

## UI/UX

### Regla

En todos los componentes de tipo asistente o paso a paso (`steppers` / `wizards`), las etiquetas de texto de cada paso no deben incluir números ni prefijos ordinales manuales (`1.`, `2.`, `3.`):

1. **No Duplicidad con la Insignia Visual**: El número ordinal de cada paso se muestra de forma centralizada y estilizada dentro del círculo/insignia (`badge`) del paso (`[ 1 ]`, `[ 2 ]`, `[ 3 ]`), por lo que anteponerlo en el texto de la etiqueta resulta redundante y satura visualmente la cabecera del formulario.
2. **Claridad y Concisión**: La etiqueta textual debe reflejar única y exclusivamente el título semántico del paso (por ejemplo, `Descripción`, `Diseño`, `Vista previa`, `Datos de usuario`, `Accesos y áreas`), facilitando la lectura accesible y evitando desfases tipográficos o rupturas de línea en dispositivos compactos.

### Ejemplo

En el diálogo modal "Nueva plataforma", la barra de navegación de pasos muestra visualmente los números 1, 2 y 3 en sus respectivos círculos indicadores, mientras que las etiquetas adyacentes muestran limpiamente `Descripción`, `Diseño` y `Vista previa` (en lugar de `1. Descripción`, `2. Diseño` y `3. Vista previa`). Igualmente, en "Nueva cuenta" se presentan como `Datos de usuario` y `Accesos y áreas`.

### Impacto

Afecta a [platform-form.tsx](../frontend/src/components/platforms/platform-form.tsx), [directory-account-form.tsx](../frontend/src/components/users/directory-account-form.tsx), [area-form.tsx](../frontend/src/components/areas/area-form.tsx) y a las suites de pruebas [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx), [directory-account-form.test.tsx](../frontend/tests/components/users/directory-account-form.test.tsx) y [areas-list.test.tsx](../frontend/tests/components/areas-list.test.tsx).

## Notificaciones de Error y Validación Mediante Toast en Formularios y Diálogos

## UI/UX

### Regla

1. **Sustitución de Banners Estáticos por Toasts**: Las alertas generales de validación (por ejemplo, "Revisa los campos marcados.") y los errores de operaciones en formularios, diálogos modales y paneles no deben renderizarse como cajas de alerta o banners visuales estáticos (`ErrorNote`) en el flujo del formulario, ya que alteran la geometría del modal y desplazan los campos de entrada. En su lugar, el sistema emite una notificación emergente no intrusiva mediante el servicio centralizado de `useToast`:
   - Errores de validación o datos faltantes: notificación con tono de advertencia (`toast.avisar('warning', ...)`).
   - Errores de API o rechazo de operaciones: notificación con tono de error (`toast.avisar('error', ...)`).
2. **Preservación de Errores de Campo y Accesibilidad**:
   - Cada campo individual que presente error conserva su indicador contextual (`FieldErrorNote`) y su borde visual para retroalimentación puntual.
   - El mensaje general de error se conserva en el DOM de forma accesible para lectores de pantalla mediante una región viva oculta (`<div className="sr-only" role="alert">{error}</div>`), cumpliendo estrictamente con los criterios WCAG 4.1.3 sin generar impacto visual ni scroll innecesario.

### Ejemplo

Al abrir el modal "Nueva plataforma" y presionar "Siguiente" con campos obligatorios vacíos, los campos "Nombre" y "Descripción" se marcan con su mensaje de error respectivo, pero no aparece ninguna caja roja debajo del stepper. En su lugar, se despliega una notificación flotante Toast en la esquina con el mensaje "Revisa los campos marcados." sin alterar el alto ni la posición de los campos del formulario.

### Impacto

Afecta a [platform-form.tsx](../frontend/src/components/platforms/platform-form.tsx), [area-form.tsx](../frontend/src/components/areas/area-form.tsx), [connector-form.tsx](../frontend/src/components/connectors/connector-form.tsx), [request-form-modal.tsx](../frontend/src/components/access/request-form-modal.tsx), [reject-dialog.tsx](../frontend/src/components/access/reject-dialog.tsx), [approve-dialog.tsx](../frontend/src/components/access/approve-dialog.tsx), [revoke-access-dialog.tsx](../frontend/src/components/users/revoke-access-dialog.tsx), [user-form.tsx](../frontend/src/components/users/user-form.tsx), [connector-delete-dialog.tsx](../frontend/src/components/connectors/connector-delete-dialog.tsx), [job-retry-dialog.tsx](../frontend/src/components/connectors/job-retry-dialog.tsx), [admin-role-dialog.tsx](../frontend/src/components/users/admin-role-dialog.tsx), [area-admins-panel.tsx](../frontend/src/components/areas/area-admins-panel.tsx), [purge-panel.tsx](../frontend/src/components/users/purge-panel.tsx), [areas-list.tsx](../frontend/src/components/areas-list.tsx) y [users-list.tsx](../frontend/src/components/users-list.tsx).

## Eliminación en Cascada de Solicitudes y Accesos al Dar de Baja una Plataforma

## Plataformas

### Regla

1. **Borrado en Cascada de Solicitudes y Registros Relacionados**:
   - Al eliminar una plataforma (`DELETE /platforms/<id>`), el sistema elimina de forma atómica e inmediata todas las solicitudes de acceso asociadas a dicha plataforma (`PlatformAccessRequest`), incluyendo especialmente aquellas en estado `pendiente`, aprobadas o rechazadas.
   - De igual forma, se eliminan los accesos asignados (`PlatformAccessGrant`), los conectores configurados (`PlatformConnector`) y las tareas de aprovisionamiento vinculadas (`ProvisioningJob`).
2. **Consistencia de Consultas y Contadores de Bandeja**:
   - Todas las consultas de solicitudes (personales en `consultas_solicitud.mias`, bandejas de aprobación en `approvals.bandeja` y métricas globales del tablero en `dashboard/summary` y `home/summary`) realizan un `INNER JOIN` con la tabla `platforms` (`Platform.id == PlatformAccessRequest.platform_id`).
   - Queda estrictamente impedido que existan solicitudes huérfanas en el sistema o que se contabilicen solicitudes pendientes de plataformas que ya han sido dadas de baja o que no existen.

### Ejemplo

Si un usuario solicita acceso a la plataforma "Finanzas ERP" y la solicitud queda en estado "pendiente", pero posteriormente el administrador elimina la plataforma "Finanzas ERP" desde la gestión de plataformas, la solicitud pendiente se elimina automáticamente de la base de datos. Como consecuencia, el indicador de la campana, el contador de la barra de navegación y la bandeja de aprobaciones reflejan de inmediato 0 solicitudes pendientes.

### Impacto

Afecta a [api.py](../app/modules/platforms/api.py), [consultas.py](../app/modules/access_requests/consultas.py), [consultas.py](../app/modules/access/consultas.py), [routes.py](../app/modules/api/routes.py), [test_baja_plataforma.py](../tests/platforms/test_baja_plataforma.py) y al esquema relacional de [models.py](../app/modules/access_requests/models.py).

## Baja de Plataformas con Accesos (FNC-144)

### Regla

- Una plataforma con accesos vigentes no se elimina: `409 plataforma_con_accesos`. Borrarla dejaría a la gente en los grupos del sistema real sin rastro en el portal.
- Sin accesos vigentes, se eliminan sus solicitudes (también las pendientes), sus accesos revocados y su conector; los trabajos de aprovisionamiento se conservan desligados. La auditoría guarda los conteos.
- Borrado en lote (usuarios, áreas, plataformas): se detiene en el primer error y avisa "Se eliminaron N de M." con el motivo; lo eliminado sale de la selección (FNC-145).

### Impacto

Afecta a [baja.py](../app/modules/platforms/baja.py), [api.py](../app/modules/platforms/api.py), [eliminar-en-lote.ts](../frontend/src/lib/eliminar-en-lote.ts) y a [test_baja_plataforma.py](../tests/platforms/test_baja_plataforma.py).

## Botón de Accesos en Áreas para Asignación de Usuarios

## Áreas

### Regla

1. **Botón de Accesos en la Barra de Herramientas de Áreas**: En la pantalla de consulta y administración de Áreas (`/admin/areas`), la barra de herramientas incorpora un botón de acción estandarizado `ACCESOS` (`Icono nombre="solicitudes"`), disponible para superadministradores y administradores de área que gestionen el área en cuestión (`isAdmin || managedIds.has(area.id)`).
2. **Reglas de Selección y Activación**:
   - **0 áreas seleccionadas**: El botón permanece deshabilitado (`disabled={true}`), con `title="Selecciona 1 área para gestionar accesos"` y `aria-label="Accesos"`.
   - **1 área seleccionada**: Se habilita (`disabled={false}` si se cuenta con permisos sobre dicha área), con `title="Accesos de {nombre_area}"` y `aria-label="Accesos de {nombre_area}"`.
   - **Más de 1 área seleccionada**: Se deshabilita preventivamente (`disabled={true}`), con `title="Solo se pueden gestionar accesos de 1 área a la vez"`.
3. **Panel Modal de Gestión de Usuarios del Área (`AreaUsersPanel`)**:
   - Al pulsar el botón `ACCESOS`, se abre el diálogo modal "Accesos — {nombre_area}" con una lista de selección dual (*Dual Picklist*):
     - **Columna izquierda (Sin acceso)**: Muestra los usuarios del sistema dentro del alcance del administrador que aún no pertenecen al área. Al hacer clic en un usuario, se transfiere a la columna derecha y se anuncia por lector de pantalla (`aria-live="polite"`).
     - **Columna derecha (Con acceso)**: Muestra los usuarios que pertenecen al área. Los usuarios recientemente agregados se marcan con badge `Nuevo`; los existentes se muestran como `Miembro`. Al hacer clic en el botón de retiro, vuelven a la columna izquierda.
   - Ambas columnas cuentan con filtros de búsqueda rápidos e independientes por nombre o correo electrónico.
   - Al presionar **Guardar**, se envía `PUT /api/v1/areas/{id}/users` con los IDs de todos los usuarios asignados al área (`user_ids`), actualizando la relación atómicamente y emitiendo una notificación Toast de confirmación (`useToast`).
   - Al vincular a los usuarios al área, quedan automáticamente habilitados para que se les pueda otorgar accesos en las plataformas pertenecientes a dicha área desde `PlatformAccessPanel`.

### Ejemplo

Un administrador de área necesita dar de alta a un usuario en una plataforma de Finanzas, pero el usuario no aparece en la lista de candidatos de la plataforma porque no pertenece al área "Finanzas". El administrador entra a `/admin/areas`, selecciona la fila de "Finanzas", hace clic en el botón **Accesos**, busca al usuario en la columna "Sin acceso" y hace clic sobre su nombre para moverlo a "Con acceso". Al hacer clic en **Guardar**, el usuario queda formalmente asignado a "Finanzas". Inmediatamente después, al gestionar los accesos de las plataformas de Finanzas, el usuario ya aparece como disponible para otorgarle acceso.

### Impacto

Afecta a [areas-list.tsx](../frontend/src/components/areas-list.tsx), [area-users-panel.tsx](../frontend/src/components/areas/area-users-panel.tsx), [api.py](../app/modules/areas/api.py), [api.ts](../frontend/src/lib/api.ts) y a las pruebas en [areas-list.test.tsx](../frontend/tests/components/areas-list.test.tsx).

## Botones de Áreas y Accesos a Plataformas en Usuarios

## Usuarios

### Regla

1. **Doble Botón de Gestión en Barra de Herramientas de Usuarios**: En la pantalla de consulta y administración de Usuarios (`/admin/users`), la barra de herramientas expone acciones de acceso diferenciadas para el usuario seleccionado:
   - **Botón `ÁREAS`** (`Icono nombre="areas"`): Permite gestionar las áreas organizativas a las que pertenece el usuario.
   - **Botón `ACCESOS`** (`Icono nombre="solicitudes"`): Permite gestionar las plataformas a las que tiene acceso el usuario.
2. **Reglas de Selección y Activación**:
   - **0 usuarios seleccionados**: Ambos botones permanecen deshabilitados (`disabled={true}`), indicando en su `title` que se debe seleccionar 1 usuario.
   - **1 usuario seleccionado**: Ambos botones se habilitan automáticamente (`disabled={false}`).
     - Al pulsar `ÁREAS`, se abre el diálogo modal "Accesos — {nombre_usuario}" con la pestaña de **Áreas** activa por defecto.
     - Al pulsar `ACCESOS`, se abre el diálogo modal "Accesos — {nombre_usuario}" con la pestaña de **Plataformas** activa por defecto (o aviso Toast si es superadmin por contar con acceso irrestricto).
   - **Más de 1 usuario seleccionado**: Ambos botones se deshabilitan preventivamente (`disabled={true}`).
3. **Modal Unificado con Pestañas y Dual Picklist (`UserAccessPanel`)**:
   - Dentro del panel modal de accesos, el administrador puede alternar libremente entre las pestañas **Áreas** y **Plataformas** mediante botones de control segmentado con contadores en tiempo real.
   - **Pestaña Áreas**: Dispone de un *Dual Picklist* para transferir áreas entre "Sin acceso" y "Con acceso". Al guardar, envía `PUT /api/v1/users/{id}/areas` con `area_ids`, actualizando de inmediato la pertenencia y habilitando la elegibilidad de plataformas de dichas áreas.
   - **Pestaña Plataformas**: Dispone de un *Dual Picklist* para transferir plataformas entre "Sin acceso" y "Con acceso". Al guardar, invoca el aprovisionamiento o revocación correspondiente (`api.grantPlatformAccess` / `api.revokeAccess`).
   - Ambas pestañas disponen de buscadores independientes, gestión accesible de foco (`useFocoTrasMover`) y notificaciones Toast al completar las modificaciones.

### Ejemplo

Un administrador de TI necesita asignar a un empleado al área "Finanzas" y posteriormente otorgarle acceso al sistema "Contabilidad". En la tabla de usuarios selecciona a dicho empleado y presiona el botón **Áreas**. En el modal que se abre, busca "Finanzas" en la columna de la izquierda y hace clic para transferirla a la derecha, guardando los cambios. Inmediatamente o desde la pestaña contigua **Plataformas**, "Contabilidad" ya aparece como elegible para otorgar el acceso sin necesidad de navegar a otros módulos.

### Impacto

Afecta a [users-list.tsx](../frontend/src/components/users-list.tsx), [user-access-panel.tsx](../frontend/src/components/users/user-access-panel.tsx), [user-access-panel.test.tsx](../frontend/tests/components/users/user-access-panel.test.tsx) y [users-list.test.tsx](../frontend/tests/components/users-list.test.tsx).

## Deshabilitación del Acceso a Plataformas para Usuarios sin Áreas Asignadas

## Usuarios

### Regla

1. **Inhabilitación Estricta de Acceso a Plataformas sin Áreas**: Un usuario que no pertenezca al menos a un área organizativa (`user.areas.length === 0`) no puede tener habilitada la acción de concesión de plataformas:
   - **En la barra de herramientas de Usuarios (`users-list.tsx`)**: El botón `ACCESOS` permanece deshabilitado (`disabled={true}`) para usuarios sin áreas asignadas, mostrando el tooltip y título explicativo: `"El usuario no tiene áreas asignadas. Asigna al menos 1 área primero"`. El botón `ÁREAS` permanece habilitado para permitirle al administrador otorgar las áreas requeridas.
   - **En el panel modal de accesos (`user-access-panel.tsx`)**: La pestaña de `Plataformas` permanece inhabilitada (`disabled={true}`) mientras el usuario no cuente con áreas asignadas (`areasConAcceso.length === 0`), con tooltip explicativo. Si por alguna vía se visualiza la sección de plataformas, se despliega una nota de estado indicando: `"El usuario no tiene áreas asignadas. Ve a la pestaña de Áreas y asigna al menos una para poder otorgarle acceso a plataformas."`, impidiendo el envío de concesiones inválidas.
2. **Coherencia con las Reglas de Negocio del Backend**: Esta restricción previene solicitudes y concesiones destinadas a fallar, dado que el backend (`rules.validar_otorgamiento`) exige estrictamente que la plataforma pertenezca a un área donde el usuario esté registrado (`plataforma.area_id in usuario.areas`).

### Ejemplo

Un administrador registra a un nuevo usuario pero aún no le asigna ningún área. Al seleccionarlo en la tabla de usuarios, observa que el botón **Accesos** se encuentra en gris deshabilitado y con el mensaje "El usuario no tiene áreas asignadas. Asigna al menos 1 área primero", mientras que el botón **Áreas** está activo. El administrador pulsa **Áreas**, le asigna el área "Sistemas" y guarda. Inmediatamente el botón **Accesos** se ilumina y se activa, permitiendo ahora otorgarle las plataformas correspondientes a Sistemas.

### Impacto

Afecta a [users-list.tsx](../frontend/src/components/users-list.tsx), [user-access-panel.tsx](../frontend/src/components/users/user-access-panel.tsx) y [users-list.test.tsx](../frontend/tests/components/users-list.test.tsx).

## Sección de Importación Masiva (Bulk Import) en Ajustes

## Configuración y Ajustes

### Regla

1. **Acceso Exclusivo de Superadministrador**: La sección de **Importación masiva** se integra como una pestaña dedicada dentro del módulo de **Ajustes** (`/settings`, pestaña `bulk-import`), visible y ejecutable única y exclusivamente por usuarios con rol `administrador`. Los usuarios sin permisos de superadministración no visualizan la pestaña ni pueden invocar sus endpoints.
2. **Entidades Soportadas y Plantillas**:
   - Soporta la importación masiva de **Usuarios y Cuentas** (`users`), **Áreas** (`areas`) y **Plataformas** (`platforms`).
   - Provee descarga de plantillas oficiales en formato CSV con cabeceras y ejemplos preconfigurados (`GET /api/v1/import/template/{entity}`).
3. **Flujo de Carga, Parseo y Previsualización**:
   - Permite la entrada de datos vía archivo (`.csv`, `.txt`, `.json`) o mediante texto pegado directamente.
   - Analiza y previsualiza los registros utilizando `DataTable`, asignando dinámicamente un distintivo de validación fila por fila:
     - **Válido**: Datos completos y sintácticamente correctos.
     - **Error**: Detalle explícito de la discrepancia (ej. correo inválido, campos obligatorios vacíos, área inexistente).
   - Muestra métricas consolidadas en tiempo real: Total de filas, Filas válidas y Filas con error.
4. **Seguridad y Restricciones de Carga**:
   - **Prohibición de Escalación de Privilegios**: Ningún registro en la importación masiva puede crearse con rol `administrador`. Las solicitudes de cuentas de superadministrador son rechazadas con error de seguridad. Solo se permite el aprovisionamiento de roles `usuario` y `admin_area`.
   - **Saneamiento Automático**: Todos los nombres de usuario, áreas y plataformas son procesados mediante `sanitize_display_name` para evitar caracteres de control o inyecciones XSS.
   - **Auditoría Transaccional**: Toda ejecución de importación masiva queda registrada en el módulo de auditoría del sistema con el detalle del número de altas efectuadas.

### Ejemplo

Un superadministrador desea incorporar 25 nuevos empleados al portal. Se dirige a **Ajustes**, hace clic en la pestaña **Importación masiva**, selecciona la entidad **Usuarios y Cuentas** y descarga la plantilla CSV. Rellena las filas con los nombres, correos y áreas correspondientes y arrastra el archivo al panel. La interfaz previsualiza los 25 registros en una tabla accesible, indicando que 24 son válidos y 1 tiene un correo mal formateado. El administrador presiona "Importar 24 registros válidos", el sistema procesa el lote en el backend, registra el evento en auditoría y muestra una confirmación Toast de éxito.

### Impacto

Afecta a [bulk_import_api.py](../app/modules/bulk_import/api.py), [services.py](../app/modules/bulk_import/services.py), [bulk-import-tab.tsx](../frontend/src/components/settings/bulk-import-tab.tsx), [settings-panel.tsx](../frontend/src/components/settings-panel.tsx), [settings-tabs.ts](../frontend/src/components/settings/settings-tabs.ts), [api.ts](../frontend/src/lib/api.ts) y [test_bulk_import.py](../tests/test_bulk_import.py).

## Asignación Múltiple de Áreas y Accesos a Plataformas en Usuarios

## Usuarios

### Regla

1. **Soporte de Selección Múltiple para Áreas y Accesos**:
   - En la lista de usuarios (`UsersList`), tanto el botón `ÁREAS` como el botón `ACCESOS` permiten ser accionados cuando hay 1 o más usuarios seleccionados (`activeSelectedIds.size >= 1`).
   - El botón `ÁREAS` permanece habilitado siempre que haya al menos 1 usuario seleccionado, permitiendo asignar o desasignar áreas organizativas en lote a todos los usuarios seleccionados simultáneamente.
   - El botón `ACCESOS` está habilitado si hay al menos 1 usuario seleccionado **y ninguno** de los usuarios seleccionados carece de áreas asignadas (`algunoSinAreas === false`). Si uno o más usuarios seleccionados no tienen áreas asignadas, el botón se deshabilita con el mensaje: `"Uno o más usuarios seleccionados no tienen áreas asignadas. Asigna al menos 1 área primero"`.
2. **Modal Multi-Usuario (`UserAccessPanel`)**:
   - El modal adapta su título e indicadores: exhibe `"Accesos — {N} usuarios seleccionados"` y un bloque contextual que desglosa la selección múltiple.
   - En la pestaña **Áreas**, la asignación o desvinculación se aplica a cada uno de los usuarios seleccionados mediante peticiones concurrentes a `PUT /api/v1/users/{id}/areas`.
   - En la pestaña **Plataformas**, otorgar o revocar plataformas aplica la acción (`api.grantPlatformAccess` / `api.revokeAccess`) a través de todos los usuarios seleccionados, excluyendo automáticamente a los superadministradores que ya cuentan con acceso universal.
   - Todas las operaciones multi-usuario informan el resultado a través de notificaciones Toast unificadas.

### Ejemplo

Un administrador selecciona 5 usuarios pertenecientes al departamento de Finanzas. Con los 5 seleccionados, presiona el botón **Accesos**. El modal de accesos se abre indicando "Accesos — 5 usuarios seleccionados". El administrador busca la plataforma "SAP Concur" en la columna de sin acceso, la transfiere a con acceso y presiona "Guardar". El sistema otorga el acceso a SAP Concur a los 5 usuarios de forma concurrente y notifica mediante un Toast: "Accesos actualizados para 5 usuarios".

### Impacto

Afecta a [users-list.tsx](../frontend/src/components/users-list.tsx), [user-access-panel.tsx](../frontend/src/components/users/user-access-panel.tsx), [user-access-panel.test.tsx](../frontend/tests/components/users/user-access-panel.test.tsx) y [users-list.test.tsx](../frontend/tests/components/users-list.test.tsx).

## Contraseña inicial de onboarding entregada por Send (FNC-138, ADR-008)

### Regla

El portal fija **solo la contraseña inicial** de una cuenta del directorio (alta); luego el superadmin puede cambiarla desde «Editar usuario» (FNC-161: cuenta `ldap` → Password Modify con la política, cuenta `local` → hash en la BD); el resto del ciclo sigue en Authelia. La contraseña cumple la política vigente (`PASSWORD_POLICY_*`, siempre validada en el backend), se escribe en OpenLDAP con Password Modify y se entrega por un Send de Vaultwarden (usuario, contraseña y URL del portal) con **solo el enlace** por correo. Nunca se guarda en la BD, la auditoría ni los logs, ni se manda en claro. Si Vaultwarden, el correo o las notificaciones fallan, la cuenta se crea igual con `credentials_status: pendientes` y el worker reintenta con una **contraseña nueva** en cada intento (`PROVISIONING_MAX_ATTEMPTS`); agotados los intentos se avisa a los superadmins, que fijan la contraseña desde «Editar usuario» (el reenvío se retiró en FNC-161). Si la `ppolicy` del directorio rechaza la contraseña, el alta responde `422` en `fields.password` y no se crea nada.

### Ejemplo

Alta de `ana.ruiz` con Vaultwarden caído: la cuenta y su entrada se crean, el estado es `pendientes`; al volver el servicio, el worker genera otra contraseña, la escribe en LDAP, crea el Send y manda el enlace.

### Impacto

`POST /users/directory`, `GET /users/password-policy`, `POST /users/<id>/credentials`, `credentials_status` en `ManagedUser`, tabla `credential_deliveries` (migración 0015), worker, plantillas `credenciales_iniciales` y `credenciales_no_entregadas`, modal de alta.

## Orden de Acciones en la Barra de Herramientas de Usuarios

## Usuarios

### Regla

En la barra de herramientas superior de la vista de Usuarios (`/admin/users`), los botones de gestión de accesos y estructura organizativa se ordenan de izquierda a derecha de la siguiente forma:

1. `ACCESOS` (`Icono nombre="solicitudes"`): Gestión y consulta de plataformas a las que tiene acceso el usuario o los usuarios seleccionados.
2. `ÁREAS` (`Icono nombre="areas"`): Asignación y desvinculación de áreas organizativas del usuario o los usuarios seleccionados.
3. `Editar` (`Icono nombre="editar"`): Edición del perfil de usuario seleccionado.
4. `Eliminar` (`Icono nombre="eliminar"`): Baja individual o masiva de usuarios seleccionados.
5. `Nuevo` (`Icono nombre="mas"`): Alta de nueva cuenta en el directorio.

### Ejemplo

Al acceder a `/admin/users`, un administrador observa en la barra de acciones superior a la derecha el botón "Accesos" en primer lugar, seguido inmediatamente por el botón "Áreas", ubicando en primer plano la consulta directa de permisos a plataformas.

### Impacto

Afecta a [users-list.tsx](../frontend/src/components/users-list.tsx) y [users-list.test.tsx](../frontend/tests/components/users-list.test.tsx).

## Columna de Administradores y Orden de Acciones en la Tabla de Áreas

## Áreas

### Regla

1. **Columna Admin en la Tabla de Áreas**:
   - En la vista principal de Áreas (`/admin/areas`), la tabla `AreasList` incorpora la columna dedicada `Admin`, situada entre `Descripción` y `Plataformas`.
   - Muestra el nombre de las cuentas con rol `admin_area` que administran dicha área (`area.admins` / `area.admin_names`). Si no cuenta con administradores delegados, despliega el texto `"Sin asignar"` en cursiva.
   - El backend serializa los administradores activos de cada área en `GET /api/v1/areas` (`admins` y `admin_names`).
2. **Orden de Acciones en la Barra de Herramientas de Áreas**:
   - En la barra de herramientas de `/admin/areas`, las acciones de fila seleccionada se ordenan de izquierda a derecha de la siguiente manera:
     1. `ACCESOS` (`Icono nombre="solicitudes"`): Gestión de usuarios asignados al área.
     2. `ADMINS` (`Icono nombre="usuarios"`): Asignación y desvinculación de administradores delegados del área (visible solo para superadmin).
     3. `Editar` (`Icono nombre="editar"`): Modificación de datos y estilo del área.
     4. `Eliminar` (`Icono nombre="eliminar"`): Baja del área (restringida si tiene plataformas o usuarios).
     5. `Nuevo` (`Icono nombre="mas"`): Creación de nueva área.

### Ejemplo

Al ingresar al catálogo de áreas en `/admin/areas`, un superadmin observa en la tabla la columna "Admin" con el nombre del administrador responsable de cada área (ej. "Admin de Área Demo"). En la barra de herramientas superior, el botón "Accesos" precede al botón "Admins", unificando el criterio de orden con la pantalla de Usuarios donde las acciones operativas de accesos se ubican en primer término.

### Impacto

Afecta a [routes.py](../app/modules/api/routes.py), [types.ts](../frontend/src/lib/types.ts), [areas-list.tsx](../frontend/src/components/areas-list.tsx) y [areas-list.test.tsx](../frontend/tests/components/areas-list.test.tsx).

## Paso de Accesos con Dual Picklist y Asignación de Administradores en Nueva Área

## Áreas

### Regla

1. **Flujo de 3 Pasos en el Asistente de Áreas (`AreaForm`)**:
   - El formulario modal de creación y edición de áreas (`AreaForm`) pasa a contar con 3 pasos secuenciales y accesibles:
     1. **Paso 1: Descripción**: Captura del Nombre (obligatorio) y la Descripción del área.
     2. **Paso 2: Estilo**: Selección de color visual, icono representativo, vista previa interactiva y estado (Activa / Inactiva).
     3. **Paso 3: Accesos**: Asignación rápida de usuarios y administradores delegados del área mediante un *Dual Picklist*.
   - La barra de navegación superior (`nav[aria-label="Progreso del formulario"]`) refleja los 3 pasos (`1. Descripción`, `2. Estilo`, `3. Accesos`), permitiendo navegación directa entre pasos validados y marcando con un cotejo (`✓`) los pasos completados.
2. **Dual Picklist en el Paso 3 (Accesos)**:
   - **Columna Izquierda ("Sin acceso")**: Despliega la lista de usuarios del sistema que aún no pertenecen al área. Incluye buscador en tiempo real, contador de usuarios y acción rápida para "Agregar todos" los filtrados. La pulsación de un usuario o su control `+` lo transfiere inmediatamente a la columna derecha.
   - **Columna Derecha ("Con acceso")**: Despliega los usuarios incorporados al área. Incluye buscador, contador de miembros y acción para "Quitar todos".
3. **Casilla de Administrador (`Admin`) por Usuario**:
   - Cada usuario dentro de la columna "Con acceso" dispone de una casilla de verificación accesible (`Checkbox` con etiqueta `Admin` y área táctil $\ge 48\text{ px}$).
   - Al marcar la casilla, el usuario es designado como administrador del área.
   - Al guardar (`save`):
     - El área se crea o actualiza (`api.createArea` / `api.updateArea`).
     - Se asignan los miembros seleccionados al área mediante `api.setAreaUsers(areaId, userIds)`.
     - Para los usuarios marcados como `Admin`: si no cuentan con rol `admin_area`, se les promueve (`api.updateUser(userId, { role: 'admin_area' })`) y se añade la nueva área a su lista de áreas administradas mediante `usersApi.setManagedAreas(userId, [...areasActuales, areaId])`.
     - Al retirar a un usuario del área o desmarcar su casilla de administrador, se retira el área de sus áreas administradas.
4. **Guardado Flexible y Accesibilidad**:
   - En el Paso 2 se mantiene disponible el botón "Guardar" para permitir guardar el área de forma directa sin requerir avanzar obligatoriamente al Paso 3 si no se desean agregar usuarios en ese momento.
   - Todos los controles interactivos respetan el área táctil mínima de 48 px (`min-h-12`, `min-w-12`), los tokens de diseño y anuncios para lectores de pantalla (`RegionDeAnuncios`).

### Ejemplo

Un superadministrador pulsa "Nueva área". En el Paso 1 escribe "Logística" y presiona "Siguiente". En el Paso 2 selecciona el color y el icono del área y presiona "Siguiente: Accesos". En el Paso 3 busca a "Carlos" en la columna de la izquierda y hace clic sobre él, trasladándolo a la columna "Con acceso". En la fila de Carlos marca la casilla "Admin". Al presionar "Crear área", el sistema crea el área "Logística", asocia a Carlos como miembro del área y le otorga el rol y administración de "Logística", todo en una sola operación ágil y sin pasos manuales posteriores.

### Impacto

Afecta a [area-form.tsx](../frontend/src/components/areas/area-form.tsx) y [areas-list.test.tsx](../frontend/tests/components/areas-list.test.tsx).

## Definición y Aislamiento de Permisos por Rol: Superadmin, Admin de Área y Usuario

## Autorización y Permisos

### Regla

1. **Superadministrador (`superadmin` / `administrador`)**:
   - Acceso irrestricto y completo a todas las secciones, módulos y funcionalidades del sistema (Dashboard, Plataformas, Administrar plataformas, Conectores, Áreas, Usuarios, Auditoría, Ajustes y Ejecuciones).
   - Es el único rol con facultades para crear nuevas áreas en el sistema (`POST /api/v1/areas`) y para designar o revocar administradores de área (`role: 'admin_area'` y asignación en `managed_areas`).
   - Puede dar de alta, editar y desvincular plataformas y usuarios en cualquier área registrada.

2. **Administrador de Área (`admin` / `admin_area`)**:
   - Ámbito operativo delimitado exclusivamente a las áreas que tiene asignadas como administrador (`session.managed_areas` / `current_user.managed_areas`).
   - En la administración de plataformas (`/admin/platforms`), únicamente puede consultar, listar y gestionar las plataformas pertenecientes a las áreas donde es administrador.
   - Puede dar de alta nuevas plataformas únicamente dentro de sus áreas administradas.
   - Puede dar de alta nuevas cuentas de usuario en el directorio y asociarlas a sus áreas, asignándoles el rol estándar de usuario (`role: 'usuario'`).
   - **Prohibiciones estrictas**: No puede dar de alta usuarios con privilegios de administrador (`admin_area` ni `administrador`) ni crear nuevas áreas. En la interfaz, el botón "Nueva área" permanece oculto para este rol, y en los asistentes de área las opciones y casillas para designar administradores quedan deshabilitadas con indicador de solo lectura y mensaje accesible.

3. **Usuario Estándar (`usuario`)**:
   - Acceso exclusivo al portal y catálogo de solicitud de plataformas (`/platforms` con `PlatformsView` y `RequestCatalog`).
   - No tiene acceso a pantallas de gestión ni de configuración global (Dashboard, Gestión de plataformas, Áreas, Usuarios, Conectores, Ajustes, Ejecuciones ni Auditoría).
   - En el menú principal (`entradasVisibles`), tanto en la barra lateral como en el menú móvil, solo se despliega la opción "Plataformas" (`/platforms`).
   - Si un usuario estándar ingresa a la raíz del portal (`/`), la compuerta de navegación (`DashboardGate`) lo redirige automáticamente a `/platforms`.
   - Se incorpora un acceso directo interactivo con área táctil accesible ($\ge 48\text{ px}$) en la barra superior (`BarraSuperior` en el adminboard), situado a un costado del interruptor de tema claro/oscuro, garantizando el acceso inmediato al catálogo de solicitudes.

### Ejemplo

- Un usuario con rol `usuario` inicia sesión: la barra lateral muestra únicamente la entrada "Plataformas", la barra superior incluye el botón con icono de plataformas junto al selector de tema, y al intentar acceder al Dashboard es redirigido a `/platforms`, donde puede visualizar el catálogo de plataformas de sus áreas y solicitar permisos.
- Un usuario con rol `admin_area` para el área de "Finanzas": ingresa al portal y en la lista de áreas observa únicamente "Finanzas"; el botón "Nueva área" no se muestra. Al crear o consultar plataformas en `/admin/platforms`, solo visualiza y puede asociar plataformas al área de "Finanzas". En la pantalla de usuarios, puede dar de alta nuevos usuarios pero no puede conferirles rol de administrador.
- Un `superadmin`: visualiza la totalidad de áreas y plataformas, puede pulsar "Nueva área", asignar administradores de área en el paso 3 de accesos y realizar cualquier cambio administrativo global.

### Impacto

Afecta a [nav-items.ts](../frontend/src/components/marco/nav-items.ts), [barra-superior.tsx](../frontend/src/components/marco/barra-superior.tsx), [dashboard-gate.tsx](../frontend/src/components/dashboard-gate.tsx), [page.tsx](../frontend/src/app/page.tsx), [platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [areas-list.tsx](../frontend/src/components/areas-list.tsx), [area-form.tsx](../frontend/src/components/areas/area-form.tsx), [users-list.tsx](../frontend/src/components/users-list.tsx), [settings/page.tsx](../frontend/src/app/settings/page.tsx), [audit/page.tsx](../frontend/src/app/audit/page.tsx), [marco-nav.test.ts](../frontend/tests/lib/marco-nav.test.ts), [navegacion-por-rol.test.tsx](../frontend/tests/components/navegacion-por-rol.test.tsx), [menu-movil.test.tsx](../frontend/tests/components/menu-movil.test.tsx), [areas-list.test.tsx](../frontend/tests/components/areas-list.test.tsx), [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx) y [marco-admin.test.tsx](../frontend/tests/components/marco-admin.test.tsx).

## Reestructuración del Asistente de Plataformas: Vista Previa en Paso 2 y Dual Picklist de Accesos en Paso 3

## Administración de Plataformas

### Regla

1. **Flujo de 3 Pasos Reorganizado**:
   - **Paso 1: Descripción**: Nombre (`name`), Descripción (`description`), Enlace directo (`direct_link`).
   - **Paso 2: Diseño y Activación**: Identidad visual (colores de fondo y texto, selector de icono o subida de imagen), **Vista previa en tiempo real de la plataforma** y el **Interruptor (Toggle) de Estado Activo/Inactivo**. Al consolidar aquí la vista previa y la activación, el administrador valida visualmente la tarjeta de la plataforma y su disponibilidad inmediatamente tras configurar su apariencia.
   - **Paso 3: Accesos**: Se renombra formalmente de "Vista previa" a "Accesos". Integra un componente **Dual Picklist** accesible de dos columnas:
     - **Columna Izquierda ("Sin acceso")**: Muestra a los usuarios pertenecientes al área de la plataforma (`form.area_id`) que actualmente no disponen de acceso a la misma. Incluye buscador reactivo, contador y acción rápida "Agregar todos".
     - **Columna Derecha ("Con acceso")**: Muestra a los usuarios autorizados para acceder a la plataforma. Incluye buscador reactivo, contador y acción rápida "Quitar todos".
2. **Transferencia e Interacción**:
   - Transferencia ágil con un solo clic: al pulsar sobre un usuario en "Sin acceso", este se transfiere a "Con acceso" con la insignia `Nuevo`. Al pulsar en "Con acceso", se transfiere de regreso a "Sin acceso".
3. **Persistencia Directa de Accesos al Guardar**:
   - Al pulsar "Guardar", se crea o actualiza la plataforma (`api.createPlatform` o `api.updatePlatform`).
   - Para los usuarios añadidos a "Con acceso", el sistema invoca de inmediato `api.grantPlatformAccess(platformId, userId, 'usuario')`.
   - Para los usuarios retirados en edición, se invoca `api.revokeAccess(accessId, 'Retirado por administrador')`.
4. **Accesibilidad y Sistema 8pt**:
   - Modal ampliado a `size="2xl"` para máxima legibilidad de la doble columna.
   - Área táctil $\ge 48\text{ px}$ (`min-h-12`) en todos los botones de transferencia y acciones en lote.
   - Foco preservado tras mover (`useFocoTrasMover`) y anuncios audibles con `RegionDeAnuncios`.

### Ejemplo

Al crear una plataforma para el área "Finanzas", en el Paso 2 el administrador elige el color azul, el icono de catálogo y ve en tiempo real la tarjeta generada junto con el interruptor "Activa". Al presionar "Siguiente", llega al Paso 3 "Accesos", donde visualiza a los usuarios de "Finanzas". Hace clic sobre "Carlos" y "Lucía" para otorgarles acceso directo a la plataforma, o pulsa "Agregar todos". Al presionar "Guardar", la plataforma se crea y ambos usuarios reciben de inmediato sus accesos sin necesidad de gestionar permisos por separado.

### Impacto

Afecta a [platform-form.tsx](../frontend/src/components/platforms/platform-form.tsx) y [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Bloqueo Obligatorio por Carta Responsiva de TI en Primer Ingreso

## Autenticación y Cumplimiento

### Regla

1. **Gatekeeper de Primer Ingreso (Consent Gate)**:
   - Todo usuario que cuente con `responsiva_firmada = False` en su cuenta queda confinado de forma estricta e infranqueable a la pantalla de **Carta Responsiva de Uso de Activos de Información y Plataformas Institucionales** (`PantallaResponsiva` en `AppShell`).
   - El sistema oculta por completo el marco de administración (`Marco`), la barra lateral, la barra superior, el menú móvil y cualquier contenido o plataforma pre-asignada.
   - Cualquier intento de navegación directa por URL (por ejemplo hacia `/`, `/platforms`, `/admin/platforms` o `/settings`) es interceptado por `AppShell`, manteniendo al usuario bloqueado en la vista de responsiva.
2. **Defensa en Profundidad en Backend**:
   - En la API Flask (`api_bp.before_request`), cualquier solicitud autenticada de un usuario con responsiva pendiente (distinto de `administrador`) es rechazada con código HTTP `403 Forbidden` (`code: 'responsiva_requerida'`), exceptuando exclusivamente `GET /api/v1/me` (consulta de sesión), `GET /api/v1/responsiva` (lectura de términos y plataformas) y `POST /api/v1/me/firmar-responsiva` (registro de firma).
   - El rol `administrador` (superadmin) queda exento del bloqueo por facultad operativa de gobernanza global.
3. **Firma y Desbloqueo Atómico**:
   - El usuario visualiza la lista de áreas y plataformas asignadas sobre las que asume responsabilidad.
   - Debe marcar la casilla de verificación obligatoria para habilitar el botón de firma.
   - Al pulsar "Firmar y acceder al portal", se ejecuta `POST /api/v1/me/firmar-responsiva`:
     - Se registra `responsiva_firmada = True` y `responsiva_firmada_at` con fecha y hora UTC.
     - Se emite un evento en la bitácora de auditoría (`audit_log`) con acción `firma_responsiva`, IP de origen y versión del documento.
     - El frontend actualiza de forma reactiva el estado de la sesión, desmontando la pantalla de bloqueo y permitiendo el acceso normal al portal.
4. **Relación con el SSO de Authelia**:
   - Authelia funge como proveedor de identidad exterior (valida usuario y contraseña contra LDAP).
   - Al validar las credenciales, Authelia redirige al usuario al portal.
   - Es el portal (Next.js + Flask) el que inspecciona el estado de la responsiva tras la autenticación y ejecuta el confinamiento antes de permitir el acceso a cualquier recurso.

### Ejemplo

Un administrador de área da de alta a "Pedro" y le asigna el área de "Operaciones" y la plataforma "Jira". Cuando Pedro inicia sesión por primera vez a través de Authelia, Authelia valida su cuenta y lo envía a la URL del portal. En ese instante, `AppShell` detecta que Pedro tiene `responsiva_firmada: false`. En lugar de mostrarle el catálogo o menú, le presenta en pantalla completa la Carta Responsiva indicando: "Hola, Pedro. Se te han asignado los siguientes activos: Área Operaciones, Plataforma Jira Software". Pedro no puede saltarse la pantalla ni navegar a otra sección. Lee los términos, marca la casilla "He leído y acepto los términos..." y presiona "Firmar y acceder al portal". El sistema registra la firma en auditoría y en ese momento se desbloquea el portal, dándole la bienvenida a su espacio de trabajo. En logins posteriores, el portal lo lleva directamente a sus plataformas sin volver a solicitarle la firma.

### Impacto

Afecta a [pantalla-responsiva.tsx](../frontend/src/components/responsiva/pantalla-responsiva.tsx), [app-shell.tsx](../frontend/src/components/app-shell.tsx), [session-provider.tsx](../frontend/src/components/session-provider.tsx), [routes.py](../app/modules/api/routes.py), [models.py](../app/modules/auth/models.py), [types.ts](../frontend/src/lib/types.ts), [api.ts](../frontend/src/lib/api.ts), [0014_responsiva_de_usuario.py](../migrations/versions/0014_responsiva_de_usuario.py) y las suites de pruebas [responsiva.test.tsx](../frontend/tests/components/responsiva.test.tsx) y [test_responsiva.py](../tests/test_responsiva.py).

## Modal Integrado de Responsiva y Aprovisionamiento Condicionado (Deferred Provisioning)

## Autenticación, Accesos y Cumplimiento

### Regla

1. **Modal Directo en el Portal (Sin Páginas Ni Rutas Separadas)**:
   - La carta responsiva opera directamente sobre el marco del portal (`Marco` en [app-shell.tsx](../frontend/src/components/app-shell.tsx)) mediante el componente unificado [modal-responsiva.tsx](../frontend/src/components/responsiva/modal-responsiva.tsx).
   - No se crean páginas externas, rutas nuevas (`/responsiva`) ni elementos huérfanos de navegación: el usuario se autentica e ingresa a su portal institucional con normalidad, desplegándose de inmediato el diálogo modal con fondo desenfocado sobre el catálogo de plataformas.
   - El diálogo no permite cierre accidental (clic fuera o tecla Escape muestran aviso de firma obligatoria) y ofrece la opción explícita de "Cerrar sesión" si el usuario no desea aceptar los términos en ese momento.
2. **Aprovisionamiento Condicionado en Backend (Deferred Provisioning)**:
   - Cuando un administrador otorga o asigna plataformas a un usuario que tiene `responsiva_firmada = False`, el acceso se registra en base de datos en estado `en_proceso` pero **se retiene el despacho del trabajo de aprovisionamiento** en [services.py](../app/modules/access/services.py) (`acceso.last_job_id = None`).
   - El usuario **no es insertado en los grupos de LDAP ni en los conectores de las plataformas** mientras la responsiva permanezca pendiente.
   - Si el usuario intentara navegar directamente por URL externa hacia la plataforma (ej. `https://jira.empresa.local`), Authelia consulta al directorio LDAP y al verificar que el usuario no pertenece al grupo de la plataforma, deniega el paso con código HTTP 403 Forbidden.
   - Los enlaces directos (`direct_link`) se enmascaran como `null` en `GET /api/v1/platforms` para usuarios sin responsiva firmada.
3. **Liberación Atómica de Aprovisionamiento**:
   - Al marcar la casilla de aceptación y pulsar "Firmar y acceder al portal" en el modal, se ejecuta `POST /api/v1/me/firmar-responsiva` en [routes.py](../app/modules/api/routes.py).
   - El backend marca `responsiva_firmada = True`, registra la fecha y la auditoría, e **inicia de inmediato el encolado de aprovisionamiento** (`queue.encolar`) para todas las plataformas pendientes del usuario.
   - La sesión reactiva del frontend cierra el modal y el usuario queda de inmediato interactuando con su catálogo en el portal.

### Ejemplo

Un empleado de nuevo ingreso recibe sus credenciales e ingresa al portal institucional. Al autenticarse con Authelia, llega a su pantalla habitual de plataformas en el portal. En ese instante, sobre el portal se despliega el modal de Carta Responsiva informándole las plataformas pre-asignadas. En LDAP, el usuario aún no forma parte de los grupos, por lo que no puede eludir el control ingresando directo a los enlaces externos. Al leer los lineamientos, marcar la casilla y pulsar "Firmar y acceder al portal", el modal se cierra fluidamente, se encola su alta en LDAP/conectores y el portal queda 100% activo y operativo. En ingresos posteriores, el modal ya no vuelve a mostrarse.

### Impacto

Afecta a [modal-responsiva.tsx](../frontend/src/components/responsiva/modal-responsiva.tsx), [app-shell.tsx](../frontend/src/components/app-shell.tsx), [services.py](../app/modules/access/services.py), [routes.py](../app/modules/api/routes.py), [test_responsiva.py](../tests/test_responsiva.py) y [responsiva.test.tsx](../frontend/tests/components/responsiva.test.tsx).

## Detección de Nuevos Accesos Aprobados y Exigencia de Responsiva al Ingreso al Portal

## Solicitudes, Accesos y Cumplimiento

### Regla

1. **Detección de Accesos Aprobados Pendientes**:
   - Cada vez que un usuario solicita una plataforma y la solicitud es aprobada por un administrador (o cuando un administrador le otorga una nueva plataforma directamente), el nuevo registro en `platform_access_grants` nace con `responsiva_firmada = False` y aprovisionamiento retenido (`last_job_id = None`).
   - Al ingresar o navegar en el portal institucional, `GET /api/v1/me` evalúa si el usuario cuenta con accesos vigentes pendientes de firma (`responsiva_firmada is False`).
   - Si se detectan accesos aprobados pendientes, la sesión reporta `responsiva_firmada: false`, activando de forma automática el modal de responsiva [modal-responsiva.tsx](../frontend/src/components/responsiva/modal-responsiva.tsx) sobre el catálogo de plataformas.
2. **Contexto Visual de Aprobación de Accesos**:
   - El modal adapta su título y mensaje explicativo:  
     *Título*: *"Carta Responsiva: Aprobación de Nuevos Accesos a Plataformas"*.  
     *Encabezado*: *"Nuevos Accesos Aprobados • Confirmación Requerida"*.  
     *Detalle*: *"Tus solicitudes de acceso a las siguientes herramientas han sido aprobadas. Por favor lee y confirma la responsiva para activar su uso en tu cuenta"*.  
     *Botón de acción*: *"Firmar y activar accesos"*.
   - El modal lista únicamente las plataformas recientemente aprobadas que motivan la confirmación.
3. **Aprovisionamiento y Desbloqueo Inmediato**:
   - Al marcar la casilla y pulsar "Firmar y activar accesos", `POST /api/v1/me/firmar-responsiva` marca `responsiva_firmada = True` en el otorgamiento y despacha los trabajos de aprovisionamiento a los grupos de LDAP y conectores correspondientes.
   - La sesión del frontend se actualiza, el modal se retira y las tarjetas de las nuevas plataformas quedan disponibles con sus enlaces directos habilitados.

### Ejemplo

"Laura" ya trabaja en la empresa y firmó su responsiva marco hace tres meses. Hoy solicita acceso a "SAP ERP" para tareas de contabilidad. El administrador de área aprueba su solicitud en la bandeja de aprobaciones. Cuando Laura ingresa al portal institucional, el sistema detecta que tiene un acceso aprobado pendiente de confirmación de responsiva. De inmediato se despliega el modal informándole: "¡Tus solicitudes de acceso han sido aprobadas! Plataforma: SAP ERP". Laura marca la casilla y presiona "Firmar y activar accesos". En ese momento, el backend encola su alta en el grupo LDAP de SAP, el modal se cierra y Laura puede ingresar a SAP ERP sin contratiempos.

### Impacto

Afecta a [modal-responsiva.tsx](../frontend/src/components/responsiva/modal-responsiva.tsx), [routes.py](../app/modules/api/routes.py), [services.py](../app/modules/access/services.py), [models.py](../app/modules/access/models.py), [0017_responsiva_en_accesos.py](../migrations/versions/0017_responsiva_en_accesos.py), [test_responsiva.py](../tests/test_responsiva.py) y [responsiva.test.tsx](../frontend/tests/components/responsiva.test.tsx).

## Firma Única Vitalicia de Responsiva Condicionada al Primer Otorgamiento de Plataformas

## Accesos, Solicitudes y Cumplimiento Normativo

### Regla

1. **Firma Única Vitalicia**: La carta responsiva de seguridad de la información y plataformas de TI se firma **UNA SOLA VEZ** en la vida del usuario dentro de la organización (`user.responsiva_firmada = True`). Una vez firmada, el usuario nunca vuelve a firmar una responsiva, sin importar cuántas plataformas solicite o le sean aprobadas en el futuro.
2. **Primer Ingreso Sin Plataformas Asignadas (Navegación y Solicitud Libre)**:
   - Si un usuario ingresa al portal institucional sin plataformas asignadas previamente (0 plataformas), el portal **no le muestra ningún modal ni bloquea su navegación**.
   - El usuario puede navegar libremente, ver las áreas y plataformas de su catálogo, y enviar solicitudes de acceso (`POST /api/v1/access-requests`).
3. **Exigencia de Responsiva al Primer Otorgamiento (Aprobación o Pre-asignación)**:
   - La responsiva se activa y se exige **únicamente cuando el usuario tiene al menos una plataforma otorgada/aprobada** y su responsiva vitalicia aún no ha sido firmada (`user.responsiva_firmada is False` y `grants_count > 0`).
   - *Caso A (Onboarding con plataformas)*: Si en el alta del usuario el administrador le pre-asignó plataformas, al entrar por primera vez al portal se le muestra la responsiva de primer ingreso antes de poder acceder a ellas.
   - *Caso B (Solicitud y Aprobación)*: Si el usuario solicitó una plataforma y el administrador aprueba la solicitud, al entrar al portal se detecta el nuevo acceso aprobado y se le despliega el modal notificándole que se le otorgó el acceso y que debe firmar la responsiva.
   - Mientras no firme, el aprovisionamiento en LDAP y conectores se retiene (`last_job_id = None`) y no se expone el enlace directo de acceso.
4. **Desbloqueo y Flujo de Plataformas Posteriores**:
   - Al marcar la casilla y firmar en el modal (`POST /api/v1/me/firmar-responsiva`), se guarda `user.responsiva_firmada = True`, se despacha el aprovisionamiento de las plataformas pendientes a LDAP y se desbloquea el portal.
   - A partir de este momento, la responsiva queda **firmada de forma permanente**.
   - Las demás plataformas que el usuario solicite en el futuro siguen el flujo habitual (solicitar y esperar aprobación, o que el admin se la otorgue directamente). Si no se la aprueban, no puede ingresar; pero una vez aprobada, el acceso se aprovisiona y queda activo de inmediato **sin volver a firmar la responsiva jamás**.

### Ejemplo

Carlos ingresa a la empresa y se le da de alta sin plataformas pre-asignadas. Al ingresar por primera vez a su portal, navega normalmente por el catálogo y solicita acceso a "Jira Software". La solicitud llega al administrador, quien la aprueba. Cuando Carlos entra a su portal, el sistema detecta que tiene su primer acceso aprobado y que aún no ha firmado su responsiva vitalicia: se despliega el modal indicándole que se le otorgó el acceso a Jira Software y que debe firmar la responsiva. Carlos lee, acepta los términos y firma; en ese instante Jira se aprovisiona y queda listo para usarse. Dos meses después, Carlos solicita "Figma" y el administrador lo aprueba. Al ingresar al portal, como Carlos ya firmó su responsiva en el pasado, el acceso a Figma se activa inmediatamente y el portal no le vuelve a pedir firmar ninguna responsiva.

### Impacto

Afecta a [routes.py](../app/modules/api/routes.py), [services.py](../app/modules/access/services.py), [modal-responsiva.tsx](../frontend/src/components/responsiva/modal-responsiva.tsx), [test_responsiva.py](../tests/test_responsiva.py) y [responsiva.test.tsx](../frontend/tests/components/responsiva.test.tsx).

## Modalidad Configurable de Responsiva (Global vs Por Plataforma) vía Variable de Entorno

## Configuración del Sistema y Cumplimiento de Accesos

### Regla

1. **Variable de Configuración en `.env`**:
   - Se incorpora la variable de entorno `RESPONSIVA_MODO` (o alternativamente `RESPONSIVA_POR_PLATAFORMA`) para definir la política de aceptación de responsivas institucional:
     - `RESPONSIVA_MODO=global` (valor por defecto si está vacío o no configurado): La responsiva se firma **una sola vez en la vida del usuario** (al primer otorgamiento). Los accesos aprobados subsecuentes se activan de inmediato sin requerir firma adicional.
     - `RESPONSIVA_MODO=por_plataforma`: Cada vez que se aprueba o asigna una nueva plataforma, el sistema exige al usuario firmar la responsiva específicamente para esa herramienta antes de que se aprovisione y quede activa en el portal.
2. **Alternativa Booleana Soportada**:
   - `RESPONSIVA_POR_PLATAFORMA=false` (equivale a `global`).
   - `RESPONSIVA_POR_PLATAFORMA=true` (equivale a `por_plataforma`).
3. **Comportamiento en Backend**:
   - Evaluado mediante la función `responsiva_por_plataforma()` en [configuracion.py](../app/modules/access/configuracion.py).
   - En [services.py](../app/modules/access/services.py), `otorgar()` consulta dicha bandera: si está en `por_plataforma`, cada nuevo acceso nace con `responsiva_firmada = False` y retiene el encolado de aprovisionamiento hasta que el usuario firme en el modal.
   - En [routes.py](../app/modules/api/routes.py), las rutas `check_responsiva()` y `me()` bloquean o exigen firma según la presencia de accesos pendientes en la tabla `platform_access_grants`.

### Ejemplo

Una empresa del sector financiero con políticas estrictas de segregación de responsabilidades configura `RESPONSIVA_MODO=por_plataforma` en su archivo `.env`. Cuando a un colaborador se le aprueba "SAP", firma la responsiva de SAP y se le activa el acceso. Semanas después solicita "Salesforce"; al ingresar al portal, el sistema le despliega el modal solicitándole la firma de responsiva correspondiente a Salesforce antes de permitirle abrirla. Por otro lado, una empresa que prefiere menor fricción define `RESPONSIVA_MODO=global`: el colaborador firma únicamente la primera vez y todas las aprobaciones posteriores quedan disponibles de inmediato.

### Impacto

Afecta a [.env.example](../.env.example), [configuracion.py](../app/modules/access/configuracion.py), [services.py](../app/modules/access/services.py), [routes.py](../app/modules/api/routes.py) y [test_responsiva.py](../tests/test_responsiva.py).

## Diseño Configurable de Plataformas y Segregación entre Vista de Usuario y Panel de Administración

## Módulo

Interfaz de Usuario, Navegación y Roles

### Regla

1. **Configuración de Diseño Exclusiva para `/platforms`**:
   - La vista del catálogo de plataformas (`/platforms`) permite elegir entre dos modos de presentación:
     - `topbar` (Solo barra superior / Launchpad): Diseño amplio sin barra lateral, contenedor centrado `max-w-7xl` y cuadrícula expansiva de 4 columnas. Es el diseño recomendado por omisión para los usuarios finales.
     - `sidebar` (Con barra lateral / Panel de control): Mantiene la barra lateral corporativa colapsable con navegación agrupada por secciones.
   - Esta elección se almacena en las preferencias de interfaz (`PreferencesTab` en `/settings`) y en el almacenamiento local del cliente (`localStorage` bajo la clave `nexus.platforms.layout`), sincronizándose en tiempo real mediante el evento `nexus:platforms-layout`.
   - **Inmutabilidad del Panel de Administración**: El cambio de diseño aplica de forma estricta y exclusiva a la vista de usuario `/platforms`. Todas las páginas y módulos administrativos (`/`, `/admin/*`, `/users`, `/areas`, `/approvals`, `/inventory`, `/settings`, `/admin/jobs`, `/audit`) permanecen inalteradas, conservando siempre su cascarón administrativo (`Marco` con barra lateral).
2. **Segregación de Vistas y Botón de Retorno para Administradores**:
   - Cuando un usuario con permisos administrativos (`session.permissions.is_admin` o `session.permissions.is_area_admin`) visita la página de plataformas (`/platforms`), la interfaz identifica su rol y expone de forma visible un botón de acción destacado: `[ ⚙️ Regresar al Panel Admin ]` que enlaza a la raíz del panel administrativo (`/`).
   - Los usuarios estándar (`rol: usuario`) no visualizan este botón ni ningún elemento del panel administrativo, garantizando una separación visual y de navegación estricta entre la experiencia del usuario y la consola de administración.

### Ejemplo

Un administrador de TI accede a `/platforms` para revisar el catálogo que ven los colaboradores. En la barra superior observa el botón `[ ⚙️ Regresar al Panel Admin ]` para retornar instantáneamente a su panel de gestión con un solo clic. Si un usuario con rol regular entra a `/platforms`, únicamente ve su catálogo de plataformas y sus herramientas asignadas sin el botón de admin ni enlaces a la consola administrativa. Si el usuario desea cambiar la presentación, acude a Ajustes > Mis Preferencias y selecciona "Con barra lateral", transformando inmediatamente su vista sin afectar al panel admin.

### Impacto

Afecta a [platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [page.tsx](../frontend/src/app/platforms/page.tsx), [preferences-tab.tsx](../frontend/src/components/settings/preferences-tab.tsx) y [platforms-layout.ts](../frontend/src/lib/platforms-layout.ts).

## Alineación y Centrado en Tarjetas de Indicadores del Dashboard

## Módulo

Dashboard y Métricas (UI/UX)

### Regla

En las tarjetas de métricas del dashboard con diseño «Dos segmentos» (`data-diseno="segmentos"`), el bloque informativo a la derecha del gráfico de anillo (compuesto por el badge con el título del indicador, la cifra principal en tipografía destacada y el porcentaje correspondiente) debe ocupar el espacio restante disponible (`flex-1`) y centrarse horizontal y verticalmente (`flex flex-col items-center justify-center text-center`). El gráfico de anillo a la izquierda mantiene su tamaño fijo sin deformación (`shrink-0`), asegurando un balance visual simétrico y evitando que el badge y los textos queden desfasados o recargados hacia el borde izquierdo dejando vacío el resto de la tarjeta.

### Ejemplo

Al visualizar las tarjetas de métricas en el dashboard principal (Áreas, Plataformas, Solicitudes, Visitas, Usuarios), el gráfico de anillo circular se muestra a la izquierda y el badge correspondiente (ej. `ÁREAS`, `PLATAFORMAS`, `USUARIOS`), junto con el número total (`2`, `0`, `4`) y el porcentaje (`50 %`, `100 %`), se despliega perfectamente centrado en todo el espacio horizontal entre la gráfica y el borde derecho de la tarjeta.

### Impacto

Afecta a [frontend/src/components/dashboard/tarjeta-indicador.tsx](../frontend/src/components/dashboard/tarjeta-indicador.tsx) y a la suite de pruebas en [frontend/tests/components/dashboard-tarjetas-indicador.test.tsx](../frontend/tests/components/dashboard-tarjetas-indicador.test.tsx).

## Segregación de Mis Solicitudes de Usuario y Exclusión del Panel de Administración

## Módulo

Portal de Usuario y Solicitudes de Acceso

### Regla

Al acceder a la sección «Mis Solicitudes» (mediante la ruta `/requests`, la píldora de navegación en la barra superior o el menú lateral del espacio de trabajo), el sistema debe mantener al usuario estrictamente dentro de la experiencia del portal de usuario (`PlatformsTopbar` o `PlatformsSidebarView`), sin redirigir ni envolver la pantalla en el cascarón del panel de administración (`Marco` / `AppShell`).
La sección despliega una tabla de datos accesible (`UserRequestsTable` basada en `DataTable`), con filtros rápidos por estado (`Todas`, `⏳ Pendientes`, `✅ Aprobadas`, `❌ Rechazadas`), campo de búsqueda y detalle de resolución. Si el usuario cuenta con permisos de administración, la barra superior conserva de manera independiente el botón `[ ⚙️ Regresar al Panel Admin ]`, manteniendo la frontera limpia entre la experiencia del colaborador y la consola administrativa.

### Ejemplo

Un usuario o administrador que se encuentra en `/platforms` hace clic en la píldora `Mis solicitudes` de la barra superior. La vista carga `/requests` conservando la identidad del portal (*VIVARO LAUNCHPAD*) y desplegando una tabla con el historial de peticiones de acceso, sus fechas, motivos y estados, sin mostrar la barra lateral de administración (`/users`, `/areas`, `/audit`). En el modo con barra lateral de usuario, hacer clic en `Mis Solicitudes` conmuta la sección dentro del mismo espacio de trabajo sin recargar la página.

### Impacto

Afecta a [frontend/src/app/requests/page.tsx](../frontend/src/app/requests/page.tsx), [frontend/src/components/platforms/user-requests-table.tsx](../frontend/src/components/platforms/user-requests-table.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx).

## Colapso y Restauración del Menú Lateral en la Vista de Espacio de Trabajo de Plataformas

## Módulo

Portal de Usuario y Espacio de Trabajo (UI/UX)

### Regla

En la vista con barra lateral del portal de usuario (`PlatformsSidebarView` en `/platforms`), la barra lateral cuenta con capacidad interactiva de colapso y restauración sin comprometer la consistencia de tokens de diseño ni los estándares de accesibilidad:

1. **Accionadores de Conmutación**:
   - **En la barra superior**: Un botón accesible (`BotonIcono`) con icono de menú (`☰`) ubicado al inicio de la cabecera, junto a la ruta de navegación (migas de pan), con estados accesibles `Expandir menú` (`aria-expanded="false"`) y `Colapsar menú` (`aria-expanded="true"`).
   - **En la barra lateral**: Un botón de acción rápida con icono `chevron-izq` ubicado en el extremo derecho del encabezado del menú lateral cuando está expandido (`Colapsar barra lateral`), y el logotipo interactivo con icono `escudo-ok` cuando está colapsado (`Expandir barra lateral`).
2. **Dimensiones y Adaptabilidad**:
   - Estado expandido: Ancho completo de 264 px (`w-lateral`), mostrando textos de navegación, títulos de sección, contadores numéricos y ficha de usuario al pie con acceso directo a ajustes.
   - Estado colapsado: Ancho reducido de 76 px (`w-lateral-colapsada`), ocultando etiquetas textuales y mostrando exclusivamente iconos centrados con atributos `title` y `aria-label` descriptivos, puntos de estado para elementos con alertas (notificaciones y solicitudes pendientes) y el avatar de usuario centrado.
3. **Persistencia**:
   - El estado de la barra se almacena en el cliente bajo la clave `nexus.platforms.sidebar_collapsed` en `localStorage`, preservando la preferencia del usuario entre sesiones y recargas.

### Ejemplo

Un usuario que utiliza el diseño con barra lateral en su espacio de trabajo desea mayor área visible para explorar sus plataformas asignadas. Hace clic en el botón de chevron en el encabezado del menú lateral (o en el botón `☰` de la barra superior). La barra lateral se contrae fluidamente a 76 px mostrando solo los iconos con sus respectivos tooltips. Al hacer clic nuevamente en el botón `☰` o en el escudo corporativo de la barra contraída, el menú lateral se expande completamente recuperando todas las etiquetas textuales y contadores.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y a la suite de pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Barra de Herramientas Estandarizada y Filtros Premium en el Espacio de Trabajo de Plataformas

## Módulo

Portal de Usuario y Catálogo de Plataformas (UI/UX)

### Regla

En la vista de espacio de trabajo de plataformas (`PlatformsSidebarView` en `/platforms`), los elementos de filtrado de "Mis Plataformas" y "Favoritas" y el buscador se integran en una barra de herramientas estandarizada de diseño premium (`border border-panel-border/80 bg-gradient-to-r from-superficie via-superficie to-superficie-hundida shadow-1 rounded-2xl p-3.5`), idéntica en estética y comportamiento al panel de administración de áreas y plataformas (DIS-081):

1. **Buscador Integrado (`nx-buscador-toolbar`)**:
   - Campo de búsqueda interactivo con icono `buscar`, altura estandarizada de 48 px (`h-12`), esquinas redondeadas (`rounded-xl`), fondo semántico (`bg-fondo`), anillo de foco accesible (`focus:ring-2 focus:ring-primary/20`) y botón de limpieza rápida (`✕`) cuando el término no está vacío.
2. **Selector de Estado/Filtro Premium**:
   - Menú desplegable con disparador de altura `h-12 min-h-12 w-48`, borde sutil y estado activo destacado (`border-primary bg-primary/10 text-primary-text`).
   - Muestra el estado activo (`Estado: Todos` o `Estado: Favoritas`) con el icono temático correspondiente (`inventario` o `favorito`) y flecha animada `chevron-abajo`.
   - Opciones accesibles con `role="option"` y contadores de plataformas disponibles, sincronizado bidireccionalmente con la barra lateral izquierda.
3. **Selector de Cuadrícula Dinámica**:
   - Menú interactivo `Cuadrícula: 2×2 / 3×3 / 4×4` (`Icono nombre="panel"`), permitiendo al usuario personalizar la distribución de columnas de la cuadrícula de tarjetas de forma reactiva (2, 3 o 4 columnas por fila).
4. **Cierre Accesible y Manejo de Foco**:
   - Ambos menús cuentan con detector de clics externos y descarte con la tecla `Escape`, manteniendo el foco accesible.

### Ejemplo

Al ingresar a su espacio de trabajo de plataformas, el usuario encuentra la barra de herramientas superior con un buscador rápido y dos controles redondeados a la derecha. Para ver solo sus herramientas prioritarias, pulsa el botón `Estado: Todos` y selecciona `Favoritas`, actualizándose inmediatamente la vista y la barra lateral. Si desea visualizar más elementos por fila, pulsa `Cuadrícula: 3×3` y elige `4×4`, adaptándose la cuadrícula automáticamente a 4 columnas.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y a la suite de pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Supresión de Encabezados Redundantes en la Vista con Barra Lateral de Plataformas

## Módulo

Portal de Usuario y Catálogo de Plataformas (UI/UX)

### Regla

En la vista con barra lateral de plataformas (`PlatformsSidebarView`), la barra de herramientas estandarizada de diseño premium (`nx-buscador-toolbar`) se posiciona en la parte superior del área de contenido como elemento de entrada principal, prescindiendo de los textos estáticos previos ("Mis Herramientas Asignadas" y "Accede a tus plataformas autorizadas con sesión única"). Para accesibilidad y navegación por lectores de pantalla, se mantiene un encabezado no visual (`<h2 className="sr-only">Plataformas</h2>`), optimizando el aprovechamiento vertical del espacio y ofreciendo una vista despejada.

### Ejemplo

Al acceder al espacio de trabajo de plataformas, la cuadrícula y las herramientas se visualizan inmediatamente bajo la barra de herramientas premium sin bloques de texto intermedios, ganando visibilidad de las tarjetas de plataformas desde el primer vistazo.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx).

## Simplificación y Supresión de Encabezado en Mis Solicitudes de Usuario

## Módulo

Portal de Usuario y Solicitudes de Acceso (UI/UX)

### Regla

En la vista y tabla de solicitudes de acceso del usuario (`UserRequestsTable`), la navegación contextual se apoya íntegramente en la barra de navegación corporativa (migas de pan en la barra superior y accesos directos en el menú lateral o píldoras del portal), por lo que se suprimen de la interfaz visual los elementos redundantes:

- El título `"Mis Solicitudes de Acceso"`.
- El subtítulo `"Historial detallado y estado en tiempo real de todas tus solicitudes para plataformas corporativas."`.
- El botón secundario `"← Volver a Plataformas"`.
Para navegación por lectores de pantalla y jerarquía de accesibilidad WCAG, se mantiene un encabezado no visible (`<h2 className="sr-only">Mis Solicitudes de Acceso</h2>`), permitiendo que la tabla de datos y sus filtros rápidos inicien inmediatamente en el tope del área de trabajo.

### Ejemplo

Al seleccionar «Mis Solicitudes» desde el menú lateral o la barra superior, la tabla de datos con sus pastillas de estado (`Todas`, `Pendientes`, `Aprobadas`, `Rechazadas`) y buscador se muestra al inicio del contenido sin franjas ni botones de retorno innecesarios, maximizando el espacio de visualización de las filas de solicitudes.

### Impacto

Afecta a [frontend/src/components/platforms/user-requests-table.tsx](../frontend/src/components/platforms/user-requests-table.tsx).

## Encapsulamiento y Diseño Estandarizado en la Barra de Herramientas de Mis Solicitudes

## Módulo

Portal de Usuario y Solicitudes de Acceso (UI/UX)

### Regla

En la vista y tabla de solicitudes de acceso del usuario (`UserRequestsTable`), los controles de búsqueda y filtrado se encapsulan en un contenedor de diseño estandarizado premium (`p-3.5 rounded-2xl border border-panel-border/80 bg-gradient-to-r from-superficie via-superficie to-superficie-hundida shadow-1`), idéntico al catálogo de plataformas y gestión de áreas:

1. **A la izquierda**: Buscador integrado de ancho flexible (`nx-buscador-toolbar`) con icono `buscar` y botón de limpieza inmediata `cerrar` (`✕`).
2. **A la derecha**: Controles modulares desplegables:
   - **Desplegable de Estado**: Botón interactivo (`min-h-12 w-48`) con icono semántico (`inventario`, `reloj`, `aprobar`, `rechazar`), contador dinámico y menú emergente para alternar entre `Todas`, `Pendientes`, `Aprobadas` y `Rechazadas`.
   - **Desplegable de Filas por Página**: Selector interactivo (`min-h-12 w-40`) con icono `panel` para ajustar la densidad de registros (5, 10, 20 o 25 filas) y sincronizar la paginación de la tabla canónica `DataTable`.
3. Ambos menús cumplen con accesibilidad completa WCAG (áreas táctiles $\ge 48\text{ px}$), control por teclado (`Escape`), foco visible y cierre automático por clic exterior.

### Ejemplo

Al acceder a «Mis Solicitudes», el usuario visualiza una barra de herramientas encapsulada, uniforme con el resto de la aplicación. Puede buscar en tiempo real o desplegar «Estado: Todas» para consultar rápidamente solo las peticiones pendientes o rechazadas con sus respectivos contadores. Asimismo, puede modificar el número de filas visibles por página mediante el desplegable «Filas: 10».

### Impacto

Afecta a [frontend/src/components/platforms/user-requests-table.tsx](../frontend/src/components/platforms/user-requests-table.tsx) y a las pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Eliminación de Botón Redundante Chevron en Encabezado de Barra Lateral de Plataformas

## Módulo

Portal de Usuario y Barra Lateral de Plataformas (UI/UX)

### Regla

El control para alternar el estado de la barra lateral (colapsar / restaurar) reside de manera única y canónica en la barra superior del portal mediante el botón con icono de menú (`BotonIcono icono="menu"`), accesible en todas las vistas tanto en móvil como en escritorio. Por ende, se elimina el botón redundante de chevron izquierdo (`<`) en el encabezado de marca de la barra lateral izquierda (`PlatformsSidebarView`). Esto evita duplicidad de controles, previene el truncamiento visual del título "Portal de Accesos" y mantiene un área de encabezado limpia y despejada. Al estar colapsada, el icono de marca (`escudo-ok`) y el botón de menú de la barra superior permanecen como puntos interactivos para restaurar la vista expandida.

### Ejemplo

Al visualizar la barra lateral de plataformas expandida, el bloque superior muestra la marca corporativa completa ("Portal de Accesos", "VIVARO") con su icono de escudo, sin botones adicionales apretando el texto. El usuario colapsa o restaura la barra lateral mediante el botón de menú ubicado en la barra superior.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y a la suite de pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Contadores Circulares Simétricos en Barra Lateral y Filtrado de Solicitudes Pendientes

## Módulo

Portal de Usuario y Barra Lateral de Plataformas (UI/UX)

### Regla

1. **Contadores Simétricos en Círculos**: Todos los indicadores numéricos del menú lateral de plataformas (`PlatformsSidebarView`) se presentan de forma homogénea dentro de un badge circular simétrico (`flex min-w-5 h-5 px-1.5 items-center justify-center rounded-full text-xs font-bold tabular-nums`). Esto aplica para «Mis Plataformas», «Favoritas», «Todas las áreas» y cada departamento del «Catálogo por Área», eliminando números en texto plano asimétricos.
2. **Contador de Mis Solicitudes**: En el elemento de navegación «Mis Solicitudes», el indicador circular se reserva exclusivamente para solicitudes que se encuentran activamente **pendientes de aprobación**. Si no existen solicitudes pendientes (`pendientesCount === 0`), no se muestra ninguna placa con «0» para evitar ruido visual; cuando hay solicitudes pendientes (`pendientesCount > 0`), se despliega el badge circular de advertencia (`bg-warning text-texto-sobre-aviso`).
3. **Filtro Inicial de Solicitudes**: Al acceder a la tabla de solicitudes (`UserRequestsTable`), la vista se inicializa por defecto con el filtro `pendiente`, asegurando que el usuario consulte inmediatamente las solicitudes que requieren atención o resolución.

### Ejemplo

Al abrir el menú lateral, los elementos con conteo muestran una pastilla circular estilizada y perfectamente alineada. Si el usuario no tiene solicitudes de acceso en curso, el renglón «Mis Solicitudes» no exhibe ningún «0» suelto. En el momento en que se genera una solicitud, aparece el badge circular en color ámbar con el número de solicitudes pendientes, y al dar clic sobre ella, la tabla muestra directamente sus peticiones en estado pendiente.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/user-requests-table.tsx](../frontend/src/components/platforms/user-requests-table.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Replicación del Layout de Cuadrícula de Admin Platform en Mi Espacio y Tarjetas Homogéneas

## Módulo

Portal de Usuario y Catálogo de Plataformas (UI/UX)

### Regla

1. **Distribución y Cuadrícula Homogénea (admin/platform)**: El cuerpo principal de «Mi Espacio» (`PlatformsSidebarView`) adopta la misma arquitectura y comportamiento de cuadrícula responsiva que el panel de administración de plataformas (`admin/platform`). La cuadrícula utiliza por omisión el preset de `2×2` (`sm:grid-cols-2 lg:grid-cols-2` y `lg:grid-rows-[repeat(2,minmax(14rem,1fr))]`), permitiendo configurar también presets como `2×3`, `3×2` y `3×3`.
2. **Aprovechamiento del Espacio y Ranuras Fantasma (Ghost Slots)**: Las tarjetas de plataforma ocupan el 100% del ancho y alto disponible de cada celda (`min-h-56 h-full w-full`). Cuando el número de plataformas asignadas o filtradas es menor al número total de celdas configuradas (`gridFilas * gridColumnas`), el espacio sobrante se completa con ranuras con borde discontinuo (`min-h-56 h-full rounded-xl border border-dashed border-panel-border/70 bg-superficie/60`) idénticas a las de administración de áreas, eliminando vacíos antiestéticos o tarjetas desproporcionadas cuando hay pocos elementos asignados.
3. **Estructura Interna de la Tarjeta (PlatformMockupCard)**: La tarjeta de plataforma replica fielmente la composición visual de `TarjetaArea`:
   - Cabecera: Chip con iniciales estilizado (`size-12 rounded-xl font-bold`), título de plataforma y descripción truncada a dos líneas, con botón de favoritos en la esquina superior derecha.
   - Cuerpo central: Dos recuadros simétricos de métricas e información (`grid flex-1 grid-cols-2 content-center gap-2.5 px-5 pb-3`), mostrando el «ÁREA» correspondiente y el «NIVEL DE ACCESO» asignado.
   - Pie de tarjeta: Divisor horizontal de extremo a extremo (`border-t border-panel-border/80 px-5 py-3 mt-auto`), ubicando a la izquierda la pastilla de estado con punto pulsante (`● ACTIVA`, `● EN REVISIÓN`, etc.) y a la derecha el botón de acción redondeado accesible (`min-h-11 px-3.5 rounded-full`).

### Ejemplo

Al ingresar a «Mi Espacio / Mis Plataformas», si el colaborador tiene una única plataforma asignada, ésta abarca el 50% del ancho en la primera fila con altura consistente y estética premium idéntica a `admin/platform`. La cuadrícula se completa armónicamente con 3 ranuras discontinuas, y la tarjeta exhibe en su interior los recuadros de «Área» y «Nivel de acceso», badge de estado activo y botón para abrir la aplicación.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Supresión de «Mis Plataformas» en Barra Lateral y Adopción del Catálogo General por Omisión

## Módulo

Portal de Usuario y Barra Lateral de Plataformas (UI/UX)

### Regla

1. **Eliminación de «Mis Plataformas» en la Barra Lateral**: En la vista de espacio de trabajo con barra lateral (`PlatformsSidebarView`), se elimina la opción redundante «Mis Plataformas» del bloque «MI ESPACIO». Dado que el diseño con barra superior (`PlatformsTopbar`) ya funge como la vista especializada en lanzar plataformas exclusivamente asignadas, mantener «Mis Plataformas» en la barra lateral generaba redundancia conceptual y fragmentaba la navegación.
2. **Estructura Depurada de «Mi Espacio»**: El bloque superior «MI ESPACIO» se enfoca en las interacciones personales del usuario: «Favoritas» (con su respectivo conteo) y «Mis Solicitudes» (con indicador de advertencia solo si hay peticiones pendientes).
3. **Catálogo General como Vista Inicial**: Al acceder al portal con barra lateral, la selección inicial por omisión es «Catálogo por Área / Todas las áreas» (`seccionActiva = 'area', areaSeleccionada = null`), desplegando el catálogo general de herramientas corporativas. Las migas de pan (`Breadcrumbs`) reflejan con precisión la sección activa: `Catálogo / Todas las áreas`, `Catálogo / [Área]` o `Mi Espacio / [Sección]`.
4. **Flujos de Retorno y Filtros**: La acción de regresar desde la tabla de solicitudes y el filtro de estado «Todos» devuelven al usuario de manera coherente al catálogo general (`seccionActiva = 'area'`).

### Ejemplo

Al ingresar a la vista con barra lateral, el usuario no encuentra un botón redundante de «Mis Plataformas» compitiendo con el catálogo. En su lugar, aterriza directamente en el «Catálogo por Área / Todas las áreas» con todas las plataformas visibles, y en «Mi Espacio» dispone de acceso directo a sus «Favoritas» y al historial de «Mis Solicitudes».

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Simetría y Alineación entre Barra de Herramientas y Cuadrícula de Tarjetas en Administración de Plataformas

## Módulo

Administración de Plataformas y Catálogo de Áreas (UI/UX)

### Regla

1. **Alineación de Bordes Exteriores (Sin Desfase de Padding)**: El contenedor de la cuadrícula de tarjetas (`Fila 2`) debe alinearse a ras con los bordes exteriores de la barra de herramientas (`Fila 1`). Queda prohibido aplicar acolchado lateral como `p-1` (4 px) al contenedor desplazable (`overflow-y-auto`), garantizando que el borde izquierdo de la primera tarjeta y el borde derecho de la última tarjeta coincidan de forma pixel-perfect con los límites de la barra de herramientas.
2. **Homogeneidad de Radio de Bordes**: La barra de herramientas, las tarjetas de área/plataforma y las ranuras con borde discontinuo (`ghost slots`) adoptan obligatoriamente el token estándar `rounded-xl` (12 px / `--radius-base`), eliminando la discrepancia visual generada por el uso previo de `rounded-2xl` en la cabecera.
3. **Distribución y Simetría Interna del Buscador**: El buscador dentro de la barra de herramientas utiliza una anchura balanceada (`max-w-xl` con `relative w-full`), eliminando la doble restricción anidada artificial (`max-w-md` dentro de `max-w-2xl`) para armonizar visualmente con la primera columna de la cuadrícula inferior y evitar huecos desproporcionados con los selectores de la derecha.
4. **Sincronización de Altura en Puntos de Ruptura (Breakpoint sm:)**: Las clases de altura de filas (`CLASES_ROWS`) aplican `sm:grid-rows-[repeat(N,minmax(14rem,1fr))]` en lugar de retrasarse hasta `lg:`. Esto asegura que en resoluciones intermedias (`sm:` y `md:`), donde la cuadrícula ya se distribuye en 2 columnas, las filas mantengan idéntica altura simétrica y eviten deformaciones verticales entre tarjetas reales y slots fantasma.

### Ejemplo

Al acceder a `General > Plataformas` en una resolución de escritorio o tablet con cuadrícula de 2 columnas, la barra de herramientas y la primera fila de tarjetas inician y concluyen exactamente en la misma coordenada horizontal $X$, sin que la barra sobresalga 4 px a los lados. El buscador se expande fluidamente en la mitad izquierda y las tarjetas junto con las ranuras vacías conservan un radio de 12 px y alturas perfectamente niveladas.

### Impacto

Afecta a [frontend/src/components/platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx) y [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Supresión de Padding Superior Fantasma y Ocupación Total de Altura en Vista Sidebar de Plataformas

## Módulo

Portal de Usuario y Catálogo de Plataformas (UI/UX)

### Regla

1. **Eliminación del Padding Superior Fantasma**: En la vista de espacio de trabajo con barra lateral (`PlatformsSidebarView`), el contenedor `<main>` sustituye `space-y-6` y el padding excesivo por `flex-1 min-h-0 flex flex-col px-4 sm:px-6 pb-4 sm:pb-6 pt-2 sm:pt-3 gap-4 overflow-y-auto`. Se elimina el selector descendente `space-y-6` que aplicaba 24 px de margen superior artificial al detectar el elemento accesible `h2.sr-only`, reduciendo el espacio superior de 48 px a un valor consistente de 8 px a 12 px (`pt-2 sm:pt-3`) inmediatamente debajo del borde de la barra superior.
2. **Encapsulamiento en Cuadrícula Auto/1fr**: La barra de herramientas y el cuerpo de la cuadrícula se estructuran bajo un contenedor de rejilla CSS vertical `grid w-full flex-1 min-h-0 grid-cols-1 grid-rows-[auto_1fr] gap-4`. La fila 1 (`auto`) absorbe la altura natural de los controles, mientras que la fila 2 (`1fr`) absorbe el 100% de la altura vertical restante del visor.
3. **Aprovechamiento Integral de la Altura Disponible**: Tanto el contenedor interior de la cuadrícula como la rejilla de tarjetas aplican `h-full flex-1` en combinación con `CLASES_ROWS` (`sm:grid-rows-[repeat(N,minmax(14rem,1fr))]`). Cada fila de tarjetas distribuye equitativamente el espacio vertical disponible, permitiendo que `PlatformMockupCard` y las ranuras discontinuas (`ghost slots`) ocupen toda la altura de la celda sin dejar franjas vacías en la parte inferior de la pantalla.
4. **Homogeneización de Vistas**: Esta estructura aplica uniformemente en todas las secciones del espacio de trabajo con barra lateral (Catálogo general, filtrado por área, sección de Favoritas y la tabla de Mis Solicitudes).

### Ejemplo

Al visualizar `Mi Espacio` o `Catálogo por Área` en la vista Sidebar, la barra de herramientas se sitúa elegantemente a 12 px debajo del header sin márgenes desproporcionados. En un monitor de escritorio estándar con cuadrícula de $2\times 2$, las dos filas de tarjetas y ranuras discontinuas se expanden verticalmente llenando el 100% del alto disponible, centrando sus recuadros de datos internos y anclando el pie de la tarjeta al límite inferior sin generar espacios muertos.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/user-requests-table.tsx](../frontend/src/components/platforms/user-requests-table.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Simetría y Alineación entre Barra de Herramientas y Cuadrícula de Tarjetas en Administración de Plataformas

## Módulo

Administración de Plataformas y Catálogo de Áreas (UI/UX)

### Regla

1. **Alineación de Bordes Exteriores (Sin Desfase de Padding)**: El contenedor de la cuadrícula de tarjetas (`Fila 2`) debe alinearse a ras con los bordes exteriores de la barra de herramientas (`Fila 1`). Queda prohibido aplicar acolchado lateral como `p-1` (4 px) al contenedor desplazable (`overflow-y-auto`), garantizando que el borde izquierdo de la primera tarjeta y el borde derecho de la última tarjeta coincidan de forma pixel-perfect con los límites de la barra de herramientas.
2. **Homogeneidad de Radio de Bordes**: La barra de herramientas, las tarjetas de área/plataforma y las ranuras con borde discontinuo (`ghost slots`) adoptan obligatoriamente el token estándar `rounded-xl` (12 px / `--radius-base`), eliminando la discrepancia visual generada por el uso previo de `rounded-2xl` en la cabecera.
3. **Distribución y Simetría Interna del Buscador**: El buscador dentro de la barra de herramientas utiliza una anchura balanceada (`max-w-xl` con `relative w-full`), eliminando la doble restricción anidada artificial (`max-w-md` dentro de `max-w-2xl`) para armonizar visualmente con la primera columna de la cuadrícula inferior y evitar huecos desproporcionados con los selectores de la derecha.
4. **Sincronización de Altura en Puntos de Ruptura (Breakpoint sm:)**: Las clases de altura de filas (`CLASES_ROWS`) aplican `sm:grid-rows-[repeat(N,minmax(14rem,1fr))]` en lugar de retrasarse hasta `lg:`. Esto asegura que en resoluciones intermedias (`sm:` y `md:`), donde la cuadrícula ya se distribuye en 2 columnas, las filas mantengan idéntica altura simétrica y eviten deformaciones verticales entre tarjetas reales y slots fantasma.

### Ejemplo

Al acceder a `General > Plataformas` en una resolución de escritorio o tablet con cuadrícula de 2 columnas, la barra de herramientas y la primera fila de tarjetas inician y concluyen exactamente en la misma coordenada horizontal $X$, sin que la barra sobresalga 4 px a los lados. El buscador se expande fluidamente en la mitad izquierda y las tarjetas junto con las ranuras vacías conservan un radio de 12 px y alturas perfectamente niveladas.

### Impacto

Afecta a [frontend/src/components/platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx) y [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Supresión de Padding Superior Fantasma y Ocupación Total de Altura en Vista Sidebar de Plataformas

## Módulo

Portal de Usuario y Catálogo de Plataformas (UI/UX)

### Regla

1. **Eliminación del Padding Superior Fantasma**: En la vista de espacio de trabajo con barra lateral (`PlatformsSidebarView`), el contenedor `<main>` sustituye `space-y-6` y el padding excesivo por `flex-1 min-h-0 flex flex-col px-4 sm:px-6 pb-4 sm:pb-6 pt-2 sm:pt-3 gap-4 overflow-y-auto`. Se elimina el selector descendente `space-y-6` que aplicaba 24 px de margen superior artificial al detectar el elemento accesible `h2.sr-only`, reduciendo el espacio superior de 48 px a un valor consistente de 8 px a 12 px (`pt-2 sm:pt-3`) inmediatamente debajo del borde de la barra superior.
2. **Encapsulamiento en Cuadrícula Auto/1fr**: La barra de herramientas y el cuerpo de la cuadrícula se estructuran bajo un contenedor de rejilla CSS vertical `grid w-full flex-1 min-h-0 grid-cols-1 grid-rows-[auto_1fr] gap-4`. La fila 1 (`auto`) absorbe la altura natural de los controles, mientras que la fila 2 (`1fr`) absorbe el 100% de la altura vertical restante del visor.
3. **Aprovechamiento Integral de la Altura Disponible**: Tanto el contenedor interior de la cuadrícula como la rejilla de tarjetas aplican `h-full flex-1` en combinación con `CLASES_ROWS` (`sm:grid-rows-[repeat(N,minmax(14rem,1fr))]`). Cada fila de tarjetas distribuye equitativamente el espacio vertical disponible, permitiendo que `PlatformMockupCard` y las ranuras discontinuas (`ghost slots`) ocupen toda la altura de la celda sin dejar franjas vacías en la parte inferior de la pantalla.
4. **Homogeneización de Vistas**: Esta estructura aplica uniformemente en todas las secciones del espacio de trabajo con barra lateral (Catálogo general, filtrado por área, sección de Favoritas y la tabla de Mis Solicitudes).

### Ejemplo

Al visualizar `Mi Espacio` o `Catálogo por Área` en la vista Sidebar, la barra de herramientas se sitúa elegantemente a 12 px debajo del header sin márgenes desproporcionados. En un monitor de escritorio estándar con cuadrícula de $2\times 2$, las dos filas de tarjetas y ranuras discontinuas se expanden verticalmente llenando el 100% del alto disponible, centrando sus recuadros de datos internos y anclando el pie de la tarjeta al límite inferior sin generar espacios muertos.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/user-requests-table.tsx](../frontend/src/components/platforms/user-requests-table.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Estandarización Exacta de Padding y Distribución de Altura de Admin/Platform en Espacio de Trabajo Sidebar

## Módulo

Portal de Usuario y Catálogo de Plataformas (UI/UX)

### Regla

1. **Calibración Idéntica de Padding con Marco Admin (`p-6`)**: El contenedor `<main>` en `PlatformsSidebarView` adopta de manera estricta la misma clase de acolchado que `admin/platform` (`min-h-0 min-w-0 flex-1 overflow-y-auto bg-fondo p-6 outline-none flex flex-col gap-4`). Queda prohibido el uso de valores asimétricos reducidos (como `pt-2` o `pt-3`), garantizando que la barra de herramientas mantenga exactamente la misma distancia de 24 px (`p-6`) respecto a la barra superior en ambas pantallas.
2. **Ubicación Externa del Título Accesible (`h2.sr-only`)**: El encabezado de accesibilidad `<h2 className="sr-only">` se posiciona fuera de la cuadrícula vertical `grid-rows-[auto_1fr]` para no alterar la asignación estricta de pistas de fila entre la barra de herramientas (`Fila 1: auto`) y la cuadrícula de tarjetas (`Fila 2: 1fr`).
3. **Distribución Uniforme de Altura al 100%**: Con `p-6` perimetral y `grid-rows-[auto_1fr]`, las dos filas de la cuadrícula (`2×2`) se expanden verticalmente ocupando toda la altura útil disponible hasta el padding inferior de 24 px, replicando al milímetro el comportamiento geométrico de `admin/platform`.

### Ejemplo

Al alternar entre `General > Plataformas` (`/admin/platforms`) y `Mi Espacio / Catálogo` (`/platforms`), el usuario aprecia exactamente la misma distancia de separación de 24 px entre el borde inferior de la barra superior y la barra de herramientas. En ambas pantallas las tarjetas se expanden a lo largo de todo el viewport vertical con absoluta coherencia visual.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/user-requests-table.tsx](../frontend/src/components/platforms/user-requests-table.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Replicación del Menú Flotante de Selección de Cuadrícula de Admin/Platform en Espacio de Trabajo Sidebar

## Módulo

Portal de Usuario y Barra de Herramientas de Plataformas (UI/UX)

### Regla

1. **Diseño Flotante Idéntico (`w-72`)**: El selector de cuadrícula en la barra de herramientas de `PlatformsSidebarView` abandona la lista vertical simple (`w-48`) y replica con absoluta fidelidad el diseño del menú emergente de `admin/platform` (`platform-admin.tsx`):
   - Contenedor flotante: `w-72 rounded-xl border border-panel-border bg-panel-fill p-3 shadow-2 backdrop-blur-md space-y-3`.
   - Cabecera: Título en mayúsculas `CUADRÍCULA` (`text-xs font-bold uppercase tracking-wider text-label`) a la izquierda y contador dinámico de slots `{gridFilas * gridColumnas} slots ({gridFilas}×{gridColumnas})` (`text-xs font-bold text-primary-text tabular-nums`) a la derecha, delimitado por un divisor inferior `border-b border-panel-border/50 pb-2`.
   - Distribución en Matriz de Botones ($2\times 2$): Opciones presentadas en una rejilla de dos columnas (`grid grid-cols-2 gap-1.5`) con pastillas táctiles accesibles (`min-h-12`).
   - Estados de selección: Opción activa resaltada en `bg-primary/20 text-primary-text font-bold` y opciones inactivas con `text-label hover:text-body-text hover:bg-superficie-hundida`.
2. **Homogeneidad de Interacción**: Ambas vistas (`/admin/platforms` y `/platforms`) comparten idéntica disposición, microinteracciones y retroalimentación visual al configurar las dimensiones de la cuadrícula.

### Ejemplo

Al presionar el botón `Cuadrícula: 2×2` en el catálogo de plataformas del usuario, se despliega un panel flotante de 288 px de ancho con la cabecera `CUADRÍCULA` y `4 slots (2×2)`. Debajo, una cuadrícula de $2\times 2$ muestra las combinaciones `2×2`, `2×3`, `3×2` y `3×3`, con la opción activa resaltada en azul primario, exactamente igual que en la consola de administración.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Eliminación de Selector de Filas en Mis Solicitudes y Estandarización de Filtros de Estado en Catálogo por Área

## Módulo

Portal de Usuario / Mis Solicitudes y Catálogo por Área (UI/UX)

### Regla

1. **Mis Solicitudes con Límite Fijo de 10 Filas**: En la sección `Mis Solicitudes` (`UserRequestsTable`), se suprime de manera definitiva el botón selector desplegable de filas por página (`filasRef`), fijando la paginación a 10 registros por página (`limite = 10`). La barra de herramientas mantiene únicamente el buscador rápido a la izquierda y el filtro de estado a la derecha.
2. **Estandarización de Filtros de Estado (Activo e Inactivo)**: Los filtros de estado de la plataforma deben categorizarse fundamentalmente por `Activo` e `Inactivo` (además de `Todos`), garantizando consistencia semántica en todo el sistema.
3. **Inclusión de Filtro Favorito en Catálogo por Área**: En el catálogo de plataformas del usuario (`PlatformsSidebarView`), el menú desplegable de `Estado` incluye cuatro opciones completas con sus respectivos contadores dinámicos e indicadores visuales:
   - `Todos`: totalidad de plataformas del área o catálogo.
   - `Activas`: plataformas con acceso activo del usuario (indicador visual circular verde).
   - `Inactivas`: plataformas sin acceso activo (indicador visual circular ámbar).
   - `Favoritas`: plataformas marcadas como favoritas (estrella dorada ★).

### Ejemplo

Al acceder a `Mi Espacio > Mis Solicitudes`, el usuario observa una tabla limpia con 10 filas por página sin selectores redundantes de filas. Al navegar por el `Catálogo por Área` (por ejemplo, «Demo Infraestructura»), el usuario abre el selector `Estado` y puede filtrar las plataformas del área seleccionada entre «Todos», «Activas», «Inactivas» o «Favoritas».

### Impacto

Afecta a [frontend/src/components/platforms/user-requests-table.tsx](../frontend/src/components/platforms/user-requests-table.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Vista Global de Áreas en Catálogo y Navegación Jerárquica hacia Plataformas

## Módulo

Portal de Usuario y Catálogo de Áreas (UI/UX)

### Regla

1. **Visualización Exclusiva de Áreas en «Todas las áreas»**: Cuando el usuario se encuentra en la opción `Todas las áreas` del catálogo (`seccionActiva === 'area' && areaSeleccionada === null`), el sistema despliega únicamente tarjetas de áreas (`TarjetaArea`) en lugar de plataformas individuales. Esto proporciona una visión panorámica y global de cuántas áreas tiene asignadas y cuántas plataformas alberga cada una.
2. **Restricción de Favoritos y Filtros de Estado en Vista de Áreas**:
   - En la vista global de áreas no aplica la opción de favoritos (las áreas no poseen atributo de favorito).
   - El menú desplegable de `Estado` de la barra de herramientas se restringe estrictamente a `Todos`, `Activas` e `Inactivas`.
   - El campo de búsqueda adopta el marcador `Buscar áreas…` y filtra dinámicamente por nombre y descripción del área.
3. **Navegación Interactiva al Área Seleccionada**:
   - Al pulsar sobre una tarjeta de área o su botón `Ver plataformas >`, la interfaz transiciona de forma reactiva al catálogo de plataformas específico de dicha área (`areaSeleccionada = area.id`).
   - La barra de navegación superior y la barra de herramientas incorporan un botón de retorno `[ < Áreas ]` e indicador del área activa.
   - Dentro del área específica, el filtro de estado habilita nuevamente las opciones completas (`Todos`, `Activas`, `Inactivas`, `Favoritas`) y el buscador se enfoca en las plataformas del área (`Buscar plataformas en [Área]…`).

### Ejemplo

Al seleccionar «Todas las áreas» en la barra lateral, el usuario visualiza una cuadrícula con tarjetas de cada departamento (ej. «Demo Finanzas», «Demo Infraestructura») mostrando sus personas y plataformas asociadas. El filtro de estado solo ofrece «Todos», «Activas» e «Inactivas». Al hacer clic en «Demo Infraestructura», la vista navega a las plataformas de esa área, permitiendo filtrarlas por favoritos o regresar a la vista global de áreas con un solo clic.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Ámbito Estricto de Filtros en Área Seleccionada (Activo, Inactivo y Favoritos)

## Módulo

Catálogo de Plataformas por Área (UI/UX)

### Regla

1. **Opciones Disponibles en Área Seleccionada**: Cuando el usuario ingresa al detalle de un área específica (`seccionActiva === 'area' && areaSeleccionada !== null`), el selector de estado de la barra de herramientas ofrece las opciones:
   - `Todos`: totalidad de plataformas pertenecientes al área actual.
   - `Activas`: plataformas con acceso activo del usuario dentro del área actual.
   - `Inactivas`: plataformas sin acceso activo dentro del área actual.
   - `Favoritas`: plataformas marcadas como favoritas pertenecientes exclusivamente al área actual.
2. **Aislamiento y Confinamiento de Ámbito (Scope Enclosure)**:
   - Cualquier filtro aplicado (`activo`, `inactivo`, `favorito` o término de búsqueda) opera de forma estricta y exclusiva sobre las plataformas del área seleccionada (`item.area.id === areaSeleccionada`).
   - Bajo ninguna circunstancia el filtro de favoritas o de estado mostrará plataformas pertenecientes a otras áreas ni cambiará la selección del área actual.
   - Si ninguna plataforma del área cumple con el filtro seleccionado, se despliega un estado vacío contextual (`Ninguna plataforma en «[Área]» coincide con los filtros aplicados`) con acción para limpiar filtros sin perder la ubicación del área.
   - Al cambiar a otra área desde la barra lateral o al volver a «Todas las áreas», los filtros se reinician a `todos` para evitar estados filtrados inconsistentes en el nuevo contexto.

### Ejemplo

Al seleccionar «Demo Infraestructura», el usuario despliega el menú de Estado y selecciona «Favoritas». La vista muestra únicamente las plataformas favoritas asociadas a «Demo Infraestructura». Si ninguna plataforma de esa área está marcada como favorita, se presenta el mensaje «Ninguna plataforma en «Demo Infraestructura» coincide con los filtros aplicados» con el botón «Limpiar filtros», sin traer plataformas favoritas de «Demo Finanzas» ni deseleccionar el área activa.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Sección Mi Widget y Configuración de Accesos Flotantes

## Módulo

Portal de Usuario y Accesibilidad Flotante (UI/UX)

### Regla

1. **Acceso y Ubicación en Mi Espacio**: En la barra lateral del portal de usuario (`PlatformsSidebarView`), bajo la sección `Mi Espacio`, se incorpora la opción `Mi Widget` con su icono representativo y contador simétrico en pastilla circular que indica la cantidad de plataformas activas en el widget.
2. **Diseño de Control Maestro y Previsualización**:
   - La vista despliega un banner de cabecera con el estado del widget (`Activo en pantalla` / `Desactivado`) y un interruptor maestro (`role="switch"`) con tamaño táctil accesible ($\ge 44\text{ px}$).
   - Cuando el widget está habilitado, se renderiza una previsualización interactiva flotante en la esquina inferior derecha con su botón lanzador y menú de accesos directos.
3. **Catálogo de Plataformas con Conmutador (Toggle)**:
   - Se muestran todas las plataformas del catálogo de forma homogénea en una cuadrícula de diseño premium.
   - Cada tarjeta de plataforma incluye su información de pertenencia (área, estado de acceso, descripción) y un conmutador individual (`Mostrar en widget`) para sumar o retirar la plataforma del lanzador flotante.
   - Los elementos con toggle activo se destacan visualmente con borde y realce de token primario (`border-primary ring-2 ring-primary/20`).
4. **Persistencia de Configuración**: La preferencia de activación del widget y la lista de IDs de plataformas seleccionadas se mantienen en almacenamiento local (`localStorage`) para ofrecer una experiencia reactiva inmediata durante la fase de validación de diseño.

### Ejemplo

El usuario accede a `Mi Espacio > Mi Widget`, visualiza el banner de cabecera con el interruptor encendido, y observa el listado de plataformas disponibles. Al activar el toggle de «Slack» y «Jira», ambas plataformas quedan marcadas con el badge «En widget» y se agregan al contador del botón flotante en la esquina inferior de su pantalla.

### Impacto

Afecta a [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Sección de Personalización de Vista y Preferencias de Visualización en Plataformas

## Módulo

Portal de Usuario y Personalización (UI/UX)

### Regla

1. **Acceso desde el Engrane de la Barra Superior (Topbar)**: En la barra superior de la vista de barra lateral (`PlatformsSidebarView`), se incluye un botón de icono con engrane (`BotonIcono icono="ajustes"`) con objetivo táctil $\ge 44\text{ px}$ (`min-h-12 min-w-12`), accesible para todos los usuarios. Al pulsarlo, conmuta a la sección de configuración y diseño de vista (`seccionActiva === 'personalizacion'`) y actualiza las migas de pan a `Mi Espacio / Ajustes de Vista`.
2. **Selector de Disposición Principal (Layout)**: Permite alternar la navegación principal entre la vista con Barra Lateral (`sidebar`) y la vista con Barra Superior (`topbar`), persistiendo la preferencia en `localStorage` (`nexus.platforms.layout`).
3. **Control de Visibilidad de Documentos (Carta Responsiva)**: Interruptor accesible (`role="switch"`) para mostrar u ocultar la sección de `DOCUMENTOS` (Carta Responsiva y su estado de firma) en la barra lateral del portal, persistiendo en `localStorage` (`nexus.platforms.show_documents`).
4. **Control de Visibilidad de Badges Circulares**: Interruptor accesible (`role="switch"`) para mostrar u ocultar los contadores numéricos simétricos en pastillas circulares (`.rounded-full`) de las secciones del menú lateral (`Favoritas`, `Mis Solicitudes`, `Mi Widget`, `Todas las áreas` y áreas específicas), persistiendo en `localStorage` (`nexus.platforms.show_sidebar_badges`).
5. **Selector de Diseño y Variante de Tarjetas**: Selector con opciones interactivas para elegir entre tres variantes de diseño de tarjetas de plataformas:
   - `Estándar`: Tarjeta completa de alta fidelidad con iniciales, chips de área, nivel de acceso y estado.
   - `Compacta`: Tarjeta minimalista de altura reducida enfocada en acceso rápido y estado.
   - `Horizontal`: Tarjeta en fila alargada ideal para visualizaciones de densidad intermedia.
   La preferencia se persiste en `localStorage` (`nexus.platforms.card_design`) y se aplica de inmediato al catálogo de tarjetas.

### Ejemplo

El usuario hace clic en el icono de engrane en la barra superior. En la pantalla de ajustes, desactiva la sección de Carta Responsiva y oculta los contadores circulares del sidebar, y elige el diseño de tarjetas "Compacta". De inmediato, el menú lateral oculta la sección de documentos y los círculos de conteo, y las plataformas del catálogo adoptan la variante compacta.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y a la suite de pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Ámbito Estricto de Filtros en Área Seleccionada (Activo, Inactivo y Favoritos)

## Módulo

Catálogo de Plataformas por Área (UI/UX)

### Regla

1. **Opciones Disponibles en Área Seleccionada**: Cuando el usuario ingresa al detalle de un área específica (`seccionActiva === 'area' && areaSeleccionada !== null`), el selector de estado de la barra de herramientas ofrece las opciones:
   - `Todos`: totalidad de plataformas pertenecientes al área actual.
   - `Activas`: plataformas con acceso activo del usuario dentro del área actual.
   - `Inactivas`: plataformas sin acceso activo dentro del área actual.
   - `Favoritas`: plataformas marcadas como favoritas pertenecientes exclusivamente al área actual.
2. **Aislamiento y Confinamiento de Ámbito (Scope Enclosure)**:
   - Cualquier filtro aplicado (`activo`, `inactivo`, `favorito` o término de búsqueda) opera de forma estricta y exclusiva sobre las plataformas del área seleccionada (`item.area.id === areaSeleccionada`).
   - Bajo ninguna circunstancia el filtro de favoritas o de estado mostrará plataformas pertenecientes a otras áreas ni cambiará la selección del área actual.
   - Si ninguna plataforma del área cumple con el filtro seleccionado, se despliega un estado vacío contextual (`Ninguna plataforma en «[Área]» coincide con los filtros aplicados`) con acción para limpiar filtros sin perder la ubicación del área.
   - Al cambiar a otra área desde la barra lateral o al volver a «Todas las áreas», los filtros se reinician a `todos` para evitar estados filtrados inconsistentes en el nuevo contexto.

### Ejemplo

Al seleccionar «Demo Infraestructura», el usuario despliega el menú de Estado y selecciona «Favoritas». La vista muestra únicamente las plataformas favoritas asociadas a «Demo Infraestructura». Si ninguna plataforma de esa área está marcada como favorita, se presenta el mensaje «Ninguna plataforma en «Demo Infraestructura» coincide con los filtros aplicados» con el botón «Limpiar filtros», sin traer plataformas favoritas de «Demo Finanzas» ni deseleccionar el área activa.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Sección Mi Widget y Configuración de Accesos Flotantes

## Módulo

Portal de Usuario y Accesibilidad Flotante (UI/UX)

### Regla

1. **Acceso y Ubicación en Mi Espacio**: En la barra lateral del portal de usuario (`PlatformsSidebarView`), bajo la sección `Mi Espacio`, se incorpora la opción `Mi Widget` con su icono representativo y contador simétrico en pastilla circular que indica la cantidad de plataformas activas en el widget.
2. **Diseño de Control Maestro y Previsualización**:
   - La vista despliega un banner de cabecera con el estado del widget (`Activo en pantalla` / `Desactivado`) y un interruptor maestro (`role="switch"`) con tamaño táctil accesible ($\ge 44\text{ px}$).
   - Cuando el widget está habilitado, se renderiza una previsualización interactiva flotante en la esquina inferior derecha con su botón lanzador y menú de accesos directos.
3. **Catálogo de Plataformas con Conmutador (Toggle)**:
   - Se muestran todas las plataformas del catálogo de forma homogénea en una cuadrícula de diseño premium.
   - Cada tarjeta de plataforma incluye su información de pertenencia (área, estado de acceso, descripción) y un conmutador individual (`Mostrar en widget`) para sumar o retirar la plataforma del lanzador flotante.
   - Los elementos con toggle activo se destacan visualmente con borde y realce de token primario (`border-primary ring-2 ring-primary/20`).
4. **Persistencia de Configuración**: La preferencia de activación del widget y la lista de IDs de plataformas seleccionadas se mantienen en almacenamiento local (`localStorage`) para ofrecer una experiencia reactiva inmediata durante la fase de validación de diseño.

### Ejemplo

El usuario accede a `Mi Espacio > Mi Widget`, visualiza el banner de cabecera con el interruptor encendido, y observa el listado de plataformas disponibles. Al activar el toggle de «Slack» y «Jira», ambas plataformas quedan marcadas con el badge «En widget» y se agregan al contador del botón flotante en la esquina inferior de su pantalla.

### Impacto

Afecta a [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Sección de Personalización de Vista y Preferencias de Visualización en Plataformas

## Módulo

Portal de Usuario y Personalización (UI/UX)

### Regla

1. **Acceso desde el Engrane de la Barra Superior (Topbar)**: En la barra superior de la vista de barra lateral (`PlatformsSidebarView`), se incluye un botón de icono con engrane (`BotonIcono icono="ajustes"`) con objetivo táctil $\ge 44\text{ px}$ (`min-h-12 min-w-12`), accesible para todos los usuarios. Al pulsarlo, conmuta a la sección de configuración y diseño de vista (`seccionActiva === 'personalizacion'`) y actualiza las migas de pan a `Mi Espacio / Ajustes de Vista`.
2. **Selector de Disposición Principal (Layout)**: Permite alternar la navegación principal entre la vista con Barra Lateral (`sidebar`) y la vista con Barra Superior (`topbar`), persistiendo la preferencia en `localStorage` (`nexus.platforms.layout`).
3. **Control de Visibilidad de Documentos (Carta Responsiva)**: Interruptor accesible (`role="switch"`) para mostrar u ocultar la sección de `DOCUMENTOS` (Carta Responsiva y su estado de firma) en la barra lateral del portal, persistiendo en `localStorage` (`nexus.platforms.show_documents`).
4. **Control de Visibilidad de Badges Circulares**: Interruptor accesible (`role="switch"`) para mostrar u ocultar los contadores numéricos simétricos en pastillas circulares (`.rounded-full`) de las secciones del menú lateral (`Favoritas`, `Mis Solicitudes`, `Mi Widget`, `Todas las áreas` y áreas específicas), persistiendo en `localStorage` (`nexus.platforms.show_sidebar_badges`).
5. **Selector de Diseño y Variante de Tarjetas**: Selector con opciones interactivas para elegir entre tres variantes de diseño de tarjetas de plataformas:
   - `Estándar`: Tarjeta completa de alta fidelidad con iniciales, chips de área, nivel de acceso y estado.
   - `Compacta`: Tarjeta minimalista de altura reducida enfocada en acceso rápido y estado.
   - `Horizontal`: Tarjeta en fila alargada ideal para visualizaciones de densidad intermedia.
   La preferencia se persiste en `localStorage` (`nexus.platforms.card_design`) y se aplica de inmediato al catálogo de tarjetas.

### Ejemplo

El usuario hace clic en el icono de engrane en la barra superior. En la pantalla de ajustes, desactiva la sección de Carta Responsiva y oculta los contadores circulares del sidebar, y elige el diseño de tarjetas "Compacta". De inmediato, el menú lateral oculta la sección de documentos y los círculos de conteo, y las plataformas del catálogo adoptan la variante compacta.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y a la suite de pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Optimización de Barra Superior y Adaptabilidad Responsiva en Vista Topbar

## Módulo

Portal de Usuario y Barra Superior (UI/UX)

### Regla

1. **Simetría de Orilla Izquierda y Derecha**: El enlace del logotipo e identidad corporativa en la barra superior (`PlatformsTopbar`) alinea su icono representativo con el espaciado interior (`padding`) estándar del encabezado (`px-4 md:px-6`), eliminando espaciados horizontales internos redundantes para asegurar simetría matemática respecto al menú de usuario en la orilla derecha.
2. **Acciones Simplificadas por Iconos con Tooltip**:
   - Los accesos a «Plataformas» y «Mis solicitudes» se representan exclusivamente mediante botones de icono accesibles con objetivo táctil $\ge 44\text{ px}$ (`CLASE_BOTON_ICONO`) e indicadores tooltip en `:hover` / `:focus` (`title` y `aria-label`).
   - El acceso de administradores «Regresar al Panel Admin» se unifica en un botón de icono representativo con flecha izquierda (`<-` / `flecha-izq`) con tooltip informativo.
   - El selector textual «Vista: Topbar» se elimina de la barra, integrando el acceso a personalización y conmutación de interfaces a través del botón de icono de engrane (`BotonIcono icono="ajustes"`).
3. **Adaptabilidad Responsiva de Ancho y Alto Completo**: En la vista de barra superior (`PlatformsLaunchpadView` y `PlatformsShell`), se elimina la restricción de ancho máximo rígido (`max-w-7xl`), permitiendo que el contenedor principal aproveche el 100% del ancho (`w-full`) y alto disponible (`flex-1 min-h-0`), desplegando la cuadrícula de tarjetas de forma expansiva y dinámica en monitores amplios y dispositivos móviles.

### Ejemplo

Al acceder al portal en modo Topbar, el usuario observa una barra superior compacta y simétrica. A la derecha figuran los iconos interactivos para navegar entre plataformas y solicitudes, el botón de flecha `<-` para administradores y el engrane para configurar la vista. Al situar el cursor sobre cualquier icono, se despliega su tooltip explicativo. El catálogo y el banner de bienvenida aprovechan la totalidad del ancho de la pantalla sin franjas laterales vacías.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/app/requests/page.tsx](../frontend/src/app/requests/page.tsx) y a la suite de pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Modal de Bienvenida Emergente con Opción de Omisión en Plataformas (Launchpad)

## Módulo

Portal de Usuario y Visualización de Plataformas (UI/UX)

### Regla

1. **Sustitución de Banner Estático por Modal Emergente**:
   - En la vista de lanzamiento de plataformas (`PlatformsLaunchpadView`), se retira el bloque estático del encabezado Hero que ocupaba espacio vertical permanente en la parte superior del catálogo.
   - En su lugar, el mensaje de bienvenida y métricas de resumen («Plataformas activas» y «Solicitudes en proceso») se despliegan mediante un diálogo modal flotante accesible (`Modal` de `@/components/form`, `role="dialog"`, con `aria-modal="true"`, trampa de foco y bloqueo de scroll).
2. **Casilla de Omisión Persistente**:
   - El pie del modal (`footer`) incorpora una casilla de verificación accesible (`Checkbox`) con la leyenda «Omitir la próxima vez» y un botón primario accesible «Entendido» ($\ge 44\text{ px}$ / `min-h-12`).
   - Al cerrar el diálogo con la casilla activada, se almacena de forma persistente la clave `'nexus.platforms.omit_welcome_modal': 'true'` en `localStorage`, evitando que el modal vuelva a interrumpir la navegación en futuras visitas o recargas.
   - Si el usuario cierra el modal sin marcar la casilla (o mediante Escape / botón de cierre), la preferencia no se fija, permitiendo mostrar el resumen en la próxima sesión.
3. **Liberación Inmediata de Espacio para el Catálogo**:
   - Al eliminarse el banner estático fijo, la barra de pastillas de filtro y la cuadrícula de tarjetas de plataformas inician directamente en la parte superior útil de la pantalla, maximizando la visibilidad del catálogo tanto en escritorio como en dispositivos móviles.

### Ejemplo

Un usuario ingresa a la vista de plataformas. En lugar de ver un contenedor oscuro permanente encima de sus herramientas, aparece una ventana modal de bienvenida con su saludo ("¡Hola, Juan! 👋"), el estado de sus plataformas y un checkbox que dice "Omitir la próxima vez". El usuario marca la casilla y hace clic en "Entendido". El modal desaparece, la cuadrícula de plataformas queda visible desde el tope de la pantalla, y en sus próximos inicios de sesión el modal ya no vuelve a abrirse.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx) y a la suite de pruebas unitarias en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Alineación y Simetría Horizontal entre Barra Superior (Header) y Cuerpo (Main) en Modo Topbar

## Módulo

Portal de Usuario y Visualización de Plataformas (UI/UX)

### Regla

1. **Simetría Horizontal Idéntica entre Header y Main**:
   - En la vista de barra superior (`PlatformsShell` y `/requests`), el contenedor principal `<main>` homologa su espaciado interior horizontal con la barra superior (`PlatformsTopbar`), aplicando `p-4 md:p-6` (`16px` en móvil y `24px` en escritorio).
   - Se elimina la regla de espaciado divergente `md:p-8` (`32px`), garantizando que la orilla izquierda y derecha del contenido del cuerpo coincidan exactamente con la posición del logotipo y menú de usuario de la barra superior.
2. **Eliminación de Franjas y Holguras Asimétricas**:
   - Al unificarse el padding horizontal a `px-4 md:px-6`, las tarjetas de plataformas, la barra de filtros y las tablas de solicitudes arrancan en la misma línea vertical de referencia que el escudo/marca institucional, evitando cualquier desfase visual o margen lateral indeseado.

### Ejemplo

Al visualizar el portal en pantalla completa en vista Topbar, la primera tarjeta de la cuadrícula y las pastillas de filtro inician exactamente a 24 px del borde izquierdo, en perfecta línea con el icono del encabezado. La última tarjeta y los controles derechos finalizan a 24 px del borde derecho, alineados con el menú del perfil de usuario.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/app/requests/page.tsx](../frontend/src/app/requests/page.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Modal de Bienvenida para Ambas Vistas (Sidebar y Topbar) con Gestión de Restauración/Omisión en Configuración

## Módulo

Portal de Usuario y Ajustes de Visualización (UI/UX)

### Regla

1. **Disponibilidad Homogénea en Ambas Vistas**:
   - El diálogo modal de bienvenida (`PlatformsWelcomeModal`) opera de manera unificada tanto en la vista con barra superior (`PlatformsLaunchpadView`) como en la vista con barra lateral (`PlatformsSidebarView`).
   - Muestra el saludo personalizado con el primer nombre del usuario, la insignia corporativa de bienvenida y las métricas en tiempo real de plataformas activas y solicitudes pendientes.
   - En el pie del diálogo, la casilla de verificación «Omitir la próxima vez» permite guardar la preferencia de omisión en `localStorage` (`nexus.platforms.omit_welcome_modal: true`).
2. **Gestión de Restauración y Omisión desde Configuración de Vista (`UserViewSettings`)**:
   - Dentro del panel de configuración de vista (accesible desde el icono de engrane en la barra superior tanto de Sidebar como de Topbar), se integra la sección dedicada «Mensaje de Bienvenida».
   - Dispone de un conmutador accesible (`Toggle`, `role="switch"`, $\ge 44\text{ px}$) para activar o desactivar la visualización del modal al ingresar.
   - Provee botones dedicados de acción rápida para «Restaurar mensaje» u «Omitir mensaje», acompañados de avisos flotantes Toast de confirmación (`useToast`).
   - Incluye el botón «Previsualizar» para permitir al usuario inspeccionar el diálogo modal interactivo en cualquier momento sin alterar su configuración guardada.
3. **Control desde Preferencias de Usuario (`PreferencesTab`)**:
   - En la sección global de ajustes (`/settings`, pestaña Mis Preferencias), se incorpora la casilla de verificación «Mostrar diálogo de bienvenida al ingresar a plataformas», permitiendo sincronizar la misma clave de almacenamiento local.

### Ejemplo

Un usuario que utiliza la vista de barra lateral cierra el diálogo de bienvenida marcando la casilla «Omitir la próxima vez». Días después, desea volver a ver el diálogo informativo; para ello, pulsa el icono de engrane en la barra superior, abre «Ajustes de Vista» y hace clic en «Restaurar mensaje» (o activa el interruptor). Al ingresar nuevamente a la plataforma o pulsar «Previsualizar», el modal de bienvenida vuelve a desplegarse con sus métricas actualizadas.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-welcome-modal.tsx](../frontend/src/components/platforms/platforms-welcome-modal.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/settings/preferences-tab.tsx](../frontend/src/components/settings/preferences-tab.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Barra de Herramientas de Lanzador (Launchpad): Eliminación de Texto Informativo, Indicador de Solicitudes Pendientes de Aprobación y Selector de Cuadrícula

## Módulo

Portal de Usuario y Vista de Barra Superior (Launchpad)

### Regla

1. **Eliminación de Texto Informativo Innecesario**:
   - Se elimina de forma permanente el texto pasivo «Mostrando N plataformas» de la barra de herramientas de filtros en `PlatformsLaunchpadView`.
2. **Selector de Cuadrícula Interactivo (Extremo Derecho)**:
   - Se incorpora en el extremo derecho de la barra de filtros el botón de configuración de cuadrícula estandarizado (`Icono nombre="panel"`, label `Cuadrícula: {f}×{c}`, `Icono nombre="chevron-abajo"`).
   - Despliega un menú emergente accesible (`role="region"`, `role="menuitem"`, $\ge 44\text{ px}$) con los ajustes predefinidos `2×2`, `2×3`, `3×2` y `3×3`.
   - Persiste las preferencias del usuario en `localStorage` bajo las claves unificadas `portal_grid_filas` (`CLAVE_GRID_FILAS`) y `portal_grid_columnas` (`CLAVE_GRID_COLUMNAS`), sincronizando la experiencia con la vista de barra lateral (`PlatformsSidebarView`) y la consola de administración (`PlatformAdmin`).
   - Adapta dinámicamente las clases de cuadrícula de las tarjetas de plataformas (`CLASES_COLS`) y rellena los espacios vacíos con tarjetas virtuales (*ghost cards*) accesibles (`Espacio disponible`).
3. **Indicador de Solicitudes Pendientes de Aprobación (A la Izquierda del Selector de Cuadrícula)**:
   - Inmediatamente a la izquierda del botón de cuadrícula, se dispone un acceso directo interactivo hacia la bandeja de solicitudes personales (`/requests`), con el contador dinámico en tiempo real (`pendientesCount`) y la leyenda gramaticalmente calibrada (`{N} pendiente de aprobación` / `{N} pendientes de aprobación`).
   - Cuando $N > 0$, el componente adopta el token de advertencia (`border-warning/40 bg-warning/10 text-warning-text`), destacando la atención del usuario sin bloquear la navegación. Cuando $N = 0$, permanece en estado sutil neutral.

### Ejemplo

Al acceder al lanzador de plataformas con barra superior, el usuario ya no visualiza el texto «Mostrando 1 plataformas». En su lugar, observa en el lateral derecho de la barra de filtros el botón «Cuadrícula: 2×3» y, a su izquierda, el enlace interactivo «0 pendientes de aprobación». Si hace clic en el enlace, es dirigido de inmediato a `/requests` para consultar sus trámites. Si abre el selector de cuadrícula y elige «3×3», las tarjetas de plataformas se reorganizan en 3 columnas y se guardan automáticamente sus preferencias en el navegador.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y a la consistencia visual y de comportamiento entre ambas vistas del catálogo.

## Eliminación de Encabezados y Subtítulos Redundantes en el Lanzador de Plataformas

## Módulo

Portal de Usuario y Lanzador de Plataformas (Launchpad)

### Regla

1. **Eliminación de Encabezados y Subtítulos Redundantes**:
   - Se suprimen de forma definitiva los títulos y subtítulos intermedios redundantes en `PlatformsLaunchpadView`:
     - «Catálogo General y Solicitudes»
     - «Solicita permisos o abre tus demás herramientas»
     - «Favoritas y Acceso Rápido»
     - «Tus herramientas más utilizadas»
   - La navegación y segmentación de plataformas queda centralizada exclusivamente en las pastillas interactivas de la barra superior («Todas», «Favoritas», «{Área}»), evitando textos redundantes que ocupen espacio vertical innecesario.
2. **Cuadrícula Unificada y Directa**:
   - Las tarjetas de plataformas se despliegan directamente bajo la barra de herramientas en una cuadrícula unificada y responsiva, siguiendo las dimensiones elegidas por el usuario en el selector de cuadrícula (`2×2`, `2×3`, `3×2`, `3×3`).
   - Las tarjetas virtuales (*ghost cards*) completan los espacios disponibles de forma limpia, logrando una estética idéntica y simétrica a la vista con barra lateral (`PlatformsSidebarView`).

### Ejemplo

Al acceder al portal en la vista de barra superior, el usuario encuentra de inmediato sus tarjetas de plataformas bajo las pastillas de filtro y el selector de cuadrícula, sin bloques de texto repetitivos ni subtítulos explicativos. Si el usuario hace clic en la pastilla «Favoritas», la cuadrícula muestra directamente las aplicaciones marcadas con estrella con fluidez visual.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx) y a las pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Botones de Filtro Simétricos con Iconos de Apoyo en Lanzador de Plataformas

## Módulo

Portal de Usuario y Barra de Filtros (Launchpad)

### Regla

1. **Simetría Dimensional y Diseño Unificado**:
   - Todos los botones de filtro de la barra superior (`Todas`, `Favoritas` y botones dinámicos por `Área`) comparten exactamente las mismas dimensiones y tokens de estilo:
     - Altura unificada de control: `h-12 min-h-12` (48px, conforme a los estándares de área táctil accesible y simétrica con los botones del lateral derecho).
     - Radio de borde: `rounded-xl` (12px).
     - Relleno interno: `px-4 py-2` con separación entre elementos `gap-2.5`.
     - Estado inactivo: `border-panel-border bg-fondo text-body-text hover:border-primary/50 hover:bg-superficie hover:shadow-1`.
     - Estado activo: `border-primary bg-primary text-texto-sobre-accion shadow-1 ring-2 ring-primary/20`.
2. **Iconos de Apoyo SVG Vectoriales Estandarizados**:
   - Cada botón incluye un icono de trazo semántico mediante el componente `<Icono tamano="sm" />`, reemplazando cualquier carácter unicode o emoji inconsistente entre navegadores:
     - `Todas`: `Icono nombre="plataformas"`
     - `Favoritas`: `Icono nombre="favorito"`
     - `Áreas`: `Icono nombre="areas"`
3. **Placa de Contador Simétrica (*Badge Pill*)**:
   - El número de plataformas asociadas a cada filtro se renderiza dentro de una cápsula o pastilla redondeada (`min-w-5 h-5 px-1.5 rounded-full text-xs font-bold tabular-nums`), con fondo traslúcido en estado activo y contraste sutil en estado inactivo.

### Ejemplo

Al visualizar la barra de filtros del lanzador, el botón «Todas», el botón «Favoritas» y los botones de áreas como «Demo Infraestructura» poseen exactamente 48px de alto, la misma curvatura y el mismo espaciado. Cada uno muestra su respectivo icono vectorial a la izquierda, el texto en el centro y una placa numérica redondeada a la derecha, logrando una simetría visual total tanto entre sí como con el selector de cuadrícula y el contador de solicitudes a la derecha de la barra.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Menú Desplegable de Usuario Premium y Modo Compacto Colapsable en la Barra Superior

## Módulo

Portal de Usuario, Barra Superior y Ajustes de Vista

### Regla

1. **Diseño Premium y Simetría del Menú Desplegable (`MenuUsuario`)**:
   - El menú desplegable de usuario (`MenuUsuario`) adopta una tarjeta de diseño premium elevada con desenfoque de fondo (`rounded-2xl border border-panel-border/80 bg-panel-fill p-2.5 shadow-2xl backdrop-blur-xl`).
   - Al desplegarse hacia abajo en la barra superior (`posicionMenu="abajo"`), mantiene una alineación simétrica perfecta hacia el extremo derecho (`top-full right-0 mt-2 min-w-64 w-64`), alineándose estéticamente con el botón activador.
   - **Tarjeta de Encabezado de Usuario**:
     - Avatar vectorial de iniciales con degradado corporativo (`from-primary via-brand to-accent text-texto-sobre-accion`).
     - Nombre completo en negrita y correo electrónico en texto secundario.
     - Insignia (*badge pill*) con el rol oficial del usuario (`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary-text border border-primary/20`).
   - **Acciones y Navegación**:
     - Botón estandarizado de «Cerrar sesión» con altura mínima accesible $\ge 44\text{ px}$ (`min-h-11`), icono de cierre y token semántico de peligro/salida (`text-error hover:bg-error/10`).
2. **Modo Compacto Colapsable del Botón de Usuario (Solo Icono)**:
   - Se incorpora en la configuración del portal (`UserViewSettings` y `PreferencesTab`) un conmutador (*Toggle / Switch*) denominado «Colapsar botón de usuario (solo mostrar icono)».
   - Cuando está **activo** (`true`), el botón de usuario en la barra superior se contrae a un tamaño cuadrado simétrico de 48×48px (`size-12 min-w-12 h-12 min-h-12 justify-center`), ocultando el texto del nombre, el rol y la flecha, y mostrando exclusivamente el avatar con las iniciales del usuario. Coincide exactamente en geometría y estilo con los demás botones de icono de la barra superior (campana, tema, ajustes).
   - Cuando está **inactivo** (`false`, por omisión), despliega la tarjeta completa con avatar, nombre, rol y chevron animado.
   - Persiste la preferencia en `localStorage` bajo la clave `nexus.platforms.compact_user_button` (`CLAVE_BOTON_USUARIO_COMPACTO`) y se sincroniza reactivamente en tiempo real mediante el evento `nexus:compact-user-button`.

### Ejemplo

Un usuario que desea una barra superior más despejada entra a «Ajustes de Vista» y activa el interruptor «Colapsar botón de usuario (solo mostrar icono)». Al instante, el botón de su perfil en la esquina superior derecha se contrae a un icono cuadrado simétrico de 48px que muestra solo su avatar «[A]». Al hacer clic sobre el icono, se despliega fluidamente hacia abajo la tarjeta premium de 256px de ancho con su avatar grande, nombre, correo, etiqueta «Administrador global» y la opción para cerrar sesión.

### Impacto

Afecta a [frontend/src/components/marco/menu-usuario.tsx](../frontend/src/components/marco/menu-usuario.tsx), [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/settings/preferences-tab.tsx](../frontend/src/components/settings/preferences-tab.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Menú Desplegable de Notificaciones en la Vista de Usuario

## Módulo

Portal de Usuario y Notificaciones

### Regla

1. **Despliegue en Menú Dropdown Exclusivo en Vista de Usuario (`MenuNotificaciones`)**:
   - En las vistas del portal de usuario (`PlatformsTopbar` y `PlatformsSidebarView`), el botón de campana opera como un disparador interactivo (`role="button"`, `aria-haspopup="dialog"`) que abre un menú desplegable flotante hacia abajo en lugar de redirigir de inmediato a la ruta `/notifications`.
   - En el panel de administración (`BarraSuperior`), el botón de notificaciones se mantiene sin cambios, navegando directamente a `/notifications`.
2. **Geometría, Simetría y Área Táctil**:
   - El botón disparador mantiene simetría cuadrada uniforme de 48×48px (`size-12 min-w-12 h-12 min-h-12`), radio de borde `rounded-xl`, borde de panel y punto de alerta de notificaciones sin leer (`bg-error-solid`).
   - El panel desplegable se posiciona hacia abajo a la derecha (`top-full right-0 mt-2 w-80 sm:w-96`) con diseño premium (`rounded-2xl border border-panel-border/80 bg-panel-fill shadow-2xl backdrop-blur-xl`).
3. **Contenido y Acciones del Panel**:
   - Encabezado con título «Notificaciones», indicador de conteo no leídas y botón accesible «Marcar leídas» que invoca `api.markNotificationsRead()` y actualiza el estado en vivo.
   - Lista con desplazamiento interno de altura acotada (`max-h-80 overflow-y-auto`) con tarjetas de notificaciones que muestran icono y tono por categoría (`exito`, `error`, `aviso`, `info` con tokens semánticos `*-text`), título, hora relativa y descripción.
   - Estados accesibles de carga con `Skeleton` y mensaje vacío amigable cuando no hay alertas.
   - Pie con enlace `Link` de altura accesible $\ge 44\text{ px}$ hacia `/notifications` («Ver todas las notificaciones →»).
   - Cierre interactivo mediante tecla `Escape` o clic fuera del componente.

### Ejemplo

Al hacer clic en la campana de notificaciones de la barra superior del portal de plataformas, en vez de abandonar la pantalla actual, se abre un menú emergente elegante mostrando las 2 notificaciones recientes (ej. "Acceso aprobado a Slack"). El usuario puede pulsar "Marcar leídas" para apagar el indicador o hacer clic en "Ver todas las notificaciones" si desea ir a la bandeja completa.

### Impacto

Afecta a [frontend/src/components/platforms/menu-notificaciones.tsx](../frontend/src/components/platforms/menu-notificaciones.tsx), [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Modal de Bienvenida Emergente con Opción de Omisión en Plataformas (Launchpad)

## Módulo

Portal de Usuario y Visualización de Plataformas (UI/UX)

### Regla

1. **Sustitución de Banner Estático por Modal Emergente**:
   - En la vista de lanzamiento de plataformas (`PlatformsLaunchpadView`), se retira el bloque estático del encabezado Hero que ocupaba espacio vertical permanente en la parte superior del catálogo.
   - En su lugar, el mensaje de bienvenida y métricas de resumen («Plataformas activas» y «Solicitudes en proceso») se despliegan mediante un diálogo modal flotante accesible (`Modal` de `@/components/form`, `role="dialog"`, con `aria-modal="true"`, trampa de foco y bloqueo de scroll).
2. **Casilla de Omisión Persistente**:
   - El pie del modal (`footer`) incorpora una casilla de verificación accesible (`Checkbox`) con la leyenda «Omitir la próxima vez» y un botón primario accesible «Entendido» ($\ge 44\text{ px}$ / `min-h-12`).
   - Al cerrar el diálogo con la casilla activada, se almacena de forma persistente la clave `'nexus.platforms.omit_welcome_modal': 'true'` en `localStorage`, evitando que el modal vuelva a interrumpir la navegación en futuras visitas o recargas.
   - Si el usuario cierra el modal sin marcar la casilla (o mediante Escape / botón de cierre), la preferencia no se fija, permitiendo mostrar el resumen en la próxima sesión.
3. **Liberación Inmediata de Espacio para el Catálogo**:
   - Al eliminarse el banner estático fijo, la barra de pastillas de filtro y la cuadrícula de tarjetas de plataformas inician directamente en la parte superior útil de la pantalla, maximizando la visibilidad del catálogo tanto en escritorio como en dispositivos móviles.

### Ejemplo

Un usuario ingresa a la vista de plataformas. En lugar de ver un contenedor oscuro permanente encima de sus herramientas, aparece una ventana modal de bienvenida con su saludo ("¡Hola, Juan! 👋"), el estado de sus plataformas y un checkbox que dice "Omitir la próxima vez". El usuario marca la casilla y hace clic en "Entendido". El modal desaparece, la cuadrícula de plataformas queda visible desde el tope de la pantalla, y en sus próximos inicios de sesión el modal ya no vuelve a abrirse.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx) y a la suite de pruebas unitarias en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Alineación y Simetría Horizontal entre Barra Superior (Header) y Cuerpo (Main) en Modo Topbar

## Módulo

Portal de Usuario y Visualización de Plataformas (UI/UX)

### Regla

1. **Simetría Horizontal Idéntica entre Header y Main**:
   - En la vista de barra superior (`PlatformsShell` y `/requests`), el contenedor principal `<main>` homologa su espaciado interior horizontal con la barra superior (`PlatformsTopbar`), aplicando `p-4 md:p-6` (`16px` en móvil y `24px` en escritorio).
   - Se elimina la regla de espaciado divergente `md:p-8` (`32px`), garantizando que la orilla izquierda y derecha del contenido del cuerpo coincidan exactamente con la posición del logotipo y menú de usuario de la barra superior.
2. **Eliminación de Franjas y Holguras Asimétricas**:
   - Al unificarse el padding horizontal a `px-4 md:px-6`, las tarjetas de plataformas, la barra de filtros y las tablas de solicitudes arrancan en la misma línea vertical de referencia que el escudo/marca institucional, evitando cualquier desfase visual o margen lateral indeseado.

### Ejemplo

Al visualizar el portal en pantalla completa en vista Topbar, la primera tarjeta de la cuadrícula y las pastillas de filtro inician exactamente a 24 px del borde izquierdo, en perfecta línea con el icono del encabezado. La última tarjeta y los controles derechos finalizan a 24 px del borde derecho, alineados con el menú del perfil de usuario.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/app/requests/page.tsx](../frontend/src/app/requests/page.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Modal de Bienvenida para Ambas Vistas (Sidebar y Topbar) con Gestión de Restauración/Omisión en Configuración

## Módulo

Portal de Usuario y Ajustes de Visualización (UI/UX)

### Regla

1. **Disponibilidad Homogénea en Ambas Vistas**:
   - El diálogo modal de bienvenida (`PlatformsWelcomeModal`) opera de manera unificada tanto en la vista con barra superior (`PlatformsLaunchpadView`) como en la vista con barra lateral (`PlatformsSidebarView`).
   - Muestra el saludo personalizado con el primer nombre del usuario, la insignia corporativa de bienvenida y las métricas en tiempo real de plataformas activas y solicitudes pendientes.
   - En el pie del diálogo, la casilla de verificación «Omitir la próxima vez» permite guardar la preferencia de omisión en `localStorage` (`nexus.platforms.omit_welcome_modal: true`).
2. **Gestión de Restauración y Omisión desde Configuración de Vista (`UserViewSettings`)**:
   - Dentro del panel de configuración de vista (accesible desde el icono de engrane en la barra superior tanto de Sidebar como de Topbar), se integra la sección dedicada «Mensaje de Bienvenida».
   - Dispone de un conmutador accesible (`Toggle`, `role="switch"`, $\ge 44\text{ px}$) para activar o desactivar la visualización del modal al ingresar.
   - Provee botones dedicados de acción rápida para «Restaurar mensaje» u «Omitir mensaje», acompañados de avisos flotantes Toast de confirmación (`useToast`).
   - Incluye el botón «Previsualizar» para permitir al usuario inspeccionar el diálogo modal interactivo en cualquier momento sin alterar su configuración guardada.
3. **Control desde Preferencias de Usuario (`PreferencesTab`)**:
   - En la sección global de ajustes (`/settings`, pestaña Mis Preferencias), se incorpora la casilla de verificación «Mostrar diálogo de bienvenida al ingresar a plataformas», permitiendo sincronizar la misma clave de almacenamiento local.

### Ejemplo

Un usuario que utiliza la vista de barra lateral cierra el diálogo de bienvenida marcando la casilla «Omitir la próxima vez». Días después, desea volver a ver el diálogo informativo; para ello, pulsa el icono de engrane en la barra superior, abre «Ajustes de Vista» y hace clic en «Restaurar mensaje» (o activa el interruptor). Al ingresar nuevamente a la plataforma o pulsar «Previsualizar», el modal de bienvenida vuelve a desplegarse con sus métricas actualizadas.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-welcome-modal.tsx](../frontend/src/components/platforms/platforms-welcome-modal.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/settings/preferences-tab.tsx](../frontend/src/components/settings/preferences-tab.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Barra de Herramientas de Lanzador (Launchpad): Eliminación de Texto Informativo, Indicador de Solicitudes Pendientes de Aprobación y Selector de Cuadrícula

## Módulo

Portal de Usuario y Vista de Barra Superior (Launchpad)

### Regla

1. **Eliminación de Texto Informativo Innecesario**:
   - Se elimina de forma permanente el texto pasivo «Mostrando N plataformas» de la barra de herramientas de filtros en `PlatformsLaunchpadView`.
2. **Selector de Cuadrícula Interactivo (Extremo Derecho)**:
   - Se incorpora en el extremo derecho de la barra de filtros el botón de configuración de cuadrícula estandarizado (`Icono nombre="panel"`, label `Cuadrícula: {f}×{c}`, `Icono nombre="chevron-abajo"`).
   - Despliega un menú emergente accesible (`role="region"`, `role="menuitem"`, $\ge 44\text{ px}$) con los ajustes predefinidos `2×2`, `2×3`, `3×2` y `3×3`.
   - Persiste las preferencias del usuario en `localStorage` bajo las claves unificadas `portal_grid_filas` (`CLAVE_GRID_FILAS`) y `portal_grid_columnas` (`CLAVE_GRID_COLUMNAS`), sincronizando la experiencia con la vista de barra lateral (`PlatformsSidebarView`) y la consola de administración (`PlatformAdmin`).
   - Adapta dinámicamente las clases de cuadrícula de las tarjetas de plataformas (`CLASES_COLS`) y rellena los espacios vacíos con tarjetas virtuales (*ghost cards*) accesibles (`Espacio disponible`).
3. **Indicador de Solicitudes Pendientes de Aprobación (A la Izquierda del Selector de Cuadrícula)**:
   - Inmediatamente a la izquierda del botón de cuadrícula, se dispone un acceso directo interactivo hacia la bandeja de solicitudes personales (`/requests`), con el contador dinámico en tiempo real (`pendientesCount`) y la leyenda gramaticalmente calibrada (`{N} pendiente de aprobación` / `{N} pendientes de aprobación`).
   - Cuando $N > 0$, el componente adopta el token de advertencia (`border-warning/40 bg-warning/10 text-warning-text`), destacando la atención del usuario sin bloquear la navegación. Cuando $N = 0$, permanece en estado sutil neutral.

### Ejemplo

Al acceder al lanzador de plataformas con barra superior, el usuario ya no visualiza el texto «Mostrando 1 plataformas». En su lugar, observa en el lateral derecho de la barra de filtros el botón «Cuadrícula: 2×3» y, a su izquierda, el enlace interactivo «0 pendientes de aprobación». Si hace clic en el enlace, es dirigido de inmediato a `/requests` para consultar sus trámites. Si abre el selector de cuadrícula y elige «3×3», las tarjetas de plataformas se reorganizan en 3 columnas y se guardan automáticamente sus preferencias en el navegador.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y a la consistencia visual y de comportamiento entre ambas vistas del catálogo.

## Eliminación de Encabezados y Subtítulos Redundantes en el Lanzador de Plataformas

## Módulo

Portal de Usuario y Lanzador de Plataformas (Launchpad)

### Regla

1. **Eliminación de Encabezados y Subtítulos Redundantes**:
   - Se suprimen de forma definitiva los títulos y subtítulos intermedios redundantes en `PlatformsLaunchpadView`:
     - «Catálogo General y Solicitudes»
     - «Solicita permisos o abre tus demás herramientas»
     - «Favoritas y Acceso Rápido»
     - «Tus herramientas más utilizadas»
   - La navegación y segmentación de plataformas queda centralizada exclusivamente en las pastillas interactivas de la barra superior («Todas», «Favoritas», «{Área}»), evitando textos redundantes que ocupen espacio vertical innecesario.
2. **Cuadrícula Unificada y Directa**:
   - Las tarjetas de plataformas se despliegan directamente bajo la barra de herramientas en una cuadrícula unificada y responsiva, siguiendo las dimensiones elegidas por el usuario en el selector de cuadrícula (`2×2`, `2×3`, `3×2`, `3×3`).
   - Las tarjetas virtuales (*ghost cards*) completan los espacios disponibles de forma limpia, logrando una estética idéntica y simétrica a la vista con barra lateral (`PlatformsSidebarView`).

### Ejemplo

Al acceder al portal en la vista de barra superior, el usuario encuentra de inmediato sus tarjetas de plataformas bajo las pastillas de filtro y el selector de cuadrícula, sin bloques de texto repetitivos ni subtítulos explicativos. Si el usuario hace clic en la pastilla «Favoritas», la cuadrícula muestra directamente las aplicaciones marcadas con estrella con fluidez visual.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx) y a las pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Botones de Filtro Simétricos con Iconos de Apoyo en Lanzador de Plataformas

## Módulo

Portal de Usuario y Barra de Filtros (Launchpad)

### Regla

1. **Simetría Dimensional y Diseño Unificado**:
   - Todos los botones de filtro de la barra superior (`Todas`, `Favoritas` y botones dinámicos por `Área`) comparten exactamente las mismas dimensiones y tokens de estilo:
     - Altura unificada de control: `h-12 min-h-12` (48px, conforme a los estándares de área táctil accesible y simétrica con los botones del lateral derecho).
     - Radio de borde: `rounded-xl` (12px).
     - Relleno interno: `px-4 py-2` con separación entre elementos `gap-2.5`.
     - Estado inactivo: `border-panel-border bg-fondo text-body-text hover:border-primary/50 hover:bg-superficie hover:shadow-1`.
     - Estado activo: `border-primary bg-primary text-texto-sobre-accion shadow-1 ring-2 ring-primary/20`.
2. **Iconos de Apoyo SVG Vectoriales Estandarizados**:
   - Cada botón incluye un icono de trazo semántico mediante el componente `<Icono tamano="sm" />`, reemplazando cualquier carácter unicode o emoji inconsistente entre navegadores:
     - `Todas`: `Icono nombre="plataformas"`
     - `Favoritas`: `Icono nombre="favorito"`
     - `Áreas`: `Icono nombre="areas"`
3. **Placa de Contador Simétrica (*Badge Pill*)**:
   - El número de plataformas asociadas a cada filtro se renderiza dentro de una cápsula o pastilla redondeada (`min-w-5 h-5 px-1.5 rounded-full text-xs font-bold tabular-nums`), con fondo traslúcido en estado activo y contraste sutil en estado inactivo.

### Ejemplo

Al visualizar la barra de filtros del lanzador, el botón «Todas», el botón «Favoritas» y los botones de áreas como «Demo Infraestructura» poseen exactamente 48px de alto, la misma curvatura y el mismo espaciado. Cada uno muestra su respectivo icono vectorial a la izquierda, el texto en el centro y una placa numérica redondeada a la derecha, logrando una simetría visual total tanto entre sí como con el selector de cuadrícula y el contador de solicitudes a la derecha de la barra.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Menú Desplegable de Usuario Premium y Modo Compacto Colapsable en la Barra Superior

## Módulo

Portal de Usuario, Barra Superior y Ajustes de Vista

### Regla

1. **Diseño Premium y Simetría del Menú Desplegable (`MenuUsuario`)**:
   - El menú desplegable de usuario (`MenuUsuario`) adopta una tarjeta de diseño premium elevada con desenfoque de fondo (`rounded-2xl border border-panel-border/80 bg-panel-fill p-2.5 shadow-2xl backdrop-blur-xl`).
   - Al desplegarse hacia abajo en la barra superior (`posicionMenu="abajo"`), mantiene una alineación simétrica perfecta hacia el extremo derecho (`top-full right-0 mt-2 min-w-64 w-64`), alineándose estéticamente con el botón activador.
   - **Tarjeta de Encabezado de Usuario**:
     - Avatar vectorial de iniciales con degradado corporativo (`from-primary via-brand to-accent text-texto-sobre-accion`).
     - Nombre completo en negrita y correo electrónico en texto secundario.
     - Insignia (*badge pill*) con el rol oficial del usuario (`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary-text border border-primary/20`).
   - **Acciones y Navegación**:
     - Botón estandarizado de «Cerrar sesión» con altura mínima accesible $\ge 44\text{ px}$ (`min-h-11`), icono de cierre y token semántico de peligro/salida (`text-error hover:bg-error/10`).
2. **Modo Compacto Colapsable del Botón de Usuario (Solo Icono)**:
   - Se incorpora en la configuración del portal (`UserViewSettings` y `PreferencesTab`) un conmutador (*Toggle / Switch*) denominado «Colapsar botón de usuario (solo mostrar icono)».
   - Cuando está **activo** (`true`), el botón de usuario en la barra superior se contrae a un tamaño cuadrado simétrico de 48×48px (`size-12 min-w-12 h-12 min-h-12 justify-center`), ocultando el texto del nombre, el rol y la flecha, y mostrando exclusivamente el avatar con las iniciales del usuario. Coincide exactamente en geometría y estilo con los demás botones de icono de la barra superior (campana, tema, ajustes).
   - Cuando está **inactivo** (`false`, por omisión), despliega la tarjeta completa con avatar, nombre, rol y chevron animado.
   - Persiste la preferencia en `localStorage` bajo la clave `nexus.platforms.compact_user_button` (`CLAVE_BOTON_USUARIO_COMPACTO`) y se sincroniza reactivamente en tiempo real mediante el evento `nexus:compact-user-button`.

### Ejemplo

Un usuario que desea una barra superior más despejada entra a «Ajustes de Vista» y activa el interruptor «Colapsar botón de usuario (solo mostrar icono)». Al instante, el botón de su perfil en la esquina superior derecha se contrae a un icono cuadrado simétrico de 48px que muestra solo su avatar «[A]». Al hacer clic sobre el icono, se despliega fluidamente hacia abajo la tarjeta premium de 256px de ancho con su avatar grande, nombre, correo, etiqueta «Administrador global» y la opción para cerrar sesión.

### Impacto

Afecta a [frontend/src/components/marco/menu-usuario.tsx](../frontend/src/components/marco/menu-usuario.tsx), [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/settings/preferences-tab.tsx](../frontend/src/components/settings/preferences-tab.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Menú Desplegable de Notificaciones en la Vista de Usuario

## Módulo

Portal de Usuario y Notificaciones

### Regla

1. **Despliegue en Menú Dropdown Exclusivo en Vista de Usuario (`MenuNotificaciones`)**:
   - En las vistas del portal de usuario (`PlatformsTopbar` y `PlatformsSidebarView`), el botón de campana opera como un disparador interactivo (`role="button"`, `aria-haspopup="dialog"`) que abre un menú desplegable flotante hacia abajo en lugar de redirigir de inmediato a la ruta `/notifications`.
   - En el panel de administración (`BarraSuperior`), el botón de notificaciones se mantiene sin cambios, navegando directamente a `/notifications`.
2. **Geometría, Simetría y Área Táctil**:
   - El botón disparador mantiene simetría cuadrada uniforme de 48×48px (`size-12 min-w-12 h-12 min-h-12`), radio de borde `rounded-xl`, borde de panel y punto de alerta de notificaciones sin leer (`bg-error-solid`).
   - El panel desplegable se posiciona hacia abajo a la derecha (`top-full right-0 mt-2 w-80 sm:w-96`) con diseño premium (`rounded-2xl border border-panel-border/80 bg-panel-fill shadow-2xl backdrop-blur-xl`).
3. **Contenido y Acciones del Panel**:
   - Encabezado con título «Notificaciones», indicador de conteo no leídas y botón accesible «Marcar leídas» que invoca `api.markNotificationsRead()` y actualiza el estado en vivo.
   - Lista con desplazamiento interno de altura acotada (`max-h-80 overflow-y-auto`) con tarjetas de notificaciones que muestran icono y tono por categoría (`exito`, `error`, `aviso`, `info` con tokens semánticos `*-text`), título, hora relativa y descripción.
   - Estados accesibles de carga con `Skeleton` y mensaje vacío amigable cuando no hay alertas.
   - Pie con enlace `Link` de altura accesible $\ge 44\text{ px}$ hacia `/notifications` («Ver todas las notificaciones →»).
   - Cierre interactivo mediante tecla `Escape` o clic fuera del componente.

### Ejemplo

Al hacer clic en la campana de notificaciones de la barra superior del portal de plataformas, en vez de abandonar la pantalla actual, se abre un menú emergente elegante mostrando las 2 notificaciones recientes (ej. "Acceso aprobado a Slack"). El usuario puede pulsar "Marcar leídas" para apagar el indicador o hacer clic en "Ver todas las notificaciones" si desea ir a la bandeja completa.

### Impacto

Afecta a [frontend/src/components/platforms/menu-notificaciones.tsx](../frontend/src/components/platforms/menu-notificaciones.tsx), [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Cuadrícula Responsiva a Todo el Alto, Botones de Filtro Simétricos y Visibilidad Condicional de Solicitudes Pendientes

## Módulo

Portal de Usuario, Lanzador de Plataformas y Notificaciones Toast

### Regla

1. **Cuadrícula Responsiva a Todo el Alto y Ancho**:
   - En `PlatformsLaunchpadView`, la cuadrícula de tarjetas de plataformas (`role="region"`) y sus slots (tarjetas reales y *ghost cards*) adoptan `flex-1 h-full min-h-0 auto-rows-fr` junto con las utilidades de filas correspondientes (`sm:grid-rows-2`, `sm:grid-rows-3`).
   - Las tarjetas distribuyen su contenido con `flex-col justify-between` y pie `mt-auto`, ocupando proporcionalmente todo el alto disponible del contenedor sin dejar espacio en blanco ocioso inferior.
2. **Visibilidad Condicional del Recuadro de Solicitudes Pendientes de Aprobación**:
   - El recuadro/enlace que muestra las solicitudes pendientes de aprobación a la izquierda del selector de cuadrícula se renderiza **únicamente** cuando el usuario tiene 1 o más solicitudes pendientes (`pendientesCount > 0`).
   - Si el conteo es 0 (`pendientesCount === 0`), el recuadro permanece completamente oculto, evitando ruido visual redundante.
3. **Simetría y Ancho Unificado en Botones de Filtro**:
   - Los botones de filtro de la barra superior («Todas», «Favoritas» y botones dinámicos por «Área») comparten de forma estricta el mismo ancho fijo y simétrico (`w-48 sm:w-52 min-w-48 sm:min-w-52 justify-between`).
   - Cada botón agrupa el icono vectorial y la etiqueta truncada a la izquierda (`flex items-center gap-2 min-w-0`), y la cápsula con el contador numérico a la derecha (`shrink-0`), asegurando alineación visual perfecta entre sí y con el selector de cuadrícula.
4. **Diseño Visual Premium en Notificaciones Toast**:
   - Las notificaciones emergentes (`Toast`) incorporan un borde de acento izquierdo pronunciado de 4px (`border-l-4`) según el tono semántico (`success`, `error`, `warning`, `info`).
   - El contenedor del icono adopta un formato de squircle elevado (`size-11 rounded-xl border shadow-xs`) con fondo traslúcido y sombra teñida.
   - La barra de progreso inferior se integra en un riel redondeado sutil (`bg-superficie-hundida/40 rounded-full h-1`) y el botón de cierre cuenta con área táctil accesible $\ge 44\text{ px}$.

### Ejemplo

Al acceder al lanzador de plataformas con una cuadrícula 2×2, las 4 tarjetas se distribuyen uniformemente abarcando todo el alto y ancho del panel principal. Si el usuario no tiene solicitudes en revisión, el recuadro de solicitudes se oculta por completo; al seleccionar filtros, los botones «Todas», «Favoritas» y «Demo Infraestructura» lucen exactamente del mismo ancho con sus números alineados. Cualquier aviso toast (ej. al solicitar acceso o guardar cambios) surge con su acento de color a la izquierda, icono elevado y diseño premium.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/src/components/toast.tsx](../frontend/src/components/toast.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Estandarización de Iconografía Vectorial en el Buscador de Plataformas

## Módulo

Portal de Usuario y Barra Superior (`PlatformsTopbar`)

### Regla

El buscador central de la barra superior del portal de plataformas utiliza exclusivamente el icono de trazo vectorial SVG estandarizado del sistema (`<Icono nombre="buscar" tamano="sm" />`), suprimiendo cualquier emoji o carácter unicode (como 🔍) para mantener consistencia cromática (`currentColor`), simetría geométrica y legibilidad en temas claro y oscuro.

### Ejemplo

Al visualizar la barra superior del portal de usuario, el campo de búsqueda de plataformas presenta a su izquierda la lupa vectorial delineada en color `text-texto-secundario` con trazo uniforme de 2px, idéntica en estética y proporciones al resto de la iconografía de la barra (escudo, plataformas, solicitudes, ajustes, campana).

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Reactividad y Sincronización en Caliente de Plataformas Favoritas

## Módulo

Portal de Usuario (`useCatalogoSolicitable`, `PlatformsLaunchpadView`, `PlatformsSidebarView`, `FavoriteButton`)

### Regla

Al alternar la estrella de favorito en cualquier tarjeta de plataforma del portal de usuario, el estado se sincroniza en caliente de forma inmediata y reactiva tanto en la colección de plataformas del cliente como en los contadores de filtros («Favoritas») y la visibilidad de las tarjetas filtradas, sin requerir recargar la página (`F5`). Se propaga la función `marcarFavorito` desde `useCatalogoSolicitable` a `PlatformMockupCard`, ejecutando una actualización optimista inmediata en la interfaz mientras se confirma la persistencia contra el endpoint `POST /platforms/:id/favorite` y se revalida en segundo plano con `mias.reload()`.

### Ejemplo

Un usuario se encuentra en el portal de plataformas con 0 favoritas y pulsa la estrella en una tarjeta activa. La estrella se ilumina en amarillo al instante, el contador del botón de filtro cambia de «Favoritas (0)» a «Favoritas (1)» en 0 milisegundos y, al seleccionar la pastilla «Favoritas», la plataforma se muestra de inmediato sin que el usuario deba refrescar su navegador.

### Impacto

Afecta a [frontend/src/components/access/use-catalogo-solicitable.ts](../frontend/src/components/access/use-catalogo-solicitable.ts), [frontend/src/components/favorite-button.tsx](../frontend/src/components/favorite-button.tsx), [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), y pruebas en [frontend/tests/components/access/use-catalogo-solicitable.test.ts](../frontend/tests/components/access/use-catalogo-solicitable.test.ts) y [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Supresión del Banner Redundante en Ajustes de Vista de Usuario

## Módulo

Portal de Usuario y Personalización (`UserViewSettings`)

### Regla

En la vista de configuración y personalización del portal de plataformas (`UserViewSettings`), se suprime el banner/encabezado superior redundante («Ajustes y Personalización de Vista») para maximizar el área útil vertical, eliminando duplicidad informativa respecto a los controles de navegación globales (barra superior y menú lateral) y permitiendo al usuario acceder directamente a las opciones de configuración (disposición del portal, tarjetas, menú y bienvenida).

### Ejemplo

Al acceder a la pantalla de Ajustes de Vista (pulsando el botón de engrane), el contenido principal despliega de inmediato el selector de Disposición Principal del Portal sin un recuadro de cabecera introductorio, optimizando la visibilidad de los controles y reduciendo el desplazamiento vertical.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Estandarización de Menú Desplegable (Dropdown) en el Filtro de Mi Widget

## Módulo

Portal de Usuario y Configuración de Widget (`UserWidgetConfig`)

### Regla

El filtro de inclusión de plataformas en «Mi Widget» utiliza un menú desplegable interactivo (`role="listbox"`) con botón disparador simétrico (`h-12 min-h-12 w-48 sm:w-52 min-w-48 sm:min-w-52`), consistente con los menús de estado de solicitudes y barra de herramientas del portal. Se sustituye la barra segmentada plana por un botón con icono temático, etiqueta «Mostrar: [Opción]», flecha chevron rotatoria y menú emergente con opciones enriquecidas con iconos, conteos numéricos `(N)` y verificación (`check`) en el elemento activo.

### Ejemplo

Al ingresar a la sección «Mi Widget», la barra de herramientas presenta el selector desplegable con `Mostrar: Todas (2)`. Al pulsar el botón, se abre el menú desplegable mostrando `Todas`, `En el Widget` y `Fuera` con sus respectivos iconos semánticos y conteos exactos, cerrándose automáticamente al seleccionar una opción, pulsar Escape o hacer clic fuera del control.

### Impacto

Afecta a [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Despliegue de Menú de Usuario, Retiro de Acceso a Configuración y Estandarización Iconográfica en Barra Lateral

## Módulo

Portal de Usuario - Vista de Barra Lateral (`PlatformsSidebarView` y `UserViewSettings`)

### Regla

El pie de la barra lateral en la vista de usuario (`PlatformsSidebarView`) debe integrar el componente canónico accesible `MenuUsuario`, el cual responde al clic del usuario abriendo un menú desplegable hacia arriba (`posicionMenu="arriba"`) con información de perfil (avatar, nombre, correo y rol) y botón para cerrar sesión (`/logout`). Queda estrictamente eliminado cualquier acceso directo o icono de engrane que enlace a `/settings` desde el pie de la barra lateral, preservando el aislamiento de áreas no autorizadas. Asimismo, toda iconografía de navegación lateral y configuraciones debe utilizar exclusivamente componentes SVG vectoriales (`Icono`), eliminando caracteres unicode o emojis arbitrarios.

### Ejemplo

Un usuario o administrador visualiza la tarjeta de perfil en el pie del sidebar. Al hacer clic sobre ella, se abre hacia arriba el menú desplegable con sus datos y la acción «Cerrar sesión». No existe ningún enlace de engrane hacia `/settings`. En las opciones de navegación lateral (Favoritas, Mis Solicitudes, Mi Widget, Áreas y Carta Responsiva) y ajustes de vista se visualizan iconos vectoriales SVG limpios (`favorito`, `solicitudes`, `panel`, `areas`, `documento`, `plataformas`).

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Estandarización de Menú Desplegable (Dropdown) en el Filtro de Mi Widget

## Módulo

Portal de Usuario y Configuración de Widget (`UserWidgetConfig`)

### Regla

El filtro de inclusión de plataformas en «Mi Widget» utiliza un menú desplegable interactivo (`role="listbox"`) con botón disparador simétrico (`h-12 min-h-12 w-48 sm:w-52 min-w-48 sm:min-w-52`), consistente con los menús de estado de solicitudes y barra de herramientas del portal. Se sustituye la barra segmentada plana por un botón con icono temático, etiqueta «Mostrar: [Opción]», flecha chevron rotatoria y menú emergente con opciones enriquecidas con iconos, conteos numéricos `(N)` y verificación (`check`) en el elemento activo.

### Ejemplo

Al ingresar a la sección «Mi Widget», la barra de herramientas presenta el selector desplegable con `Mostrar: Todas (2)`. Al pulsar el botón, se abre el menú desplegable mostrando `Todas`, `En el Widget` y `Fuera` con sus respectivos iconos semánticos y conteos exactos, cerrándose automáticamente al seleccionar una opción, pulsar Escape o hacer clic fuera del control.

### Impacto

Afecta a [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Despliegue de Menú de Usuario, Retiro de Acceso a Configuración y Estandarización Iconográfica en Barra Lateral

## Módulo

Portal de Usuario - Vista de Barra Lateral (`PlatformsSidebarView` y `UserViewSettings`)

### Regla

El pie de la barra lateral en la vista de usuario (`PlatformsSidebarView`) debe integrar el componente canónico accesible `MenuUsuario`, el cual responde al clic del usuario abriendo un menú desplegable hacia arriba (`posicionMenu="arriba"`) con información de perfil (avatar, nombre, correo y rol) y botón para cerrar sesión (`/logout`). Queda estrictamente eliminado cualquier acceso directo o icono de engrane que enlace a `/settings` desde el pie de la barra lateral, preservando el aislamiento de áreas no autorizadas. Asimismo, toda iconografía de navegación lateral y configuraciones debe utilizar exclusivamente componentes SVG vectoriales (`Icono`), eliminando caracteres unicode o emojis arbitrarios.

### Ejemplo

Un usuario o administrador visualiza la tarjeta de perfil en el pie del sidebar. Al hacer clic sobre ella, se abre hacia arriba el menú desplegable con sus datos y la acción «Cerrar sesión». No existe ningún enlace de engrane hacia `/settings`. En las opciones de navegación lateral (Favoritas, Mis Solicitudes, Mi Widget, Áreas y Carta Responsiva) y ajustes de vista se visualizan iconos vectoriales SVG limpios (`favorito`, `solicitudes`, `panel`, `areas`, `documento`, `plataformas`).

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Preservación de Borde Superior y Holgura en Animaciones Hover de Tarjetas de Catálogo

## Módulo

Catálogo de Áreas y Plataformas (`TarjetaArea`, `PlatformMockupCard`, `PlatformsSidebarView`, `PlatformAdmin`, `PlatformsLaunchpadView`)

### Regla

Los contenedores scrollables con `overflow-y-auto` que albergan cuadrículas de tarjetas interactivas (`TarjetaArea` y `PlatformMockupCard`) deben contar con holgura perimetral mínima de 4px (`p-1`). Esto garantiza que la elevación por animación al pasar el cursor (`hover` con `transform: translateY(-2px)` y sombra `box-shadow`) no empuje el borde superior ni las curvas de las esquinas (`rounded-xl`) fuera del límite de recorte del contenedor de desbordamiento, conservando el borde superior, esquinas redondeadas y halos de iluminación intactos y 100% visibles. Asimismo, la regla `.nx-area-card:hover` cuenta con `z-index: 2` para elevar su plano visual sobre elementos adyacentes.

### Ejemplo

Al colocar el cursor sobre la tarjeta de un área en la cuadrícula (como «Demo Finanzas»), la tarjeta se eleva suavemente hacia arriba con su halo de color sin que su borde superior sea recortado o desaparecido por el límite del contenedor scrollable.

### Impacto

Afecta a [frontend/src/styles/components.css](../frontend/src/styles/components.css), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Eliminación de Elementos Redundantes (Botón de Áreas y Badge de Área) en Toolbar de Barra Lateral

## Módulo

Portal de Usuario - Vista de Barra Lateral (`PlatformsSidebarView`)

### Regla

En la vista con barra lateral (`PlatformsSidebarView`), la barra de herramientas del contenido no debe contener el botón de retorno «Áreas» (`Volver a áreas`) ni la pastilla/badge del área activa (`Área activa: [nombre]`). Dado que la barra lateral izquierda ya expone de forma permanente la jerarquía completa de navegación («Todas las áreas» y el listado de cada área) y la cabecera superior ya incluye las migas de pan interactivas (`Todas las áreas / [Área]`), dichos elementos resultan redundantes y fuera de contexto en una interfaz de navegación lateral.

### Ejemplo

Al seleccionar un área (por ejemplo «Demo Finanzas») en la barra lateral o al pulsar «Ver plataformas», la barra de herramientas del contenido muestra únicamente el buscador contextual y los selectores de Estado y Cuadrícula. No se renderiza ningún botón `[ < Áreas ]` ni badge duplicado del área, permitiendo navegar entre áreas directamente desde el menú lateral izquierdo o las migas de pan.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Comportamiento del Filtro de Estado en la Sección Favoritas de la Barra Lateral

## Módulo

Portal de Usuario - Vista de Barra Lateral (`PlatformsSidebarView`)

### Regla

Al acceder a la sección «Favoritas» desde la barra lateral (`seccionActiva === 'favoritas'`), el ámbito del catálogo se acota estrictamente al subconjunto de plataformas marcadas como favoritas por el usuario. En esta sección:

1. El selector de estado no debe mostrar la opción «Favoritas» en su menú desplegable, ya que resulta redundante e induce a confusión. Las únicas opciones mostradas son «Todos», «Activas» e «Inactivas».
2. La selección de «Todos», «Activas» o «Inactivas» filtra exclusivamente dentro del conjunto de plataformas favoritas, respetando su condición de actividad o inactividad.
3. Cambiar el filtro de estado dentro de «Favoritas» no debe alterar la sección activa (`seccionActiva`) ni restablecer la vista al catálogo general de áreas (`Todas las áreas`).

### Ejemplo

Un usuario con 2 plataformas favoritas (ambas activas) hace clic en «Favoritas» en la barra lateral. Se le muestran sus 2 plataformas favoritas. Al desplegar el filtro «Estado: Todos», el menú ofrece únicamente «Todos (2)», «Activas (2)» e «Inactivas (0)» sin la opción «Favoritas». Si pulsa «Activas», la vista permanece en la sección Favoritas mostrando las plataformas activas; si pulsa «Inactivas», muestra el estado vacío informativo correspondiente sin redirigirlo a la vista global de áreas.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Estandarización de Tarjetas Fantasma (Ghost Cards) en Cuadrículas de Catálogo

## Módulo

Portal de Usuario y Catálogo de Plataformas/Áreas (`PlatformGhostCard`, `PlatformsLaunchpadView`, `PlatformsSidebarView`, `PlatformAdmin`)

### Regla

Los espacios vacíos que completan la cuadrícula visual configurada (2×2, 2×3, 3×2, 3×3 o 4×2) en cualquier vista del portal (barra superior/launchpad, barra lateral/sidebar y catálogo de áreas en administración) deben utilizar un componente unificado estándar (`PlatformGhostCard`). Dicho componente debe mostrar:

1. Contenedor simétrico con esquinas redondeadas (`rounded-2xl`), borde punteado con token (`border-2 border-dashed border-panel-border/40`), fondo sutil (`bg-panel-fill/20`) y selección desactivada (`select-none pointer-events-none`).
2. Icono central representativo (`panel` o `areas`) enmarcado en pastilla de 40×40px (`w-10 h-10 rounded-xl bg-superficie-hundida`).
3. Mensaje tipográfico estándar «Espacio disponible» con token de color secundario (`text-xs font-medium text-label/60`).
4. Altura mínima sincronizada según la variante de tarjeta (`min-h-56` para estándar/áreas, `min-h-44` para compacta y `min-h-24` para horizontal) ocupando el 100% del alto disponible (`h-full`).

### Ejemplo

Al visualizar una cuadrícula de 2×2 con 1 sola plataforma configurada en cualquier modo de disposición (Topbar o Sidebar), los 3 espacios vacíos restantes muestran de forma idéntica una tarjeta con borde punteado suave, un recuadro central con el icono vectorial de panel y la leyenda «Espacio disponible», eliminando huecos en blanco o cajas vacías sin diseño.

### Impacto

Afecta a [frontend/src/components/platforms/platform-ghost-card.tsx](../frontend/src/components/platforms/platform-ghost-card.tsx), [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platform-admin.tsx](../frontend/src/components/platform-admin.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y [frontend/tests/components/platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Reubicación de Plataformas a Gestión y Nuevo Acceso a Portal en Menú Lateral Administrativo

## Módulo

Marco Administrativo - Navegación Principal y Barra Superior (`nav-items.ts`, `barra-superior.tsx`, `nav-principal.tsx`)

### Regla

En la barra lateral del panel administrativo (`AdminBoard`):

1. El elemento de administración de plataformas (`/admin/platforms` con etiqueta «Plataformas») se reubica dentro de la sección **Gestión** (junto a Áreas, Usuarios, Conectores y Auditoría).
2. Se incorpora una nueva entrada en la sección **General** denominada **Portal** (`/platforms` con icono `plataformas`), que brinda acceso directo al catálogo de usuario.
3. Se retira el botón redundante «Ver Portal (Topbar)» de la barra superior administrativa (`barra-superior.tsx`), centralizando el acceso al portal de usuario desde el menú lateral.

### Ejemplo

Un administrador en el dashboard visualiza en el menú lateral izquierdo la sección «GENERAL» con «Dashboard» y «Portal». Al hacer clic en «Portal», ingresa al catálogo de plataformas de usuario. En la sección «GESTIÓN» visualiza «Plataformas», «Áreas», «Usuarios», etc. La barra superior ya no muestra el botón «Ver Portal (Topbar)».

### Impacto

Afecta a [frontend/src/components/marco/nav-items.ts](../frontend/src/components/marco/nav-items.ts), [frontend/src/components/marco/barra-superior.tsx](../frontend/src/components/marco/barra-superior.tsx), [frontend/tests/lib/marco-nav.test.ts](../frontend/tests/lib/marco-nav.test.ts) y [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Estandarización Simétrica y Pastillas de Pestañas en Ajustes del Admin Board

## Módulo

Administración del Sistema - Pestañas de Ajustes (`SettingsPanel`, `Tabs`, `tabs.tsx`)

### Regla

Los botones de pestañas del panel de Ajustes (`/settings`) deben presentar ancho y alto estandarizados y simétricos siguiendo el diseño de pastillas interactivas del Portal Topbar (`variant="pills"`):

1. **Dimensiones uniformes**: Todos los botones de pestaña comparten exactamente el mismo ancho (`w-48 sm:w-52 min-w-48 sm:min-w-52`) y la misma altura (`h-12 min-h-12`), garantizando simetría visual sin importar la longitud del texto.
2. **Iconografía de soporte**: Cada pestaña incluye un icono vectorial semántico a la izquierda (`plataformas` para Portal, `solicitudes` para Correo, `documento` para Plantillas, `usuarios` para Directorio, `auditoria` para Respaldo, `mas` para Importación masiva y `ajustes` para Mis preferencias).
3. **Estados interactivos**:
   - Pestaña activa: Fondo sólido primario (`bg-primary text-texto-sobre-accion shadow-1 ring-2 ring-primary/20`) con borde coordinado.
   - Pestañas inactivas: Tarjeta con borde sutil (`border-panel-border bg-fondo text-body-text hover:border-primary/50 hover:bg-superficie hover:shadow-1`).

### Ejemplo

Al acceder a `/settings` como superadministrador, la barra de navegación muestra 7 pastillas simétricas con idéntico ancho y altura, cada una con su icono vectorial y texto («Portal», «Correo», «Plantillas», etc.). La pestaña activa se ilumina con el fondo azul corporativo mientras que las restantes se muestran como tarjetas suaves con bordes coordinados y respuesta hover.

### Impacto

Afecta a [frontend/src/components/tabs.tsx](../frontend/src/components/tabs.tsx), [frontend/src/components/settings-panel.tsx](../frontend/src/components/settings-panel.tsx) y pruebas en [frontend/tests/components/pestanas-conmutadores.test.tsx](../frontend/tests/components/pestanas-conmutadores.test.tsx).

## Separadores de Sección y Estandarización de Acciones en la Barra Superior del Portal Topbar

## Módulo

Portal de Usuario - Barra Superior (`platforms-topbar.tsx`, `platforms-sidebar-view.tsx`)

### Regla

En la barra superior del portal (`PlatformsTopbar`), el grupo de acciones y navegación a la derecha se estructura de forma modular delimitando 3 secciones funcionales claras mediante 2 líneas divisorias verticales sutiles (`h-6 w-px bg-panel-border/80 self-center mx-0.5 sm:mx-1 shrink-0`):

1. **Sección 1 — Navegación del portal**:
   - Para usuarios administradores (`esAdmin`): Botón de acceso directo al Panel de Administración (`href="/"`, tooltip «Regresar al panel de administración»), ubicado obligatoriamente como el **primer elemento de izquierda a derecha**. Su diseño se estandariza con la clase uniforme de botones cuadrados (`CLASE_BOTON_ICONO`, borde sutil, fondo de superficie y estados interactivos neutros, sin fondo sólido azul) e incorpora el icono de tablero/dashboard (`panel`).
   - Acceso al catálogo de plataformas (`/platforms`, icono `plataformas`).
   - Acceso a solicitudes personales (`/requests`, icono `solicitudes` con insignia de pendientes).
2. **Primer divisor vertical**: Línea de separación inmediatamente a la izquierda del engrane de ajustes (`divisor-topbar-seccion-1`).
3. **Sección 2 — Herramientas y preferencias de sistema**:
   - Conmutador de configuración y diseño de vista (icono `ajustes`).
   - Conmutador de tema visual (icono `sol`/`luna`).
   - Centro de notificaciones desplegable (icono `campana`).
4. **Segundo divisor vertical**: Línea de separación inmediatamente a la derecha de la campana de notificaciones (`divisor-topbar-seccion-2`).
5. **Sección 3 — Perfil y sesión**:
   - Menú de usuario desplegable con avatar del usuario autenticado.

### Ejemplo

Un administrador accede a `/platforms` en modo Topbar. En la esquina superior derecha observa el botón con el icono de 4 cuadrantes (panel) para volver al admin board, seguido de las opciones «Plataformas» y «Mis solicitudes». A continuación, visualiza una línea vertical de división, seguida de los iconos de ajustes (engrane), tema (luna/sol) y notificaciones (campana). Finalmente, otra línea divisoria vertical separa estos controles del avatar del perfil de usuario, comunicando de manera limpia y jerarquizada cada zona de control.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Corrección de Placeholder y Atajo de Teclado en Buscador de Topbar

## Módulo

Portal de Usuario - Barra Superior (`platforms-topbar.tsx`)

### Regla

En el campo de búsqueda central de la barra superior del portal (`PlatformsTopbar`), el texto de sugerencia (`placeholder`) debe mantenerse conciso y directo con la leyenda «Buscar plataforma...», eliminando listas de ejemplos en paréntesis `(Slack, AWS, Jira...)` o instrucciones textuales de pulsación `o presiona ⌘K`.
La indicación del atajo de teclado se presenta exclusivamente a través de la insignia visual interactiva `<kbd>⌘K</kbd>` posicionada en el extremo derecho del campo, evitando redundancia entre el texto de marcador y el componente visual del atajo.

### Ejemplo

Al acceder al catálogo de plataformas en modo Topbar en pantallas medianas o grandes, el buscador central muestra el icono de lupa a la izquierda, el texto gris sutil «Buscar plataforma...» en el área de entrada y la pastilla `⌘K` a la derecha.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Reubicación del Conmutador Maestro de «Mi Widget» a la Barra de Herramientas y Supresión de Banner Superior

## Módulo

Portal de Usuario - Configuración de Mi Widget (`user-widget-config.tsx`)

### Regla

En la vista de configuración de «Mi Widget» (`UserWidgetConfig`), se suprime el bloque de banner superior que desplegaba el icono, título y descripción extensa («Widget Flotante de Acceso Rápido...»), optimizando el espacio vertical para el catálogo de plataformas.
El conmutador maestro de activación/desactivación del widget flotante se integra directamente dentro de la barra de herramientas principal, posicionándose a la derecha del menú desplegable de filtro (`Mostrar: Todas`):

1. **Dimensiones y apariencia coordinada**: Posee altura de 48 px (`h-12 min-h-12`), bordes redondeados (`rounded-xl`), borde de panel (`border border-panel-border`) y fondo de superficie (`bg-fondo`).
2. **Indicador de estado visual**: Punto circular de pulso activo (`bg-success animate-pulse`) cuando el widget está encendido, o indicador tenue cuando está apagado.
3. **Etiqueta dinámica**: Texto «Widget Encendido» o «Widget Apagado» según el estado booleano de la preferencia.
4. **Interruptor accesible**: Botón interactivo con `role="switch"`, `aria-checked`, `aria-label="Activar o desactivar widget flotante"` y objetivo táctil ergonómico ($\ge 48\text{ px}$).
5. **Divisor de sección**: Línea vertical sutil (`h-6 w-px bg-panel-border/80`) que separa visualmente el filtro desplegable del conmutador maestro.

### Ejemplo

Al acceder a la sección «Mi Widget» desde la barra lateral, el usuario no encuentra un banner superior voluminoso; en su lugar, visualiza directamente la barra de herramientas que contiene el buscador de plataformas a la izquierda, el filtro desplegable `Mostrar: Todas` a la derecha y, junto a este (separado por una línea vertical), el botón conmutador `Widget Encendido` con su switch interactivo.

### Impacto

Afecta a [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Distribución Modular y Rol Centrado en 1 Sola Fila en el Menú de Usuario

## Módulo

Marco Global - Menú Desplegable de Usuario (`menu-usuario.tsx`)

### Regla

En la tarjeta de cabecera del menú emergente de usuario (`MenuUsuario`), los datos de identidad y la insignia de rol se estructuran en dos filas funcionales para asegurar que el rol no se divida en múltiples renglones:

1. **Fila superior (Identidad)**: Se ubica el avatar circular/cuadrado con las iniciales del usuario (`iniciales(session.name)`) alineado a la izquierda, junto al nombre completo (`session.name`) y el correo/cuenta (`session.email`).
2. **Fila inferior (Rol centrado en 1 sola fila)**: La insignia del rol del usuario (`etiquetaRol(session.role)`) se posiciona inmediatamente abajo ocupando el ancho total del contenedor con centrado horizontal (`flex justify-center w-full`) y sin salto de línea (`whitespace-nowrap`).
De este modo, roles con nombres extensos como «Administrador global» o «Administrador de área» disponen del 100% del ancho del popover para desplegarse horizontalmente en una única fila limpia, evitando que la presencia del avatar lateral cause saltos de línea antiestéticos.

### Ejemplo

Al pulsar el botón de usuario en el pie de la barra lateral o en la barra superior, la tarjeta emergente muestra en la parte superior el avatar con la inicial «A» junto al nombre «admin» y correo «admin». Abajo, centrado horizontalmente en una pastilla azul con fondo suave, se lee «Administrador global» en una sola fila completa y simétrica.

### Impacto

Afecta a [frontend/src/components/marco/menu-usuario.tsx](../frontend/src/components/marco/menu-usuario.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y [frontend/tests/components/marco-admin.test.tsx](../frontend/tests/components/marco-admin.test.tsx).

## Icono y Sección de Carta Responsiva en Modo Topbar y Barra Lateral

## Módulo

Portal de Usuario - Barra Superior y Secciones de Navegación (`platforms-topbar.tsx`, `platforms-shell.tsx`, `user-responsiva-section.tsx`, `platforms-sidebar-view.tsx`)

### Regla

En el portal de usuario en modo Topbar (y análogamente en modo Sidebar):

1. **Icono en la barra de navegación del Topbar**: Se incorpora en el grupo de navegación (`<nav aria-label="Navegación del portal">`) el botón interactivo de **Carta Responsiva** (`Icono nombre="documento"` con dimensiones `CLASE_BOTON_ICONO`), acompañado de su respectivo tooltip (`title="Carta Responsiva: Firmada"` o `"Pendiente"`) y un punto indicador de estado (`bg-success` verde si está firmada digitalmente o `bg-warning` ámbar si está pendiente). Este botón se exhibe por defecto y respeta la preferencia de usuario `mostrarDocumentos`.
2. **Sección de Carta Responsiva (`UserResponsivaSection`)**: Al hacer clic en el botón de Carta Responsiva (o al invocar la ruta con el parámetro `?seccion=responsiva`), la vista principal transiciona hacia la sección dedicada de Carta Responsiva:
   - Cabecera con botón de retorno al catálogo («Volver al catálogo»), icono representativo y credencial de estado de firma («Firmada digitalmente» o «Pendiente de firma»).
   - Rejilla informativa de 4 columnas con metadatos del usuario titular, rol en el sistema, versión del documento y fecha/registro de firma digital.
   - Lista detallada de plataformas y áreas institucionales amparadas bajo el marco del documento normativo.
   - Visor con los términos y lineamientos de ciberseguridad, confidencialidad, uso institucional y resguardo de credenciales.
3. **Equivalencia en Barra Lateral**: En la barra lateral (`PlatformsSidebarView`), la opción «Carta Responsiva» dentro de la sección Documentos funciona como botón interactivo que abre la misma vista (`UserResponsivaSection`) con actualización de las migas de pan a `Carta Responsiva`.

### Ejemplo

Un usuario ingresa a `/platforms` en modo Topbar. En la barra superior observa junto a «Plataformas» y «Mis solicitudes» el icono de documento con un punto verde. Al pulsar dicho icono, el catálogo se sustituye por la sección completa de la Carta Responsiva, permitiéndole revisar el documento legal de TI, sus herramientas asignadas y la fecha en que fue firmada. Al presionar «Volver al catálogo», regresa de inmediato a la cuadrícula de plataformas.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/components/platforms/user-responsiva-section.tsx](../frontend/src/components/platforms/user-responsiva-section.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Diseño Vertical y Centrado en Cabecera del Menú de Usuario

## Módulo

Marco Global - Menú Desplegable de Usuario (`menu-usuario.tsx`)

### Regla

En la cabecera emergente del menú de usuario (`MenuUsuario`):

1. **Disposición Vertical Centrada**: Los componentes se apilan de manera vertical (`flex flex-col items-center text-center`) para eliminar colisiones de espacio horizontal:
   - **Avatar superior**: El avatar de usuario (`iniciales(session.name)`) se sitúa en la parte superior centrado, con tamaño proporcionado `size-12` (48 px) y bordes redondeados consistentes.
   - **Identidad intermedia**: Inmediatamente abajo del avatar se centran el nombre (`session.name`) y correo del usuario (`session.email`), aprovechando el ancho disponible para evitar truncamientos prematuros.
   - **Insignia de rol inferior**: En la fila inferior se ubica la pastilla de rol (`etiquetaRol(session.role)`) centrada horizontalmente (`flex justify-center w-full`) con `whitespace-nowrap`, asegurando que roles con denominaciones largas («Administrador global», «Administrador de área») se mantengan en 1 sola fila continua sin dividirse en dos líneas.
2. **Ancho Mínimo de Contenedor**: El menú emergente garantiza un ancho mínimo de al menos `min-w-64` (256 px) tanto en posición superior como inferior, evitando cualquier compresión de los elementos de cabecera.

### Ejemplo

Al desplegar el menú de cuenta desde la barra lateral o la barra superior, la tarjeta muestra en la parte superior el avatar cuadrado púrpura con la letra «A». Justo debajo aparece centrado «admin» y el correo «admin». En la parte inferior de la cabecera se despliega la insignia azul con el texto completo «Administrador global» en una única fila horizontal y perfectamente centrada.

### Impacto

Afecta a [frontend/src/components/marco/menu-usuario.tsx](../frontend/src/components/marco/menu-usuario.tsx) y a las pruebas asociadas en [frontend/tests/components/marco-admin.test.tsx](../frontend/tests/components/marco-admin.test.tsx).

## Persistencia Bidireccional de Sección Activa al Alternar Disposición y Estandarización de Anchura en Menú de Usuario

## Módulo

Portal de Usuario - Shell y Barra Lateral (`platforms-shell.tsx`, `platforms-sidebar-view.tsx`, `menu-usuario.tsx`)

### Regla

1. **Persistencia Bidireccional de Sección Activa en el Portal**: Al alternar entre la disposición de Barra Superior (Topbar) y Barra Lateral (Sidebar) mediante `UserViewSettings`:
   - El estado de la sección activa (`seccionActiva: 'personalizacion' | 'responsiva' | 'catalogo' / 'area'`) se sincroniza bidireccionalmente entre `PlatformsShell` y `PlatformsSidebarView`.
   - Si el usuario se encuentra configurando sus preferencias en «Mi Espacio / Ajustes de Vista» (`seccionActiva === 'personalizacion'`) y conmuta de Topbar a Sidebar (o viceversa), el sistema no interrumpe su flujo ni lo redirige a «Todas las áreas»: mantiene la vista en «Ajustes de Vista» adaptando fluidamente el layout.
   - De forma análoga, si se encuentra en «Carta Responsiva», la transición entre disposiciones preserva la permanencia en dicha sección.
2. **Estandarización de Dimensiones del Menú de Usuario**: La tarjeta emergente desplegable de usuario (`MenuUsuario`) estandariza su ancho de forma homogénea a `w-72` (288 px) en todas las disposiciones del sistema:
   - Modo barra superior (`posicionMenu === 'abajo'`).
   - Modo barra lateral colapsada (`colapsada: bottom-0 left-full ml-2`).
   - Modo barra lateral expandida (`posicionMenu === 'arriba': bottom-full left-0 mb-2`).
   Esto asegura que el componente mantenga idéntico volumen, espaciado y consistencia estética tanto en vistas administrativas como en el portal de usuarios.

### Ejemplo

Un usuario se encuentra en `/platforms` en modo Barra Superior y hace clic en el engrane para ingresar a «Ajustes de Vista». Allí selecciona la tarjeta «Vista Barra Lateral (Sidebar)». La interfaz cambia instantáneamente a la estructura con barra lateral de 264 px y conserva activa la sección de «Ajustes de Vista» con la miga de pan «Mi Espacio / Ajustes de Vista». Al abrir su menú de perfil en el pie del sidebar o en la cabecera, la ventana emergente exhibe un ancho uniforme de 288 px (`w-72`) con el avatar centrado en la parte superior y el rol en una sola fila.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/marco/menu-usuario.tsx](../frontend/src/components/marco/menu-usuario.tsx) y a la suite en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Elevación de Diseño Premium y Concisión en Estados Vacíos (Empty States)

## Módulo

Componentes UI - Notificaciones y Estados Vacíos (`premium-message.tsx`, `note.tsx`, `platforms-launchpad-view.tsx`, `platforms-sidebar-view.tsx`, `user-widget-config.tsx`, `menu-notificaciones.tsx`)

### Regla

Los componentes de estado vacío (`PremiumEmptyState` y `EmptyNote`) elevan su lenguaje visual a nivel SaaS de alta gama bajo las siguientes directrices:

1. **Atmósfera Cromática Multicapa**:
   - Tarjeta contenedora con radio amplio (`rounded-3xl`), borde sutil (`border-primary/20`), fondo con degradado vertical (`bg-gradient-to-b from-primary/[0.04] via-panel-fill/95 to-panel-fill`), sombra proyectada suave (`shadow-lg`) y efecto de cristal esmerilado (`backdrop-blur-md`).
   - Doble halo de iluminación ambiental: resplandor Cobalt superior (`bg-gradient-to-b from-primary/20 via-brand/10 to-transparent blur-3xl opacity-80`) y halo Violet/Accent inferior derecho (`bg-accent/10 blur-3xl opacity-50`).
2. **Caja de Icono Estilo Joya con Aro Concéntrico**:
   - Estructura concéntrica de dos niveles: un aro exterior `size-20` con esquinas redondeadas (`rounded-3xl`), borde sutil y degradado suave, que aloja en su interior la gema elevada `size-full` (`rounded-2xl`) con gradiente vibrante (`from-primary/25 via-brand/20 to-accent/25`), borde iluminado (`border-primary/30`), sombra de elevación (`shadow-md`) y microinteracción táctil (`hover:scale-105`).
   - Punto de luz / aura decorativa superior en la esquina del contenedor.
3. **Jerarquía Tipográfica y Concisión de Textos**:
   - Se priorizan textos cortos y directos: título contundente de 1 a 3 palabras (`text-base sm:text-lg font-black tracking-tight text-body-text`) y subtítulo explicativo conciso de 1 sola frase corta (`text-xs sm:text-sm text-texto-secundario leading-relaxed`), evitando párrafos largos redundantes.
   - En vistas con filtros activos (como catálogo de plataformas o áreas), se ofrece de manera consistente la acción contextual primaria o secundaria para limpiar o restablecer filtros inmediatamente.

### Ejemplo

Al aplicar un filtro que no arroja resultados en el catálogo de plataformas, se despliega una tarjeta centrada con bordes redondeados y doble halo luminoso. En el centro resalta la joya de icono concéntrica con el símbolo de plataforma. Debajo se lee el encabezado claro «Sin resultados» y la leyenda breve «Ninguna plataforma coincide con los filtros aplicados.», acompañado del botón «Restablecer filtros».

### Impacto

Afecta a [frontend/src/components/premium-message.tsx](../frontend/src/components/premium-message.tsx), [frontend/src/components/note.tsx](../frontend/src/components/note.tsx), [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx), [frontend/src/components/platforms/menu-notificaciones.tsx](../frontend/src/components/platforms/menu-notificaciones.tsx) y pruebas en [frontend/tests/components/premium-message.test.tsx](../frontend/tests/components/premium-message.test.tsx).

## Acceso y Configuración de Mi Widget desde la Barra Superior (Topbar)

## Módulo

Portal de Usuario - Barra Superior y Configuración de Accesos Rápidos (`platforms-topbar.tsx`, `platforms-shell.tsx`, `user-widget-config.tsx`)

### Regla

1. **Acceso al Widget en Modo Topbar**: En la barra superior del portal (`PlatformsTopbar`), se incorpora de forma permanente en el clúster de navegación (`<nav aria-label="Navegación del portal">`) el botón interactivo de **Mi Widget** (`Icono nombre="panel"` con dimensiones estándar `CLASE_BOTON_ICONO` y tooltip descriptivo `Mi Widget: Configurar accesos rápidos`).
2. **Navegación Directa e Integrada**: Al pulsar el botón de Mi Widget en modo Topbar (o al navegar a la ruta con el parámetro `?seccion=widget`), el portal conmuta reactivamente a la vista de configuración del widget flotante (`UserWidgetConfig`), permitiendo al usuario:
   - Habilitar o apagar el widget flotante de acceso rápido mediante su interruptor maestro.
   - Filtrar y buscar plataformas del catálogo institucional para incluirlas o removerlas de su widget personal.
   - Probar y manipular el lanzador flotante en tiempo real sin requerir cambiar su preferencia de interfaz a la vista lateral (Sidebar).
3. **Botón de Retorno al Catálogo**: La barra de herramientas de `UserWidgetConfig` incorpora el botón de navegación secundaria «Volver al catálogo» (`onVolver`), permitiendo un retorno inmediato al catálogo de tarjetas con un solo clic.

### Ejemplo

Un usuario que utiliza el portal en modo Barra Superior (Topbar) hace clic en el icono de cuadrícula/panel situado entre «Mis solicitudes» y «Carta Responsiva». La pantalla transiciona directamente a la sección de configuración de «Mi Widget», donde puede activar o desactivar herramientas para su widget flotante persistente. Al presionar el botón «Volver al catálogo», regresa de inmediato a la cuadrícula de plataformas conservando su disposición preferida.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Comportamiento del Filtro de Estado en la Sección Favoritas de la Barra Lateral

## Módulo

Portal de Usuario - Vista de Barra Lateral (`PlatformsSidebarView`)

### Regla

Al acceder a la sección «Favoritas» desde la barra lateral (`seccionActiva === 'favoritas'`), el ámbito del catálogo se acota estrictamente al subconjunto de plataformas marcadas como favoritas por el usuario. En esta sección:

1. El selector de estado no debe mostrar la opción «Favoritas» en su menú desplegable, ya que resulta redundante e induce a confusión. Las únicas opciones mostradas son «Todos», «Activas» e «Inactivas».
2. La selección de «Todos», «Activas» o «Inactivas» filtra exclusivamente dentro del conjunto de plataformas favoritas, respetando su condición de actividad o inactividad.
3. Cambiar el filtro de estado dentro de «Favoritas» no debe alterar la sección activa (`seccionActiva`) ni restablecer la vista al catálogo general de áreas (`Todas las áreas`).

### Ejemplo

Un usuario con 2 plataformas favoritas (ambas activas) hace clic en «Favoritas» en la barra lateral. Se le muestran sus 2 plataformas favoritas. Al desplegar el filtro «Estado: Todos», el menú ofrece únicamente «Todos (2)», «Activas (2)» e «Inactivas (0)» sin la opción «Favoritas». Si pulsa «Activas», la vista permanece en la sección Favoritas mostrando las plataformas activas; si pulsa «Inactivas», muestra el estado vacío informativo correspondiente sin redirigirlo a la vista global de áreas.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Estandarización de Tarjetas Fantasma (Ghost Cards) en Cuadrículas de Catálogo

## Módulo

Portal de Usuario y Catálogo de Plataformas/Áreas (`PlatformGhostCard`, `PlatformsLaunchpadView`, `PlatformsSidebarView`, `PlatformAdmin`)

### Regla

Los espacios vacíos que completan la cuadrícula visual configurada (2×2, 2×3, 3×2, 3×3 o 4×2) en cualquier vista del portal (barra superior/launchpad, barra lateral/sidebar y catálogo de áreas en administración) deben utilizar un componente unificado estándar (`PlatformGhostCard`). Dicho componente debe mostrar:

1. Contenedor simétrico con esquinas redondeadas (`rounded-2xl`), borde punteado con token (`border-2 border-dashed border-panel-border/40`), fondo sutil (`bg-panel-fill/20`) y selección desactivada (`select-none pointer-events-none`).
2. Icono central representativo (`panel` o `areas`) enmarcado en pastilla de 40×40px (`w-10 h-10 rounded-xl bg-superficie-hundida`).
3. Mensaje tipográfico estándar «Espacio disponible» con token de color secundario (`text-xs font-medium text-label/60`).
4. Altura mínima sincronizada según la variante de tarjeta (`min-h-56` para estándar/áreas, `min-h-44` para compacta y `min-h-24` para horizontal) ocupando el 100% del alto disponible (`h-full`).

### Ejemplo

Al visualizar una cuadrícula de 2×2 con 1 sola plataforma configurada en cualquier modo de disposición (Topbar o Sidebar), los 3 espacios vacíos restantes muestran de forma idéntica una tarjeta con borde punteado suave, un recuadro central con el icono vectorial de panel y la leyenda «Espacio disponible», eliminando huecos en blanco o cajas vacías sin diseño.

### Impacto

Afecta a [frontend/src/components/platforms/platform-ghost-card.tsx](../frontend/src/components/platforms/platform-ghost-card.tsx), [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platform-admin.tsx](../frontend/src/components/platform-admin.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y [frontend/tests/components/platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Reubicación de Plataformas a Gestión y Nuevo Acceso a Portal en Menú Lateral Administrativo

## Módulo

Marco Administrativo - Navegación Principal y Barra Superior (`nav-items.ts`, `barra-superior.tsx`, `nav-principal.tsx`)

### Regla

En la barra lateral del panel administrativo (`AdminBoard`):

1. El elemento de administración de plataformas (`/admin/platforms` con etiqueta «Plataformas») se reubica dentro de la sección **Gestión** (junto a Áreas, Usuarios, Conectores y Auditoría).
2. Se incorpora una nueva entrada en la sección **General** denominada **Portal** (`/platforms` con icono `plataformas`), que brinda acceso directo al catálogo de usuario.
3. Se retira el botón redundante «Ver Portal (Topbar)» de la barra superior administrativa (`barra-superior.tsx`), centralizando el acceso al portal de usuario desde el menú lateral.

### Ejemplo

Un administrador en el dashboard visualiza en el menú lateral izquierdo la sección «GENERAL» con «Dashboard» y «Portal». Al hacer clic en «Portal», ingresa al catálogo de plataformas de usuario. En la sección «GESTIÓN» visualiza «Plataformas», «Áreas», «Usuarios», etc. La barra superior ya no muestra el botón «Ver Portal (Topbar)».

### Impacto

Afecta a [frontend/src/components/marco/nav-items.ts](../frontend/src/components/marco/nav-items.ts), [frontend/src/components/marco/barra-superior.tsx](../frontend/src/components/marco/barra-superior.tsx), [frontend/tests/lib/marco-nav.test.ts](../frontend/tests/lib/marco-nav.test.ts) y [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Estandarización Simétrica y Pastillas de Pestañas en Ajustes del Admin Board

## Módulo

Administración del Sistema - Pestañas de Ajustes (`SettingsPanel`, `Tabs`, `tabs.tsx`)

### Regla

Los botones de pestañas del panel de Ajustes (`/settings`) deben presentar ancho y alto estandarizados y simétricos siguiendo el diseño de pastillas interactivas del Portal Topbar (`variant="pills"`):

1. **Dimensiones uniformes**: Todos los botones de pestaña comparten exactamente el mismo ancho (`w-48 sm:w-52 min-w-48 sm:min-w-52`) y la misma altura (`h-12 min-h-12`), garantizando simetría visual sin importar la longitud del texto.
2. **Iconografía de soporte**: Cada pestaña incluye un icono vectorial semántico a la izquierda (`plataformas` para Portal, `solicitudes` para Correo, `documento` para Plantillas, `usuarios` para Directorio, `auditoria` para Respaldo, `mas` para Importación masiva y `ajustes` para Mis preferencias).
3. **Estados interactivos**:
   - Pestaña activa: Fondo sólido primario (`bg-primary text-texto-sobre-accion shadow-1 ring-2 ring-primary/20`) con borde coordinado.
   - Pestañas inactivas: Tarjeta con borde sutil (`border-panel-border bg-fondo text-body-text hover:border-primary/50 hover:bg-superficie hover:shadow-1`).

### Ejemplo

Al acceder a `/settings` como superadministrador, la barra de navegación muestra 7 pastillas simétricas con idéntico ancho y altura, cada una con su icono vectorial y texto («Portal», «Correo», «Plantillas», etc.). La pestaña activa se ilumina con el fondo azul corporativo mientras que las restantes se muestran como tarjetas suaves con bordes coordinados y respuesta hover.

### Impacto

Afecta a [frontend/src/components/tabs.tsx](../frontend/src/components/tabs.tsx), [frontend/src/components/settings-panel.tsx](../frontend/src/components/settings-panel.tsx) y pruebas en [frontend/tests/components/pestanas-conmutadores.test.tsx](../frontend/tests/components/pestanas-conmutadores.test.tsx).

## Separadores de Sección y Estandarización de Acciones en la Barra Superior del Portal Topbar

## Módulo

Portal de Usuario - Barra Superior (`platforms-topbar.tsx`, `platforms-sidebar-view.tsx`)

### Regla

En la barra superior del portal (`PlatformsTopbar`), el grupo de acciones y navegación a la derecha se estructura de forma modular delimitando 3 secciones funcionales claras mediante 2 líneas divisorias verticales sutiles (`h-6 w-px bg-panel-border/80 self-center mx-0.5 sm:mx-1 shrink-0`):

1. **Sección 1 — Navegación del portal**:
   - Para usuarios administradores (`esAdmin`): Botón de acceso directo al Panel de Administración (`href="/"`, tooltip «Regresar al panel de administración»), ubicado obligatoriamente como el **primer elemento de izquierda a derecha**. Su diseño se estandariza con la clase uniforme de botones cuadrados (`CLASE_BOTON_ICONO`, borde sutil, fondo de superficie y estados interactivos neutros, sin fondo sólido azul) e incorpora el icono de tablero/dashboard (`panel`).
   - Acceso al catálogo de plataformas (`/platforms`, icono `plataformas`).
   - Acceso a solicitudes personales (`/requests`, icono `solicitudes` con insignia de pendientes).
2. **Primer divisor vertical**: Línea de separación inmediatamente a la izquierda del engrane de ajustes (`divisor-topbar-seccion-1`).
3. **Sección 2 — Herramientas y preferencias de sistema**:
   - Conmutador de configuración y diseño de vista (icono `ajustes`).
   - Conmutador de tema visual (icono `sol`/`luna`).
   - Centro de notificaciones desplegable (icono `campana`).
4. **Segundo divisor vertical**: Línea de separación inmediatamente a la derecha de la campana de notificaciones (`divisor-topbar-seccion-2`).
5. **Sección 3 — Perfil y sesión**:
   - Menú de usuario desplegable con avatar del usuario autenticado.

### Ejemplo

Un administrador accede a `/platforms` en modo Topbar. En la esquina superior derecha observa el botón con el icono de 4 cuadrantes (panel) para volver al admin board, seguido de las opciones «Plataformas» y «Mis solicitudes». A continuación, visualiza una línea vertical de división, seguida de los iconos de ajustes (engrane), tema (luna/sol) y notificaciones (campana). Finalmente, otra línea divisoria vertical separa estos controles del avatar del perfil de usuario, comunicando de manera limpia y jerarquizada cada zona de control.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Corrección de Placeholder y Atajo de Teclado en Buscador de Topbar

## Módulo

Portal de Usuario - Barra Superior (`platforms-topbar.tsx`)

### Regla

En el campo de búsqueda central de la barra superior del portal (`PlatformsTopbar`), el texto de sugerencia (`placeholder`) debe mantenerse conciso y directo con la leyenda «Buscar plataforma...», eliminando listas de ejemplos en paréntesis `(Slack, AWS, Jira...)` o instrucciones textuales de pulsación `o presiona ⌘K`.
La indicación del atajo de teclado se presenta exclusivamente a través de la insignia visual interactiva `<kbd>⌘K</kbd>` posicionada en el extremo derecho del campo, evitando redundancia entre el texto de marcador y el componente visual del atajo.

### Ejemplo

Al acceder al catálogo de plataformas en modo Topbar en pantallas medianas o grandes, el buscador central muestra el icono de lupa a la izquierda, el texto gris sutil «Buscar plataforma...» en el área de entrada y la pastilla `⌘K` a la derecha.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Reubicación del Conmutador Maestro de «Mi Widget» a la Barra de Herramientas y Supresión de Banner Superior

## Módulo

Portal de Usuario - Configuración de Mi Widget (`user-widget-config.tsx`)

### Regla

En la vista de configuración de «Mi Widget» (`UserWidgetConfig`), se suprime el bloque de banner superior que desplegaba el icono, título y descripción extensa («Widget Flotante de Acceso Rápido...»), optimizando el espacio vertical para el catálogo de plataformas.
El conmutador maestro de activación/desactivación del widget flotante se integra directamente dentro de la barra de herramientas principal, posicionándose a la derecha del menú desplegable de filtro (`Mostrar: Todas`):

1. **Dimensiones y apariencia coordinada**: Posee altura de 48 px (`h-12 min-h-12`), bordes redondeados (`rounded-xl`), borde de panel (`border border-panel-border`) y fondo de superficie (`bg-fondo`).
2. **Indicador de estado visual**: Punto circular de pulso activo (`bg-success animate-pulse`) cuando el widget está encendido, o indicador tenue cuando está apagado.
3. **Etiqueta dinámica**: Texto «Widget Encendido» o «Widget Apagado» según el estado booleano de la preferencia.
4. **Interruptor accesible**: Botón interactivo con `role="switch"`, `aria-checked`, `aria-label="Activar o desactivar widget flotante"` y objetivo táctil ergonómico ($\ge 48\text{ px}$).
5. **Divisor de sección**: Línea vertical sutil (`h-6 w-px bg-panel-border/80`) que separa visualmente el filtro desplegable del conmutador maestro.

### Ejemplo

Al acceder a la sección «Mi Widget» desde la barra lateral, el usuario no encuentra un banner superior voluminoso; en su lugar, visualiza directamente la barra de herramientas que contiene el buscador de plataformas a la izquierda, el filtro desplegable `Mostrar: Todas` a la derecha y, junto a este (separado por una línea vertical), el botón conmutador `Widget Encendido` con su switch interactivo.

### Impacto

Afecta a [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Distribución Modular y Rol Centrado en 1 Sola Fila en el Menú de Usuario

## Módulo

Marco Global - Menú Desplegable de Usuario (`menu-usuario.tsx`)

### Regla

En la tarjeta de cabecera del menú emergente de usuario (`MenuUsuario`), los datos de identidad y la insignia de rol se estructuran en dos filas funcionales para asegurar que el rol no se divida en múltiples renglones:

1. **Fila superior (Identidad)**: Se ubica el avatar circular/cuadrado con las iniciales del usuario (`iniciales(session.name)`) alineado a la izquierda, junto al nombre completo (`session.name`) y el correo/cuenta (`session.email`).
2. **Fila inferior (Rol centrado en 1 sola fila)**: La insignia del rol del usuario (`etiquetaRol(session.role)`) se posiciona inmediatamente abajo ocupando el ancho total del contenedor con centrado horizontal (`flex justify-center w-full`) y sin salto de línea (`whitespace-nowrap`).
De este modo, roles con nombres extensos como «Administrador global» o «Administrador de área» disponen del 100% del ancho del popover para desplegarse horizontalmente en una única fila limpia, evitando que la presencia del avatar lateral cause saltos de línea antiestéticos.

### Ejemplo

Al pulsar el botón de usuario en el pie de la barra lateral o en la barra superior, la tarjeta emergente muestra en la parte superior el avatar con la inicial «A» junto al nombre «admin» y correo «admin». Abajo, centrado horizontalmente en una pastilla azul con fondo suave, se lee «Administrador global» en una sola fila completa y simétrica.

### Impacto

Afecta a [frontend/src/components/marco/menu-usuario.tsx](../frontend/src/components/marco/menu-usuario.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y [frontend/tests/components/marco-admin.test.tsx](../frontend/tests/components/marco-admin.test.tsx).

## Icono y Sección de Carta Responsiva en Modo Topbar y Barra Lateral

## Módulo

Portal de Usuario - Barra Superior y Secciones de Navegación (`platforms-topbar.tsx`, `platforms-shell.tsx`, `user-responsiva-section.tsx`, `platforms-sidebar-view.tsx`)

### Regla

En el portal de usuario en modo Topbar (y análogamente en modo Sidebar):

1. **Icono en la barra de navegación del Topbar**: Se incorpora en el grupo de navegación (`<nav aria-label="Navegación del portal">`) el botón interactivo de **Carta Responsiva** (`Icono nombre="documento"` con dimensiones `CLASE_BOTON_ICONO`), acompañado de su respectivo tooltip (`title="Carta Responsiva: Firmada"` o `"Pendiente"`) y un punto indicador de estado (`bg-success` verde si está firmada digitalmente o `bg-warning` ámbar si está pendiente). Este botón se exhibe por defecto y respeta la preferencia de usuario `mostrarDocumentos`.
2. **Sección de Carta Responsiva (`UserResponsivaSection`)**: Al hacer clic en el botón de Carta Responsiva (o al invocar la ruta con el parámetro `?seccion=responsiva`), la vista principal transiciona hacia la sección dedicada de Carta Responsiva:
   - Cabecera con botón de retorno al catálogo («Volver al catálogo»), icono representativo y credencial de estado de firma («Firmada digitalmente» o «Pendiente de firma»).
   - Rejilla informativa de 4 columnas con metadatos del usuario titular, rol en el sistema, versión del documento y fecha/registro de firma digital.
   - Lista detallada de plataformas y áreas institucionales amparadas bajo el marco del documento normativo.
   - Visor con los términos y lineamientos de ciberseguridad, confidencialidad, uso institucional y resguardo de credenciales.
3. **Equivalencia en Barra Lateral**: En la barra lateral (`PlatformsSidebarView`), la opción «Carta Responsiva» dentro de la sección Documentos funciona como botón interactivo que abre la misma vista (`UserResponsivaSection`) con actualización de las migas de pan a `Carta Responsiva`.

### Ejemplo

Un usuario ingresa a `/platforms` en modo Topbar. En la barra superior observa junto a «Plataformas» y «Mis solicitudes» el icono de documento con un punto verde. Al pulsar dicho icono, el catálogo se sustituye por la sección completa de la Carta Responsiva, permitiéndole revisar el documento legal de TI, sus herramientas asignadas y la fecha en que fue firmada. Al presionar «Volver al catálogo», regresa de inmediato a la cuadrícula de plataformas.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/components/platforms/user-responsiva-section.tsx](../frontend/src/components/platforms/user-responsiva-section.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Diseño Vertical y Centrado en Cabecera del Menú de Usuario

## Módulo

Marco Global - Menú Desplegable de Usuario (`menu-usuario.tsx`)

### Regla

En la cabecera emergente del menú de usuario (`MenuUsuario`):

1. **Disposición Vertical Centrada**: Los componentes se apilan de manera vertical (`flex flex-col items-center text-center`) para eliminar colisiones de espacio horizontal:
   - **Avatar superior**: El avatar de usuario (`iniciales(session.name)`) se sitúa en la parte superior centrado, con tamaño proporcionado `size-12` (48 px) y bordes redondeados consistentes.
   - **Identidad intermedia**: Inmediatamente abajo del avatar se centran el nombre (`session.name`) y correo del usuario (`session.email`), aprovechando el ancho disponible para evitar truncamientos prematuros.
   - **Insignia de rol inferior**: En la fila inferior se ubica la pastilla de rol (`etiquetaRol(session.role)`) centrada horizontalmente (`flex justify-center w-full`) con `whitespace-nowrap`, asegurando que roles con denominaciones largas («Administrador global», «Administrador de área») se mantengan en 1 sola fila continua sin dividirse en dos líneas.
2. **Ancho Mínimo de Contenedor**: El menú emergente garantiza un ancho mínimo de al menos `min-w-64` (256 px) tanto en posición superior como inferior, evitando cualquier compresión de los elementos de cabecera.

### Ejemplo

Al desplegar el menú de cuenta desde la barra lateral o la barra superior, la tarjeta muestra en la parte superior el avatar cuadrado púrpura con la letra «A». Justo debajo aparece centrado «admin» y el correo «admin». En la parte inferior de la cabecera se despliega la insignia azul con el texto completo «Administrador global» en una única fila horizontal y perfectamente centrada.

### Impacto

Afecta a [frontend/src/components/marco/menu-usuario.tsx](../frontend/src/components/marco/menu-usuario.tsx) y a las pruebas asociadas en [frontend/tests/components/marco-admin.test.tsx](../frontend/tests/components/marco-admin.test.tsx).

## Persistencia Bidireccional de Sección Activa al Alternar Disposición y Estandarización de Anchura en Menú de Usuario

## Módulo

Portal de Usuario - Shell y Barra Lateral (`platforms-shell.tsx`, `platforms-sidebar-view.tsx`, `menu-usuario.tsx`)

### Regla

1. **Persistencia Bidireccional de Sección Activa en el Portal**: Al alternar entre la disposición de Barra Superior (Topbar) y Barra Lateral (Sidebar) mediante `UserViewSettings`:
   - El estado de la sección activa (`seccionActiva: 'personalizacion' | 'responsiva' | 'catalogo' / 'area'`) se sincroniza bidireccionalmente entre `PlatformsShell` y `PlatformsSidebarView`.
   - Si el usuario se encuentra configurando sus preferencias en «Mi Espacio / Ajustes de Vista» (`seccionActiva === 'personalizacion'`) y conmuta de Topbar a Sidebar (o viceversa), el sistema no interrumpe su flujo ni lo redirige a «Todas las áreas»: mantiene la vista en «Ajustes de Vista» adaptando fluidamente el layout.
   - De forma análoga, si se encuentra en «Carta Responsiva», la transición entre disposiciones preserva la permanencia en dicha sección.
2. **Estandarización de Dimensiones del Menú de Usuario**: La tarjeta emergente desplegable de usuario (`MenuUsuario`) estandariza su ancho de forma homogénea a `w-72` (288 px) en todas las disposiciones del sistema:
   - Modo barra superior (`posicionMenu === 'abajo'`).
   - Modo barra lateral colapsada (`colapsada: bottom-0 left-full ml-2`).
   - Modo barra lateral expandida (`posicionMenu === 'arriba': bottom-full left-0 mb-2`).
   Esto asegura que el componente mantenga idéntico volumen, espaciado y consistencia estética tanto en vistas administrativas como en el portal de usuarios.

### Ejemplo

Un usuario se encuentra en `/platforms` en modo Barra Superior y hace clic en el engrane para ingresar a «Ajustes de Vista». Allí selecciona la tarjeta «Vista Barra Lateral (Sidebar)». La interfaz cambia instantáneamente a la estructura con barra lateral de 264 px y conserva activa la sección de «Ajustes de Vista» con la miga de pan «Mi Espacio / Ajustes de Vista». Al abrir su menú de perfil en el pie del sidebar o en la cabecera, la ventana emergente exhibe un ancho uniforme de 288 px (`w-72`) con el avatar centrado en la parte superior y el rol en una sola fila.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/marco/menu-usuario.tsx](../frontend/src/components/marco/menu-usuario.tsx) y a la suite en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Elevación de Diseño Premium y Concisión en Estados Vacíos (Empty States)

## Módulo

Componentes UI - Notificaciones y Estados Vacíos (`premium-message.tsx`, `note.tsx`, `platforms-launchpad-view.tsx`, `platforms-sidebar-view.tsx`, `user-widget-config.tsx`, `menu-notificaciones.tsx`)

### Regla

Los componentes de estado vacío (`PremiumEmptyState` y `EmptyNote`) elevan su lenguaje visual a nivel SaaS de alta gama bajo las siguientes directrices:

1. **Atmósfera Cromática Multicapa**:
   - Tarjeta contenedora con radio amplio (`rounded-3xl`), borde sutil (`border-primary/20`), fondo con degradado vertical (`bg-gradient-to-b from-primary/[0.04] via-panel-fill/95 to-panel-fill`), sombra proyectada suave (`shadow-lg`) y efecto de cristal esmerilado (`backdrop-blur-md`).
   - Doble halo de iluminación ambiental: resplandor Cobalt superior (`bg-gradient-to-b from-primary/20 via-brand/10 to-transparent blur-3xl opacity-80`) y halo Violet/Accent inferior derecho (`bg-accent/10 blur-3xl opacity-50`).
2. **Caja de Icono Estilo Joya con Aro Concéntrico**:
   - Estructura concéntrica de dos niveles: un aro exterior `size-20` con esquinas redondeadas (`rounded-3xl`), borde sutil y degradado suave, que aloja en su interior la gema elevada `size-full` (`rounded-2xl`) con gradiente vibrante (`from-primary/25 via-brand/20 to-accent/25`), borde iluminado (`border-primary/30`), sombra de elevación (`shadow-md`) y microinteracción táctil (`hover:scale-105`).
   - Punto de luz / aura decorativa superior en la esquina del contenedor.
3. **Jerarquía Tipográfica y Concisión de Textos**:
   - Se priorizan textos cortos y directos: título contundente de 1 a 3 palabras (`text-base sm:text-lg font-black tracking-tight text-body-text`) y subtítulo explicativo conciso de 1 sola frase corta (`text-xs sm:text-sm text-texto-secundario leading-relaxed`), evitando párrafos largos redundantes.
   - En vistas con filtros activos (como catálogo de plataformas o áreas), se ofrece de manera consistente la acción contextual primaria o secundaria para limpiar o restablecer filtros inmediatamente.

### Ejemplo

Al aplicar un filtro que no arroja resultados en el catálogo de plataformas, se despliega una tarjeta centrada con bordes redondeados y doble halo luminoso. En el centro resalta la joya de icono concéntrica con el símbolo de plataforma. Debajo se lee el encabezado claro «Sin resultados» y la leyenda breve «Ninguna plataforma coincide con los filtros aplicados.», acompañado del botón «Restablecer filtros».

### Impacto

Afecta a [frontend/src/components/premium-message.tsx](../frontend/src/components/premium-message.tsx), [frontend/src/components/note.tsx](../frontend/src/components/note.tsx), [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx), [frontend/src/components/platforms/menu-notificaciones.tsx](../frontend/src/components/platforms/menu-notificaciones.tsx) y pruebas en [frontend/tests/components/premium-message.test.tsx](../frontend/tests/components/premium-message.test.tsx).

## Acceso y Configuración de Mi Widget desde la Barra Superior (Topbar)

## Módulo

Portal de Usuario - Barra Superior y Configuración de Accesos Rápidos (`platforms-topbar.tsx`, `platforms-shell.tsx`, `user-widget-config.tsx`)

### Regla

1. **Acceso al Widget en Modo Topbar**: En la barra superior del portal (`PlatformsTopbar`), se incorpora de forma permanente en el clúster de navegación (`<nav aria-label="Navegación del portal">`) el botón interactivo de **Mi Widget** (`Icono nombre="panel"` con dimensiones estándar `CLASE_BOTON_ICONO` y tooltip descriptivo `Mi Widget: Configurar accesos rápidos`).
2. **Navegación Directa e Integrada**: Al pulsar el botón de Mi Widget en modo Topbar (o al navegar a la ruta con el parámetro `?seccion=widget`), el portal conmuta reactivamente a la vista de configuración del widget flotante (`UserWidgetConfig`), permitiendo al usuario:
   - Habilitar o apagar el widget flotante de acceso rápido mediante su interruptor maestro.
   - Filtrar y buscar plataformas del catálogo institucional para incluirlas o removerlas de su widget personal.
   - Probar y manipular el lanzador flotante en tiempo real sin requerir cambiar su preferencia de interfaz a la vista lateral (Sidebar).
3. **Botón de Retorno al Catálogo**: La barra de herramientas de `UserWidgetConfig` incorpora el botón de navegación secundaria «Volver al catálogo» (`onVolver`), permitiendo un retorno inmediato al catálogo de tarjetas con un solo clic.

### Ejemplo

Un usuario que utiliza el portal en modo Barra Superior (Topbar) hace clic en el icono de cuadrícula/panel situado entre «Mis solicitudes» y «Carta Responsiva». La pantalla transiciona directamente a la sección de configuración de «Mi Widget», donde puede activar o desactivar herramientas para su widget flotante persistente. Al presionar el botón «Volver al catálogo», regresa de inmediato a la cuadrícula de plataformas conservando su disposición preferida.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Diferenciación Visual e Iconografía entre Portal de Usuario y Gestión de Plataformas en el Admin Board

## Módulo

Navegación del Marco Administrativo (`nav-items.ts`, `BarraLateral`, `NavPrincipal`)

### Regla

1. **Diferenciación Semántica e Iconográfica**: Para evitar colisiones visuales y confusión cognitiva en la navegación del Admin Board, los elementos de navegación para el Portal de usuarios (`/platforms`) y la consola de gestión de plataformas (`/admin/platforms`) deben utilizar iconos claramente diferenciados:
   - `Portal` (`/platforms`, sección `General`): Utiliza el icono `catalogo` (caja isométrica tridimensional con tapa abierta), representando el catálogo de aplicaciones, lanzador y portal del colaborador.
   - `Plataformas` (`/admin/platforms`, sección `Gestión`): Conserva el icono `plataformas` (doble servidor en rack con leds indicadores), representando la infraestructura y administración de plataformas IT.
2. **Consistencia Visual**: Ambos iconos mantienen el mismo grosor de trazo (`strokeWidth={2}`), vista de coordenadas $24 \times 24$ y estilos de color y estado (activo/inactivo/hover) definidos en el sistema de diseño.

### Ejemplo

Un administrador navega en la barra lateral del Admin Board. En la sección «General» visualiza el acceso «Portal» identificado con el icono de catálogo/caja 3D. En la sección «Gestión», observa el acceso «Plataformas» representado con el icono de servidores en rack. De esta forma, reconoce de un vistazo la diferencia entre consultar el portal de autoservicio para usuarios y gestionar las plataformas del sistema.

### Impacto

Afecta a [frontend/src/components/marco/nav-items.ts](../frontend/src/components/marco/nav-items.ts) y pruebas en [frontend/tests/lib/marco-nav.test.ts](../frontend/tests/lib/marco-nav.test.ts) y [frontend/tests/components/marco-admin.test.tsx](../frontend/tests/components/marco-admin.test.tsx).

## Línea de Separación entre Botones de Pestañas y Contenido en Ajustes y Componentes Tablist Pills

## Módulo

Interfaz de Usuario, Ajustes del Sistema y Navegación por Pestañas (`Tabs`, `SettingsPanel`, `tokens.css`)

### Regla

1. **Separación Visual Estructural (border-b)**: En el componente unificado de pestañas con variante de pastillas (`variant="pills"`), el contenedor `<div role="tablist">` debe incorporar una línea horizontal de separación inferior continua (`border-b border-borde`) junto con espaciado vertical simétrico (`pb-4`, respetando el sistema de 8pt / `--space-3`).
2. **Delimitación Nítida de Capas**: Esta línea divide formalmente el clúster de botones de navegación (`[Portal]`, `[Correo]`, `[Plantillas]`, `[Directorio]`, `[Respaldo]`, `[Importación masiva]`, `[Mis preferencias]`) respecto a las tarjetas y paneles de configuración (`TabPanel`, `Card`), eliminando la ambigüedad espacial y replicando la consistencia del diseño de filtros utilizado en el portal topbar (`platforms-launchpad-view`).
3. **Resiliencia de Flexbox**: El contenedor añade `shrink-0` para prevenir contracción vertical no deseada ante contenidos extensos en paneles hijos.

### Ejemplo

Un superadministrador ingresa a `Admin Board > Ajustes`. Observa la hilera superior con las pestañas simétricas de configuración (`Portal`, `Correo`, etc.). Justo debajo de los botones, se despliega una línea divisoria horizontal sutil y nítida (`border-borde`) que separa limpiamente la barra de navegación del panel de identidad visual del portal, proporcionando un encuadre pulido y profesional.

### Impacto

Afecta a [frontend/src/components/tabs.tsx](../frontend/src/components/tabs.tsx), [frontend/src/components/settings-panel.tsx](../frontend/src/components/settings-panel.tsx) y pruebas en [frontend/tests/components/pestanas-conmutadores.test.tsx](../frontend/tests/components/pestanas-conmutadores.test.tsx).

## Modal Preventivo de Transición al Portal de Usuario desde el Admin Board

## Módulo

Navegación del Marco Administrativo (`NavPrincipal`, `ModalTransicionPortal`, `PreferencesTab`)

### Regla

1. **Transición Asistida y Modal Preventivo**: Al pulsar el enlace «Portal» (`href="/platforms"`) desde el menú de navegación del panel administrativo (`NavPrincipal`), la aplicación intercepta la navegación directa para desplegar un diálogo modal informativo (`ModalTransicionPortal`) que previene cambios visuales y contextuales bruscos para el administrador.
2. **Contenido Informativo del Modal**:
   - Título claro y semántico: «Ir al Portal de Usuario» con icono de catálogo (`catalogo`).
   - Insignia destacada: «🧭 Transición de entorno».
   - Explicación de que el usuario accederá a la perspectiva del colaborador para visualizar y solicitar plataformas.
   - Recordatorio visual de que puede retornar al panel de administración en cualquier momento mediante el botón de retorno en la barra superior.
3. **Casilla de Omisión para Visitas Futuras**:
   - En el pie del modal se incluye la casilla accesible (`Checkbox id="omitir-modal-portal"`) con la leyenda «No volver a mostrar este aviso».
   - Si el administrador marca la casilla y pulsa «Continuar al portal», la preferencia se almacena en el almacenamiento local (`localStorage.setItem('nexus.admin.omit_portal_redirect_modal', 'true')`), de modo que en visitas posteriores la navegación se realiza de manera inmediata sin mostrar el modal.
4. **Botón de Cancelación**:
   - El botón «Cancelar» (o cerrar el modal con Escape o ✕) anula la redirección y mantiene al administrador en la pantalla actual del panel de administración sin alterar las preferencias de omisión.
5. **Restauración desde Ajustes**:
   - En `Ajustes > Mis preferencias` (`PreferencesTab`), los administradores disponen del interruptor «Mostrar confirmación antes de ingresar al portal de usuario» para reactivar el diálogo informativo si en algún momento decidieron omitirlo.

### Ejemplo

Un administrador de TI se encuentra en el Dashboard y pulsa «Portal» en el menú lateral. En lugar de una conmutación abrupta de pantalla, aparece el diálogo «Ir al Portal de Usuario» explicando el cambio de entorno. El administrador marca la casilla «No volver a mostrar este aviso» y pulsa «Continuar al portal». La aplicación lo lleva a `/platforms`. En sus siguientes clics a «Portal», ingresará instantáneamente. Si más adelante desea volver a ver la confirmación, acude a Ajustes y reactiva la opción.

### Impacto

Afecta a [frontend/src/components/marco/modal-transicion-portal.tsx](../frontend/src/components/marco/modal-transicion-portal.tsx), [frontend/src/components/marco/nav-principal.tsx](../frontend/src/components/marco/nav-principal.tsx), [frontend/src/components/settings/preferences-tab.tsx](../frontend/src/components/settings/preferences-tab.tsx) y pruebas en [frontend/tests/components/modal-transicion-portal.test.tsx](../frontend/tests/components/modal-transicion-portal.test.tsx) y [frontend/tests/components/nav-principal-transicion.test.tsx](../frontend/tests/components/nav-principal-transicion.test.tsx).

## Modal Preventivo de Retorno al Panel de Administración desde el Portal de Usuario

## Módulo

Portal de Usuario y Navegación Administrativa (`PlatformsTopbar`, `PlatformsSidebarView`, `ModalTransicionAdmin`, `PreferencesTab`)

### Regla

1. **Transición Asistida y Modal Preventivo de Retorno**: Al pulsar el botón de retorno «Regresar al panel de administración» en la barra superior del portal (`PlatformsTopbar` y `PlatformsSidebarView`), la aplicación intercepta la redirección directa para desplegar el diálogo modal informativo (`ModalTransicionAdmin`), evitando saltos contextuales y visuales bruscos desde el catálogo de plataformas hacia la consola técnica del Admin Board.
2. **Contenido Informativo del Modal**:
   - Título claro y semántico: «Regresar al Panel de Administración» con el icono del panel (`panel`).
   - Insignia destacada: «⚙️ Retorno a Administración».
   - Explicación de que el administrador volverá a la consola técnica de administración (`/`) para gestionar plataformas, áreas, usuarios y auditorías.
   - Recordatorio visual de que puede volver al portal de colaboradores en cualquier instante seleccionando «Portal» en la barra lateral del Admin Board.
3. **Casilla de Omisión para Visitas Futuras**:
   - En el pie del modal se incluye la casilla accesible (`Checkbox id="omitir-modal-admin"`) con la leyenda «No volver a mostrar este aviso».
   - Si el administrador marca la casilla y pulsa «Continuar al panel admin», la preferencia se almacena en el almacenamiento local (`localStorage.setItem('nexus.platforms.omit_admin_redirect_modal', 'true')`), de modo que en visitas posteriores el retorno sea instantáneo sin desplegar el modal.
4. **Botón de Cancelación**:
   - El botón «Cancelar» (o cerrar el modal con Escape o ✕) anula la redirección y mantiene al usuario en el portal de plataformas sin alterar las preferencias de omisión.
5. **Configuración y Reactivación desde Ajustes**:
   - En `Ajustes > Mis preferencias` (`PreferencesTab`), los administradores disponen del interruptor «Mostrar confirmación antes de regresar al panel de administración» para restablecer el aviso si previamente fue omitido.

### Ejemplo

Un administrador navega por el Portal de Usuario revisando las plataformas de finanzas y hace clic en el icono de panel en la barra superior. En lugar de cambiar abruptamente a la consola administrativa, se abre el diálogo informativo explicando el retorno a la administración técnica. El administrador marca «No volver a mostrar este aviso» y pulsa «Continuar al panel admin». En ocasiones futuras, el clic lo redirige inmediatamente.

### Impacto

Afecta a [frontend/src/components/platforms/modal-transicion-admin.tsx](../frontend/src/components/platforms/modal-transicion-admin.tsx), [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/settings/preferences-tab.tsx](../frontend/src/components/settings/preferences-tab.tsx) y pruebas en [frontend/tests/components/modal-transicion-admin.test.tsx](../frontend/tests/components/modal-transicion-admin.test.tsx) y [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Optimización Visual y Textos Concisos en Modales de Transición entre Entornos

## Módulo

Navegación e Interfaz de Usuario (`ModalTransicionPortal`, `ModalTransicionAdmin`)

### Regla

1. **Reubicación de Casilla de Omisión en el Cuerpo del Modal**:
   - La casilla de verificación «No volver a mostrar este aviso» se ubica al pie del contenido del cuerpo del diálogo modal (`space-y-4 py-2`), separada sutilmente por un borde superior (`border-t border-panel-border/60 pt-2`), aprovechando el ancho horizontal completo del contenedor modal.
   - Con esto se evita el estrangulamiento visual y salto de línea innecesario en múltiples renglones que ocurría al forzarla a compartir el pie del modal con los botones de acción.
2. **Textos Breves y Concisos en Botones de Acción**:
   - En el pie del modal (`footer`), los botones de confirmación adoptan etiquetas concisas de alta legibilidad:
     - En `ModalTransicionPortal`: «Ir al portal» (en lugar del texto extenso «Continuar al portal»).
     - En `ModalTransicionAdmin`: «Ir a admin» (en lugar del texto extenso «Continuar al panel admin»).
   - Los botones se alinean al extremo derecho (`flex items-center justify-end gap-3 w-full`), manteniendo prioridad visual en la acción principal.

### Ejemplo

Un administrador pulsa «Portal» en el menú lateral. El modal emergente muestra la casilla «No volver a mostrar este aviso» en una sola línea clara dentro del cuerpo del mensaje. En el pie del diálogo únicamente aparecen los botones «Cancelar» e «Ir al portal», luciendo limpios, balanceados y sin deformación de textos.

### Impacto

Afecta a [frontend/src/components/marco/modal-transicion-portal.tsx](../frontend/src/components/marco/modal-transicion-portal.tsx), [frontend/src/components/platforms/modal-transicion-admin.tsx](../frontend/src/components/platforms/modal-transicion-admin.tsx) y pruebas en [frontend/tests/components/modal-transicion-portal.test.tsx](../frontend/tests/components/modal-transicion-portal.test.tsx), [frontend/tests/components/modal-transicion-admin.test.tsx](../frontend/tests/components/modal-transicion-admin.test.tsx) y [frontend/tests/components/nav-principal-transicion.test.tsx](../frontend/tests/components/nav-principal-transicion.test.tsx).

## Supresión de Línea Divisoria sobre Casilla de Omisión en Modales de Transición

## Módulo

Navegación e Interfaz de Usuario (`ModalTransicionPortal`, `ModalTransicionAdmin`)

### Regla

1. **Flujo Visual Limpio y sin Ruido Estructural**: En el cuerpo de los modales de transición entre entornos (`ModalTransicionPortal` y `ModalTransicionAdmin`), la casilla de verificación «No volver a mostrar este aviso» se integra de forma continua en el layout (`<div className="pt-1">`) sin ninguna línea divisoria horizontal superior (`border-t`).
2. **Minimización de Separadores**: Al existir ya un contenedor visual claro para la nota informativa («Podrás regresar...») y una línea divisoria natural entre el cuerpo y el pie del modal, se evita la sobrecarga de divisores visuales intermedios, logrando una presentación minimalista y premium.

### Ejemplo

Al abrir el modal «Ir al Portal de Usuario» o «Regresar al Panel de Administración», la casilla «No volver a mostrar este aviso» aparece limpia directamente debajo del recuadro de consejo, sin una línea divisoria adicional que fragmente el contenido.

### Impacto

Afecta a [frontend/src/components/marco/modal-transicion-portal.tsx](../frontend/src/components/marco/modal-transicion-portal.tsx) y [frontend/src/components/platforms/modal-transicion-admin.tsx](../frontend/src/components/platforms/modal-transicion-admin.tsx).

## Corrección de Validación y Manejo Defensivo de Filtros en Estado Vacío de PlatformsLaunchpadView

## Módulo

Portal de Usuario - Catálogo Launchpad (`PlatformsLaunchpadView`, `EmptyNote`, `PlatformsPageShell`)

### Regla

1. **Consistencia de Variables de Filtro en Componentes Desacoplados**: En `PlatformsLaunchpadView`, la condición que determina si el estado vacío (`EmptyNote`) debe mostrar el mensaje de filtros y la acción «Restablecer filtros» debe evaluar exclusivamente los estados pertenecientes a este componente: `(searchTerm || '').trim()`, `areaId !== null` o `soloFavoritas`, sin referenciar variables inexistentes de otras vistas como `filtroEstado`.
2. **Defensiva contra `undefined` en Búsqueda**: Las operaciones de recorte (`.trim()`) o conversión a minúsculas (`.toLowerCase()`) sobre el término de búsqueda deben ejecutarse de forma segura `(searchTerm || '').trim()` para evitar excepciones de tipo en tiempo de ejecución (`TypeError: Cannot read properties of undefined`).
3. **Propagación de Restablecimiento**: Al pulsar «Restablecer filtros», `PlatformsLaunchpadView` invoca `onSearchChange?.('')`, restablece el área a `null` (`setAreaId(null)`) y desactiva el filtro de favoritas (`setSoloFavoritas(false)`).

### Ejemplo

Un usuario en la vista de barra superior (Topbar / Launchpad) escribe un término de búsqueda inexistente (ej. «xyz») o selecciona un área sin plataformas asignadas. El componente renderiza de forma segura el mensaje «Ninguna plataforma coincide con los filtros aplicados.» con el botón «Restablecer filtros». Al hacer clic en el botón, el buscador se vacía y se muestran nuevamente todas las plataformas sin provocar errores de renderizado.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx) y [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx).

## Estandarización de Iconografía Vectorial y Ajuste Espacial en Modales de Transición

## Módulo

Navegación e Interfaz de Usuario (`ModalTransicionPortal`, `ModalTransicionAdmin`)

### Regla

1. **Iconografía Vectorial Consistente sin Emojis**:
   - En cumplimiento estricto del sistema de diseño unificado, los modales de transición entre entornos descartan el uso de emojis del sistema operativo (`💡`, `⚙️`, `🧭`).
   - Se reemplazan por los iconos vectoriales SVG oficiales del componente `<Icono>`:
     - En el badge superior de contexto: icono `catalogo` (`tamano="xs"`) para la transición al Portal y `panel` (`tamano="xs"`) para el retorno a Administración.
     - En el recuadro informativo (callout): icono `info` (`tamano="sm"`) con clase `text-primary-text mt-0.5`.
2. **Proximidad Visual de la Casilla de Omisión**:
   - La casilla «No volver a mostrar este aviso» se asocia directamente al contenedor de la nota informativa con un margen superior estrecho (`mt-2.5`), evitando que quede flotando o desconectada verticalmente.
3. **Simetría y Equilibrio Espacial**:
   - Se elimina el espaciado vertical forzado intermedio (`py-2`) y la altura mínima arbitraria en la casilla que inflaba el margen inferior, logrando que el espacio en blanco inferior hacia la barra de botones coincida en simetría perfecta con el margen superior del modal (`py-6` / 24px).

### Ejemplo

Al pulsar «Portal» desde el menú de administración o «Regresar al Panel Admin» desde el portal de usuario, el modal emergente muestra la insignia y el consejo informativo con los iconos vectoriales institucionales (`catalogo`/`panel` e `info`). La casilla de no volver a mostrar se ubica pegada de forma natural al contenedor informativo, y el espacio en blanco inferior es armónico y equivalente al espaciado superior.

### Impacto

Afecta a [frontend/src/components/marco/modal-transicion-portal.tsx](../frontend/src/components/marco/modal-transicion-portal.tsx), [frontend/src/components/platforms/modal-transicion-admin.tsx](../frontend/src/components/platforms/modal-transicion-admin.tsx) y pruebas en [frontend/tests/components/modal-transicion-portal.test.tsx](../frontend/tests/components/modal-transicion-portal.test.tsx) y [frontend/tests/components/modal-transicion-admin.test.tsx](../frontend/tests/components/modal-transicion-admin.test.tsx).

## Diferenciación Iconográfica de «Mi Widget» y «Regresar al Panel Admin» en Barra Superior

## Módulo

Portal de Usuario - Barra Superior y Accesos Rápidos (`PlatformsTopbar`, `PlatformsSidebarView`, `UserWidgetConfig`, `Icono`)

### Regla

1. **Unicidad e Identidad Iconográfica por Acción**:
   - En la barra de navegación del portal (`PlatformsTopbar`), cada botón de acción debe contar con un icono vector SVG único y diferenciado para evitar colisiones visuales o ambigüedad cognitiva.
   - El icono `panel` (cuadrícula de 4 rectángulos) se reserva de manera exclusiva para el retorno al **Panel de Administración** (`BotonRegresarAdmin` hacia `/`), coincidiendo con la identidad del Dashboard en la consola de gestión.
2. **Icono Dedicado para «Mi Widget»**:
   - La sección de configuración y lanzador flotante de «Mi Widget» adopta el icono oficial dedicado `widget` (marco contenedor modular con partición de cabecera y columnas de tarjeta).
   - Este icono se aplica de manera consistente en:
     - El botón de acceso directo en la barra superior (`PlatformsTopbar`).
     - El elemento de menú en la barra lateral (`PlatformsSidebarView`).
     - El botón disparador flotante interactivo y encabezados en la vista de configuración (`UserWidgetConfig`).

### Ejemplo

Un administrador navega en el Portal de Usuario. En la barra superior observa en orden: «Regresar al Panel Admin» con el icono de panel (`panel`), «Plataformas» con icono de servidores (`plataformas`), «Mis solicitudes» con icono de documento y cotejo (`solicitudes`), «Mi Widget» con el icono modular de plantilla de widgets (`widget`), y «Carta Responsiva» con icono de documento y punto de estado (`documento`). Ningún icono se repite en la secuencia de navegación.

### Impacto

Afecta a [frontend/src/components/icono-trazos.ts](../frontend/src/components/icono-trazos.ts), [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx) y pruebas en [frontend/tests/components/icono.test.tsx](../frontend/tests/components/icono.test.tsx) y [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Supresión de Botón de Retorno Redundante en Encabezado de Carta Responsiva

## Módulo

Portal de Usuario - Documentos Corporativos (`UserResponsivaSection`, `PlatformsPageShell`)

### Regla

1. **Eliminación de Controles Redundantes de Navegación**:
   - En la vista de **Carta Responsiva de Activos y Herramientas** (`UserResponsivaSection`), el encabezado principal descarta el botón de retorno contextual (`flecha-izq` / «Volver al catálogo»).
   - La navegación y conmutación entre el catálogo de plataformas y la carta responsiva se realiza de forma directa mediante los controles globales de navegación:
     - En modo Topbar: pulsando directamente sobre el botón de Plataformas o conmutando el botón de Carta Responsiva en la barra superior.
     - En modo Sidebar: seleccionando cualquier área, sección de favoritas o catálogo en el menú lateral.
2. **Alineación Visual Limpia**:
   - Al remover el botón de flecha, el encabezado inicia directamente con el icono representativo del documento (`documento`) y la jerarquía de títulos («Carta Responsiva de Activos y Herramientas»), logrando un diseño más despejado y limpio.

### Ejemplo

Al acceder a la sección de Carta Responsiva en el Portal de Usuario, el panel superior muestra a la izquierda el icono de documento con el título normativo y a la derecha el estado de firma digital («Firmada digitalmente» o «Pendiente de firma»), sin botones redundantes de flecha hacia atrás.

### Impacto

Afecta a [frontend/src/components/platforms/user-responsiva-section.tsx](../frontend/src/components/platforms/user-responsiva-section.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Modo de Demostración y Simulación de Firma de Carta Responsiva en Barra Superior

## Módulo

Portal de Usuario - Documentos y Flujo de Primer Ingreso (`PlatformsTopbar`, `PlatformsSidebarView`, `ModalResponsiva`, `PlatformsPageShell`)

### Regla

1. **Acceso Temporal a Simulación de Primer Ingreso**:
   - En la barra superior (`PlatformsTopbar` y cabecera de `PlatformsSidebarView`), se incluye un control temporal («Probar Responsiva») para permitir a administradores y diseñadores visualizar de forma fidedigna e interactiva la experiencia del usuario que aún no ha firmado su carta responsiva de seguridad.
2. **Comportamiento del Diálogo de Demostración**:
   - Al pulsar «Probar Responsiva», se despliega el modal interactivo `ModalResponsiva` con los datos de sesión simulados (`responsiva_firmada: false`), mostrando:
     - El encabezado de cumplimiento normativo y bienvenida personalizada.
     - El listado de áreas y activos tecnológicos pre-asignados a la cuenta.
     - El visor desplazable con las cláusulas de confidencialidad y uso de TI.
     - La casilla de aceptación obligatoria.
     - El botón de acción «Firmar y acceder al portal» bloqueado hasta que el usuario marque la casilla de aceptación.
   - En modo demostración, el modal permite cerrar la previsualización en cualquier momento mediante el botón «Cerrar vista previa» o el control de cierre superior sin forzar el cierre de sesión real. Al completar la firma, emite el toast de confirmación y cierra el diálogo.

### Ejemplo

Un administrador pulsa el botón «Probar Responsiva» en la barra superior del portal. De inmediato se abre el diálogo modal bloqueante mostrando la carta responsiva tal como la experimenta un colaborador en su primer inicio de sesión. El administrador revisa el texto, marca la casilla de aceptación y el botón de firma se ilumina en azul primario, permitiéndole simular la firma o cerrar la vista previa.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/components/responsiva/modal-responsiva.tsx](../frontend/src/components/responsiva/modal-responsiva.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Rediseño Horizontal del Encabezado en el Menú Desplegable de Usuario

## Módulo

Marco Global - Menú de Usuario (`MenuUsuario`)

### Regla

1. **Disposición Horizontal de Identidad y Rol**:
   - En el menú desplegable de cuenta (`MenuUsuario`), el encabezado de perfil organiza la información del usuario en un esquema horizontal claro y equilibrado:
     - **Lado Izquierdo**: El avatar/icono representativo con las iniciales del usuario (`iniciales(session.name)`) sobre un contenedor estilizado con bordes redondeados y degradado de acento corporativo.
     - **Lado Derecho**: Columna de texto orientada a la izquierda que contiene el nombre del usuario (`session.name`) en tipografía destacada seminegrita/negrita, el correo electrónico (`session.email`) en tipografía secundaria, y situado directamente debajo de ellos, la insignia o badge con el rol institucional (`etiquetaRol(session.role)`).
2. **Consistencia Visual y Espaciado 8pt**:
   - Se emplean clases semánticas de Tailwind basadas en design tokens (`bg-superficie-hundida/50`, `border-panel-border/80`, `text-body-text`, `text-texto-secundario`, `bg-primary/10`, `text-primary-text`), manteniendo espaciados homogéneos (`p-3`, `gap-3`, `mt-2`) sin estilos inline ni valores arbitrarios.

### Ejemplo

Al desplegar el menú de usuario en la esquina superior del portal o en el pie de la barra lateral, en la parte superior del menú aparece a la izquierda el recuadro con la inicial «A» y a su derecha «admin» junto con el correo «<admin@ejemplo.com>»; inmediatamente abajo del nombre y correo se encuentra la píldora azul con el rol «Administrador global», seguida por la opción de «Cerrar sesión».

### Impacto

Afecta a [frontend/src/components/marco/menu-usuario.tsx](../frontend/src/components/marco/menu-usuario.tsx) y pruebas en [frontend/tests/components/marco-admin.test.tsx](../frontend/tests/components/marco-admin.test.tsx).

## Contraste e Identidad Visual de Iconos de Apoyo en Barra Lateral del Portal

## Módulo

Portal de Usuario - Barra Lateral (`PlatformsSidebarView`)

### Regla

1. **Diferenciación entre Estado Inactivo y Estado Activo**:
   - Para evitar saturación visual y conflicto con el fondo de selección activa (`bg-primary`), los iconos de apoyo de las opciones de navegación en la barra lateral (`PlatformsSidebarView`):
     - **En estado inactivo**: Utilizan el token secundario de barra lateral (`text-barra-lateral-secundario`), con realce suave al pasar el cursor (`group-hover:text-barra-lateral-texto`), evitando el uso de tonos azules estáticos en reposo. En el caso de «Favoritas», mantiene su distintivo tono ámbar (`text-warning-text`).
     - **En estado activo**: Al seleccionarse una sección (p. ej. «Todas las áreas», «Mis Solicitudes», «Mi Widget», «Carta Responsiva» o un departamento específico), el botón adopta el fondo azul primario (`bg-primary`) y el icono de apoyo conmuta obligatoriamente a blanco puro (`text-texto-sobre-accion`), manteniendo una relación de contraste superior a 7:1 contra el fondo azul y garantizando que el icono nunca se pierda ni se vuelva invisible.
2. **Jerarquía Visual y Accesibilidad**:
   - Cada botón incluye la clase `group` para coordinar de manera fluida las transiciones de color del icono y el texto, garantizando máxima legibilidad tanto en modo claro como en modo oscuro.

### Ejemplo

Al seleccionar «Todas las áreas» en la barra lateral del portal, el botón se ilumina con el fondo azul primario corporativo (`bg-primary`). El icono de cuadrícula de áreas se muestra nítidamente en color blanco (`text-texto-sobre-accion`) junto al texto «Todas las áreas», eliminando el problema de icono azul sobre fondo azul y asegurando visibilidad inmediata del glifo de apoyo.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Eliminación del Botón Redundante de Retorno en Barra de Herramientas de Mi Widget

## Módulo

Portal de Usuario - Configuración de Mi Widget (`UserWidgetConfig`, `PlatformsShell`, `PlatformsSidebarView`)

### Regla

1. **Consistencia de Navegación Global**:
   - En la vista de configuración y personalización de «Mi Widget» (`UserWidgetConfig`), se omite el botón redundante «Volver al catálogo» (`[ ← Volver al catálogo ]`) dentro de la barra de herramientas superior.
   - El retorno hacia la vista principal del catálogo o la alternancia entre secciones se realiza de forma directa y unificada mediante los controles de navegación primarios:
     - En el modo Topbar: conmutando el botón de icono «Mi Widget» en la barra superior o seleccionando cualquier otro control de navegación.
     - En el modo Sidebar: seleccionando directamente «Todas las áreas» o cualquier otra sección en la barra lateral izquierda.
2. **Optimización del Espacio Horizontal**:
   - Al remover el botón redundante, el campo de búsqueda de plataformas para agregar al widget (`buscar-plataformas-widget`) obtiene prioridad y amplitud visual, manteniendo la alineación simétrica con el selector de filtro y el interruptor de activación del widget.

### Ejemplo

Un usuario ingresa a la configuración de accesos rápidos pulsando el icono de widget. En la barra de herramientas superior de la sección, se despliega directamente el campo «Buscar plataforma para agregar al widget…» junto al filtro y el interruptor «Widget Encendido», sin botones secundarios de retorno. Para volver a explorar plataformas, el usuario pulsa nuevamente el botón de widget en la barra superior o elige un área en la barra lateral.

### Impacto

Afecta a [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Contraste e Identidad Visual de Iconos de Apoyo en Barra Lateral del Portal

## Módulo

Portal de Usuario - Barra Lateral (`PlatformsSidebarView`)

### Regla

1. **Diferenciación entre Estado Inactivo y Estado Activo**:
   - Para evitar saturación visual y conflicto con el fondo de selección activa (`bg-primary`), los iconos de apoyo de las opciones de navegación en la barra lateral (`PlatformsSidebarView`):
     - **En estado inactivo**: Utilizan el token secundario de barra lateral (`text-barra-lateral-secundario`), con realce suave al pasar el cursor (`group-hover:text-barra-lateral-texto`), evitando el uso de tonos azules estáticos en reposo. En el caso de «Favoritas», mantiene su distintivo tono ámbar (`text-warning-text`).
     - **En estado activo**: Al seleccionarse una sección (p. ej. «Todas las áreas», «Mis Solicitudes», «Mi Widget», «Carta Responsiva» o un departamento específico), el botón adopta el fondo azul primario (`bg-primary`) y el icono de apoyo conmuta obligatoriamente a blanco puro (`text-texto-sobre-accion`), manteniendo una relación de contraste superior a 7:1 contra el fondo azul y garantizando que el icono nunca se pierda ni se vuelva invisible.
2. **Jerarquía Visual y Accesibilidad**:
   - Cada botón incluye la clase `group` para coordinar de manera fluida las transiciones de color del icono y el texto, garantizando máxima legibilidad tanto en modo claro como en modo oscuro.

### Ejemplo

Al seleccionar «Todas las áreas» en la barra lateral del portal, el botón se ilumina con el fondo azul primario corporativo (`bg-primary`). El icono de cuadrícula de áreas se muestra nítidamente en color blanco (`text-texto-sobre-accion`) junto al texto «Todas las áreas», eliminando el problema de icono azul sobre fondo azul y asegurando visibilidad inmediata del glifo de apoyo.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Eliminación del Botón Redundante de Retorno en Barra de Herramientas de Mi Widget

## Módulo

Portal de Usuario - Configuración de Mi Widget (`UserWidgetConfig`, `PlatformsShell`, `PlatformsSidebarView`)

### Regla

1. **Consistencia de Navegación Global**:
   - En la vista de configuración y personalización de «Mi Widget» (`UserWidgetConfig`), se omite el botón redundante «Volver al catálogo» (`[ ← Volver al catálogo ]`) dentro de la barra de herramientas superior.
   - El retorno hacia la vista principal del catálogo o la alternancia entre secciones se realiza de forma directa y unificada mediante los controles de navegación primarios:
     - En el modo Topbar: conmutando el botón de icono «Mi Widget» en la barra superior o seleccionando cualquier otro control de navegación.
     - En el modo Sidebar: seleccionando directamente «Todas las áreas» o cualquier otra sección en la barra lateral izquierda.
2. **Optimización del Espacio Horizontal**:
   - Al remover el botón redundante, el campo de búsqueda de plataformas para agregar al widget (`buscar-plataformas-widget`) obtiene prioridad y amplitud visual, manteniendo la alineación simétrica con el selector de filtro y el interruptor de activación del widget.

### Ejemplo

Un usuario ingresa a la configuración de accesos rápidos pulsando el icono de widget. En la barra de herramientas superior de la sección, se despliega directamente el campo «Buscar plataforma para agregar al widget…» junto al filtro y el interruptor «Widget Encendido», sin botones secundarios de retorno. Para volver a explorar plataformas, el usuario pulsa nuevamente el botón de widget en la barra superior o elige un área en la barra lateral.

### Impacto

Afecta a [frontend/src/components/platforms/user-widget-config.tsx](../frontend/src/components/platforms/user-widget-config.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Validación de Seguridad con Captcha Anti-Error en Firma de Carta Responsiva

## Módulo

Portal de Usuario - Firma de Carta Responsiva (`ModalResponsiva`)

### Regla

1. **Doble Factor de Consentimiento (Casilla + Captcha)**:
   - Para prevenir firmas involuntarias, accidentales o automáticas en el documento normativo de responsiva de TI (`ModalResponsiva`), el botón «Firmar y acceder al portal» requiere obligatoriamente dos condiciones concurrentes:
     1. Que la casilla de aceptación legal esté marcada.
     2. Que el usuario resuelva exitosamente el desafío de confirmación (código de seguridad/captcha) ingresando el código alfanumérico generado aleatoriamente.
2. **Generación y Regeneración de Código Alfanumérico**:
   - El captcha genera dinámicamente un código de 5 caracteres alfanuméricos en mayúsculas, excluyendo caracteres ambiguos (como O, 0, I, 1).
   - Se muestra dentro de una tarjeta de seguridad estilizada con textura de ruido visual y tipografía monoespaciada de alta legibilidad.
   - Cuenta con una acción explícita «Nuevo código» para permitir al usuario cambiar la combinación en caso de requerirlo.
3. **Eliminación de Texto Redundante**:
   - Se omite el texto estático «Marca la casilla para firmar» debajo del botón de firma. El estado deshabilitado del botón y las validaciones reactivas del formulario proporcionan la guía contextual directa.

### Ejemplo

Un colaborador abre la carta responsiva institucional. Marca la casilla de aceptación; el botón de firma continúa bloqueado. Directamente debajo de la casilla, observa el recuadro de seguridad que muestra el código «7K9WB». El usuario escribe «7K9WB» en el campo de texto; el sistema muestra la validación verde «Código verificado correctamente» y el botón «Firmar y acceder al portal» se ilumina en azul primario, permitiéndole enviar su firma con plena conciencia e intención.

### Impacto

Afecta a [frontend/src/components/responsiva/modal-responsiva.tsx](../frontend/src/components/responsiva/modal-responsiva.tsx) y pruebas en [frontend/tests/components/responsiva.test.tsx](../frontend/tests/components/responsiva.test.tsx) y [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Eliminación de Tarjeta Redundante de Saludo en Carta Responsiva

## Módulo

Portal de Usuario - Firma de Carta Responsiva (`ModalResponsiva`)

### Regla

1. **Enfoque Directo en Términos Normativos**:
   - Para maximizar la claridad y el área de lectura en el modal de responsiva legal (`ModalResponsiva`), se retira la tarjeta superior secundaria de saludo y metadatos («Primer Ingreso • Cumplimiento Normativo / Hola, [usuario] / versión / rol»).
   - El encabezado del diálogo (`Modal`) ya provee la identificación formal del documento («Carta Responsiva de Uso de Activos de Información y Plataformas Institucionales») y la identidad del usuario ya reside en la sesión activa, permitiendo enfocar la atención inmediatamente en los activos/herramientas asignadas y los términos y obligaciones legales.

### Ejemplo

Al desplegarse la responsiva institucional (tanto en primer ingreso como en la vista previa del administrador), la interfaz no muestra tarjetas intermedias de bienvenida con el nombre del usuario. El flujo pasa directamente a los activos asignados y al cuadro de lectura obligatoria con el captcha de validación.

### Impacto

Afecta a [frontend/src/components/responsiva/modal-responsiva.tsx](../frontend/src/components/responsiva/modal-responsiva.tsx) y pruebas en [frontend/tests/components/responsiva.test.tsx](../frontend/tests/components/responsiva.test.tsx).

## Optimización de Altura y Feedback en Línea para Captcha de Responsiva

## Módulo

Portal de Usuario - Validación de Captcha (`ModalResponsiva`)

### Regla

1. **Preservación de Altura Fija del Contenedor de Seguridad**:
   - Para prevenir cambios de dimensiones verticales (layout shifts o saltos de altura) al escribir y validar el código de confirmación, se elimina el párrafo inferior de retroalimentación y el texto estático secundario «Evita firmas por error».
   - En su lugar, el estado de verificación se proyecta directamente en la esquina superior derecha de la cabecera de la tarjeta («Confirmación de Seguridad»):
     - Si el código es correcto: se muestra «Código verificado correctamente» en color de éxito con icono de check.
     - Si hay caracteres ingresados pero no coinciden: se muestra «Código no coincide» en tono de advertencia.
     - Si está vacío: el espacio permanece limpio y la fila conserva su altura fija (`min-h-5`).
2. **Estabilidad del Layout**:
   - El contenedor mantiene dimensiones estrictamente constantes antes, durante y después de la verificación del código, evitando empujar hacia abajo los botones de acción («Firmar y acceder al portal»).

### Ejemplo

Un usuario se dispone a firmar la responsiva. Al tipear los caracteres del captcha, no se despliegan renglones adicionales debajo del formulario; en cuanto ingresa el último carácter correspondiente, el texto verde «Código verificado correctamente» aparece limpiamente alineado a la derecha en la barra superior de la tarjeta, manteniendo el pie del modal totalmente estático.

### Impacto

Afecta a [frontend/src/components/responsiva/modal-responsiva.tsx](../frontend/src/components/responsiva/modal-responsiva.tsx) y pruebas en [frontend/tests/components/responsiva.test.tsx](../frontend/tests/components/responsiva.test.tsx).

## Retiro de Control Temporal de Demostración de Responsiva

## Módulo

Portal de Usuario - Barra de Navegación y Vistas (`PlatformsTopbar`, `PlatformsSidebarView`, `PlatformsShell`)

### Regla

1. **Retiro de Acciones Temporales**:
   - Concluida la fase de revisión y validación de la experiencia de usuario y del mecanismo de captcha anti-error en la carta responsiva, se retira definitivamente el botón temporal «Probar Responsiva» de la barra superior (`PlatformsTopbar`) y de la cabecera de la barra lateral (`PlatformsSidebarView`).
2. **Operación Exclusiva por Estado de Sesión**:
   - El despliegue de `ModalResponsiva` opera únicamente a través del gatekeeper de autenticación/sesión (`session.responsiva_firmada === false`), asegurando que solo los usuarios que efectivamente tengan pendiente la firma de la responsiva sean interceptados con el diálogo modal legal.

### Ejemplo

Cualquier usuario o administrador que ingrese al portal con su responsiva ya firmada observa la barra de herramientas limpia y despejada, sin botones de simulación o demostración. Si un nuevo usuario ingresa por primera vez sin firma registrada, el portal lo intercepta automáticamente con la carta responsiva como requisito indispensable de acceso.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Visualización y Registro de Fecha de Firma en Carta Responsiva

## Módulo

Portal de Usuario - Documentos de Seguridad (`UserResponsivaSection`, `api.get_me`, `api.get_responsiva`)

### Regla

1. **Visibilidad Obligatoria de la Fecha de Firma**:
   - En la vista de consulta de la carta responsiva de activos y herramientas (`UserResponsivaSection`), la cuarta tarjeta de metadatos muestra de forma destacada la **Fecha de Firma** exacta en formato legible en español (`DD de [Mes] de YYYY a las HH:MM`).
   - El indicador secundario refleja el estado de cumplimiento normativo (`Aceptada digitalmente` / `Requiere confirmación`).
2. **Resiliencia en el Registro Histórico (Retrocompatibilidad)**:
   - Para usuarios existentes que contaban con la responsiva previamente marcada como firmada pero sin timestamp registrado en base de datos (`responsiva_firmada_at IS NULL`), el backend proporciona automáticamente como respaldo la fecha de creación de su cuenta (`created_at`), asegurando que siempre se exponga una fecha de registro válida y verificable.

### Ejemplo

Un colaborador o administrador accede al apartado «Carta Responsiva» desde la barra de navegación. En la cuadrícula de metadatos superiores, observa su nombre, rol, versión del documento (v1.0) y en la tarjeta de firma: «28 de octubre de 2026 a las 01:03 p.m.» junto con la etiqueta «Aceptada digitalmente», confirmando fehacientemente el momento en que se formalizó su compromiso de seguridad.

### Impacto

Afecta a [app/modules/api/routes.py](../app/modules/api/routes.py), [frontend/src/components/platforms/user-responsiva-section.tsx](../frontend/src/components/platforms/user-responsiva-section.tsx), base de datos de usuarios y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Diferenciación Arquitectónica y Visual entre Cards de Área y Cards de Plataforma

## Módulo

Portal de Usuario y Catálogo de TI (`TarjetaArea`, `PlatformMockupCard`)

### Regla

1. **Diferenciación de Contrato de Información**:
   - Aunque ambos componentes se representan formalmente como tarjetas en cuadrícula (`grid`), su contenido y rol en el flujo del usuario son mutuamente excluyentes:
     - **Card de Área (Entidad Organizativa)**: Agrupa y jerarquiza recursos. Muestra métricas colectivas (**personas asignadas**, **conteo de plataformas activas**), un **cluster de logotipos superpuestos** (`+N`) de las herramientas que contiene, y su acción de navegación conduce al catálogo filtrado del área (`Ver área →`).
     - **Card de Plataforma (Herramienta Operativa)**: Representa un software individual. Muestra el **área de pertenencia**, el **rol/nivel de acceso del usuario** (`Colaborador`, `Administrador`, `Lectura`), el **estado de autorización** (`Activo`, `En revisión / Pendiente`, `Disponible para solicitud`), control de favoritos (`★`) y una acción contextual directa (`Abrir ↗` o `Solicitar +`).
2. **Consistencia Visual con Design Tokens**:
   - Ambas familias de tarjetas respetan el radio base de esquinas (`rounded-2xl` o `rounded-xl`), la elevación estándar (`shadow-1` / `shadow-2` en hover) y la tipografía en escala de grises y contrastes semánticos (`text-body-text`, `text-label`, `border-panel-border`), evitando colisiones o estilos inline.

### Ejemplo

Al ingresar a «Todas las áreas», el usuario observa tarjetas de área con métricas de equipo (ej. *Tecnología & TI • 28 personas • 9 herramientas*). Al hacer clic en un área o seleccionar una categoría, la interfaz transiciona a tarjetas de plataforma con acciones operativas individuales (ej. *Slack • Rol Colaborador • Abrir plataforma ↗*).

### Impacto

Afecta a [frontend/src/components/areas/tarjeta-area.tsx](../frontend/src/components/areas/tarjeta-area.tsx) y [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx).

## Formato Simplificado de Fecha de Firma en Carta Responsiva

## Módulo

Portal de Usuario - Documentos de Seguridad (`UserResponsivaSection`)

### Regla

1. **Visualización Enfocada en Fecha (Día/Mes/Año)**:
   - En la tarjeta «Fecha de Firma» de la sección de responsiva (`UserResponsivaSection`), se presenta exclusivamente la fecha en formato extendido (`DD de [Mes] de YYYY`, ej. `28 de octubre de 2026`).
   - Se omite la hora en la interfaz de usuario para mantener la estética limpia en una sola línea dentro de la cuadrícula de metadatos, evitando saturación visual.
2. **Registro Preciso en Base de Datos (Auditoría Admin Pendiente)**:
   - La estampa de tiempo completa con hora, minutos y segundos se conserva íntegra en la base de datos (`responsiva_firmada_at`), disponible para futuras auditorías o paneles de administración avanzados.

### Ejemplo

Al consultar su carta responsiva, el usuario visualiza en la tarjeta de metadatos «Fecha de Firma: 28 de octubre de 2026» en una sola línea clara y legible, acompañada de la etiqueta «Aceptada digitalmente».

### Impacto

Afecta a [frontend/src/components/platforms/user-responsiva-section.tsx](../frontend/src/components/platforms/user-responsiva-section.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Catálogo Multiestilo de Cards Reutilizables de Plataforma y Área

## Módulo

Catálogo y Gestión de Experiencia de Usuario (`PlatformMockupCard`, `TarjetaArea`, `UI_GUIDE.md`)

### Regla

1. **Coexistencia Integral de Variantes**:
   - Tanto las tarjetas de plataforma como las de área preservan tanto sus primeros diseños estructurados orientados a métricas corporativas y control de accesos (`estandar`, `compacta`, `horizontal`) como las variantes visualmente ricas inspiradas en referencias de producto (`enmarcada`, `duotono`, `evento`, `split`, `onda`, `directorio`).
2. **Reutilización por Propiedad `variante`**:
   - Cada componente encapsula sus variantes mediante la propiedad `variante`, garantizando que puedan intercambiarse dinámicamente en cualquier pantalla (Launchpad, Administración, Directorio o Catálogo) sin bifurcar la lógica de negocio ni alterar los enlaces de acceso o permisos.

### Ejemplo

Un administrador o usuario puede optar por desplegar el catálogo de plataformas en formato compacto para maximizar densidad, o en formato `enmarcada` o `duotono` para una experiencia visual de alto impacto con portadas dedicadas, manteniendo siempre activos los controles de favoritos, validación de estado y apertura segura.

### Impacto

Afecta a [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx), [frontend/src/components/areas/tarjeta-area.tsx](../frontend/src/components/areas/tarjeta-area.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y maquetas de diseño en `mockups_cards.html`.

## Configuración Independiente de Tarjetas de Plataforma y Área en Preferencias de Vista

## Módulo

Portal de Usuario - Personalización de Vista (`UserViewSettings`, `PlatformsSidebarView`, `PlatformsShell`)

### Regla

1. **Separación Arquitectónica de Controles de Cards**:
   - En el panel «Configurar vista» (`UserViewSettings`), los controles de selección de diseño de tarjetas se dividen en dos secciones independientes:
     - **Diseño de Tarjetas de Plataforma**: Administra la variante visual para los servicios individuales (`estandar`, `compacta`, `horizontal`, `enmarcada`, `duotono`, `evento`).
     - **Diseño de Tarjetas de Área**: Administra la variante visual para los departamentos y agrupaciones organizativas (`estandar`, `split`, `onda`, `directorio`).
2. **Persistencia Local Desacoplada**:
   - Cada preferencia se almacena en llaves independientes de `localStorage` (`nexus.platforms.card_design` y `nexus.platforms.area_card_design`), garantizando que la elección del estilo de un área no sobreescriba ni condicione la visualización de las plataformas.

### Ejemplo

Un usuario puede ingresar a «Configurar vista» y elegir para las Áreas el diseño editorial `Split 50/50` (Harvest Vase) y, simultáneamente, seleccionar para las Plataformas el diseño `Enmarcada Pastel` o `Compacta`, observando de inmediato cada selección reflejada en sus respectivas pantallas sin interferencias.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx) y almacenamiento `localStorage`.

## Colección de 6 Diseños Diferenciados para Plataformas y 6 para Áreas Organizativas

## Módulo

Portal de Usuario - Componentes Visuales y Personalización de Vista (`PlatformMockupCard`, `TarjetaArea`, `UserViewSettings`)

### Regla

1. **6 Estilos Estructuralmente Distintos para Plataformas**:
   - `duotono`: Portada a sangre con degradado oscuro y fotografía inmersiva (estilo ciudades nocturnas).
   - `enmarcada`: Marco perimetral acolchado con foto interior centrada y botón redondeado (estilo Heading Here).
   - `evento`: Ficha ticket de concierto/evento con badges flotantes de versión (`VER 2.4`), favoritos (`❤️`), lista con iconos de región/acceso y botón doble (estilo Summer Concert).
   - `split`: Composición 50/50 horizontal (mitad izquierda visual con monograma, mitad derecha editorial con descripción y CTA).
   - `glass`: Glassmorphism neón tech con bordes cian translúcidos, glow sutil y tipografía monoespaciada.
   - `editorial`: Estilo suizo minimalista con gran número de catálogo al agua (`#01` / `#06`), fuente serif y enlace en flecha.
2. **6 Estilos Estructuralmente Distintos para Áreas Organizativas**:
   - `split`: Composición 50/50 horizontal con monograma e indicadores de personas y plataformas (estilo Harvest Vase).
   - `onda`: Cabecera asimétrica con curva SVG orgánica, icono central y botón de píldora degradada.
   - `directorio`: Portada corporativa con clúster de avatares superpuestos y acceso al equipo y catálogo.
   - `bento`: Mosaico cuadrante asimétrico con métricas de especialistas, herramientas y botón expandible.
   - `medallon`: Emblema heráldico/medallón circular en relieve superpuesto a la banda superior con sellos de estado.
   - `estandar`: Panel métrico corporativo (DIS-102) con cajas gemelas de cifras (Personas / Plataformas) y fila de chips de logos.
3. **Compatibilidad y Persistencia**:
   - Los 6 estilos de plataforma y los 6 de área se configuran por separado en `UserViewSettings` y persisten independientemente en `localStorage` (`nexus.platforms.card_design` y `nexus.platforms.area_card_design`), admitiendo además los 3 layouts clásicos para plena retrocompatibilidad.

### Ejemplo

Al acceder al diálogo «Configurar vista», el usuario puede seleccionar entre 6 variantes radicalmente diferentes tanto en el bloque de Plataformas como en el de Áreas. Al seleccionar por ejemplo `duotono` para plataformas y `bento` para áreas, el sistema almacena las opciones en `localStorage` y actualiza inmediatamente la cuadrícula del portal sin recargas de página.

### Impacto

Afecta a [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx), [frontend/src/components/areas/tarjeta-area.tsx](../frontend/src/components/areas/tarjeta-area.tsx), [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), `UI_GUIDE.md` y maquetas interactivas en `cards_interactive_preview.html` y `mockups_cards.html`.

## Estructura por Pestañas (General y Diseño) con Vista Previa en Vivo en Configuración Visual

## Módulo

Portal de Usuario - Configuración de Visualización (`UserViewSettings`, `PlatformMockupCard`, `TarjetaArea`)

### Regla

1. **Navegación por Pestañas (`General` y `Diseño`)**:
   - La vista de configuración visual (`UserViewSettings`) se reorganiza mediante dos botones de pestaña accesibles (`role="tablist"` y `role="tab"`):
     - **Pestaña «General»**: Agrupa la configuración de arquitectura y controles globales: Disposición Principal (Sidebar vs Topbar), Visibilidad de Elementos del Menú Lateral (Carta Responsiva, Badges de contadores circulares, Colapso de botón de usuario) y Control del Mensaje de Bienvenida (Restaurar u omitir).
     - **Pestaña «Diseño»**: Agrupa en exclusiva la personalización visual de tarjetas y la previsualización interactiva.
2. **Vista Previa en Vivo (Live Preview)**:
   - En la parte superior de la pestaña «Diseño», se despliega un contenedor interactivo de previsualización que renderiza simultáneamente:
     - La tarjeta de plataforma en vivo (`PlatformMockupCard`) reflejando la variante activa (`disenoCards`).
     - La tarjeta de área organizativa en vivo (`TarjetaArea`) reflejando la variante activa (`disenoCardsArea`).
   - Cada clic en los selectores inferiores de plataforma (6 variantes + 3 clásicas) o de área (6 variantes) actualiza instantáneamente la vista previa en pantalla sin recargas ni necesidad de salir de la sección.

### Ejemplo

Un usuario ingresa a «Configurar vista» desde el engrane superior o el menú lateral, abre la pestaña «Diseño» y hace clic en la opción «Foto Enmarcada Pastel» de plataformas y «Medallón Insignia» de áreas. Ambas tarjetas en la caja superior de «Vista Previa en Vivo» actualizan su apariencia en tiempo real con datos de demostración, permitiendo evaluar el diseño final antes de regresar al portal.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx), `UI_GUIDE.md` y maquetas interactivas en `cards_interactive_preview.html`.

## Prevención de Rectángulos Vacíos y Preservación de Estructura en Carga Inicial

## Módulo

Portal de Usuario - Ciclo de Vida y Estados de Carga (`PlatformsSidebarView`, `PlatformsLaunchpadView`, `useCatalogoSolicitable`)

### Regla

1. **Preservación Inmediata de la Estructura Visual (Shell First)**:
   - Al ingresar por primera vez a la vista de usuario (`/platforms`), el sistema nunca debe interrumpir el renderizado completo del portal para mostrar únicamente 4 rectángulos esqueléticos flotantes (`Skeleton count={4}`).
   - La estructura base (Barra Lateral con marca corporativa, navegación, encabezado superior y contenedor de trabajo) se monta de manera inmediata y estable.
2. **Carga Integrada No Invasiva**:
   - Dentro del área de contenido (`<main id="contenido">`), si el catálogo se encuentra en proceso de obtención inicial (`catalogo.loading && !catalogo.data`), se muestra un indicador de carga centrado y estilizado (`Spinner label="Cargando catálogo…"`) con tipografía sutil en lugar de una pila descontextualizada de rectángulos grises pulsantes.
3. **Estrategia Stale-While-Revalidate (SWR)**:
   - Se configuran claves de caché en memoria (`nexus.access.catalog`, `nexus.platforms.mine`, `nexus.platforms.areas`) en los hooks `useAsync`, asegurando que visitas subsecuentes o cambios entre secciones rendericen instantáneamente sin parpadeos visuales.

### Ejemplo

Cuando un colaborador accede por primera vez al portal de accesos, visualiza inmediatamente la barra lateral izquierda con su perfil, las opciones de navegación ("Plataformas", "Todas las áreas", etc.) y la barra superior. En el panel central aparece un spinner estético indicando "Cargando catálogo…", el cual da paso fluidamente a las tarjetas en cuanto la respuesta del servidor concluye, eliminando el parpadeo de 4 bloques vacíos.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [frontend/src/components/access/use-catalogo-solicitable.ts](../frontend/src/components/access/use-catalogo-solicitable.ts), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Erradicación de Rectángulos Esqueléticos en Dashboard y Vistas de Panel

## Módulo

Administración y Dashboard - Ciclo de Vida y Estados de Carga (`Dashboard`, `FavoritesList`, `CatalogGrid`)

### Regla

1. **Erradicación de Rectángulos Esqueléticos en Bloque**:
   - En el panel principal Dashboard (`/`), catálogo y favoritos, queda estrictamente prohibido renderizar pilas verticales de tarjetas esqueléticas de gran altura (`Skeleton variant="tarjeta" count={5}`) como estado de carga temporal.
   - En su lugar, se implementa un contenedor de carga centrado, pulcro y ligero (`Spinner label="Cargando estadísticas…"`) que no desfigura la cuadrícula ni simula cajas vacías gigantescas.
2. **Caché en Memoria SWR (Stale-While-Revalidate)**:
   - Se aplican claves de persistencia (`nexus.admin.stats`, `nexus.admin.home_summary`, `nexus.platforms.favorites`) en los hooks `useAsync`, permitiendo que el cambio de navegación entre Dashboard y las demás secciones sea inmediato y libre de cualquier parpadeo.

### Ejemplo

Al acceder al panel administrativo («General > Dashboard»), en lugar de desplegar 5 rectángulos blancos gigantes apilados verticalmente que ocupaban toda la pantalla, se despliega un indicador sutil y centrado de carga con texto descriptivo («Cargando estadísticas…»), pasando limpiamente a la fila de 5 tarjetas indicadoras compactas y gráficos.

### Impacto

Afecta a [frontend/src/components/dashboard.tsx](../frontend/src/components/dashboard.tsx), [frontend/src/components/favorites-list.tsx](../frontend/src/components/favorites-list.tsx), [frontend/src/components/access/catalog-grid.tsx](../frontend/src/components/access/catalog-grid.tsx) y pruebas en [frontend/tests/components/dashboard.test.tsx](../frontend/tests/components/dashboard.test.tsx).

## Estandarización de Vistas de Carga Premium a Pantalla Completa y Secciones

## Módulo

Experiencia de Carga y Microinteracciones (`PantallaCarga`, `Spinner`, `AppShell`, `PlatformsShell`, `RequireRole`, `LoginForm`)

### Regla

1. **Pantalla de Carga de Alta Gama (Full Page Loader)**:
   - Toda vista que requiera espera completa de sesión o autorización (`app-shell`, `platforms-shell`, `require-role`, `login-form`, `requests`) debe implementar el componente unificado `PantallaCarga`.
   - Queda estrictamente prohibido mostrar un lienzo en blanco plano con un único indicador circular diminuto y texto huérfano en el centro.
   - La pantalla de carga debe incorporar:
     - Orbe de luz ambiental difusa (`bg-gradient-to-tr blur-3xl`).
     - Tarjeta central flotante glassmórfica con bordes redondeados y sombra suave.
     - Emblema corporativo oficial (Escudo degradado con anillo de luz y halo pulsante).
     - Tipografía institucional ("Portal de accesos - Vivaro").
     - Barra de progreso de haz luminoso continuo (`nx-loading-beam`) con soporte para movimiento reducido.
     - Mensaje accesible y punto pulsante (`animate-ping`) sincronizado.
2. **Spinner de Sección y Controles**:
   - En áreas internas de componentes (`Dashboard`, cuadrícula de plataformas, formularios, modales), `Spinner` implementa un anillo orbital dual concéntrico con punto luminoso y tipografía subordinada, garantizando consistencia estética en toda la suite.

### Ejemplo

Cuando un usuario ingresa al sistema y la sesión aún no ha terminado de responder, en lugar de una pantalla blanca vacía con un círculo solitario, visualiza una tarjeta estética de cristal centrada sobre una suave iluminación ambiental, con el escudo del portal, el nombre de la institución y una barra de progreso luminosa que denota un sistema de alta calidad y confianza institucional.

### Impacto

Afecta a [frontend/src/components/pantalla-carga.tsx](../frontend/src/components/pantalla-carga.tsx), [frontend/src/components/ui.tsx](../frontend/src/components/ui.tsx), [frontend/src/components/app-shell.tsx](../frontend/src/components/app-shell.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [frontend/src/components/require-role.tsx](../frontend/src/components/require-role.tsx), [frontend/src/components/login-form.tsx](../frontend/src/components/login-form.tsx), [frontend/src/styles/components.css](../frontend/src/styles/components.css) y pruebas en [frontend/tests/components/avisos-y-estados.test.tsx](../frontend/tests/components/avisos-y-estados.test.tsx).

## Supresión de Re-animación Repetitiva en Gráficas de Dashboard

## Módulo

Dashboard de Administración - Ciclo de Vida y Gráficas Recharts (`Dashboard`, `Estadisticas`, `BarChart`)

### Regla

1. **Control de Ciclo de Vida de Animaciones en Gráficas (Single-Run per Session)**:
   - Al entrar por primera vez al Dashboard durante una sesión de navegación, las gráficas de barras de Recharts (`Plataformas por área` y `Más visitadas`) y los anillos de tarjetas indicadoras ejecutan su animación de entrada una única vez.
   - Si el usuario navega a otras áreas del portal (por ejemplo: Plataformas, Áreas, Usuarios, Solicitudes o Ajustes) y posteriormente regresa al Dashboard, el sistema debe suprimir la animación repetitiva (`isAnimationActive={false}` y clase `.nx-sin-animacion-graficas`).
2. **Persistencia en Memoria de Sesión**:
   - El estado de animación ya ejecutada se registra tanto en una variable en memoria del módulo (`graficasYaAnimadasMemoria`) como en `sessionStorage` (`nexus.dashboard.animado`), asegurando que las barras y anillos se rendericen instantáneamente y fijos al 100%, sin saltos visuales ni parpadeos acumulados (CLS = 0).

### Ejemplo

Un administrador ingresa al sistema y observa la animación inicial de llenado de las barras de concurrencia y plataformas. Posteriormente navega a "Plataformas" para revisar un servicio y luego regresa a "Dashboard". Al regresar, las gráficas y tarjetas indicadoras se muestran de inmediato en su posición final sin volver a animarse desde cero.

### Impacto

Afecta a [frontend/src/components/dashboard.tsx](../frontend/src/components/dashboard.tsx), [frontend/src/styles/components.css](../frontend/src/styles/components.css) y pruebas en [frontend/tests/components/dashboard.test.tsx](../frontend/tests/components/dashboard.test.tsx).

## Inicialización Inmediata del Diseño de Tarjetas en Dashboard sin Parpadeo

## Módulo

Dashboard de Administración - Preferencias de Tarjetas de Indicador (`useDisenoTarjetas`, `diseno-tarjetas.ts`)

### Regla

1. **Inicialización Síncrona Perezosa (Lazy Initial State)**:
   - El hook `useDisenoTarjetas` debe inicializar su estado local síncronamente mediante una función perezosa (`useState(() => leerDisenoTarjetas())`) leyendo directamente `localStorage`.
   - Queda prohibido inicializar el estado con el valor estático por defecto (`DISENO_POR_OMISION` / `'segmentos'`) para luego actualizarlo en `useEffect`. Dicho patrón generaba una doble renderización visible ("flash of default design") donde las tarjetas se mostraban momentáneamente con el diseño fijo antes de adoptar la preferencia guardada por el usuario.
2. **Defensa contra Entornos sin Window**:
   - La función `leerDisenoTarjetas` valida `typeof window === 'undefined'` para garantizar compatibilidad con renderizado en servidor (SSR), retornando con seguridad el valor por defecto sin lanzar excepciones de referencia.

### Ejemplo

Un usuario que configuró el diseño «Anillo con brillo» (`brillo`) o «Medidor» (`medidor`) en las 5 tarjetas superiores del Dashboard navega hacia el módulo de "Plataformas" o "Usuarios" y posteriormente regresa al Dashboard. Desde el primer frame de renderizado, las tarjetas se pintan directamente con el diseño guardado («brillo» o «medidor»), eliminando por completo el salto visual o parpadeo desde el diseño fijo de dos segmentos.

### Impacto

Afecta a [frontend/src/components/dashboard/use-diseno-tarjetas.ts](../frontend/src/components/dashboard/use-diseno-tarjetas.ts), [frontend/src/components/dashboard/diseno-tarjetas.ts](../frontend/src/components/dashboard/diseno-tarjetas.ts) y pruebas en [frontend/tests/components/dashboard-diseno-barra.test.tsx](../frontend/tests/components/dashboard-diseno-barra.test.tsx).

## Botón e Icono de Favoritos con Geometrías y Tamaños Exclusivos por Variante de Tarjeta

## Módulo

Plataformas y Catálogo de Accesos - Botón de Favorito (`FavoriteButton`, `PlatformMockupCard`, `PlatformCard`)

### Regla

1. **Identidad Visual y Geometría Exclusiva por Variante**:
   - Cada estilo de tarjeta (`duotono`, `enmarcada`, `evento`, `split`, `glass`, `editorial`, `horizontal`, `estandar` / `compacta`) debe contar con una personalidad gráfica, geometría y contenedor propios para su botón e icono de favoritos.
   - Queda prohibido renderizar un glifo de texto plano unificado (`★` / `☆`) idéntico para todas las tarjetas.
   - En la variante `duotono`: contenedor oscuro translúcido con borde neón, retícula crosshairs y estrella cyber con halo luminoso.
   - En la variante `enmarcada`: squircle tecnológico con corchetes en las esquinas y estrella protegida.
   - En la variante `evento`: sello de boleto / ticket VIP de cine con borde concéntrico punteado y estrella de medalla en relieve (inspirado en boletos de función).
   - En la variante `split`: estrella dividida verticalmente en dos mitades (bicolor ámbar e índigo).
   - En la variante `glass`: botón de cristal líquido / acrylic blur con destellos de prisma y gema facetada.
   - En la variante `editorial`: rosa de los vientos / estrella de 8 puntas de alta costura tipográfica Vogue con núcleo cuadrado rotado.
   - En la variante `horizontal`: cápsula integrada de acción con icono y etiqueta de estado textual.
   - En la variante `estandar` y `compacta`: botón flotante moderno elevado con estrella de 5 puntas curva.
2. **Dimensiones Accesibles y Tamaño Prominente (DIS-008 / WCAG)**:
   - El botón interactivo mantiene un área de pulsación mínima de 48px (`min-h-12 min-w-12 size-12`) cumpliendo la pauta WCAG 2.2 AA.
   - El icono SVG vectorial escala a un tamaño prominente y de alta visibilidad (`size-7` / 28px, o `size-6` / 24px en horizontal) con trazo grueso y relleno de alto contraste, eliminando la sensación de tamaño reducido previa.

### Ejemplo

Al seleccionar el estilo «Evento» en Ajustes de Vista, las tarjetas de plataformas muestran el icono de favoritos con forma de sello de ticket de cine con anillo perforado; al seleccionar «Editorial», el icono adopta la rosa de los vientos de 8 puntas; y en «Duotono», una estrella neón con mirilla cibernética, todas con tamaño amplio y legible.

### Impacto

Afecta a [frontend/src/components/favorite-button.tsx](../frontend/src/components/favorite-button.tsx), [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx), [frontend/src/components/platform-card.tsx](../frontend/src/components/platform-card.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y [frontend/tests/components/favorites-list.test.tsx](../frontend/tests/components/favorites-list.test.tsx).

## Estandarización de Pestañas (Tabs) y Barra de Ubicación (Location Bar) en Modo Topbar

## Módulo

Plataformas y Configuración de Vista (`user-view-settings.tsx`, `platforms-topbar.tsx`)

### Regla

1. **Unificación de Diseño de Pestañas (Tabs Buttons)**:
   - Las pestañas de navegación en "Ajustes de Vista" (`General` y `Diseño`) deben utilizar de manera estricta la misma arquitectura visual y de componentes que las pastillas de filtrado del catálogo de plataformas (`PlatformsLaunchpadView`).
   - Queda prohibido el uso de contenedores segmentados cerrados tipo iOS (`bg-superficie-hundida p-1.5 rounded-2xl`).
   - Cada pestaña debe constituir un botón píldora independiente (`h-12 min-h-12 w-44 sm:w-48`), con esquinas redondeadas (`rounded-xl`), borde individual (`border-panel-border` o `border-primary`), icono temático en el extremo izquierdo, etiqueta centrada y badge circular numérico a la derecha con el conteo de secciones correspondientes (`3` en General, `2` en Diseño).
2. **Barra de Ubicación (Location Bar / Breadcrumbs) en Modo Topbar**:
   - La barra superior exclusiva de usuario (`PlatformsTopbar`) debe incorporar la barra de ubicación jerárquica contigua a la marca institucional (Brand).
   - Estructura para administradores: `General › Portal [› Subsección activa]`.
   - Estructura para usuarios regulares: `Portal [› Subsección activa]`.
   - Subsecciones admitidas: `Ajustes de Vista`, `Carta Responsiva`, `Mi Widget`, `Mis Solicitudes`.
   - Cada segmento antecesor es interactivo permitiendo retornar al catálogo de plataformas de forma inmediata.

### Ejemplo

Al ingresar a Ajustes de Vista en modo Topbar, el usuario visualiza en la cabecera superior la ruta `General › Portal › Ajustes de Vista` con separadores vectoriales `chevron-der`, y en el cuerpo de la página las pestañas `General (3)` y `Diseño (2)` con el mismo formato de tarjetas/pastillas independientes que las pestañas `Todas (2)` y `Favoritas (1)` del catálogo.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx) y pruebas en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Acción Única y Limpieza Visual en Tarjetas de Plataforma y Modal de Solicitud de Acceso con CAPTCHA

## Módulo

Portal de Usuario, Catálogo de Plataformas y Solicitudes de Acceso (`platform-mockup-card.tsx`, `request-form-modal.tsx`)

### Regla

1. **Acción Única y Exclusión de Botón "Detalles"**:
   - Cada tarjeta de plataforma en el portal de usuario (`PlatformMockupCard`) debe presentar un único botón/enlace de acción principal contextual en su pie o zona de acción, quedando estrictamente prohibida la presencia de un botón secundario redundante "Detalles".
   - Acciones permitidas según el estado del usuario:
     - Con acceso activo y enlace directo: botón/enlace principal «Abrir» o «Ir a herramienta →» (`min-h-12`).
     - Sin acceso vigente con permiso para solicitar: botón principal «Solicitar acceso» o «Solicitar →» (`min-h-12`).
     - Con solicitud pendiente: indicador contextual textual «En revisión» o «En trámite».
2. **Supresión de Etiquetas de Rol/Administrador en el Contenido de la Tarjeta**:
   - Se eliminan las etiquetas o menciones fijas de rol (e.g., «Administrador», «🛡️ Administrador») dentro del banner o pie de las variantes de tarjeta (`evento`, `editorial`, `duotono`, `split`). Las tarjetas exhiben exclusivamente la información funcional de la plataforma (iniciales, nombre, área y descripción de la herramienta).
3. **Modal de Solicitud de Acceso Explicativo con Checkbox y CAPTCHA por Plataforma**:
   - Al pulsar «Solicitar acceso», se despliega el modal enriquecido (`RequestFormModal`), el cual incorpora:
     - **Ficha explicativa de la herramienta**: Muestra las iniciales temáticas de la plataforma, nombre, badge de su área, descripción institucional completa y aviso informativo sobre el flujo de revisión y aprobación administrativa.
     - **Nivel de acceso solicitado**: Selector de nivel (`Usuario` o `Administrador`) y justificación opcional (hasta 500 caracteres).
     - **Casilla obligatoria de uso responsable (Checkbox)**: Checkbox de aceptación de términos donde el usuario confirma requerir el acceso para sus funciones y se compromete al uso responsable y confidencial conforme a las políticas de seguridad.
     - **Confirmación de seguridad anti-error (CAPTCHA por plataforma)**: Código alfanumérico aleatorio de 5 caracteres renderizado en una caja estilizada monoespaciada con botón de regeneración ("Nuevo código"). El botón «Enviar solicitud» permanece estrictamente deshabilitado hasta que se marque la casilla de responsabilidad y el código ingresado coincida exactamente con el CAPTCHA generado.

### Ejemplo

Un usuario sin permisos en la consola corporativa AWS visualiza su tarjeta (variante Evento) con un único botón de ancho completo «Solicitar acceso». Al hacer clic, se abre el modal que detalla las características de AWS, le permite elegir el nivel solicitado, le exige marcar la casilla de compromiso institucional y resolver el CAPTCHA exclusivo antes de enviar la petición para aprobación.

### Impacto

Afecta a [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx), [frontend/src/components/access/request-form-modal.tsx](../frontend/src/components/access/request-form-modal.tsx), [frontend/src/components/access/catalog-grid.tsx](../frontend/src/components/access/catalog-grid.tsx) y a las pruebas en [frontend/tests/components/access/request-catalog.test.tsx](../frontend/tests/components/access/request-catalog.test.tsx).

## Supresión de Badges Circulares Numéricos en Pestañas de Ajustes de Vista

## Módulo

Configuración Visual del Usuario (`user-view-settings.tsx`)

### Regla

En las pestañas de navegación de «Ajustes de Vista» (`General` y `Diseño`), se suprimen los badges circulares numéricos (`3` y `2`). A diferencia de las pestañas de filtrado del catálogo de plataformas (donde los números representan la cantidad de plataformas asociadas al filtro), en la vista de configuración representan meramente subdivisiones de opciones, lo cual genera confusión cognitiva. Cada pestaña se renderiza limpia y centrada con su icono representativo y su etiqueta de texto (`min-h-12 px-5`).

### Ejemplo

Al ingresar a Ajustes de Vista, las pestañas superiores muestran `[ ⊞ General ]` y `[ 🗄 Diseño ]` en formato píldora estilizada e interactiva sin ningún círculo numérico accesorio a la derecha.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y a la interfaz de usuario en el portal.

## Navegación Resiliente en Modo Topbar y Supresión de Redundancias en Location Bar

## Módulo

Navegación del Portal, Barra Superior y Migas de Pan (`platforms-topbar.tsx`, `platforms-sidebar-view.tsx`, `platforms-shell.tsx`)

### Regla

1. **Navegación Inmediata a Catálogo desde Topbar (`onNavigateCatalogo`)**:
   - Cuando el usuario se encuentra en subsecciones de configuración o gestión del portal (`Ajustes de Vista`, `Carta Responsiva`, `Mi Widget`), cualquier interacción con el botón principal «Plataformas» de la barra superior, el logotipo corporativo o la miga de pan inicial «Catálogo» intercepta la navegación con `e.preventDefault()` y ejecuta `onNavigateCatalogo()` para restituir la vista de catálogo (`seccionActiva = 'catalogo'`). Esto garantiza que la transición de estado sea inmediata en el cliente sin depender de recargas ni quedar bloqueada por estar en la misma ruta `/platforms`.
2. **Depuración de la Barra de Ubicación (Eliminación de "Todas las áreas")**:
   - Se suprime por completo el segmento intermedio redundante «Todas las áreas» del location bar / migas de pan.
   - Jerarquía limpia y sin ruido visual:
     - Raíz del catálogo: muestra exclusivamente `Catálogo`.
     - Dentro de un departamento: muestra `Catálogo / [Nombre del Área]`, donde `Catálogo` es un botón interactivo para regresar a la vista raíz del catálogo.
     - En ajustes de vista: muestra `Catálogo / Ajustes de Vista`, con `Catálogo` interactivo para regresar al catálogo.
     - En otras secciones: muestra `Mi Espacio / [Favoritas | Mis Solicitudes | Mi Widget | Carta Responsiva]`.
3. **Claridad de Disponibilidad en Tarjetas de Plataforma (Supresión de "Administrador")**:
   - En el recuadro secundario de datos de la tarjeta estándar (`PlatformMockupCard`), se reemplaza la métrica de rol «NIVEL DE ACCESO: Administrador» por «DISPONIBILIDAD: Habilitado / Disponible». Esto evita que el usuario interprete erróneamente que la tarjeta requiere privilegios de administración o que se confunda la función de la plataforma con el rol del usuario.

### Ejemplo

Al seleccionar el área «Demo Infraestructura», el breadcrumb superior exhibe `Catálogo / Demo Infraestructura` (sin el texto redundante intermedio «Todas las áreas»). Al hacer clic en `Catálogo`, el usuario regresa limpiamente a la raíz del catálogo.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx) y [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx).

## Diseños de Tarjetas con Imagen de Fondo Temática y Cinematográfica (Variante Portada)

## Módulo

Catálogo de Plataformas, Tarjetas de Área Organizativa y Ajustes de Vista (`platform-mockup-card.tsx`, `tarjeta-area.tsx`, `card-backgrounds.ts`, `user-view-settings.tsx`)

### Regla

1. **Inclusión de Variante «Portada Fotográfica / Cine»**:
   - Se incorpora formalmente una variante de diseño inmersivo con imagen de fondo fotográfica tanto para tarjetas de plataforma (`PlatformMockupCard`, variante `portada`) como para tarjetas de área organizativa (`TarjetaArea`, variante `portada`).
2. **Arquitectura Visual y Cumplimiento Estricto de Prohibición de `style=""`**:
   - Cada tarjeta con imagen de fondo implementa la imagen mediante un elemento semántico `<img src="..." alt="" loading="lazy" decoding="async" className="absolute inset-0 size-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out pointer-events-none" />` sin hacer uso de `style=""` inline.
   - Sobre la imagen se superpone una capa de gradiente protector de legibilidad (`bg-gradient-to-t from-black/95 via-black/75 to-black/35 pointer-events-none`) que garantiza contraste tipográfico conforme a WCAG AA/AAA tanto en tema claro como en tema oscuro.
   - En la tarjeta de plataforma (`portada`):
     - Cabecera: Monograma con borde translúcido (`bg-white/15 backdrop-blur-md text-white`) + Badge del área (`bg-black/50 text-white/90 backdrop-blur-md`) + Botón de favoritos con halo estelar dorado (`variante="portada"`).
     - Cuerpo: Título en tipografía prominente (`text-white font-bold drop-shadow-sm`) y descripción de dos líneas con sombra sutil (`text-slate-300`).
     - Pie: Botón de acción único destacado de ancho completo (`w-full min-h-12`) con feedback visual interactivo (`hover:scale-[1.02] active:scale-[0.98]`).
   - En la tarjeta de área organizativa (`portada`):
     - Cabecera: Icono institucional sobre vidrio esmerilado + Badge interactivo de estado de área (`EstadoBadgeBoton`).
     - Cuerpo: Título departamental en negrita extrema (`text-white font-black text-xl`) y descripción corporativa.
     - Métricas: Dos módulos translúcidos con efecto glassmorphism (`bg-white/10 backdrop-blur-md border border-white/15 text-white`) indicando Personas y Plataformas.
     - Pie: Pila de logos con contador `+N` sobre fondo oscuro translúcido y botón «Ver plataformas →».
3. **Mapeo Curado de Imágenes (`card-backgrounds.ts`)**:
   - Las imágenes de fondo se resuelven contextualmente a través de `obtenerImagenFondoPlataforma` y `obtenerImagenFondoArea` mapeando palabras clave funcionales (servidores, código, comunicación, finanzas, seguridad, operaciones) a imágenes de alta definición con caché permanente.

### Ejemplo

Al seleccionar el estilo «Portada / Cine» en Ajustes de Vista, la tarjeta de AWS Cloud Console muestra una vista nocturna de servidores con luces azuladas en el fondo, texto blanco de alto contraste y un botón de ancho completo «Ir a la herramienta», mientras que el área Tecnología & TI muestra un fondo de centro de datos con métricas en vidrio esmerilado.

### Impacto

Afecta a [frontend/src/lib/card-backgrounds.ts](../frontend/src/lib/card-backgrounds.ts), [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx), [frontend/src/components/areas/tarjeta-area.tsx](../frontend/src/components/areas/tarjeta-area.tsx), [frontend/src/components/favorite-button.tsx](../frontend/src/components/favorite-button.tsx), [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx) y [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx).

## Distribución en Dos Columnas de la Pestaña General en Ajustes de Vista para Eliminar Scroll

## Módulo

Configuración Visual del Usuario (`user-view-settings.tsx`)

### Regla

1. **Composición en Dos Columnas Responsivas (`grid grid-cols-1 lg:grid-cols-2 gap-4`)**:
   - En la pestaña «General» de la vista de personalización (`UserViewSettings`), los bloques de configuración se distribuyen en una cuadrícula de dos columnas equilibradas para eliminar el desbordamiento vertical y el scroll en pantallas estándar (`min-h-screen`, 1080p y 900p).
   - **Columna 1 (Izquierda)**:
     - Bloque 1: **Disposición Principal del Portal** (selector interactivo con opciones simétricas para Barra Lateral y Barra Superior).
     - Bloque 2: **Mensaje de Bienvenida** (control de estado, conmutador Toggle y acciones «Restaurar / Omitir mensaje» y «Previsualizar»).
   - **Columna 2 (Derecha)**:
     - Bloque 3: **Elementos de la Barra Lateral** (conmutadores para Carta Responsiva, Badges Circulares y Modo Compacto del Botón de Usuario).
2. **Equilibrio Visual y Altura Compacta**:
   - Ambas columnas mantienen una altura sincronizada (~305px), permitiendo visualizar la totalidad de los controles de la pestaña «General» dentro del primer pliegue de la ventana sin requerir desplazamiento vertical.

### Ejemplo

Al abrir «Ajustes de Vista» y permanecer en la pestaña «General», el usuario observa a la izquierda la configuración de disposición principal y el mensaje de bienvenida, y a la derecha los componentes de la barra lateral, visualizando todas las opciones simultáneamente sin barra de scroll.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y pruebas de interfaz en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Eliminación de Retorno Redundante y Separación de Diseño en Pestañas Áreas y Plataformas en 2 Columnas

## Módulo

Configuración Visual y Navegación del Usuario (`user-view-settings.tsx`)

### Regla

1. **Eliminación del Botón Redundante de Retorno**:
   - En la cabecera de pestañas de `UserViewSettings`, se suprime el botón «Volver a Plataformas». La navegación y conmutación de vuelta al catálogo se realiza de forma unificada desde la barra de herramientas superior o el menú lateral.
2. **Reemplazo de la Pestaña Unificada «Diseño» por Pestañas Dedicadas**:
   - Se elimina la pestaña genérica «Diseño».
   - En su lugar, se proporcionan tres pestañas independientes de navegación rápida con iconos y diseño de catálogo:
     - **General**: Configuración de layout, mensaje de bienvenida y componentes auxiliares.
     - **Áreas**: Especializada en la personalización de tarjetas departamentales.
     - **Plataformas**: Especializada en la personalización de tarjetas de aplicaciones y herramientas.
3. **Distribución en 2 Columnas sin Scroll Vertical**:
   - Tanto la pestaña «Áreas» como la pestaña «Plataformas» dividen su contenido en 2 columnas balanceadas (`grid grid-cols-1 lg:grid-cols-12 gap-5`):
     - **Columna 1 (Izquierda, `lg:col-span-5`)**: Previsualización interactiva en vivo de la tarjeta con badge de estilo actual y demostración de acciones reactivas.
     - **Columna 2 (Derecha, `lg:col-span-7`)**: Selector de estilos visuales con opciones distribuidas en 2 columnas internas (`grid grid-cols-1 sm:grid-cols-2 gap-2.5`).
   - Al coincidir la altura de ambas columnas (~380px a ~440px), todo el contenido se presenta en una sola pantalla sin necesidad de scroll vertical.

### Ejemplo

Al acceder a Ajustes de Vista, el usuario ve las tres pestañas: General, Áreas y Plataformas. Al pulsar «Áreas», a la izquierda ve la tarjeta en vivo de Tecnología & TI y a la derecha las 7 opciones de diseño en dos columnas. Al hacer clic en «Mosaico Bento Grid», la tarjeta izquierda cambia al instante sin ningún salto ni scroll en la pantalla.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y la suite de pruebas [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Sincronización Canónica de Iconos de Favoritos y Catálogo Institucional de Trazos

## Módulo

Iconografía y Sistema de Favoritos (`favorite-button.tsx`, `icono.tsx`, `icono-trazos.ts`)

### Regla

1. **Sincronización Canónica del Icono de Favoritos**:
   - Todas las variantes de tarjetas de plataforma (`PlatformMockupCard`, `PlatformCard`, `RequestCatalogCard`) deben utilizar de forma obligatoria y unificada el icono canónico institucional de favoritos (`Icono` con `nombre="favorito"`), correspondiente a la estrella estandarizada de 5 puntas de `icono-trazos.ts`.
   - Queda estrictamente prohibido el uso de símbolos alternativos (corazones, listones/marcadores de libros, tachuelas, medallas roseta, destellos de 4 puntas, rombos o banderas).
   - Cuando el elemento está marcado como favorito (`favorite === true`), la estrella adopta el color y relleno dorado/ámbar (`text-amber-400 fill-amber-400`) sincronizado con el indicador de la barra lateral (`platforms-sidebar-view.tsx`) y las pastillas del catálogo (`platforms-launchpad-view.tsx`).
   - Cuando no está marcado (`favorite === false`), se muestra el trazo exterior con `fill="none"` y color atenuado.
2. **Homogeneización del Catálogo Institucional de Iconos**:
   - Se erradican emojis y símbolos no estandarizados (p.ej. `👥`, `📦`, `📊`, `★`, `❤️`) en favor de componentes formales `<Icono>` (`usuarios`, `plataformas`, `panel`, `favorito`).
   - El componente `<Icono>` admite la escala `'2xl'` (28px) y la propiedad `relleno?: boolean` (`fill="currentColor"` cuando es verdadero, `fill="none"` cuando es falso) preservando el trazo de 2px y puntas redondeadas.

### Ejemplo

Al visualizar una tarjeta en cualquier variante de diseño (sea Portada, Duotono, Split, Enmarcada, Evento, Glass, Editorial, Horizontal o Estándar), el botón de favoritos muestra la misma estrella de 5 puntas que aparece en «Favoritas» en el menú lateral. Al pulsarla, se ilumina en ámbar sincronizadamente con el contador de la barra lateral.

### Impacto

Afecta a [frontend/src/components/favorite-button.tsx](../frontend/src/components/favorite-button.tsx), [frontend/src/components/icono.tsx](../frontend/src/components/icono.tsx), [frontend/src/components/areas/tarjeta-area.tsx](../frontend/src/components/areas/tarjeta-area.tsx), [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y suites de pruebas asociadas.

## Supresión de Badges Circulares Numéricos en Pestañas de Ajustes de Vista

## Módulo

Configuración Visual del Usuario (`user-view-settings.tsx`)

### Regla

En las pestañas de navegación de «Ajustes de Vista» (`General` y `Diseño`), se suprimen los badges circulares numéricos (`3` y `2`). A diferencia de las pestañas de filtrado del catálogo de plataformas (donde los números representan la cantidad de plataformas asociadas al filtro), en la vista de configuración representan meramente subdivisiones de opciones, lo cual genera confusión cognitiva. Cada pestaña se renderiza limpia y centrada con su icono representativo y su etiqueta de texto (`min-h-12 px-5`).

### Ejemplo

Al ingresar a Ajustes de Vista, las pestañas superiores muestran `[ ⊞ General ]` y `[ 🗄 Diseño ]` en formato píldora estilizada e interactiva sin ningún círculo numérico accesorio a la derecha.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y a la interfaz de usuario en el portal.

## Navegación Resiliente en Modo Topbar y Supresión de Redundancias en Location Bar

## Módulo

Navegación del Portal, Barra Superior y Migas de Pan (`platforms-topbar.tsx`, `platforms-sidebar-view.tsx`, `platforms-shell.tsx`)

### Regla

1. **Navegación Inmediata a Catálogo desde Topbar (`onNavigateCatalogo`)**:
   - Cuando el usuario se encuentra en subsecciones de configuración o gestión del portal (`Ajustes de Vista`, `Carta Responsiva`, `Mi Widget`), cualquier interacción con el botón principal «Plataformas» de la barra superior, el logotipo corporativo o la miga de pan inicial «Catálogo» intercepta la navegación con `e.preventDefault()` y ejecuta `onNavigateCatalogo()` para restituir la vista de catálogo (`seccionActiva = 'catalogo'`). Esto garantiza que la transición de estado sea inmediata en el cliente sin depender de recargas ni quedar bloqueada por estar en la misma ruta `/platforms`.
2. **Depuración de la Barra de Ubicación (Eliminación de "Todas las áreas")**:
   - Se suprime por completo el segmento intermedio redundante «Todas las áreas» del location bar / migas de pan.
   - Jerarquía limpia y sin ruido visual:
     - Raíz del catálogo: muestra exclusivamente `Catálogo`.
     - Dentro de un departamento: muestra `Catálogo / [Nombre del Área]`, donde `Catálogo` es un botón interactivo para regresar a la vista raíz del catálogo.
     - En ajustes de vista: muestra `Catálogo / Ajustes de Vista`, con `Catálogo` interactivo para regresar al catálogo.
     - En otras secciones: muestra `Mi Espacio / [Favoritas | Mis Solicitudes | Mi Widget | Carta Responsiva]`.
3. **Claridad de Disponibilidad en Tarjetas de Plataforma (Supresión de "Administrador")**:
   - En el recuadro secundario de datos de la tarjeta estándar (`PlatformMockupCard`), se reemplaza la métrica de rol «NIVEL DE ACCESO: Administrador» por «DISPONIBILIDAD: Habilitado / Disponible». Esto evita que el usuario interprete erróneamente que la tarjeta requiere privilegios de administración o que se confunda la función de la plataforma con el rol del usuario.

### Ejemplo

Al seleccionar el área «Demo Infraestructura», el breadcrumb superior exhibe `Catálogo / Demo Infraestructura` (sin el texto redundante intermedio «Todas las áreas»). Al hacer clic en `Catálogo`, el usuario regresa limpiamente a la raíz del catálogo.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx) y [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx).

## Diseños de Tarjetas con Imagen de Fondo Temática y Cinematográfica (Variante Portada)

## Módulo

Catálogo de Plataformas, Tarjetas de Área Organizativa y Ajustes de Vista (`platform-mockup-card.tsx`, `tarjeta-area.tsx`, `card-backgrounds.ts`, `user-view-settings.tsx`)

### Regla

1. **Inclusión de Variante «Portada Fotográfica / Cine»**:
   - Se incorpora formalmente una variante de diseño inmersivo con imagen de fondo fotográfica tanto para tarjetas de plataforma (`PlatformMockupCard`, variante `portada`) como para tarjetas de área organizativa (`TarjetaArea`, variante `portada`).
2. **Arquitectura Visual y Cumplimiento Estricto de Prohibición de `style=""`**:
   - Cada tarjeta con imagen de fondo implementa la imagen mediante un elemento semántico `<img src="..." alt="" loading="lazy" decoding="async" className="absolute inset-0 size-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out pointer-events-none" />` sin hacer uso de `style=""` inline.
   - Sobre la imagen se superpone una capa de gradiente protector de legibilidad (`bg-gradient-to-t from-black/95 via-black/75 to-black/35 pointer-events-none`) que garantiza contraste tipográfico conforme a WCAG AA/AAA tanto en tema claro como en tema oscuro.
   - En la tarjeta de plataforma (`portada`):
     - Cabecera: Monograma con borde translúcido (`bg-white/15 backdrop-blur-md text-white`) + Badge del área (`bg-black/50 text-white/90 backdrop-blur-md`) + Botón de favoritos con halo estelar dorado (`variante="portada"`).
     - Cuerpo: Título en tipografía prominente (`text-white font-bold drop-shadow-sm`) y descripción de dos líneas con sombra sutil (`text-slate-300`).
     - Pie: Botón de acción único destacado de ancho completo (`w-full min-h-12`) con feedback visual interactivo (`hover:scale-[1.02] active:scale-[0.98]`).
   - En la tarjeta de área organizativa (`portada`):
     - Cabecera: Icono institucional sobre vidrio esmerilado + Badge interactivo de estado de área (`EstadoBadgeBoton`).
     - Cuerpo: Título departamental en negrita extrema (`text-white font-black text-xl`) y descripción corporativa.
     - Métricas: Dos módulos translúcidos con efecto glassmorphism (`bg-white/10 backdrop-blur-md border border-white/15 text-white`) indicando Personas y Plataformas.
     - Pie: Pila de logos con contador `+N` sobre fondo oscuro translúcido y botón «Ver plataformas →».
3. **Mapeo Curado de Imágenes (`card-backgrounds.ts`)**:
   - Las imágenes de fondo se resuelven contextualmente a través de `obtenerImagenFondoPlataforma` y `obtenerImagenFondoArea` mapeando palabras clave funcionales (servidores, código, comunicación, finanzas, seguridad, operaciones) a imágenes de alta definición con caché permanente.

### Ejemplo

Al seleccionar el estilo «Portada / Cine» en Ajustes de Vista, la tarjeta de AWS Cloud Console muestra una vista nocturna de servidores con luces azuladas en el fondo, texto blanco de alto contraste y un botón de ancho completo «Ir a la herramienta», mientras que el área Tecnología & TI muestra un fondo de centro de datos con métricas en vidrio esmerilado.

### Impacto

Afecta a [frontend/src/lib/card-backgrounds.ts](../frontend/src/lib/card-backgrounds.ts), [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx), [frontend/src/components/areas/tarjeta-area.tsx](../frontend/src/components/areas/tarjeta-area.tsx), [frontend/src/components/favorite-button.tsx](../frontend/src/components/favorite-button.tsx), [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx) y [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx).

## Distribución en Dos Columnas de la Pestaña General en Ajustes de Vista para Eliminar Scroll

## Módulo

Configuración Visual del Usuario (`user-view-settings.tsx`)

### Regla

1. **Composición en Dos Columnas Responsivas (`grid grid-cols-1 lg:grid-cols-2 gap-4`)**:
   - En la pestaña «General» de la vista de personalización (`UserViewSettings`), los bloques de configuración se distribuyen en una cuadrícula de dos columnas equilibradas para eliminar el desbordamiento vertical y el scroll en pantallas estándar (`min-h-screen`, 1080p y 900p).
   - **Columna 1 (Izquierda)**:
     - Bloque 1: **Disposición Principal del Portal** (selector interactivo con opciones simétricas para Barra Lateral y Barra Superior).
     - Bloque 2: **Mensaje de Bienvenida** (control de estado, conmutador Toggle y acciones «Restaurar / Omitir mensaje» y «Previsualizar»).
   - **Columna 2 (Derecha)**:
     - Bloque 3: **Elementos de la Barra Lateral** (conmutadores para Carta Responsiva, Badges Circulares y Modo Compacto del Botón de Usuario).
2. **Equilibrio Visual y Altura Compacta**:
   - Ambas columnas mantienen una altura sincronizada (~305px), permitiendo visualizar la totalidad de los controles de la pestaña «General» dentro del primer pliegue de la ventana sin requerir desplazamiento vertical.

### Ejemplo

Al abrir «Ajustes de Vista» y permanecer en la pestaña «General», el usuario observa a la izquierda la configuración de disposición principal y el mensaje de bienvenida, y a la derecha los componentes de la barra lateral, visualizando todas las opciones simultáneamente sin barra de scroll.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y pruebas de interfaz en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Eliminación de Retorno Redundante y Separación de Diseño en Pestañas Áreas y Plataformas en 2 Columnas

## Módulo

Configuración Visual y Navegación del Usuario (`user-view-settings.tsx`)

### Regla

1. **Eliminación del Botón Redundante de Retorno**:
   - En la cabecera de pestañas de `UserViewSettings`, se suprime el botón «Volver a Plataformas». La navegación y conmutación de vuelta al catálogo se realiza de forma unificada desde la barra de herramientas superior o el menú lateral.
2. **Reemplazo de la Pestaña Unificada «Diseño» por Pestañas Dedicadas**:
   - Se elimina la pestaña genérica «Diseño».
   - En su lugar, se proporcionan tres pestañas independientes de navegación rápida con iconos y diseño de catálogo:
     - **General**: Configuración de layout, mensaje de bienvenida y componentes auxiliares.
     - **Áreas**: Especializada en la personalización de tarjetas departamentales.
     - **Plataformas**: Especializada en la personalización de tarjetas de aplicaciones y herramientas.
3. **Distribución en 2 Columnas sin Scroll Vertical**:
   - Tanto la pestaña «Áreas» como la pestaña «Plataformas» dividen su contenido en 2 columnas balanceadas (`grid grid-cols-1 lg:grid-cols-12 gap-5`):
     - **Columna 1 (Izquierda, `lg:col-span-5`)**: Previsualización interactiva en vivo de la tarjeta con badge de estilo actual y demostración de acciones reactivas.
     - **Columna 2 (Derecha, `lg:col-span-7`)**: Selector de estilos visuales con opciones distribuidas en 2 columnas internas (`grid grid-cols-1 sm:grid-cols-2 gap-2.5`).
   - Al coincidir la altura de ambas columnas (~380px a ~440px), todo el contenido se presenta en una sola pantalla sin necesidad de scroll vertical.

### Ejemplo

Al acceder a Ajustes de Vista, el usuario ve las tres pestañas: General, Áreas y Plataformas. Al pulsar «Áreas», a la izquierda ve la tarjeta en vivo de Tecnología & TI y a la derecha las 7 opciones de diseño en dos columnas. Al hacer clic en «Mosaico Bento Grid», la tarjeta izquierda cambia al instante sin ningún salto ni scroll en la pantalla.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y la suite de pruebas [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Sincronización Canónica de Iconos de Favoritos y Catálogo Institucional de Trazos

## Módulo

Iconografía y Sistema de Favoritos (`favorite-button.tsx`, `icono.tsx`, `icono-trazos.ts`)

### Regla

1. **Sincronización Canónica del Icono de Favoritos**:
   - Todas las variantes de tarjetas de plataforma (`PlatformMockupCard`, `PlatformCard`, `RequestCatalogCard`) deben utilizar de forma obligatoria y unificada el icono canónico institucional de favoritos (`Icono` con `nombre="favorito"`), correspondiente a la estrella estandarizada de 5 puntas de `icono-trazos.ts`.
   - Queda estrictamente prohibido el uso de símbolos alternativos (corazones, listones/marcadores de libros, tachuelas, medallas roseta, destellos de 4 puntas, rombos o banderas).
   - Cuando el elemento está marcado como favorito (`favorite === true`), la estrella adopta el color y relleno dorado/ámbar (`text-amber-400 fill-amber-400`) sincronizado con el indicador de la barra lateral (`platforms-sidebar-view.tsx`) y las pastillas del catálogo (`platforms-launchpad-view.tsx`).
   - Cuando no está marcado (`favorite === false`), se muestra el trazo exterior con `fill="none"` y color atenuado.
2. **Homogeneización del Catálogo Institucional de Iconos**:
   - Se erradican emojis y símbolos no estandarizados (p.ej. `👥`, `📦`, `📊`, `★`, `❤️`) en favor de componentes formales `<Icono>` (`usuarios`, `plataformas`, `panel`, `favorito`).
   - El componente `<Icono>` admite la escala `'2xl'` (28px) y la propiedad `relleno?: boolean` (`fill="currentColor"` cuando es verdadero, `fill="none"` cuando es falso) preservando el trazo de 2px y puntas redondeadas.

### Ejemplo

Al visualizar una tarjeta en cualquier variante de diseño (sea Portada, Duotono, Split, Enmarcada, Evento, Glass, Editorial, Horizontal o Estándar), el botón de favoritos muestra la misma estrella de 5 puntas que aparece en «Favoritas» en el menú lateral. Al pulsarla, se ilumina en ámbar sincronizadamente con el contador de la barra lateral.

### Impacto

Afecta a [frontend/src/components/favorite-button.tsx](../frontend/src/components/favorite-button.tsx), [frontend/src/components/icono.tsx](../frontend/src/components/icono.tsx), [frontend/src/components/areas/tarjeta-area.tsx](../frontend/src/components/areas/tarjeta-area.tsx), [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y suites de pruebas asociadas.

## Variantes de Tarjetas de Plataforma con Imagen de Fondo (Hero Banner y Flotante Inmersiva)

## Módulo

Catálogo de Plataformas y Ajustes de Vista (`platform-mockup-card.tsx`, `user-view-settings.tsx`, `favorite-button.tsx`, `platforms-shell.tsx`, `platforms-sidebar-view.tsx`)

### Regla

1. **Ampliación de Diseños Fotográficos en Tarjetas de Plataformas**:
   - Se incorporan dos nuevas variantes de tarjetas de plataforma que soportan imágenes de fondo dinámicas de alta definición (`obtenerImagenFondoPlataforma`), completando 3 variantes con fotografía fotográfica (`'portada'`, `'banner'`, `'flotante'`):
     - **Hero Banner (`'banner'`)**: Cabecera panorámica fotográfica superior (`h-28 sm:h-32`) con degradado oscuro de protección de contraste, badge de área y estrella de favoritos sobrepuesta, chip de iniciales con borde protector y cuerpo inferior estructurado con título, descripción y botón de acción principal de ancho completo.
     - **Flotante Inmersiva (`'flotante'`)**: Fotografía inmersiva a sangre en todo el contenedor de la tarjeta, con viñeta cinematográfica y un panel interior flotante de cristal esmerilado (`backdrop-blur-xl bg-black/75 border border-white/20`) que resalta el monograma, el título y el botón de acción accesible.
2. **Prohibición de Estilos en Línea y Cumplimiento de Accesibilidad**:
   - Todas las imágenes de fondo se implementan mediante `<img className="absolute inset-0 size-full object-cover group-hover:scale-105 pointer-events-none" />` y gradientes Tailwind sin atributos `style=""`.
   - Todos los botones de acción respetan la altura táctil mínima de 48px (`min-h-12`) y el botón de favoritos utiliza la estrella canónica institucional (`<Icono nombre="favorito" />`).
3. **Persistencia e Integración en Ajustes de Vista**:
   - Ambas variantes son seleccionables desde el selector de la pestaña «Plataformas» de Ajustes de Vista (Opciones 11 y 12) y se persisten en `localStorage` bajo la clave `nexus.platforms.card_design`.

### Ejemplo

Al acceder a Ajustes de Vista > Plataformas, el usuario puede seleccionar la opción 11 «Hero Banner» o la opción 12 «Flotante Inmersiva». Al seleccionarlas, la vista previa interactiva en la columna izquierda refleja inmediatamente la tarjeta con su fotografía temática correspondiente y el portal de plataformas renderiza las herramientas con el nuevo diseño.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/platforms/platform-mockup-card.tsx](../frontend/src/components/platforms/platform-mockup-card.tsx), [frontend/src/components/favorite-button.tsx](../frontend/src/components/favorite-button.tsx), [frontend/src/components/platforms/platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx) y [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx).

## Distribución del Panel General en Ajustes de Vista (Grid 2 Filas x 1 Columna con Fila Superior Bipartita)

## Módulo

Ajustes de Vista (`user-view-settings.tsx`)

### Regla

1. **Estructura Arquitectónica del Panel General**:
   - El panel «General» (`tabActiva === 'general'`) se organiza en una cuadrícula de 2 filas y 1 columna principal (`grid grid-cols-1 gap-4`) que abarca todo el ancho del cuerpo:
     - **Fila 1 (Grid 1 fila x 2 columnas, `grid grid-cols-1 lg:grid-cols-2 gap-4 items-stretch`)**:
       - *Columna Izquierda*: Contenedor «Disposición Principal del Portal» con la selección de Sidebar vs Topbar.
       - *Columna Derecha*: Contenedor «Mensaje de Bienvenida» con botones de acción (Restaurar/Omitir, Previsualizar) y conmutador.
     - **Fila 2 (Ancho completo)**:
       - Contenedor «Elementos de la Barra Lateral» abarcando el 100% del ancho del cuerpo, distribuyendo sus 3 conmutadores (Documentos, Badges Circulares y Botón Compacto de Usuario) en una subcuadrícula horizontal equilibrada (`grid grid-cols-1 md:grid-cols-3 gap-3`).
2. **Eliminación de Vacíos Visuales y Scroll**:
   - Con esta distribución, no quedan espacios vacíos asimétricos y el contenido se reparte equitativamente en toda la pantalla sin generar scroll vertical innecesario en escritorio.

### Ejemplo

Al abrir Ajustes de Vista en la pestaña «General», el usuario observa arriba dos tarjetas simétricas en paralelo (Disposición a la izquierda y Mensaje de Bienvenida a la derecha) y abajo una tarjeta extendida con los tres controles de la barra lateral repartidos en tres columnas.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y [UI_GUIDE.md](../UI_GUIDE.md).

Reorganización de la Pestaña Áreas: Selector a la Izquierda con Rejilla Completa de 8 Diseños y Vista Previa Simétrica al 100% de Altura

## Módulo

Ajustes de Vista (`user-view-settings.tsx`) y Catálogo de Áreas (`tarjeta-area.tsx`)

### Regla

1. **Distribución en Dos Columnas con Selector a la Izquierda**:
   - En la pestaña «Áreas» (`tabActiva === 'areas'`), la columna izquierda (`lg:col-span-7`) alberga el selector «Diseño de Tarjetas de Área Organizativa» con 8 tipos de diseño estructurados en una cuadrícula completa de 4 filas $\times$ 2 columnas (`grid grid-cols-1 sm:grid-cols-2 gap-3`), eliminando cualquier celda vacía o desbalance visual.
   - Las 8 variantes de tarjeta de área son:
     1. `split`: Split 50/50 estilo Harvest Vase.
     2. `onda`: Onda Curva Asimétrica SVG.
     3. `directorio`: Directorio Corporativo de Equipo.
     4. `bento`: Mosaico Bento Grid con métricas.
     5. `medallon`: Medallón Insignia Central en Relieve.
     6. `estandar`: Métricas Ejecutivas DIS-102.
     7. `portada`: Portada Fotográfica de alta definición con métricas glassmórficas.
     8. `banner`: Hero Banner Fotográfico panorámico con avatar de área superpuesto.
2. **Vista Previa en Vivo a la Derecha con 100% de Altura**:
   - La columna derecha (`lg:col-span-5`) aloja la «Vista Previa en Vivo» de la tarjeta de área utilizando el 100% del alto disponible (`items-stretch` en la cuadrícula exterior y `h-full flex flex-col justify-between` en el contenedor de previsualización) para lograr simetría geométrica perfecta con el panel selector de la izquierda.
3. **Consistencia Dimensional y Eliminación de Saltos de Altura**:
   - Todas las variantes de `TarjetaArea` estandarizan su contenedor raíz con `h-full min-h-[300px] w-full flex flex-col justify-between`.
   - En la vista previa, la tarjeta se confina a un marco estable de `<div className="w-full max-w-sm h-[320px] flex flex-col">`. Ningún cambio de estilo altera las dimensiones externas de la tarjeta ni provoca que la tarjeta crezca o se encoja al conmutar entre los 8 diseños.

### Ejemplo

Al ingresar a Ajustes de Vista > pestaña «Áreas», el usuario observa a la izquierda el catálogo completo de 8 estilos distribuidos en un bloque homogéneo de 2 columnas sin huecos vacíos. A la derecha, el recuadro de previsualización ocupa exactamente el 100% del alto para igualar la altura de las 8 opciones. Al alternar entre cualquiera de los 8 estilos, la tarjeta mostrada conserva dimensiones idénticas y constantes sin saltos visuales ni redimensionamientos abruptos.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/areas/tarjeta-area.tsx](../frontend/src/components/areas/tarjeta-area.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx), [frontend/tests/components/tarjeta-area.test.tsx](../frontend/tests/components/tarjeta-area.test.tsx) y [UI_GUIDE.md](../UI_GUIDE.md).

Reorganización de la Pestaña Plataformas: Selector a la Izquierda con Paginación de 6 Elementos por Página (2 Columnas x 3 Filas) y Vista Previa en Vivo Simétrica al 100% de Altura

## Módulo

Ajustes de Vista (`user-view-settings.tsx`) y Tarjetas de Plataforma (`platform-mockup-card.tsx`)

### Regla

1. **Distribución en Dos Columnas con Selector a la Izquierda**:
   - En la pestaña «Plataformas» (`tabActiva === 'plataformas'`), la columna izquierda (`lg:col-span-7`) contiene el selector «Diseño de Tarjetas de Plataformas», mientras que la columna derecha (`lg:col-span-5`) aloja la «Vista Previa en Vivo».
2. **Paginación Simétrica de 6 Elementos por Página (2 Columnas x 3 Filas)**:
   - Para presentar los 12 estilos de diseño disponibles de forma compacta y sin desbordamiento de scroll, el selector implementa paginación estricta de 6 elementos por página (`grid grid-cols-1 sm:grid-cols-2 gap-2.5`):
     - **Página 1 (Opciones 1 a 6)**: `1. Duotono a Sangre`, `2. Foto Enmarcada`, `3. Ficha con Insignias`, `4. Split 50/50 Horizontal`, `5. Glassmorphism Neón`, `6. Editorial Suizo`.
     - **Página 2 (Opciones 7 a 12)**: `7. Diseño Estándar`, `8. Diseño Compacto`, `9. Diseño Horizontal`, `10. Portada / Cine`, `11. Hero Banner`, `12. Flotante Inmersiva`.
   - La barra de paginación inferior incluye controles accesibles con objetivos táctiles $\ge 40\text{–}48\text{px}$: botones interactivos de página «1» y «2» con estado activo diferenciado (`bg-primary text-texto-sobre-accion shadow-1`), botones «Anterior» y «Siguiente» con deshabilitación condicional en los extremos, e indicador de estado «Página X de 2 · Mostrando X–Y de 12 estilos».
3. **Simetría Vertical al 100% de Altura**:
   - La cuadrícula exterior implementa `items-stretch` y la columna de previsualización en vivo aplica `h-full flex flex-col justify-between`, asegurando que el marco de demostración a la derecha mantenga una altura equilibrada e idéntica a la del bloque selector paginado de la izquierda.
4. **Estabilidad Dimensional**:
   - La maqueta interactiva se aloja dentro de un slot protegido `<div className="w-full max-w-sm h-[320px] flex flex-col">`, manteniendo proporciones y alineaciones estables sin redimensionamientos al conmutar entre los 12 estilos.

### Ejemplo

Al acceder a Ajustes de Vista > pestaña «Plataformas», el usuario visualiza a la izquierda una cuadrícula simétrica de 6 tarjetas de diseño (2 columnas por 3 filas) con su paginador numérico al pie. A la derecha, la tarjeta interactiva de plataforma ocupa el 100% del alto disponible. Al navegar a la página 2, se despliegan de inmediato los estilos 7 a 12 con la misma estructura y altura constante.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y [UI_GUIDE.md](../UI_GUIDE.md).

Distribución en Filas Separadas para las Opciones de Elementos de la Barra Lateral

## Módulo

Ajustes de Vista (`user-view-settings.tsx`)

### Regla

1. **Opciones en Filas Independientes Apiladas**:
   - En la pestaña «General» (`tabActiva === 'general'`), el contenedor «Elementos de la Barra Lateral» distribuye sus opciones de configuración en filas horizontales independientes apiladas verticalmente (`flex flex-col gap-3`):
     - **Fila 1**: `Mostrar Sección de Documentos (Carta Responsiva)` con su interruptor toggle correspondiente.
     - **Fila 2**: `Mostrar Badges Circulares con Contadores en el Sidebar` con su interruptor toggle correspondiente.
     - **Fila 3**: `Colapsar botón de usuario (solo mostrar icono)` con su interruptor toggle correspondiente.
2. **Aprovechamiento Integral del Espacio y Eliminación de Huecos Vacíos**:
   - Cada fila cuenta con acolchado perimetral espacioso (`p-4`), tipografía legible y descripción completa sin truncamiento forzado, abarcando el 100% del ancho del contenedor.
   - Esta disposición vertical ocupa de manera armónica la altura de la pantalla, eliminando los huecos en blanco inferiores y evitando el apiñamiento horizontal.

### Ejemplo

Al acceder a Ajustes de Vista > pestaña «General», la tarjeta inferior de «Elementos de la Barra Lateral» exhibe sus tres controles en tres renglones amplios y ordenados uno debajo del otro, ocupando la altura disponible de forma proporcional y sin dejar vacíos en la parte baja del cuerpo.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y [UI_GUIDE.md](../UI_GUIDE.md).

Simetría en Cabeceras y Expansión del Contenedor de Toggle en Mensaje de Bienvenida

## Módulo

Ajustes de Vista (`user-view-settings.tsx`)

### Regla

1. **Nivelación Estricta de Cabeceras**:
   - En la primera fila de la pestaña «General» (`tabActiva === 'general'`), las cabeceras de «Disposición Principal del Portal» y «Mensaje de Bienvenida» alinean sus títulos y subtítulos con precisión milimétrica (`items-start`, `mb-3`, `text-sm font-bold` y `mt-1`), evitando que la presencia de botones de acción desplace la línea base del texto hacia abajo.
2. **Supresión del Botón Redundante de Restaurar Mensaje**:
   - Se elimina de la cabecera el botón secundario «Restaurar mensaje» / «Omitir mensaje». La activación o desactivación de la bienvenida se gestiona de forma canónica mediante el interruptor interactivo toggle. En la cabecera se conserva únicamente el botón de acción contextual «Previsualizar».
3. **Expansión y Simetría del Contenedor de Toggle**:
   - El contenedor del conmutador de bienvenida crece verticalmente (`mt-auto flex-1 flex flex-col justify-between p-3.5 rounded-xl border border-panel-border bg-superficie`), replicando la estructura de tarjeta, padding y altura de los botones de disposición de la columna izquierda.
   - Cuenta con cabecera interna con icono de información, título, botón switch accesible ($\ge 48\text{px}$) y descripción explicativa multilínea (`line-clamp-3`), garantizando simetría perfecta en altura y forma entre ambos módulos superiores.

### Ejemplo

Al ingresar a Ajustes de Vista > «General», el usuario observa que los títulos de «Disposición Principal del Portal» y «Mensaje de Bienvenida» se encuentran a la misma altura superior. A la derecha sólo aparece el botón «Previsualizar». Abajo, el recuadro del toggle de bienvenida tiene la misma altura y bordes que los botones de Sidebar y Topbar de la izquierda.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y [UI_GUIDE.md](../UI_GUIDE.md).

Estandarización de Tamaño en Botones de Pestaña (Tab Buttons) de Ajustes de Vista

## Módulo

Ajustes de Vista (`user-view-settings.tsx`)

### Regla

1. **Dimensiones Estandarizadas e Idénticas**:
   - Los botones de pestaña (`tabActiva`) en la barra de navegación superior de Ajustes de Vista («General», «Áreas», «Plataformas») deben compartir exactamente las mismas dimensiones fijas y consistentes (`h-12 min-h-12 w-36 sm:w-40 shrink-0`), impidiendo que varíen de ancho en función de la longitud del texto de cada etiqueta.
2. **Centrado Óptico y Ergonomía Táctil**:
   - Cada botón aplica centrado horizontal y vertical (`items-center justify-center`), holgura interna uniforme (`px-4 py-2`), separación entre icono y texto (`gap-2`) y radio perimetral consistente (`rounded-xl`).
   - El objetivo táctil cumple estrictamente con el sistema 8pt y la regla de modo táctil de mínimo 48px de alto (`min-h-12`).

### Ejemplo

Al abrir los Ajustes de Vista, las pestañas «General», «Áreas» y «Plataformas» se visualizan en una fila uniforme donde cada botón tiene exactamente la misma anchura (160px en escritorio / 144px en pantallas compactas) y la misma altura (48px), logrando una cadencia visual armónica y simétrica.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y [UI_GUIDE.md](../UI_GUIDE.md).

Simetría en Cabeceras y Expansión del Contenedor de Toggle en Mensaje de Bienvenida

## Módulo

Ajustes de Vista (`user-view-settings.tsx`)

### Regla

1. **Nivelación Estricta de Cabeceras**:
   - En la primera fila de la pestaña «General» (`tabActiva === 'general'`), las cabeceras de «Disposición Principal del Portal» y «Mensaje de Bienvenida» alinean sus títulos y subtítulos con precisión milimétrica (`items-start`, `mb-3`, `text-sm font-bold` y `mt-1`), evitando que la presencia de botones de acción desplace la línea base del texto hacia abajo.
2. **Supresión del Botón Redundante de Restaurar Mensaje**:
   - Se elimina de la cabecera el botón secundario «Restaurar mensaje» / «Omitir mensaje». La activación o desactivación de la bienvenida se gestiona de forma canónica mediante el interruptor interactivo toggle. En la cabecera se conserva únicamente el botón de acción contextual «Previsualizar».
3. **Expansión y Simetría del Contenedor de Toggle**:
   - El contenedor del conmutador de bienvenida crece verticalmente (`mt-auto flex-1 flex flex-col justify-between p-3.5 rounded-xl border border-panel-border bg-superficie`), replicando la estructura de tarjeta, padding y altura de los botones de disposición de la columna izquierda.
   - Cuenta con cabecera interna con icono de información, título, botón switch accesible ($\ge 48\text{px}$) y descripción explicativa multilínea (`line-clamp-3`), garantizando simetría perfecta en altura y forma entre ambos módulos superiores.

### Ejemplo

Al ingresar a Ajustes de Vista > «General», el usuario observa que los títulos de «Disposición Principal del Portal» y «Mensaje de Bienvenida» se encuentran a la misma altura superior. A la derecha sólo aparece el botón «Previsualizar». Abajo, el recuadro del toggle de bienvenida tiene la misma altura y bordes que los botones de Sidebar y Topbar de la izquierda.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y [UI_GUIDE.md](../UI_GUIDE.md).

Estandarización de Tamaño en Botones de Pestaña (Tab Buttons) de Ajustes de Vista

## Módulo

Ajustes de Vista (`user-view-settings.tsx`)

### Regla

1. **Dimensiones Estandarizadas e Idénticas**:
   - Los botones de pestaña (`tabActiva`) en la barra de navegación superior de Ajustes de Vista («General», «Áreas», «Plataformas») deben compartir exactamente las mismas dimensiones fijas y consistentes (`h-12 min-h-12 w-36 sm:w-40 shrink-0`), impidiendo que varíen de ancho en función de la longitud del texto de cada etiqueta.
2. **Centrado Óptico y Ergonomía Táctil**:
   - Cada botón aplica centrado horizontal y vertical (`items-center justify-center`), holgura interna uniforme (`px-4 py-2`), separación entre icono y texto (`gap-2`) y radio perimetral consistente (`rounded-xl`).
   - El objetivo táctil cumple estrictamente con el sistema 8pt y la regla de modo táctil de mínimo 48px de alto (`min-h-12`).

### Ejemplo

Al abrir los Ajustes de Vista, las pestañas «General», «Áreas» y «Plataformas» se visualizan en una fila uniforme donde cada botón tiene exactamente la misma anchura (160px en escritorio / 144px en pantallas compactas) y la misma altura (48px), logrando una cadencia visual armónica y simétrica.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y [UI_GUIDE.md](../UI_GUIDE.md).

Distribución 100% Responsiva de los Contenedores de Pestañas (Tab Content) en Ajustes de Vista

## Módulo

Ajustes de Vista (`user-view-settings.tsx`)

### Regla

1. **Propagación Completa de la Cadena Flex (100% Altura y Anchura)**:
   - El contenedor raíz de `UserViewSettings` y cada panel de contenido (`#panel-general`, `#panel-areas`, `#panel-plataformas`) deben aplicar `flex-1 min-h-0 h-full w-full`, ocupando el 100% del espacio vertical y horizontal disponible dentro del viewport.
2. **Distribución Responsiva sin Vacíos Muertos**:
   - En «General», la fila superior de disposición y bienvenida conserva su tamaño natural (`shrink-0`), mientras la fila de «Elementos de la Barra Lateral» se expande proporcionalmente (`flex-1 min-h-0 flex flex-col justify-between`), distribuyendo sus 3 renglones en el espacio vertical disponible para evitar zonas vacías en la parte baja.
   - En «Áreas» y «Plataformas», la columna izquierda del catálogo de estilos (`lg:col-span-7`) y la columna derecha de previsualización en vivo (`lg:col-span-5`) crecen simultáneamente al 100% de la altura (`h-full min-h-0`). La cuadrícula de opciones distribuye sus filas verticalmente (`flex-1 content-between my-auto`) y el marco de previsualización se expande (`flex-1 min-h-[320px]`) manteniendo la maqueta centrada ópticamente y los controles de paginación o notas firmemente anclados al fondo.
3. **Adaptabilidad Fluida**:
   - En pantallas compactas o móviles, los contenedores mantienen su flujo apilado natural sin recortes de texto ni desbordamientos indeseados.

### Ejemplo

Al alternar entre «General», «Áreas» y «Plataformas», tanto las tarjetas de configuración como los marcos de vista previa se extienden armoniosamente hasta la base del contenedor visible en el navegador, aprovechando el 100% de la pantalla de forma responsiva.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y [UI_GUIDE.md](../UI_GUIDE.md).

Paginación Compacta Exclusiva con Botones Chevron (< >) en Catálogo de Tarjetas de Plataformas

## Módulo

Ajustes de Vista (`user-view-settings.tsx`)

### Regla

1. **Control Compacto de Paginación (< >)**:
   - En la pestaña «Plataformas», la navegación entre páginas de estilos prescinde de contadores textuales (`Página 1 de 2`), indicadores de fracción (`1/5`) y botones numéricos (`1`, `2`).
   - Se implementa una cápsula compacta (`inline-flex items-center rounded-xl border border-panel-border bg-superficie p-1 shadow-xs`) ubicada al pie derecho de la columna de opciones (`lg:col-span-7`), conteniendo exclusivamente dos botones con iconos chevron:
     - Botón anterior: `<` con `aria-label="Página anterior"`, deshabilitado visualmente (`text-label/30 cursor-not-allowed`) en la página 1.
     - Botón siguiente: `>` con `aria-label="Página siguiente"`, deshabilitado en la última página.
2. **Preservación Estricta de la Estructura Bicolumna**:
   - La barra de paginación se ubica estrictamente dentro del contenedor izquierdo (`lg:col-span-7`), anclada al pie (`mt-auto pt-3 border-t`), garantizando que la cuadrícula conserve sus 2 columnas maestras (`lg:col-span-7` y `lg:col-span-5`) sin desfasar ni superponer la columna de vista previa.

### Ejemplo

Al acceder a Ajustes de Vista > «Plataformas», el usuario visualiza los 6 estilos de tarjeta a la izquierda y la maqueta en vivo a la derecha. Al pie derecho del panel de estilos se presenta una pequeña cápsula redondeada con únicamente las flechas `<` y `>` para alternar entre los estilos 1-6 y 7-12 sin ruido visual.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx) y [UI_GUIDE.md](../UI_GUIDE.md).

Simetría Geométrica y Adaptabilidad Bicolumna en Ajustes de Vista de Portal

## Módulo

Ajustes de Vista del Portal (`user-view-settings.tsx`)

### Regla

1. **Puntos de Quiebre Responsivos para Cuadrícula Bicolumna (`md:grid-cols-12`)**:
   - En las pestañas «Áreas» y «Plataformas», la cuadrícula principal adopta `grid-cols-1 md:grid-cols-12 gap-4 lg:gap-5 items-stretch`, asignando `md:col-span-7` para el panel selector de estilos y `md:col-span-5` para el panel de previsualización en vivo.
   - Previene el colapso a una sola columna en pantallas y ventanas de ancho medio ($\approx 768\text{px}$ a $1024\text{px}$), garantizando que las opciones y la vista previa permanezcan lado a lado en 2 columnas ocupando el 100% del contenedor visible.
2. **Estandarización Absoluta de Botones de Opciones y Vistas Previas Miniatura**:
   - Todas las tarjetas de selección (tanto las 12 opciones de Plataformas como las 8 opciones de Áreas) implementan:
     - Cuadrícula con filas equitativas: `grid grid-cols-1 sm:grid-cols-2 gap-3 flex-1 auto-rows-fr my-auto`.
     - Altura unificada en botones: `h-full min-h-[148px] p-3.5 rounded-xl border flex flex-col justify-between`.
     - Área de descripción homogénea: `line-clamp-2 h-8 mb-2 shrink-0`, garantizando que textos de 1 o 2 líneas consuman exactamente el mismo espacio vertical.
     - Contenedores de vista previa miniatura idénticos: altura fija obligatoria `h-10 w-full rounded-lg ... mt-auto shrink-0 shadow-2xs`, evitando que estilos fotográficos crezcan desproporcionadamente o estilos minimalistas se encojan, logrando una simetría visual del 100%.
3. **Estabilidad de la Maqueta en Vivo**:
   - El marco de previsualización en vivo derecho utiliza `min-h-[300px] h-full` con centrado vertical `max-w-sm max-h-[340px]`, impidiendo desplazamientos o variaciones de tamaño de contenedor al alternar entre variantes.

### Ejemplo

En cualquier resolución $\ge 768\text{px}$, el usuario observa en «Plataformas» 6 tarjetas de selección exactamente idénticas en tamaño (2 columnas x 3 filas) con sus miniaturas estilizadas en cajas uniformes de 40px de alto (`h-10`), junto al contenedor de maqueta en vivo a la derecha, sin desbordes verticales ni huecos asimétricos.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx) y [UI_GUIDE.md](../UI_GUIDE.md).

## Supresión de Descripciones Técnicas en Selectores de Diseño de Tarjetas

### Regla

En el panel de ajustes de vista del portal (`UserViewSettings`), los botones selectores de variantes visuales para tarjetas de Áreas (8 opciones) y Plataformas (12 opciones) suprimen cualquier párrafo descriptivo con terminología técnica o conceptos de diseño complejos (como "Harvest Vase", "halo brillante", "vidrio translúcido", etc.). Cada botón selector presenta exclusivamente:

1. **Cabecera limpia**: Número ordinal y nombre directo del estilo junto con el indicador circular accesible de selección (`✓`).
2. **Miniatura gráfica normalizada**: Recuadro de vista previa con altura obligatoria de 40 px (`h-10 w-full rounded-lg`) que exhibe la maqueta geométrica del diseño.

Esta simplificación optimiza la altura de los botones a 96 px (`min-h-[96px]`), permitiendo una cuadrícula compacta, perfectamente simétrica y de rápida comprensión para cualquier perfil de usuario. La accesibilidad para tecnologías de asistencia y lectores de pantalla se preserva intacta mediante el atributo `aria-label` detallado en cada elemento con `role="radio"`.

### Ejemplo

Al ingresar a la pestaña «Áreas» o «Plataformas» en Ajustes de Vista, el usuario observa una cuadrícula limpia donde cada tarjeta contiene únicamente su título (ej. "1. Split 50/50", "2. Onda Curva SVG") y su miniatura geométrica en un bloque equilibrado de 96 px de altura, visualizando el resultado en tiempo real en la maqueta interactiva contigua.

### Impacto

Afecta a [user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas automatizadas en [platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Cuadrícula Simétrica de 10 Estilos de Tarjetas sin Paginación en Ajustes de Vista

### Regla

En el panel de configuración de vista del portal (`UserViewSettings`), tanto la pestaña de «Áreas» como la de «Plataformas» adoptan una estructura simétrica unificada consistente en una cuadrícula fija de 10 variantes de diseño organizadas en 2 columnas por 5 filas (`grid grid-cols-1 sm:grid-cols-2 gap-3 flex-1 auto-rows-fr my-auto`):

1. **Áreas Organizativas (10 Opciones)**:
   - Se incorporan dos nuevas variantes de alta gama visual a la colección existente: «9. Glassmorphism Neón» (`glass`) y «10. Flotante Inmersiva» (`flotante`), sumándose a las 8 opciones previas (`split`, `onda`, `directorio`, `bento`, `medallon`, `estandar`, `portada`, `banner`).
   - El componente canónico [tarjeta-area.tsx](../frontend/src/components/areas/tarjeta-area.tsx) implementa el renderizado completo y responsivo para ambas variantes en previsualización en vivo y catálogo departamental.
2. **Plataformas (10 Opciones sin Paginación)**:
   - Se suprime la barra y estado de paginación (`paginaCards`), renderizando de forma directa las 10 opciones principales (`duotono`, `enmarcada`, `split`, `glass`, `editorial`, `estandar`, `compacta`, `horizontal`, `banner`, `flotante`).
   - Todos los estilos son accesibles al instante sin necesidad de conmutar de página, logrando simetría geométrica 1:1 entre Áreas y Plataformas con altura mínima compacta de 96 px (`min-h-[96px]`) y cajas miniatura estandarizadas de 40 px (`h-10 w-full rounded-lg`).

### Ejemplo

Al alternar entre «Áreas» y «Plataformas» en los botones de pestaña de Ajustes de Vista, el usuario observa en ambos paneles exactamente 10 tarjetas de selección distribuidas en una cuadrícula de 2 columnas por 5 filas, con previsualizaciones gráficas compactas y la maqueta interactiva contigua a la derecha, sin saltos de tamaño, asimetrías ni controles de paginación accesorios.

### Impacto

Afecta a [user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [tarjeta-area.tsx](../frontend/src/components/areas/tarjeta-area.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Simetría e Igualdad de Altura en Contenedores de Fila Superior en Ajustes de Vista (General)

### Regla

En la pestaña «General» de Ajustes de Vista del Portal (`UserViewSettings`), los dos contenedores principales de la primera fila («Disposición Principal del Portal» y «Mensaje de Bienvenida») y sus subcontenedores interactivos internos mantienen una altura estrictamente idéntica y simétrica:

1. **Nivelación de Cabeceras**: Ambas cabeceras implementan `min-h-[46px] mb-3 shrink-0 flex items-start justify-between gap-3`, compensando la presencia del botón secundario «Previsualizar» en la columna derecha para que el origen vertical de las cajas inferiores coincida exactamente.
2. **Subcontenedores con `flex-1 h-full`**:
   - En la columna izquierda («Disposición Principal»), el grid contenedor adopta `flex-1 auto-rows-fr` y cada botón de layout («Vista Barra Lateral» y «Vista Barra Superior») porta `h-full min-h-[96px] flex flex-col justify-between p-3.5`.
   - En la columna derecha («Mensaje de Bienvenida»), el recuadro del conmutador toggle implementa `flex-1 h-full flex flex-col justify-between p-3.5 rounded-xl border`.
3. Esto garantiza que la tarjeta del toggle de mensaje de bienvenida y los dos botones de selección de disposición posean exactamente la misma altura física en pantalla, eliminando escalonamientos o discrepancias visuales.

### Ejemplo

Al acceder a `Ajustes de Vista > General`, el usuario visualiza en la fila superior dos bloques principales de igual altura donde los botones de «Vista Barra Lateral (Sidebar)» y «Vista Barra Superior (Topbar)» a la izquierda tienen la misma altura matemática que el recuadro de «Mostrar mensaje de bienvenida al entrar» a la derecha.

### Impacto

Afecta a [user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas de interfaz en [platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Iconografía de Diseño en Selectores de Variantes Visuales

### Regla

En el panel de ajustes de vista del portal (`UserViewSettings`), los botones selectores de variantes de diseño para tarjetas de Áreas (10 opciones) y Plataformas (10 opciones) suprimen los prefijos numéricos ordinales (`1.`, `2.`, ..., `10.`) y los sustituyen de forma estandarizada por el icono canónico de diseño (`Icono nombre="diseno" tamano="xs"`):

1. **Neutralidad y Ausencia de Sesgo Jerárquico**: La numeración artificial induce a concebir las opciones como una secuencia cronológica, jerarquía de calidad o flujo por pasos. La sustitución por el icono semántico de diseño valida que todas las tarjetas son opciones de catálogo visual equivalentes y paralelas.
2. **Presencia Visual y Anclaje Estético**: Cada botón selector presenta un encabezado equilibrado compuesto por:
   - Icono `diseno` teñido con el acento de la marca (`text-primary-text shrink-0`).
   - Título tipográfico limpio y descriptivo de la variante (ej. `Split 50/50`, `Onda Curva SVG`, `Duotono a Sangre`, `Glassmorphism Neón`, etc.).
   - Indicador de estado circular accesible (`✓` cuando está seleccionado).
3. **Escalabilidad**: Permite reordenar, filtrar o incorporar futuras variantes estilísticas sin desfasar numeraciones ni alterar las aserciones de accesibilidad (`aria-label`).

### Ejemplo

Al visualizar la pestaña «Áreas» o «Plataformas» en Ajustes de Vista, el usuario ya no observa "1. Split 50/50" o "10. Flotante Inmersiva", sino una cuadrícula con un icono de paleta de diseño estilizado contiguo al nombre de cada estilo, aportando identidad de diseño y empaque gráfico profesional.

### Impacto

Afecta a [frontend/src/components/platforms/user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [frontend/src/components/icono-trazos.ts](../frontend/src/components/icono-trazos.ts), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [frontend/tests/components/icono.test.tsx](../frontend/tests/components/icono.test.tsx) y [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Location Bar Dinámico y Jerarquía Estricta de 2 Niveles en el Portal de Plataformas

### Regla

En el portal de plataformas (`PlatformsTopbar` y `PlatformsSidebarView`), la barra de ubicación o migas de pan (Location Bar) estandariza una jerarquía limpia donde la raíz única es siempre `Catálogo`, suprimiendo de forma permanente el prefijo redundante `General >` para todos los roles (incluyendo administradores):

1. **Supresión del prefijo `General >`**: Ninguna vista dentro del portal antepone "General". Las rutas secundarias tienen un máximo estricto de 2 niveles:
   - Ajustes de Vista: `Catálogo > Ajustes de Vista` (exactamente 2 niveles, nunca 3).
   - Mis Solicitudes: `Catálogo > Mis Solicitudes`.
   - Carta Responsiva: `Catálogo > Carta Responsiva`.
   - Mi Widget: `Catálogo > Mi Widget`.
2. **Navegación Dinámica Reactiva en el Catálogo**:
   - Vista de Áreas: Cuando se visualiza la cuadrícula de áreas organizativas o la sección de áreas sin selección activa, el Location Bar muestra `Catálogo > Áreas`.
   - Área Específica: Cuando el usuario selecciona un área determinada (por pastilla o menú lateral), el Location Bar muestra `Catálogo > [Nombre del Área]`.
   - Favoritos: Al activar el filtro o pestaña de favoritas, el Location Bar muestra `Catálogo > Favoritos`.
   - Raíz del Catálogo: Al visualizar todas las plataformas sin filtros, muestra simplemente `Catálogo`.
3. **Interactividad y Retorno**: El primer segmento `Catálogo` actúa como disparador accesible (`button` con foco visible `focus-visible:ring-2 focus-visible:ring-primary` o `Link`). Al hacer clic en `Catálogo`, el portal restablece el estado de filtros a la raíz sin recargar la página. El separador entre segmentos utiliza el icono canónico `<Icono nombre="chevron-der" tamano="xs" />` (`>`).

### Ejemplo

Al estar en el modo Launchpad y hacer clic en la pastilla "Favoritas", la barra superior actualiza de inmediato su ruta a `Catálogo > Favoritos`. Si el usuario hace clic en el área "Tecnología & TI", la ruta pasa a `Catálogo > Tecnología & TI`. Al abrir el panel de personalización desde el engrane, se visualiza `Catálogo > Ajustes de Vista`. Al pulsar sobre `Catálogo` en cualquiera de estas pantallas, el usuario regresa instantáneamente a la vista principal del catálogo.

### Impacto

Afecta a [platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [platforms-launchpad-view.tsx](../frontend/src/components/platforms/platforms-launchpad-view.tsx), [platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y [platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Visibilidad Condicional del Buscador en Barra Superior (PlatformsTopbar)

### Regla

En la barra superior del portal de accesos (`PlatformsTopbar`), el buscador central de plataformas (`<input type="search" placeholder="Buscar plataforma..." />` con atajo `⌘K`) se renderiza **únicamente** cuando el usuario se encuentra navegando activamente en el catálogo de plataformas (`seccionActiva === 'catalogo'` o por defecto):

1. **Ocultamiento en Secciones Ajenas**: Cuando el usuario ingresa a cualquier otra sección del portal que no presente el catálogo de herramientas (por ejemplo: `personalizacion` / Ajustes de Vista, `responsiva` / Carta Responsiva, `widget` / Mi Widget, o rutas secundarias como `esSolicitudes` / `/requests`), el buscador se oculta completamente de la interfaz.
2. **Preservación del Espaciado y Balance Flex**: Al ocultarse el buscador, la barra superior renderiza un espaciador flexible vacío (`<div className="flex-1" />`), garantizando que la alineación entre la identidad/ruta de navegación a la izquierda y los botones de acción rápida/perfil a la derecha se mantenga simétrica e idéntica.
3. **Desactivación del Atajo de Teclado**: El escuchador del atajo `⌘K` / `Ctrl+K` valida activamente la visibilidad del buscador (`if (!mostrarBuscador) return;`), evitando la intercepción no deseada de combinaciones de teclas o llamadas a métodos de foco sobre elementos desmontados del DOM.

### Ejemplo

Un usuario se encuentra en el catálogo de plataformas y utiliza el buscador o presiona `⌘K` para filtrar herramientas en tiempo real. Al hacer clic en el engrane de «Ajustes de Vista» o en «Carta Responsiva», el buscador desaparece de la cabecera superior ya que en dichas vistas no hay listado de plataformas que filtrar, evitando confusión y clics infructuosos. Al regresar a «Catálogo» o «Plataformas», el buscador reaparece de inmediato.

### Impacto

Afecta a [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [frontend/src/app/requests/page.tsx](../frontend/src/app/requests/page.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas unitarias en [frontend/tests/components/platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Preservación del Diseño Limpio de URLs en Navegación y Location Bar del Portal

### Regla

El portal de plataformas (`PlatformsShell`, `PlatformsTopbar`, `PlatformsSidebarView`) garantiza de manera estricta el diseño limpio de URLs (Clean URLs / Pretty URLs) en todas las transiciones de sección y clics sobre la barra de ubicación (Location Bar):

1. **Supresión de Parámetros Query**: Ningún enlace interno ni botón de navegación hacia o dentro del portal genera URLs sucias con cadenas de consulta tales como `?seccion=widget` o `?seccion=responsiva`. Los enlaces dirigen exclusivamente a la ruta base limpia `/platforms`.
2. **Transferencia de Estado Desacoplada de la URL**: Cuando una sección secundaria debe abrirse tras una navegación externa (por ejemplo, desde `/requests`), la intención se comunica mediante almacenamiento de sesión efímero (`sessionStorage.setItem('nexus.platforms.seccion_inicial', seccion)`), el cual se consume e invalida de inmediato al montar la vista sin contaminar la barra de direcciones del navegador.
3. **Limpieza Reactiva Inmediata en el Location Bar y Transiciones de Sección**:
   - Al hacer clic en «Catálogo» o cualquier segmento interactivo del Location Bar (`PlatformsTopbar`, `PlatformsSidebarView`), el manejador ejecuta una purga activa de parámetros (`window.history.replaceState(null, '', window.location.pathname)`).
   - En el cascarón principal (`PlatformsShell`), ante cualquier cambio de `seccionActiva` o carga inicial con parámetros heredados en URL, el sistema normaliza la barra de direcciones a la ruta limpia `/platforms`.

### Ejemplo

Un usuario se encuentra configurando «Mi Widget» o visualizando «Carta Responsiva» y pulsa «Catálogo» en la barra de ubicación (Location Bar). El portal actualiza de inmediato el contenido al catálogo de plataformas y garantiza que la barra de direcciones del navegador permanezca como `http://localhost:3000/platforms`, eliminando permanentemente parámetros residuales como `?seccion=widget`.

### Impacto

Afecta a [platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx), [platforms-shell.tsx](../frontend/src/components/platforms/platforms-shell.tsx), [platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a la suite de pruebas en [platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Encabezados Diferenciados en Paneles de Configuración General (Ajustes de Vista)

### Regla

En la pestaña «General» del panel de ajustes de vista (`UserViewSettings`), los tres contenedores principales («Disposición Principal del Portal», «Mensaje de Bienvenida» y «Elementos de la Barra Lateral») estructuran una clara separación arquitectónica entre su cabecera (header) y su cuerpo (body):

1. **Diferenciación Cromática de la Cabecera**: Cada panel cuenta con una cabecera delimitada que utiliza el token semántico de superficie hundida/elevada (`bg-surface-container`), separada del cuerpo mediante un borde inferior nítido (`border-b border-panel-border`).
2. **Jerarquía y Peso Visual**: El título del encabezado (`h4`) se presenta con tipografía destacada (`text-sm font-bold text-body-text`), acompañado por el icono temático (`text-primary-text`) y subtítulo descriptivo (`text-xs text-label mt-1`), estableciendo una identidad visual sólida frente a las opciones interactivas inferiores.
3. **Contención y Simetría**: El contenedor exterior del panel aplica `rounded-2xl border border-panel-border bg-panel-fill shadow-1 overflow-hidden`, garantizando que la franja de la cabecera quede recortada en las esquinas superiores sin alterar la simetría de altura (`items-stretch`, `min-h-[64px]`) entre los paneles de la primera fila.

### Ejemplo

Al acceder a Ajustes de Vista > pestaña «General», el usuario distingue de inmediato una franja de cabecera grisácea/contrastada en la parte superior de cada tarjeta («Disposición Principal del Portal», «Mensaje de Bienvenida» y «Elementos de la Barra Lateral»), lo cual separa con nitidez los títulos descriptivos del área blanca interactiva inferior donde residen los conmutadores e interruptores.

### Impacto

Afecta a [user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas de integración en [platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Disponibilidad Condicional de Opciones de Navegación según el Modo de Layout en Ajustes de Vista

### Regla

En la pestaña «General» del panel de ajustes de vista (`UserViewSettings`), las opciones de configuración asociadas a elementos específicos de interfaz se habilitan o deshabilitan dinámicamente según la disposición (`layout`) activa del portal (`topbar` vs `sidebar`):

1. **Colapsar Botón de Usuario (Solo Icono)**:
   - **Activa en `layout === 'topbar'`**: Esta opción modifica la anchura del botón de usuario exclusivamente en la barra superior.
   - **Deshabilitada en `layout === 'sidebar'`**: Cuando el usuario selecciona la vista con Barra Lateral, la opción se deshabilita visual y funcionalmente (`disabled`, `aria-disabled="true"`, opacidad reducida `opacity-60 cursor-not-allowed` y badge explicativo `Solo en Topbar`). El clic queda inhabilitado para evitar confusiones, indicando que en modo sidebar el usuario cuenta con su botón persistente en la parte inferior del menú lateral.
2. **Mostrar Badges Circulares con Contadores en el Sidebar**:
   - **Activa en `layout === 'sidebar'`**: Habilita la exhibición de pastillas numéricas simétricas en las categorías del menú lateral.
   - **Deshabilitada en `layout === 'topbar'`**: Cuando el usuario selecciona la vista con Barra Superior, la opción se deshabilita (`disabled`, `aria-disabled="true"`, opacidad `opacity-60 cursor-not-allowed` y badge `Solo en Sidebar`), ya que en modo Topbar no existe un árbol vertical de navegación que aloje dichos contadores.
3. **Preservación del Estado Subyacente**: El valor guardado de cada preferencia (`mostrarBadgesSidebar` y `botonUsuarioCompacto`) se preserva sin sobreescribirse ni resetearse; si el usuario conmuta nuevamente el layout, la opción se reactiva inmediatamente reflejando su estado configurado previo.

### Ejemplo

Un colaborador selecciona «Vista Barra Lateral (Sidebar)». Inmediatamente, en la sección «Elementos de la Barra Lateral», el conmutador de «Colapsar botón de usuario» se atenúa y muestra la insignia «Solo en Topbar», impidiendo su clic. Si el colaborador conmuta a «Vista Barra Superior (Topbar)», «Colapsar botón de usuario» se vuelve interactivo y en cambio «Mostrar Badges Circulares con Contadores en el Sidebar» se deshabilita mostrando «Solo en Sidebar».

### Impacto

Afecta a [user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas unitarias en [platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Identificación de Áreas en Location Bar de Administración de Plataformas

### Regla

En la vista de administración de plataformas (`/admin/platforms`), la primera entrada visual del catálogo corresponde a la lista de áreas organizativas:

1. **Identificación Jerárquica Inicial**: La barra de localización (`RutaNavegacion` en `BarraSuperior`) exhibe la ruta canónica `Gestión › Plataformas › Áreas`, identificando explícitamente que el usuario se encuentra visualizando el catálogo de áreas y no directamente una lista plana de plataformas individuales.
2. **Navegación al Seleccionar un Área**: Cuando el administrador selecciona un área específica (ej. «Finanzas»), la barra actualiza a `Gestión › Plataformas › Áreas › [Nombre Área]`. Tanto el segmento «Plataformas» como el segmento «Áreas» funcionan como enlaces interactivos que al pulsarse limpian la selección del área y retornan de inmediato al catálogo de todas las áreas sin parámetros sucios en la URL.

### Ejemplo

Al acceder a `/admin/platforms`, el location bar superior muestra `Gestión › Plataformas › Áreas`. Si el administrador pulsa en la tarjeta de «Demo Infraestructura», la ruta pasa a ser `Gestión › Plataformas › Áreas › Demo Infraestructura`. Al pulsar sobre «Áreas» o «Plataformas», se regresa a la cuadrícula de áreas y el location bar vuelve a `Gestión › Plataformas › Áreas`.

### Impacto

Afecta a [ruta-navegacion.tsx](../frontend/src/components/marco/ruta-navegacion.tsx), [barra-superior.tsx](../frontend/src/components/marco/barra-superior.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [marco-admin.test.tsx](../frontend/tests/components/marco-admin.test.tsx).

## Botón y Panel Lateral de Selección de Diseño de Tarjetas de Área en Plataformas

### Regla

En la barra de herramientas principal de administración de plataformas (`PlatformAdmin`), se ubica un control dedicado para personalizar el aspecto visual de las tarjetas departamentales:

1. **Ubicación y Estilo del Botón**: Se posiciona inmediatamente a la izquierda del selector de estado («Estado: Todos») bajo la denominación «Diseño», con icono vectorial `diseno`, altura unificada de 48 px (`h-12 min-h-12`) y estilo simétrico con los demás controles de la toolbar.
2. **Despliegue Lateral (Drawer)**: Al pulsar el botón «Diseño», se abre un popup lateral emergente desde la derecha (`Drawer`, ancho responsivo hasta 620 px), con captura de foco accesible, cierre con Escape o clic fuera y devolución del foco al botón disparador (`devolverA`).
3. **Contenido Exclusivo de Tarjetas de Área**: El panel despliega únicamente la configuración de tarjetas de área organizativa:
   - Cabecera descriptiva con título e instrucciones.
   - Previsualización en vivo (`TarjetaArea`) que refleja reactivamente la variante activa con el distintivo del diseño.
   - Cuadrícula con las 10 opciones de diseño departamental (`split`, `onda`, `directorio`, `bento`, `medallon`, `estandar`, `portada`, `banner`, `glass`, `flotante`), con sus miniaturas mockup exactas y botones de opción accesibles (`role="radio"`).
4. **Persistencia y Actualización en Tiempo Real**: Al seleccionar cualquier variante, la preferencia se almacena en `localStorage` bajo la clave `nexus.platforms.area_card_design` y se actualiza de inmediato tanto la previsualización del panel como la cuadrícula de áreas del catálogo que se encuentra de fondo, notificando con un toast confirmatorio.

### Ejemplo

Un administrador de plataformas hace clic en el botón «Diseño» situado a la izquierda del filtro de estado. Se abre el panel lateral desde la derecha mostrando la vista previa y los 10 estilos. Al seleccionar «Onda Curva SVG», la previsualización superior y todas las tarjetas de área visibles en la pantalla cambian de forma instantánea al estilo orgánico con cabecera curva y degradado, quedando la preferencia guardada en el navegador.

### Impacto

Afecta a [platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [area-card-design-drawer.tsx](../frontend/src/components/platforms/area-card-design-drawer.tsx), [user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las suites de pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Simetría Dimensional en los Tres Controles de la Barra de Herramientas de Plataformas

### Regla

En la barra de herramientas principal de administración de plataformas (`PlatformAdmin`), los tres botones de control interactivo agrupados a la derecha («Diseño», «Estado» y «Cuadrícula») mantienen una simetría dimensional rigurosa e idéntica:

1. **Ancho y Alto Uniforme**: Cada uno de los tres botones aplica exactamente `w-48 min-w-48 h-12 min-h-12` (192 px de ancho por 48 px de alto táctil mínimo), eliminando cualquier desproporción visual entre botones con texto corto («Diseño») y selectores con opciones («Estado» y «Cuadrícula»).
2. **Estructura Flex Justificada**: Los tres controles implementan `inline-flex items-center justify-between gap-2 rounded-xl border px-3.5 text-xs font-semibold shadow-xs`:
   - Lado izquierdo: Icono contextual temático (`tamano="sm"` text-primary-text) junto con la etiqueta textual descriptiva («Diseño», «Estado: [filtro]», «Cuadrícula: [F]×[C]»).
   - Lado derecho: Indicador vectorial (`chevron-der` para el cajón lateral de diseño, `chevron-abajo` para los desplegables de estado y cuadrícula).
3. **Comportamiento en Estado Activo**: Al abrirse el cajón lateral o cualquiera de los menús desplegables, el botón respectivo aplica de forma homogénea `border-primary bg-primary/10 text-primary-text ring-2 ring-primary/20 shadow-1`.

### Ejemplo

Un administrador visualiza la barra de herramientas superior en `/admin/platforms`: a la izquierda se ubica el buscador de áreas, y a la derecha se alinean tres botones con el mismo ancho exacto de 192 px y altura de 48 px: «Diseño >», «Estado: Todos v» y «Cuadrícula: 2×2 v».

### Impacto

Afecta a [platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Cabecera Contrastada y Optimización Espacial en el Drawer de Diseño de Áreas

### Regla

En el cajón lateral de diseño de tarjetas de área (`AreaCardDesignDrawer`), la estructura visual prioriza la claridad jerárquica y la eficiencia de espacio vertical sin sobrecarga cognitiva ni scroll innecesario:

1. **Diferenciación Cromática de Cabecera**: La franja superior del cajón utiliza el token de fondo hundido/elevado (`bg-surface-container`) delimitada por un borde inferior nítido (`border-b border-panel-border`). Despliega el título con icono temático `diseno` y subtítulo descriptivo, identificando con total peso visual la sección del encabezado frente al cuerpo interactivo.
2. **Botón Único de Cierre con Icono X**: Se suprime el botón de texto «CERRAR» y se reemplaza por un botón de acción rápida con icono vectorial `X` (`cerrar`), tamaño simétrico de 40 px (`size-10 min-h-10 min-w-10 rounded-xl border border-panel-border bg-superficie`), accesible mediante `aria-label="Cerrar"` y foco visible.
3. **Eliminación de Vista Previa Redundante y Supresión de Scroll**: Se retira el recuadro estático de previsualización interna en vivo, dado que la tarjeta real en la pantalla del catálogo se transforma en tiempo real inmediatamente al pulsar cualquier opción. Esto permite que las 10 opciones de diseño queden visibles a simple vista sin forzar al usuario a desplazarse verticalmente.
4. **Eliminación del Botón Redundante «Listo»**: Al existir el botón de cierre con icono `X` en la cabecera y el soporte nativo para cerrar con tecla `Escape` o clic en el velo de fondo, se descarta el botón duplicado «Listo» en el pie del panel.

### Ejemplo

Un administrador pulsa «Diseño» en `/admin/platforms`. Se despliega el panel lateral con una cabecera sombreada y delimitada con un botón `X` a la derecha. Inmediatamente debajo se muestran las 10 opciones en cuadrícula de dos columnas sin requerir desplazamiento. Al pulsar «Onda Curva SVG», las tarjetas en la página de fondo cambian instantáneamente al diseño elegido; al pulsar la `X`, el panel se cierra.

### Impacto

Afecta a [area-card-design-drawer.tsx](../frontend/src/components/platforms/area-card-design-drawer.tsx), [drawer.tsx](../frontend/src/components/drawer.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

## Forzar Diseño Institucional de Tarjetas y Desactivación en Configuración de Vista

### Regla

1. **Control Administrativo de Forzado de Diseño (`AreaCardDesignDrawer`)**:
   - En el panel lateral emergente de diseño de tarjetas de área (`AreaCardDesignDrawer`), se incluye un conmutador de palanca accesible (`role="switch"`, `id="toggle-forzar-diseno-area"`, `aria-checked`, persistencia en `nexus.platforms.force_area_card_design`) etiquetado como «Forzar diseño en todo el portal».
   - Al estar activo, fija el diseño corporativo elegido para todas las tarjetas de área e inhabilita las opciones de personalización individual en el portal de usuarios.
2. **Pie de Panel Lateral Bipolar (Cerrar a la Izquierda, Reestablecer a la Derecha)**:
   - En la parte inferior del panel lateral (`Drawer`), se ubica un contenedor de pie fijo (`footer`) con token de fondo contrastado (`bg-surface-container border-t border-panel-border`) y dos botones accesibles de 48 px de altura táctil (`h-12 min-h-12`):
     - **Cerrar** (a la izquierda): Cierra el panel lateral sin alterar las configuraciones seleccionadas.
     - **Reestablecer** (a la derecha): Restaura inmediatamente el diseño de tarjetas al estilo por defecto institucional (`'estandar'` - Métricas Ejecutivas) y desactiva el forzado de diseño (`forzarDiseno = false`), desbloqueando la personalización.
3. **Inhabilitación y Bloqueo en Configuración de Vista del Portal (`UserViewSettings`)**:
   - Cuando el administrador activa el forzado de diseño de área (o plataforma):
     - Las opciones de selección en la pestaña correspondiente de `UserViewSettings` se desactivan en su totalidad (`disabled`, `aria-disabled="true"`, clase visual `opacity-60 cursor-not-allowed border-panel-border bg-surface-container/50`).
     - Se muestra un distintivo en la cabecera «Bloqueado por Admin» con icono de protección (`escudo`) junto con una alerta informativa accesible (`role="alert"`) que notifica al usuario que el diseño fue fijado por el administrador y que la personalización individual está temporalmente inhabilitada.

### Ejemplo

Un administrador abre el panel «Diseño» en la gestión de plataformas, selecciona «Mosaico Bento Grid» y activa el interruptor «Forzar diseño en todo el portal». Cuando cualquier usuario visita el Portal y accede a «Ajustes de Vista › Áreas», encuentra las 10 opciones atenuadas y bloqueadas con una pastilla «Bloqueado por Admin», impidiendo que se sobreescriba el diseño corporativo. Cuando el administrador pulsa «Reestablecer» en el pie del panel, el diseño vuelve automáticamente a «Métricas Ejecutivas» y las opciones del portal vuelven a estar activas y seleccionables.

### Impacto

Afecta a [area-card-design-drawer.tsx](../frontend/src/components/platforms/area-card-design-drawer.tsx), [user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [drawer.tsx](../frontend/src/components/drawer.tsx), [platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las suites de pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx) y [platforms-shell.test.tsx](../frontend/tests/components/platforms-shell.test.tsx).

## Diferenciación Semántica de Iconografía en el Drawer de Diseño

### Regla

En el cajón lateral de configuración de diseño de tarjetas de área (`AreaCardDesignDrawer`), se establece una distinción iconográfica clara entre los distintos niveles jerárquicos para evitar la repetición del mismo glifo en elementos con diferentes propósitos semánticos:

1. **Cabecera Principal**: Conserva el icono de paleta artística (`diseno`, `tamano="sm"`), representando la funcionalidad general de personalización y estilo visual corporativo.
2. **Encabezado de Sección («Variantes de Diseño Disponibles»)**: Adopta el icono de retícula/mosaico (`panel`, `tamano="xs"`), representando una colección o catálogo de plantillas modulares y cuadrículas disponibles.
3. **Botones de Tarjetas Individuales**: Conservan el icono indicador de diseño (`diseno`, `tamano="xs"`), marcando cada alternativa específica seleccionable dentro del grupo de opciones.

### Ejemplo

Al abrir el panel «Diseño» en la gestión de plataformas, el usuario observa el icono de paleta en el título superior «Diseño de Tarjetas de Área», mientras que el subtítulo «VARIANTES DE DISEÑO DISPONIBLES» exhibe el icono de cuadrícula de 4 recuadros (`panel`). Esto genera una jerarquía visual limpia y sin redundancia iconográfica.

### Impacto

Afecta a [area-card-design-drawer.tsx](../frontend/src/components/platforms/area-card-design-drawer.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

Depuración Visual del Toolbar y Simplificación de Ruta en Plataformas

## Plataformas

### Regla

1. **Supresión del Badge Redundante de Área en la Barra de Herramientas**: En la vista de administración de plataformas de un área activa (`/admin/platforms`), se elimina la pastilla/badge repetida que mostraba el nombre del área inmediatamente a la derecha del campo de búsqueda de plataformas. El contexto del área ya está presente en el marcador de posición del buscador («Buscar plataformas en [Área]...») y en la barra de localización superior.
2. **Simplificación de la Barra de Navegación de Ruta (Location Bar)**: Al ingresar a un área específica dentro de `/admin/platforms`, la miga de pan suprime el segmento intermedio redundante «Áreas», desplegando directamente la jerarquía concisa: `Gestión › Plataformas › [Nombre del Área]`.
   - Cuando no hay ningún área seleccionada (catálogo general de áreas en `/admin/platforms`), la ruta muestra `Gestión › Plataformas › Áreas`.
   - Al pulsar sobre el enlace interactivo «Plataformas» dentro de la ruta cuando se visualiza un área activa, se ejecuta la limpieza del estado del área seleccionada (`limpiarArea`), retornando al catálogo general de áreas.

### Ejemplo

Un administrador ingresa a `/admin/platforms` y visualiza en la barra de localización `Gestión › Plataformas › Áreas`. Al hacer clic en el área «Demo Finanzas», la ruta muestra directamente `Gestión › Plataformas › Demo Finanzas`. En la barra de herramientas inferior, el buscador de plataformas se presenta despejado sin ningún badge repetido a su derecha. Al hacer clic sobre el enlace «Plataformas» en la miga de pan, regresa a la vista de todas las áreas.

### Impacto

Afecta a [platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [ruta-navegacion.tsx](../frontend/src/components/marco/ruta-navegacion.tsx), [UI_GUIDE.md](../UI_GUIDE.md), [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx) y [marco-admin.test.tsx](../frontend/tests/components/marco-admin.test.tsx).

Simetría Dimensional de Botones en el Pie del Cajón de Diseño de Áreas

## Plataformas

### Regla

En el pie del cajón lateral de diseño de tarjetas de área (`AreaCardDesignDrawer`), los botones de acción inferior («Cerrar» y «Reestablecer») aplican simetría dimensional rigurosa e idéntica independientemente de la disparidad en la cantidad de caracteres de sus etiquetas:

1. **Dimensiones Idénticas**: Ambos botones comparten exactamente el mismo ancho y altura:
   - En escritorio y tablets (`sm:` y superior): `sm:w-48 sm:min-w-48` (192 px de ancho fijo), garantizando que «Cerrar» y «Reestablecer» tengan exactamente el mismo volumen visual simétrico.
   - En pantallas pequeñas / móviles: `w-[calc(50%-0.5rem)]` (50% simétrico del ancho del contenedor menos el espaciador `gap-3`), asegurando igualdad milimétrica en cualquier resolución.
   - Altura estándar: 48 px (`h-12 min-h-12`), cumpliendo con la cuadrícula de 8pt y el estándar táctil WCAG AAA.
2. **Tipografía y Alineación**: Ambos botones centran su texto (`justify-center text-center !px-3 font-semibold`), garantizando equilibrio óptico absoluto en la barra de pie sin diferencias por el ancho intrínseco del texto.

### Ejemplo

Al abrir el cajón lateral «Diseño» en `/admin/platforms`, el pie inferior presenta a la izquierda el botón «Cerrar» y a la derecha el botón «Reestablecer». Ambos botones lucen con un ancho idéntico de 192 px y altura de 48 px, erradicando cualquier desproporción dimensional.

### Impacto

Afecta a [area-card-design-drawer.tsx](../frontend/src/components/platforms/area-card-design-drawer.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

Simetría de Padding Vertical en Cabecera y Pie del Drawer de Diseño

## Plataformas

### Regla

En el cajón lateral de diseño (`AreaCardDesignDrawer`) y en la arquitectura de paneles laterales (`Drawer`), se garantiza simetría vertical estricta e idéntica entre los rellenos superior e inferior:

1. **Igualdad de Padding Vertical en Header y Footer**:
   - Cabecera: `px-5 py-4 sm:px-6 sm:py-4.5` (16 px en móvil, 18 px en escritorio).
   - Pie (Footer): `px-5 py-4 sm:px-6 sm:py-4.5` (16 px en móvil, 18 px en escritorio).
   - Los botones del pie (`Cerrar` y `Reestablecer`) cuentan con exactamente 18 px de distancia desde la línea divisoria superior (`border-t`) y 18 px de distancia hacia el borde inferior del contenedor (`items-center`), erradicando cualquier desnivel visual o sensación de descolgamiento.
2. **Restricción de Altura Mínima Flex (`min-h-0`)**:
   - El contenedor scrollable intermedio del Drawer (`flex-1 min-h-0 overflow-y-auto`) implementa `min-h-0` para garantizar que el contenido del cuerpo respete rigurosamente los límites de la ventana modal y jamás desborde verticalmente empujando o recortando el pie contra el borde inferior de la pantalla.

### Ejemplo

Al abrir el modal lateral de diseño en `/admin/platforms`, el espacio superior sobre los botones de pie (desde la línea divisoria hasta el borde superior de los botones) y el espacio inferior bajo los mismos (desde el borde inferior de los botones hasta el final del cajón) es exactamente el mismo (18 px), logrando simetría vertical absoluta.

### Impacto

Afecta a [drawer.tsx](../frontend/src/components/drawer.tsx), [area-card-design-drawer.tsx](../frontend/src/components/platforms/area-card-design-drawer.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las suites de pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

Botón y Drawer de Diseño de Plataformas con Vista Previa en Vivo

## Plataformas

### Regla

En la vista de administración de plataformas de un área activa (`/admin/platforms`, Sección 2):

1. **Botón de Diseño en Toolbar**: Inmediatamente a la izquierda del botón «Accesos» en la barra de herramientas, se incorpora el botón «Diseño» (`variant="fila"`, icono temático `diseno`, altura táctil estándar de 48 px `min-h-12`). Permanece visible y activo para administradores con permisos de gestión (`canManage`).
2. **Cajón Lateral de Diseño de Plataformas (`PlatformCardDesignDrawer`)**: Al presionar «Diseño», se abre un panel lateral accesible que permite configurar el diseño de tarjetas de plataforma en el catálogo del portal (`nexus.platforms.card_design`):
   - **Vista Previa en Vivo Obligatoria**: Debido a que la pantalla administrativa de plataformas despliega una tabla de datos (`DataTable`) y no tarjetas visuales, el cajón lateral integra un recuadro destacado de previsualización en vivo (`PlatformMockupCard` interactiva con botón de favoritos y estado de acceso) que reacciona instantáneamente a cada variante seleccionada.
   - **Forzar Diseño Institucional**: Conmutador accesible de palanca (`role="switch"`, `CLAVE_FORZAR_DISENO_PLATAFORMA`) que fija el estilo seleccionado para todas las plataformas e inhabilita las opciones de personalización individual de los usuarios en el portal.
   - **10 Variantes de Tarjetas de Plataforma**: Presenta la cuadrícula de 10 alternativas (Duotono a Sangre, Foto Enmarcada, Split 50/50, Glassmorphism Neón, Editorial Suizo, Diseño Estándar, Diseño Compacto, Diseño Horizontal, Hero Banner, Flotante Inmersiva) con miniaturas ilustrativas y selección accesible.
   - **Pie Simétrico**: Barra inferior con botones simétricos de 192 px de ancho y 48 px de altura: «Cerrar» a la izquierda y «Reestablecer» a la derecha (este último regresa el diseño a `estandar` y desactiva el forzado de diseño).

### Ejemplo

Al acceder al área «Finanzas» en `/admin/platforms`, el administrador observa el botón «Diseño» a la izquierda de «Accesos». Al pulsarlo, se despliega el cajón lateral derecho mostrando en su parte superior la maqueta en vivo «Tarjeta de Plataforma». Al seleccionar «Glassmorphism Neón», la tarjeta de vista previa se actualiza inmediatamente mostrando el efecto de cristal y neón. Al pulsar «Reestablecer», el estilo vuelve a «Diseño Estándar».

### Impacto

Afecta a [platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [platform-card-design-drawer.tsx](../frontend/src/components/platforms/platform-card-design-drawer.tsx), [user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

Simetría Dimensional de Botones en el Pie del Cajón de Diseño de Áreas

## Plataformas

### Regla

En el pie del cajón lateral de diseño de tarjetas de área (`AreaCardDesignDrawer`), los botones de acción inferior («Cerrar» y «Reestablecer») aplican simetría dimensional rigurosa e idéntica independientemente de la disparidad en la cantidad de caracteres de sus etiquetas:

1. **Dimensiones Idénticas**: Ambos botones comparten exactamente el mismo ancho y altura:
   - En escritorio y tablets (`sm:` y superior): `sm:w-48 sm:min-w-48` (192 px de ancho fijo), garantizando que «Cerrar» y «Reestablecer» tengan exactamente el mismo volumen visual simétrico.
   - En pantallas pequeñas / móviles: `w-[calc(50%-0.5rem)]` (50% simétrico del ancho del contenedor menos el espaciador `gap-3`), asegurando igualdad milimétrica en cualquier resolución.
   - Altura estándar: 48 px (`h-12 min-h-12`), cumpliendo con la cuadrícula de 8pt y el estándar táctil WCAG AAA.
2. **Tipografía y Alineación**: Ambos botones centran su texto (`justify-center text-center !px-3 font-semibold`), garantizando equilibrio óptico absoluto en la barra de pie sin diferencias por el ancho intrínseco del texto.

### Ejemplo

Al abrir el cajón lateral «Diseño» en `/admin/platforms`, el pie inferior presenta a la izquierda el botón «Cerrar» y a la derecha el botón «Reestablecer». Ambos botones lucen con un ancho idéntico de 192 px y altura de 48 px, erradicando cualquier desproporción dimensional.

### Impacto

Afecta a [area-card-design-drawer.tsx](../frontend/src/components/platforms/area-card-design-drawer.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

Simetría de Padding Vertical en Cabecera y Pie del Drawer de Diseño

## Plataformas

### Regla

En el cajón lateral de diseño (`AreaCardDesignDrawer`) y en la arquitectura de paneles laterales (`Drawer`), se garantiza simetría vertical estricta e idéntica entre los rellenos superior e inferior:

1. **Igualdad de Padding Vertical en Header y Footer**:
   - Cabecera: `px-5 py-4 sm:px-6 sm:py-4.5` (16 px en móvil, 18 px en escritorio).
   - Pie (Footer): `px-5 py-4 sm:px-6 sm:py-4.5` (16 px en móvil, 18 px en escritorio).
   - Los botones del pie (`Cerrar` y `Reestablecer`) cuentan con exactamente 18 px de distancia desde la línea divisoria superior (`border-t`) y 18 px de distancia hacia el borde inferior del contenedor (`items-center`), erradicando cualquier desnivel visual o sensación de descolgamiento.
2. **Restricción de Altura Mínima Flex (`min-h-0`)**:
   - El contenedor scrollable intermedio del Drawer (`flex-1 min-h-0 overflow-y-auto`) implementa `min-h-0` para garantizar que el contenido del cuerpo respete rigurosamente los límites de la ventana modal y jamás desborde verticalmente empujando o recortando el pie contra el borde inferior de la pantalla.

### Ejemplo

Al abrir el modal lateral de diseño en `/admin/platforms`, el espacio superior sobre los botones de pie (desde la línea divisoria hasta el borde superior de los botones) y el espacio inferior bajo los mismos (desde el borde inferior de los botones hasta el final del cajón) es exactamente el mismo (18 px), logrando simetría vertical absoluta.

### Impacto

Afecta a [drawer.tsx](../frontend/src/components/drawer.tsx), [area-card-design-drawer.tsx](../frontend/src/components/platforms/area-card-design-drawer.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las suites de pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

Botón y Drawer de Diseño de Plataformas con Vista Previa en Vivo

## Plataformas

### Regla

En la vista de administración de plataformas de un área activa (`/admin/platforms`, Sección 2):

1. **Botón de Diseño en Toolbar**: Inmediatamente a la izquierda del botón «Accesos» en la barra de herramientas, se incorpora el botón «Diseño» (`variant="fila"`, icono temático `diseno`, altura táctil estándar de 48 px `min-h-12`). Permanece visible y activo para administradores con permisos de gestión (`canManage`).
2. **Cajón Lateral de Diseño de Plataformas (`PlatformCardDesignDrawer`)**: Al presionar «Diseño», se abre un panel lateral accesible que permite configurar el diseño de tarjetas de plataforma en el catálogo del portal (`nexus.platforms.card_design`):
   - **Vista Previa en Vivo Obligatoria**: Debido a que la pantalla administrativa de plataformas despliega una tabla de datos (`DataTable`) y no tarjetas visuales, el cajón lateral integra un recuadro destacado de previsualización en vivo (`PlatformMockupCard` interactiva con botón de favoritos y estado de acceso) que reacciona instantáneamente a cada variante seleccionada.
   - **Forzar Diseño Institucional**: Conmutador accesible de palanca (`role="switch"`, `CLAVE_FORZAR_DISENO_PLATAFORMA`) que fija el estilo seleccionado para todas las plataformas e inhabilita las opciones de personalización individual de los usuarios en el portal.
   - **10 Variantes de Tarjetas de Plataforma**: Presenta la cuadrícula de 10 alternativas (Duotono a Sangre, Foto Enmarcada, Split 50/50, Glassmorphism Neón, Editorial Suizo, Diseño Estándar, Diseño Compacto, Diseño Horizontal, Hero Banner, Flotante Inmersiva) con miniaturas ilustrativas y selección accesible.
   - **Pie Simétrico**: Barra inferior con botones simétricos de 192 px de ancho y 48 px de altura: «Cerrar» a la izquierda y «Reestablecer» a la derecha (este último regresa el diseño a `estandar` y desactiva el forzado de diseño).

### Ejemplo

Al acceder al área «Finanzas» en `/admin/platforms`, el administrador observa el botón «Diseño» a la izquierda de «Accesos». Al pulsarlo, se despliega el cajón lateral derecho mostrando en su parte superior la maqueta en vivo «Tarjeta de Plataforma». Al seleccionar «Glassmorphism Neón», la tarjeta de vista previa se actualiza inmediatamente mostrando el efecto de cristal y neón. Al pulsar «Reestablecer», el estilo vuelve a «Diseño Estándar».

### Impacto

Afecta a [platform-admin.tsx](../frontend/src/components/platform-admin.tsx), [platform-card-design-drawer.tsx](../frontend/src/components/platforms/platform-card-design-drawer.tsx), [user-view-settings.tsx](../frontend/src/components/platforms/user-view-settings.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

Optimización y Paginación 2x2 en Cajón de Diseño de Plataformas

## Plataformas

### Regla

En el cajón lateral de configuración de tarjetas de plataforma (`PlatformCardDesignDrawer`):

1. **Conmutador Compacto**: El interruptor «Forzar diseño en todo el portal» prescinde del párrafo de descripción secundaria, condensándose en una fila horizontal estilizada de baja altura (`px-3.5 py-2.5 sm:px-4 sm:py-3`), lo cual reduce significativamente el consumo de espacio vertical.
2. **Vista Previa Compacta**: El bloque de previsualización en vivo reduce su altura a un contenedor contenido (`max-h-[155px]`, `p-2.5 sm:p-3`), escalando la tarjeta interactiva de demostración (`transform scale-[0.78] sm:scale-[0.82]`) para mantener visible y operativa la maqueta sin generar desbordamiento ni desplazar los controles inferiores.
3. **Paginación de 4 Diseños por Página (Cuadrícula 2x2)**: Con el objetivo de eliminar por completo el scroll vertical dentro del panel en resoluciones de escritorio habituales, el catálogo de 10 variantes se divide en 3 páginas con un paginador en la cabecera de la sección:
   - Página 1: Duotono a Sangre, Foto Enmarcada, Split 50/50 y Glassmorphism Neón (4 opciones).
   - Página 2: Editorial Suizo, Diseño Estándar, Diseño Compacto y Diseño Horizontal (4 opciones).
   - Página 3: Hero Banner y Flotante Inmersiva (2 opciones).
4. **Tarjetas Fantasma (Ghost Cards) de Simetría Estricta**: Para preservar la cuadrícula simétrica de 2 columnas por 2 filas en la página 3, se incorporan automáticamente 2 tarjetas fantasma estandarizadas (`data-testid="platform-design-ghost-card"`, borde punteado `border-dashed border-panel-border/70`, `min-h-[96px]`) que representan espacio disponible, impidiendo asimetrías o huecos vacíos en la composición.

### Ejemplo

Al acceder al área «Finanzas» en `/admin/platforms` y abrir «Diseño», el cajón se presenta completamente contenido en el alto del viewport sin barra de desplazamiento vertical. El usuario visualiza la página 2 con su diseño activo «Diseño Estándar». Al usar las flechas del paginador navega a la página 3 («Pág. 3 de 3»), donde observa «Hero Banner», «Flotante Inmersiva» y 2 tarjetas fantasma con el icono de panel y la leyenda «Espacio disponible», manteniendo intacta la simetría 2x2.

### Impacto

Afecta a [platform-card-design-drawer.tsx](../frontend/src/components/platforms/platform-card-design-drawer.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

Distribución de Cabecera en Vista Previa de Tarjetas de Plataforma

## Plataformas

### Regla

En la cabecera del recuadro de previsualización en vivo dentro del cajón lateral de diseño de plataformas (`PlatformCardDesignDrawer`):

1. **Alineación del Título**: El encabezado «Tarjeta de Plataforma» se posiciona anclado al extremo izquierdo del contenedor (`text-xs font-bold text-body-text`).
2. **Ubicación del Distintivo de Vista Previa**: El badge animado de «Vista Previa en Vivo» (`bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border-emerald-500/30`) se traslada al extremo derecho (`justify-between`), ocupando la posición final.
3. **Supresión del Badge de Variante**: Se elimina el distintivo estático con el nombre en mayúsculas de la variante seleccionada (ej. «FLOTANTE»), eliminando redundancia visual dado que el estilo ya se aprecia inmediatamente en la maqueta interactiva y en el selector de variantes.

### Ejemplo

Al abrir el cajón «Diseño» en la gestión de plataformas, la tarjeta superior muestra a la izquierda «Tarjeta de Plataforma» y a la derecha el indicador verde con punto pulsante «VISTA PREVIA EN VIVO», suprimiéndose la etiqueta con el nombre del estilo.

### Impacto

Afecta a [platform-card-design-drawer.tsx](../frontend/src/components/platforms/platform-card-design-drawer.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

Adaptación Proporcional por Altura y Restablecimiento de Descripción en Cajón de Diseño

## Plataformas

### Regla

En el cajón lateral de diseño de plataformas (`PlatformCardDesignDrawer`):

1. **Distribución Proporcional de Altura (Flex/Porcentaje)**: El contenedor principal implementa `h-full min-h-full flex flex-col justify-between`, asegurando que las distintas secciones se distribuyan de forma continua a lo largo del alto total del panel lateral, eliminando espacios vacíos desproporcionados antes del pie de página.
2. **Restablecimiento de la Descripción en el Conmutador**: Se reintegra el texto descriptivo en la tarjeta del interruptor («Aplica este diseño a todas las tarjetas de plataforma e inhabilita las opciones de personalización en la vista de usuario del portal.») para aportar contexto institucional claro al administrador.
3. **Vista Previa Proporcional y Ergonómica**: El bloque de previsualización en vivo adopta dimensionamiento elástico (`flex-1 min-h-[170px] max-h-[38%]`), con la tarjeta maqueta escalada proporcionalmente (`scale-[0.85] sm:scale-[0.92]`), garantizando presencia visual sin provocar scroll vertical.
4. **Cuadrícula 2x2 Auto-expandible**: La matriz de 4 elementos por página utiliza `flex-1 min-h-[220px] grid grid-cols-2 grid-rows-2`, permitiendo que tanto las tarjetas de variantes como las ghost cards de simetría abarquen toda la altura de su fila (`h-full min-h-[96px]`).

### Ejemplo

Al abrir el panel de diseño de plataformas en cualquier resolución de pantalla, el contenido llena de forma balanceada y armoniosa la altura del drawer: el interruptor superior muestra su descripción, la maqueta de vista previa ocupa el tercio central y las 4 tarjetas de la cuadrícula 2x2 se expanden hasta encontrarse de forma simétrica con los botones inferiores («Cerrar» y «Reestablecer»), sin vacíos blancos ni barra de desplazamiento vertical.

### Impacto

Afecta a [platform-card-design-drawer.tsx](../frontend/src/components/platforms/platform-card-design-drawer.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

Vista Previa Ampliada y Supresión de Toast en Cajón de Diseño de Plataformas

## Plataformas

### Regla

En el cajón lateral de configuración de diseño de plataformas (`PlatformCardDesignDrawer`):

1. **Ampliación y Renderizado Completo de la Vista Previa**: El recuadro de maqueta en vivo amplía sus dimensiones interiores (`min-h-[230px]`, `p-3 sm:p-4`) suprimiendo cualquier recorte por desbordamiento (`overflow-hidden`) o escalas forzadas. Esto garantiza que todos los elementos de las tarjetas (incluyendo la cabecera departamental, el botón de favoritos de estrella, el título, la descripción y el enlace de acción) se muestren íntegros y sin truncamiento visual en todas las variantes.
2. **Supresión de Alertas Toast en Interacciones del Drawer**: Se suprimen todas las notificaciones toast (`avisar`) generadas por el cambio de diseño, conmutación de forzado institucional o pulsación de reestablecer dentro del panel. Dado que los cambios se reflejan inmediatamente en la maqueta interactiva y en los botones de radio, la supresión de toasts evita que los globos flotantes en la esquina inferior derecha cubran y bloqueen la visibilidad de los botones del pie («Cerrar» y «Reestablecer»).

### Ejemplo

Al seleccionar la variante «Editorial Suizo» o «Hero Banner» en el cajón lateral, la maqueta se presenta nítida y completa, mostrando la etiqueta de área superior y la estrella de favoritos sin bordes amputados. La aplicación del diseño ocurre de forma silenciosa e instantánea, permitiendo al administrador pulsar «Reestablecer» o «Cerrar» libremente sin que un toast cubra los botones.

### Impacto

... [truncated for diff preview]
Afecta a [platform-card-design-drawer.tsx](../frontend/src/components/platforms/platform-card-design-drawer.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [platform-admin.test.tsx](../frontend/tests/components/platform-admin.test.tsx).

Diseño Premium Institucional en Acceso y Cierre de Sesión (Login / Logout)

## Autenticación

### Regla

Las vistas de acceso (`LoginForm`), autenticación local/emergencia (`FormularioLoginLocal`, `AccesoEmergenciaForm`) y cierre de sesión (`LogoutView`) implementan la identidad visual corporativa de Aduana (Manual de Marca):
1. **Atmósfera Dark-First**: Lienzo centrado con Navy Profundo (`#1B2A38` / `bg-fondo`), sutil resplandor ambiental tecnológico en los vértices superiores e inferiores mediante halos difuminados en Cian Tecnológico (`#1CB5E0`) y Naranja Control (`#F26419`).
2. **Contenedor de Isotipo Canónico**: Caja redondeada con borde (`border-aduana-border`), superficie oscura (`bg-superficie`), anillo de énfasis (`ring-4 ring-aduana-cyan/15`) y renderizado del isotipo oficial `/brand/isotype-aduana.png`.
3. **Título Display y Microcopy**: Titulares en tipografía `Montserrat` (`font-display font-extrabold`), acompañados de insignias de seguridad (`Control de Acceso • Portal Vivaro`, `Desconexión segura completada`, `Superadmin Local • Modo Recuperación`) y textos descriptivos canónicos.
4. **Tarjeta Principal con Borde de Acento**: Superficie `bg-panel-fill/95 backdrop-blur-xl` con barra superior en degradado de acento corporativo (`from-aduana-cyan to-aduana-orange`), inputs de alta ergonomía con focus ring cian y botones de acción principal en degradado corporativo (`from-aduana-cyan to-aduana-cyan-hover`) con microinteracción hover/active y estado deshabilitado accesible.
5. **Cierre de Sesión Asistido**: `LogoutView` presenta confirmación nítida con isotipo oficial, estado accesible de desconexión y enlace de retorno directo en botón primario de alta visibilidad.

### Ejemplo

Al ingresar a `/login`, el usuario es recibido por una pantalla inmersiva con el isotipo de Aduana en alta definición, la insignia «Control de Acceso • Portal Vivaro», la tarjeta de acceso con bisel degradado cian-naranja y el botón de acción en Cian Tecnológico. Al cerrar sesión en `/logout`, la vista despliega la insignia verde/cian de «Desconexión segura completada» junto con el botón «Volver a iniciar sesión» en formato primario destacado.

### Impacto

Afecta a [login-form.tsx](../frontend/src/components/login-form.tsx), [formulario-login-local.tsx](../frontend/src/components/formulario-login-local.tsx), [logout-view.tsx](../frontend/src/components/logout-view.tsx), [acceso-emergencia-form.tsx](../frontend/src/components/acceso-emergencia-form.tsx), [UI_GUIDE.md](../UI_GUIDE.md) y a las pruebas en [login-oidc.test.tsx](../frontend/tests/components/auth/login-oidc.test.tsx).


Erradicación Total de Sesión y Tokens Persistentes en Logout

## Autenticación

### Regla

Al invocar el cierre de sesión (`POST /api/v1/auth/logout`), el sistema debe ejecutar una purga completa y garantizada de todas las credenciales de sesión en el cliente. Esto requiere invalidar la sesión en servidor, desvincular al usuario en Flask-Login y forzar explícitamente en la respuesta HTTP la eliminación (`delete_cookie`) tanto de la cookie de sesión (`nexus_session`) como del token persistente (`remember_token`). Esto previene que una reconexión a `/login` reactive automáticamente la sesión previa vía `remember_token` y redirija erróneamente al `/dashboard`.

### Ejemplo

Un usuario hace clic en «Cerrar sesión» y aterriza en `/logout`. El backend responde eliminando las cookies `nexus_session` y `remember_token` fijando su caducidad en el pasado (`Max-Age=0`). Cuando el usuario hace clic en «Volver a iniciar sesión» y navega a `/login`, la llamada a `/api/v1/auth/context` devuelve `authenticated: false`, permitiendo al usuario ver el formulario de acceso o botón SSO en lugar de ser redirigido automáticamente a `/dashboard`.

### Impacto

Afecta a [app/modules/api/auth.py](../app/modules/api/auth.py), [tests/test_sesion_y_logout.py](../tests/test_sesion_y_logout.py) y al flujo de navegación de autenticación en [frontend/src/components/login-form.tsx](../frontend/src/components/login-form.tsx).


Identidad de Marca en Barra Lateral del Dashboard

## Navegación y Marca

### Regla

En la barra lateral principal del sistema (`BarraLateral`), la cabecera de marca superior despliega el isotipo canónico de Aduana acompañado de la denominación oficial:
- Título principal: `Aduana` (en tipografía bold, color `text-barra-lateral-texto`).
- Subtítulo: `Accesos Vivaro` (en tipografía texto secundario, color `text-barra-lateral-secundario`).

### Ejemplo

Al ingresar al Dashboard o cualquier vista dentro del layout principal con menú lateral (`AppShell`), el usuario visualiza en la esquina superior izquierda el isotipo corporativo junto con los textos «Aduana» y «Accesos Vivaro».

### Impacto

Afecta a [frontend/src/components/marco/barra-lateral.tsx](../frontend/src/components/marco/barra-lateral.tsx) y a la suite de pruebas unitarias en [frontend/tests/components/marco-admin.test.tsx](../frontend/tests/components/marco-admin.test.tsx).


Sincronización Temática del Isotipo Corporativo de Aduana

## Marca y Temas (Dark / Light Mode)

### Regla

El contenedor del isotipo oficial de Aduana (`isotype-aduana.png`) debe sincronizarse automáticamente con el tema activo de la interfaz utilizando los tokens semánticos `bg-superficie` y `border-panel-border`:
- En **Tema Claro (Light)**: El fondo del isotipo es blanco puro (`#FFFFFF` / `bg-superficie`) con borde perimetral sutil (`#E2E8F0` / `border-panel-border`), evitando fondos oscuros fijos o cajas negras en cabeceras claras.
- En **Tema Oscuro (Dark)**: El fondo del isotipo transmuta automáticamente al Navy Profundo corporativo (`#1A2634` / `--p-noche-850`) con borde perimetral tecnológico (`#334A60` / `--p-noche-700`).
Se prohíbe el uso de colores hexadecimales fijos (`#1B2A38`, `#334A60`) en los contenedores del isotipo en cabeceras de navegación, barras laterales y pies de página.

### Ejemplo

Al alternar entre el tema claro y oscuro en la portada (`/`) o en el portal/dashboard (`/dashboard`), el contenedor del logotipo de Aduana en la barra superior y lateral cambia de fondo blanco a fondo azul noche oscuro, armonizando con la superficie de la interfaz.

### Impacto

Afecta a [frontend/src/components/portada/pagina-portada.tsx](../frontend/src/components/portada/pagina-portada.tsx), [frontend/src/components/marco/barra-lateral.tsx](../frontend/src/components/marco/barra-lateral.tsx), [frontend/src/components/platforms/platforms-topbar.tsx](../frontend/src/components/platforms/platforms-topbar.tsx) y [frontend/src/components/platforms/platforms-sidebar-view.tsx](../frontend/src/components/platforms/platforms-sidebar-view.tsx).


Eliminación de Tokens Persistentes (`remember=False`) en Sesiones Locales y SSO

## Seguridad y Autenticación

### Regla

El portal no emite cookies persistentes de larga duración (`remember_token`). En el inicio de sesión (`_abrir_sesion`), la autenticación se realiza con `login_user(cuenta, remember=False)`:
1. **Acceso de Emergencia (Superadmin Local)**: Por motivos de alta seguridad, la cuenta con privilegios totales de administración jamás debe dejar tokens persistentes de 1 año en los dispositivos donde se ejecute recuperación o mantenimiento. La sesión está acotada estrictamente a la cookie de sesión cifrada (`nexus_session`).
2. **Acceso Corporativo (Authelia SSO / OIDC)**: La persistencia y el tiempo de vida de la sesión corporativa están centralizados y gobernados exclusivamente por Authelia (IdP). El portal no duplica estados de persistencia local que sobrevivan al cierre del navegador o a la expiración de la sesión corporativa.
3. **Defensa en Profundidad**: Se fija `REMEMBER_COOKIE_DURATION = timedelta(hours=12)` a nivel de configuración de la aplicación para mitigar cualquier llamada accidental futura a tokens persistentes.

### Ejemplo

Cuando un superadmin ingresa por `/acceso-emergencia` con credenciales locales para atender una contingencia, el navegador solo recibe la cookie de sesión `nexus_session`. Al cerrar la sesión o cerrar el navegador, las credenciales quedan completamente desvinculadas sin dejar rastro de tokens de 365 días.

### Impacto

Afecta a [app/modules/api/auth.py](../app/modules/api/auth.py), [app/__init__.py](../app/__init__.py), [tests/test_sesion_y_logout.py](../tests/test_sesion_y_logout.py) y [tests/test_login_local.py](../tests/test_login_local.py).


Diseño Split-Screen Corporativo de la Pantalla de Login

## Frontend y Autenticación

### Regla

La pantalla de acceso corporativo (`/login`) adopta una arquitectura visual split-screen de dos paneles:
1. **Panel Institucional (Showcase Desktop)**: Exhibe la identidad institucional de Aduana (isotipo oficial v2.0, pilares de gobernanza Zero-Trust, federación SSO, catálogo unificado y trazabilidad inmutable) en una columna izquierda dedicada con atmósfera tecnológica oscura, fondos con degradados perimetrales y micro-tarjetas informativas.
2. **Panel de Autenticación**: Columna derecha limpia, ergonómica y accesible donde reside la tarjeta de autenticación (`Card`), el estado de conexión con Authelia / SSO corporativo, acciones de inicio de sesión de alto contraste (botón con elevación y gradiente cian corporativo), retroalimentación de estado accesible y enlaces institucionales.
3. **Responsividad Móvil**: En pantallas móviles y tablets (`< lg`), el panel de showcase se oculta fluidamente priorizando la tarjeta de autenticación y preservando una cabecera institucional compacta.
4. **Contratos Técnicos y de Navegación**: Se respeta de manera estricta la ausencia de clases de bloqueo de scroll (`h-screen`, `h-dvh`, `overflow-hidden`), utilizando `min-h-screen` y preservando intactos los contratos de integración con Authelia, modos de login local y accesibilidad semántica.

### Ejemplo

Al acceder a `/login` desde un navegador de escritorio, el usuario observa a la izquierda la propuesta de valor y los estándares de seguridad corporativa de Vivaro, y a la derecha una tarjeta centrada con el botón "Entrar con Authelia". En dispositivos móviles, la interfaz se adapta automáticamente a una vista vertical limpia y deslizable sin desbordamientos de pantalla.

### Impacto

Afecta a [frontend/src/components/login-form.tsx](../frontend/src/components/login-form.tsx), [frontend/tests/components/auth/login-oidc.test.tsx](../frontend/tests/components/auth/login-oidc.test.tsx) y [frontend/tests/components/raiz-desplazable.test.tsx](../frontend/tests/components/raiz-desplazable.test.tsx).


Enfoque Exclusivo de Autenticación en la Pantalla de Login (Separación de Portada)

## Frontend y Autenticación

### Regla

La pantalla de acceso corporativo (`/login`) mantiene un enfoque exclusivo y centrado en la autenticación e identidad del usuario, delegando toda información comercial, módulos, características y presentación de la plataforma a la portada institucional (`/`):
1. **Separación de Responsabilidades**: La portada (`/`) es el espacio destinado a la presentación del producto, métricas, beneficios y arquitectura. La pantalla de login (`/login`) es un centro de autenticación directo, libre de bloques de marketing, listas de características o información redundante de la plataforma.
2. **Arquitectura Visual Focalizada**: La interfaz se estructura en tres secciones verticales utilizando `min-h-screen`:
   - *Cabecera Superior*: Marca institucional discreta (isotipo y versión v2.0) y enlace contextual a la portada cuando esté activa (`PORTADA_ACTIVA`).
   - *Área Central*: Tarjeta de acceso (`Card`) perfectamente proporcionada (`max-w-[440px]`), con borde superior institucional continuo (gradiente cian a naranja), isotipo corporativo en contenedor sincronizado con el tema, indicador de conexión segura y acción de entrada con Authelia SSO de alto contraste.
   - *Pie Inferior*: Enlaces mínimos de gobernanza y estado de cifrado perimetral (TLS 1.3).
3. **Ambiente y Profundidad Sin Distracciones**: Se emplean halos de luz ambiental sutiles (`blur-[120px]`) y una cuadrícula técnica tenue que proporcionan calidez y solidez visual sin sobrecargar el espacio ni competir con el formulario de acceso.
4. **Restricciones de Desplazamiento**: Se prohíbe el uso de `overflow-hidden`, `h-screen` o `h-dvh` en el componente para preservar la total navegabilidad y desplazamiento en pantallas pequeñas o en modos de alta densidad.

### Ejemplo

Un usuario que navega a `https://aduana.vivaro.com/login` encuentra inmediatamente el centro de autenticación corporativo con el botón "Entrar con Authelia" y la indicación de seguridad SSO, sin distracciones de diapositivas o párrafos informativos de marketing. Si desea conocer la plataforma, puede hacer clic en el enlace superior hacia la portada.

### Impacto

Afecta a [frontend/src/components/login-form.tsx](../frontend/src/components/login-form.tsx), [frontend/tests/components/auth/login-oidc.test.tsx](../frontend/tests/components/auth/login-oidc.test.tsx) y [frontend/tests/components/raiz-desplazable.test.tsx](../frontend/tests/components/raiz-desplazable.test.tsx).


Arquitectura Split-Screen Visual para la Pantalla de Login

## Frontend y Autenticación

### Regla

La pantalla de acceso corporativo (`/login`) adopta un layout split-screen visual que equilibra la identidad institucional con la ergonomía de acceso sin sobrecargar al usuario con textos promocionales:
1. **Columna Izquierda (Showcase Visual de la Plataforma)**: En pantallas de escritorio (`>= lg`), despliega un escaparate visual de alta fidelidad que enmarca la interfaz real de Aduana (`/screenshots/catalogo-plataformas.png`) dentro de una ventana estilizada de sistema operativo con semáforos de control (`bg-error`, `bg-warning`, `bg-success`) y badge de catálogo oficial. Se excluyen deliberadamente textos comerciales, bloques de marketing y listas de características para mantener la pulcritud y sobriedad de la herramienta.
2. **Columna Derecha (Tarjeta de Autenticación)**: Contiene la tarjeta de acceso de 420px de ancho con acento perimetral superior en gradiente, isotipo oficial en contenedor dinámico sincronizado con el tema, estado de SSO corporativo y el botón de acción principal de alta visibilidad para Authelia.
3. **Flujos de Acceso Local**:
   - Con `OIDC_HABILITADO=false`: La interfaz detecta `local_login=true` y despliega automáticamente el formulario de credenciales locales (`FormularioLoginLocal`) para cuentas de base de datos.
   - Con `OIDC_HABILITADO=true`: La entrada con credenciales locales de contingencia se realiza directamente a través de la ruta protegida `/acceso-emergencia`.
4. **Restricciones Técnicas**: Uso exclusivo de tokens semánticos (cero colores literales o funciones de color directas), `min-h-screen` y total ausencia de clases de bloqueo de desplazamiento (`h-screen`, `h-dvh`, `overflow-hidden`).

### Ejemplo

Al acceder a `/login` en escritorio, el usuario observa a la izquierda una vista limpia de la interfaz del catálogo de plataformas en una ventana flotante elegante y a la derecha el botón de ingreso con Authelia SSO.

### Impacto

Afecta a [frontend/src/components/login-form.tsx](../frontend/src/components/login-form.tsx), [frontend/tests/components/auth/login-oidc.test.tsx](../frontend/tests/components/auth/login-oidc.test.tsx) y [frontend/tests/components/raiz-desplazable.test.tsx](../frontend/tests/components/raiz-desplazable.test.tsx).


Diseño Split-Card Flotante con Fotografía Estética para Pantalla de Login

## Frontend y Autenticación

### Regla

La pantalla de acceso corporativo (`/login`) implementa una tarjeta flotante centralizada tipo Split-Card (inspirada en patrones de diseño editorial y minimalista):
1. **Composición Dual Flotante**: Un contenedor central de bordes redondeados (`rounded-[2rem]`) con borde superior en gradiente continuo institucional y sombra profunda (`shadow-2xl`) flotando sobre una superficie con sutiles destellos ambientales.
2. **Panel Izquierdo (Formulario de Acceso)**: Área de alta legibilidad y espacio generoso (`p-8 sm:p-12 lg:p-14`), con isotipo oficial sincronizado dinámicamente con el tema, saludo de bienvenida ("¡Bienvenido de nuevo!"), pastilla de estado corporativo y botón de acción principal de alta visibilidad para Authelia SSO.
3. **Panel Derecho (Fotografía Artística a Sangre)**: En escritorio y tabletas (`md:block`), la mitad derecha se viste con una fotografía estética y artística de alta resolución a sangre completa (`login-showcase.jpg`), con un detalle de costura flotante (insignia de seguridad) y una pastilla glassmorphism discreta de estado de infraestructura. No contiene capturas de pantalla de la interfaz ni textos comerciales redundantes.
4. **Comportamiento Responsivo**: En dispositivos móviles (`< md`), el panel fotográfico se oculta fluidamente y el contenedor mantiene el enfoque total en el formulario de autenticación, preservando la navegabilidad sin desbordamientos de pantalla (`min-h-screen`).

### Ejemplo

Un usuario que ingresa a `/login` desde un equipo de escritorio observa una tarjeta flotante estilizada con una imagen arquitectónica/artística en el costado derecho y el formulario limpio con el botón "Entrar con Authelia" en el costado izquierdo.

### Impacto

Afecta a [frontend/src/components/login-form.tsx](../frontend/src/components/login-form.tsx), [frontend/tests/components/auth/login-oidc.test.tsx](../frontend/tests/components/auth/login-oidc.test.tsx) y [frontend/tests/components/raiz-desplazable.test.tsx](../frontend/tests/components/raiz-desplazable.test.tsx).


Simplificación y Minimalismo Editorial para la Pantalla de Login

## Frontend y Autenticación

### Regla

La pantalla de acceso corporativo (`/login`) adopta una composición Split-Card estrictamente minimalista y libre de sobrecarga visual:
1. **Identidad de Marca Única**: Se prohíbe la duplicidad de isotipos, títulos o emblemas de Aduana en la pantalla. Únicamente existe un único logotipo discreto en la esquina superior izquierda del panel de formulario.
2. **Ausencia de Sobrecarga Visual**: Se eliminan todos los elementos flotantes redundantes sobre la imagen (pastillas informativas, insignias en la costura, indicadores de pulsación o semáforos de sistema operativo). La fotografía artística ocupa la totalidad de la mitad derecha (`rounded-r-3xl`) con sobriedad y serenidad.
3. **Tarjeta Centrada Espaciosa**: El contenedor central (`max-w-4xl`) flota en la vista con bordes redondeados (`rounded-3xl`), sombra suave (`shadow-2xl`) y una división 50/50 balanceada entre el formulario y la fotografía.
4. **Ergonomía de Acceso**: El formulario presenta únicamente el encabezado ("Iniciar Sesión"), un subtítulo breve y el botón de acción principal de Authelia SSO (o inputs locales si `local_login=true`), manteniendo el pie de página con el enlace a la portada y la identificación institucional de Vivaro.

### Ejemplo

Al ingresar a `/login`, el usuario ve una tarjeta limpia con un solo logo de Aduana, título "Iniciar Sesión", botón "Entrar con Authelia" y a la derecha una fotografía limpia de arquitectura/naturaleza, sin insignias superpuestas ni marcos complejos.

### Impacto

Afecta a [frontend/src/components/login-form.tsx](../frontend/src/components/login-form.tsx), [frontend/tests/components/auth/login-oidc.test.tsx](../frontend/tests/components/auth/login-oidc.test.tsx) y [frontend/tests/components/raiz-desplazable.test.tsx](../frontend/tests/components/raiz-desplazable.test.tsx).


Diseño Split-Card Homologado para la Pantalla de Acceso de Emergencia

## Frontend y Autenticación

### Regla

La interfaz de contingencia administrativa (`/acceso-emergencia`) replica fielmente la arquitectura Split-Card minimalista del acceso principal para mantener consistencia visual y ergonomía:
1. **Composición Split-Card Homologada**: La tarjeta flotante central (`max-w-4xl rounded-3xl border border-panel-border bg-superficie shadow-2xl`) cuenta con una división balanceada entre el formulario local a la izquierda y la fotografía estética a sangre a la derecha (`login-showcase.jpg`).
2. **Identidad de Contingencia**:
   - Cabecera con isotipo corporativo acompañado del indicador de estado «Recuperación» en color ámbar/naranja corporativo (`border-aduana-orange/30 bg-aduana-orange/10 text-aduana-orange`).
   - Título explícito "Acceso de emergencia" y subtítulo de seguridad para contingencias de red.
3. **Formulario de Credenciales Locales**: Renderiza `FormularioLoginLocal` con inputs ergonomizados y botón accesible de inicio de sesión (`POST /api/v1/auth/local`).
4. **Navegación Asistida**: Incluye enlace directo de retorno al acceso corporativo (`/login`) para evitar que administradores queden atrapados en la vista de contingencia.
5. **Restricciones Técnicas**: Cumple con `min-h-screen`, total ausencia de bloqueos de scroll (`overflow-hidden`, `h-screen`, `h-dvh`) y cero colores literales fuera de los tokens semánticos.

### Ejemplo

Un superadministrador que necesita recuperar el sistema accede a `https://aduana.vivaro.com/acceso-emergencia` y encuentra una interfaz limpia con el mismo diseño Split-Card que el login general, con su respectivo distintivo de «Recuperación», los campos de usuario y contraseña y el enlace de retorno a `/login`.

### Impacto

Afecta a [frontend/src/components/acceso-emergencia-form.tsx](../frontend/src/components/acceso-emergencia-form.tsx), [frontend/src/components/formulario-login-local.tsx](../frontend/src/components/formulario-login-local.tsx), [frontend/tests/components/auth/login-oidc.test.tsx](../frontend/tests/components/auth/login-oidc.test.tsx) y [frontend/tests/accesibilidad/colores-literales.test.ts](../frontend/tests/accesibilidad/colores-literales.test.ts).


Depuración y Limpieza de Variables Heredadas de Authelia SSO

## Configuración y Autenticación

### Regla

Las variables de entorno obsoletas `AUTHELIA_ENABLED` y `DEBUG_AUTH` quedan formalmente retiradas tanto de `.env` como de `.env.example`:
1. **Retiro de `AUTHELIA_ENABLED`**: Esta variable pertenecía a la arquitectura original de autenticación por cabeceras HTTP inversas (`Remote-Email`/`Remote-User`), la cual fue revocada en ADR-009 y reemplazada por el estándar OIDC federado (`OIDC_HABILITADO`).
2. **Retiro de `DEBUG_AUTH`**: Variable huérfana de desarrollo que no era leída por ningún módulo de la aplicación.
3. **Control Exclusivo por OIDC**: La activación o desactivación de la autenticación federada se rige exclusivamente por `OIDC_HABILITADO` y el bloque canónico `OIDC_*`.

### Ejemplo

Un entorno de producción o desarrollo no incluye `AUTHELIA_ENABLED` ni `DEBUG_AUTH` en su archivo `.env`, manteniendo el archivo de configuración limpio y libre de variables sin efecto operativo.

### Impacto

Afecta a [.env](file:///.env), [.env.example](../.env.example), [docs/configuracion/VARIABLES.md](../docs/configuracion/VARIABLES.md) y a las pruebas de regresión en [tests/test_oidc.py](../tests/test_oidc.py).


Redirección Canónica a Dashboard tras Autenticación OIDC

## Autenticación y Navegación

### Regla

Tras un inicio de sesión exitoso mediante el proveedor OIDC (Authelia SSO), el flujo de retorno en el backend (`/api/v1/auth/oidc/callback`) redirige de manera canónica y directa a `/dashboard` en lugar de la raíz `/`:
1. **Evitar Detención en Portada Institucional**: Si la portada informativa (`PORTADA_ACTIVA=true`) está habilitada, redirigir a la raíz causaba que el usuario autenticado quedara en la portada externa en vez de entrar directamente a la consola operativa.
2. **Consistencia de Experiencia de Acceso**: Alinea el flujo federado OIDC con el flujo local y la navegación de frontend, los cuales dirigen siempre al usuario con sesión activa a su panel principal (`/dashboard`).
3. **Mantenimiento de RUTA_INICIO**: La constante canónica `RUTA_INICIO` en `app/modules/api/auth.py` queda fijada como `/dashboard`.

### Ejemplo

Un usuario pulsa «Iniciar sesión con Authelia», completa el flujo en el IdP institucional y es devuelto a `https://aduana.vivaro.com/api/v1/auth/oidc/callback`. El servidor procesa el token OIDC, crea o actualiza la sesión y emite un `302 Found` con cabecera `Location: /dashboard`, llevando al usuario de inmediato a su panel de control.

### Impacto

Afecta a [app/modules/api/auth.py](file:///home/dtovar/bayblade/pokemon/app/modules/api/auth.py), [tests/test_oidc.py](file:///home/dtovar/bayblade/pokemon/tests/test_oidc.py) y al flujo de inicio de sesión SSO con Authelia.


Páginas de Error Corporativas de Nginx con Identidad ADUANA

## Infraestructura y Reverse Proxy

### Regla

El proxy inverso Nginx cuenta con un catálogo de páginas de error estáticas personalizadas bajo la identidad visual corporativa de ADUANA:
1. **Páginas Cubiertas**: Códigos HTTP `403` (Acceso Restringido), `404` (Página No Encontrada), `500` (Error Interno), `502` (Servicio No Disponible / Bad Gateway), `503` (Mantenimiento / Unavailable), `504` (Tiempo Agotado) y `50x` (Fallo Genérico de Servidor).
2. **Separación Estricta de Capas y Resiliencia**: Las páginas son 100% estáticas y residen en `deploy/errors/` servidas directamente por Nginx mediante `location ^~ /errors/ { alias @PREFIX@/deploy/errors/; }`. No dependen de que Node.js/Next.js o Python/Flask se encuentren en ejecución. Prohibición estricta de `style=""`, `<style>` o `<script>` inline: los estilos se cargan desde `/errors/assets/css/error.css` y las interacciones desde `/errors/assets/js/error.js`.
3. **Identidad Visual Corporativa**: Implementan los Design Tokens oficiales del Manual de Identidad Corporativa de ADUANA (Navy Profundo `#1B2A38`, Tarjeta `#233546`, Cian Tecnológico `#1CB5E0`, Naranja Control `#F26419`, tipografías Montserrat/Inter/JetBrains Mono, barra degradada superior y el isotipo oficial). Soporta automáticamente temas Dark y Light mediante `prefers-color-scheme`.

### Ejemplo

Si el backend o frontend entra en despliegue o falla (`502 Bad Gateway`), el usuario no visualiza la pantalla estándar genérica en blanco y negro de Nginx, sino una interfaz corporativa con el isotipo de ADUANA, el diagnóstico técnico del error y botones de acción ("Reintentar conexión" o "Ir al Dashboard").

### Impacto

Afecta a [deploy/nginx.conf.tmpl](file:///home/dtovar/bayblade/pokemon/deploy/nginx.conf.tmpl), los archivos en [deploy/errors/](file:///home/dtovar/bayblade/pokemon/deploy/errors/) y las pruebas en [tests/deploy/test_nginx_error_pages.py](file:///home/dtovar/bayblade/pokemon/tests/deploy/test_nginx_error_pages.py).


Orientación de Permisos y Solicitud en Authelia para Errores de Acceso (403 y 502)

## Control de Acceso y Experiencia de Usuario

### Regla

Las páginas de error `403.html` (Forbidden) y `502.html` (Bad Gateway / Denegación de Upstream) de Nginx orientan de forma explícita al usuario sobre la causa del bloqueo y la vía canónica de resolución:
1. **Mensaje de Permisos Insuficientes**: Se especifica que el usuario no cuenta con los permisos necesarios para acceder a la plataforma solicitada.
2. **Canal Oficial de Solicitud en Authelia**: Se instruye al usuario a solicitar sus roles y permisos directamente a través de Authelia (SSO institucional) o mediante el líder administrativo de su área.
3. **Llamado a la Acción Directo**: Se incluye un botón de acción principal «Solicitar acceso en Authelia» apuntando al flujo de inicio/reautenticación institucional (`/login`).

### Ejemplo

Un colaborador que intenta ingresar a una plataforma restringida sin estar dado de alta en los grupos correspondientes de Authelia recibe la página corporativa con el código HTTP correspondiente, informándole claramente: «No tienes permisos para acceder a esta plataforma. Tienes que solicitarlos en Authelia para que tu perfil sea habilitado por el administrador», con un botón directo para acceder a la pantalla de autenticación.

### Impacto

Afecta a [deploy/errors/403.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/403.html), [deploy/errors/502.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/502.html) y las pruebas en [tests/deploy/test_nginx_error_pages.py](file:///home/dtovar/bayblade/pokemon/tests/deploy/test_nginx_error_pages.py).


Clarificación de Bloqueo por Authelia y Solicitud al Administrador en Plataforma ADUANA

## Control de Acceso y Experiencia de Usuario

### Regla

En las páginas de error `403.html` (Forbidden) y `502.html` (Bad Gateway) de Nginx se establece con exactitud técnica y de experiencia de usuario:
1. **Identificación de la Causa del Bloqueo**: Se indica explícitamente que Authelia (el proveedor SSO) está bloqueando el acceso porque la cuenta no cuenta con los permisos requeridos.
2. **Canal Oficial de Gestión de Permisos**: Se aclara al usuario que el trámite de asignación de roles no se realiza en el proveedor de identidad, sino que debe solicitar el acceso al administrador a través de la plataforma ADUANA.
3. **Acción Principal**: El botón primario de navegación («Solicitar acceso en ADUANA») dirige al catálogo de plataformas y gestión de solicitudes (`/platforms`).

### Ejemplo

Un usuario que navega a una herramienta interna sin la membresía de grupos necesaria visualiza en pantalla: «Authelia está bloqueando el acceso a esta plataforma porque tu cuenta no cuenta con los permisos necesarios. Para poder ingresar, debes solicitar el acceso al administrador a través de la plataforma ADUANA», con un botón directo hacia el catálogo de ADUANA.

### Impacto

Afecta a [deploy/errors/403.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/403.html), [deploy/errors/502.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/502.html) y [tests/deploy/test_nginx_error_pages.py](file:///home/dtovar/bayblade/pokemon/tests/deploy/test_nginx_error_pages.py).


Detección Contextual Dinámica de Plataforma y Enlace de Búsqueda en Páginas de Error

## Experiencia de Usuario e Infraestructura

### Regla

Las páginas de error de Nginx (`403.html`, `502.html`) detectan dinámicamente en tiempo de ejecución en el navegador la plataforma específica que el usuario intentó acceder:
1. **Detección por Host y Parámetros SSO**: Mediante `deploy/errors/assets/js/error.js`, se inspecciona el subdominio (`window.location.hostname`), la ruta solicitada y los parámetros de redirección provistos por Authelia (`rd`, `target`, `redirect_uri`).
2. **Inyección en Tiempo Real**: Se reemplazan automáticamente los marcadores `[data-plataforma-nombre]` y `[data-plataforma-host]`, mostrando al usuario el nombre amigable de la plataforma bloqueada (ej. «terminal-packet») y su host/ruta exacta de destino.
3. **Pre-filtrado en ADUANA**: El botón «Solicitar acceso en ADUANA» (`[data-link-aduana]`) concatena automáticamente el parámetro `?buscar=<nombre_plataforma>`, permitiendo que al hacer clic, el catálogo de ADUANA ya esté filtrado en la herramienta requerida para solicitar el acceso de inmediato.

### Ejemplo

Un usuario intenta ingresar a `https://terminal-packet.vivaro.com/core/` y es bloqueado por Authelia. La página muestra: «Authelia está bloqueando el acceso a «terminal-packet» porque tu cuenta no cuenta con los permisos necesarios...», detallando en el recuadro técnico `terminal-packet.vivaro.com/core/`, y el botón redirige directamente a `/platforms?buscar=terminal-packet`.

### Impacto

Afecta a [deploy/errors/assets/js/error.js](file:///home/dtovar/bayblade/pokemon/deploy/errors/assets/js/error.js), [deploy/errors/403.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/403.html), [deploy/errors/502.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/502.html) y [tests/deploy/test_nginx_error_pages.py](file:///home/dtovar/bayblade/pokemon/tests/deploy/test_nginx_error_pages.py).


Diseño Simplificado de Error por Falta de Acceso con Icono de Plataforma

## Experiencia de Usuario y Comunicación Directa

### Regla

Las páginas de error `403.html` y `502.html` de Nginx se simplifican para el usuario final, eliminando tecnicismos y detalles de infraestructura interna:
1. **Sin Mención a Proveedores Técnicos**: Se omite cualquier referencia a nombres de software de autenticación interna (como Authelia) que un usuario de nuevo ingreso desconoce.
2. **Mensaje Breve y Directo**: Se comunica exclusivamente: «No tienes acceso al recurso solicitado. Tienes que pedir acceso a tu administrador para ingresar.»
3. **Omisión de Detalles Técnicos**: Se retira el recuadro técnico de diagnóstico para evitar confusión o alarma innecesaria en el colaborador.
4. **Icono y Nombre de Plataforma**: Se muestra en el cuerpo de la pantalla el icono/avatar dinámico de la plataforma requerida (con iniciales de respaldo) y su nombre formateado.
5. **Botón a ADUANA**: Se mantiene el botón principal «Solicitar acceso en ADUANA» apuntando al catálogo para gestionar la solicitud de acceso de inmediato.

### Ejemplo

Un usuario que intenta abrir una plataforma sin tener los permisos asignados ve en pantalla el icono y título de la herramienta, acompañado únicamente del texto: «No tienes acceso al recurso solicitado. Tienes que pedir acceso a tu administrador para ingresar», junto al botón que lo envía a ADUANA.

### Impacto

Afecta a [deploy/errors/403.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/403.html), [deploy/errors/502.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/502.html), [deploy/errors/assets/css/error.css](file:///home/dtovar/bayblade/pokemon/deploy/errors/assets/css/error.css) y [deploy/errors/assets/js/error.js](file:///home/dtovar/bayblade/pokemon/deploy/errors/assets/js/error.js).


Mapeo de Grupos OIDC de Authelia y Asignación de Roles y Áreas

## Autenticación, Autorización y Multitenancy

### Regla

1. **Mapeo de Grupos Authelia a Roles**:
   La pertenencia a grupos enviada por Authelia mediante OIDC (claim `groups` habilitado con el scope `groups`) determina automáticamente el rol del usuario en la plataforma ADUANA según la siguiente jerarquía de precedencia:
   - **Superadmin (`administrador`)**: Asignado al pertenecer al grupo configurado en `OIDC_GROUP_SUPERADMIN` (por omisión: `infraestructuraVoIP`).
   - **Administrador de Área (`admin_area`)**: Asignado al pertenecer al grupo configurado en `OIDC_GROUP_AREA_ADMIN` (por omisión: `app-aduana-admins`).
   - **Usuario Regular (`usuario`)**: Asignado al pertenecer al grupo configurado en `OIDC_GROUP_USER` (por omisión: `app-aduana-users`).
   - Si la cuenta no pertenece a ningún grupo mapeado o no se especifican grupos, entra por omisión como `usuario`.
   - La cuenta local de emergencia (`admin`) se mantiene reservada y protegida como punto de recuperación ante contingencias de conectividad o infraestructura SSO.

2. **Sincronización Dinámica de Roles en SSO**:
   En cada inicio de sesión exitoso por OIDC, si los grupos del colaborador cambiaron en Authelia, su rol en ADUANA se actualiza automáticamente. Si un usuario deja de ser `admin_area`, sus áreas administradas se limpian y sus accesos automáticos de administrador bajan a nivel `usuario` (grupo `-users`) y los conserva, en la misma transacción auditada (`Evento.ROL_CAMBIADO`; FNC-185).

3. **Gestión y Asignación de Áreas**:
   - **Alta por Admin de Área**: Cuando un `admin_area` da de alta una nueva área (`POST /api/v1/areas`), él se convierte automáticamente en el administrador asignado a dicha área (`current_user.managed_areas.append(area)`).
   - **Alta por Superadmin**: Cuando un `administrador` (superadmin) crea un área, no se asigna ningún administrador por defecto (`area.admins = []`), mostrándose como «Sin asignar» en el listado.
   - **Visibilidad y Delegación para Superadmin**: El superadmin visualiza en el listado de áreas (`GET /api/v1/areas` y tabla en panel web) todas las áreas existentes y la lista de administradores asignados (`admins`, `admin_names`). La asignación y reasignación de administradores a cada área es controlada por el superadmin mediante `PUT /api/v1/users/<id>/managed-areas` desde el modal de administración de áreas.

### Ejemplo

1. Un colaborador que pertenece al grupo `infraestructuraVoIP` inicia sesión mediante Authelia y obtiene de inmediato el rol `administrador` (superadmin) en ADUANA.
2. Un colaborador que pertenece a `app-aduana-admins` obtiene el rol `admin_area`. Al crear el área «Operaciones Marítimas», queda inmediatamente vinculado como su administrador.
3. El superadmin crea el área «Carga General». El área queda registrada sin administradores («Sin asignar»), hasta que el superadmin asigna manualmente a un `admin_area` a través del panel de áreas.

### Impacto

Afecta a [app/modules/auth/oidc.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/oidc.py), [app/modules/auth/oidc_cuentas.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/oidc_cuentas.py), [app/modules/auth/oidc_configuracion.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/oidc_configuracion.py), [app/modules/areas/api.py](file:///home/dtovar/bayblade/pokemon/app/modules/areas/api.py), [.env.example](file:///home/dtovar/bayblade/pokemon/.env.example), [docs/configuracion/VARIABLES.md](file:///home/dtovar/bayblade/pokemon/docs/configuracion/VARIABLES.md) y [tests/test_oidc.py](file:///home/dtovar/bayblade/pokemon/tests/test_oidc.py).


Autorización Estricta OIDC por Grupos de Authelia (Deny by Default)

## Autenticación y Control de Acceso (RBAC)

### Regla

1. **Principio de Denegación por Defecto (Deny by Default)**:
   La pertenencia a al menos uno de los grupos autorizados (`infraestructuraVoIP`, `app-aduana-admins` o `app-aduana-users`) es condición obligatoria para ingresar al portal ADUANA vía OIDC.
2. **Rechazo Inmediato para Cuentas No Mapeadas**:
   Si una cuenta autenticada en Authelia no pertenece a ninguno de los grupos autorizados (o el claim `groups` está vacío o solo contiene grupos ajenos a la plataforma):
   - El acceso es rechazado inmediatamente con código `acceso_denegado` (`ErrorOidc(ERROR_DENEGADO)`).
   - No se crea cuenta en la base de datos ni se abre sesión de usuario.
   - Si se trataba de una cuenta existente de SSO a la que se le retiraron los grupos en el directorio/Authelia, no se le permite iniciar sesión y el intento fallido se audita como `ACCESO OIDC FALLIDO`.
3. **Mapeo Explícito y Estricto**:
   - `infraestructuraVoIP` $\rightarrow$ `administrador` (Superadmin)
   - `app-aduana-admins` $\rightarrow$ `admin_area` (Admin de Área)
   - `app-aduana-users` $\rightarrow$ `usuario` (Usuario estándar)
   - Ningún otro grupo concede acceso o privilegios.

### Ejemplo

Un colaborador de la empresa que tiene credenciales activas en Authelia para otros sistemas internos intenta ingresar a ADUANA sin haber sido incorporado al grupo `app-aduana-users`. El callback OIDC detecta que no cuenta con ninguno de los tres grupos autorizados y rechaza el acceso con `error=acceso_denegado`, impidiendo su ingreso al portal.

### Impacto

Afecta a [app/modules/auth/oidc_cuentas.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/oidc_cuentas.py), [tests/oidc_simulado.py](file:///home/dtovar/bayblade/pokemon/tests/oidc_simulado.py) y [tests/test_oidc.py](file:///home/dtovar/bayblade/pokemon/tests/test_oidc.py).


Enlaces Absolutos a ADUANA en Páginas de Error Nginx

## Infraestructura y Páginas de Error Nginx

### Regla

1. **Rutas Absolutas Hacia el Dominio Central de ADUANA**:
   Todas las páginas de error corporativas de Nginx (403, 404, 500, 502, 503, 504, 50x) alojadas en la capa de reverse proxy para sitios satélite (`netbox`, `bookstack`, `graylog`, etc.) deben emplear exclusivamente URLs absolutas apuntando a `https://aduana.vivaro.com`.
2. **Prohibición de Enlaces Relativos**:
   Queda prohibido el uso de rutas relativas como `/platforms` o `/dashboard` en las plantillas HTML o en los scripts asociados, dado que el navegador las resolvería contra el propio dominio satélite en el que se originó el error (ej. `https://netbox-mon.vivaro.com/platforms`), provocando errores de navegación o bloqueos recurrentes.
3. **Normalización Dinámica y Prefiltrado**:
   - El botón primario "Solicitar acceso en ADUANA" debe apuntar a `https://aduana.vivaro.com/platforms?buscar={slug_plataforma}`.
   - El botón secundario "Ir al Dashboard" debe apuntar a `https://aduana.vivaro.com/dashboard`.
   - `error.js` garantiza la normalización forzosa de cualquier enlace hacia `https://aduana.vivaro.com` si se cargara sin protocolo absoluto.

### Ejemplo

Un usuario sin permisos accede a `https://netbox-mon.vivaro.com/login` y recibe el error 403. Al hacer clic en "Solicitar acceso en ADUANA", el botón lo redirige de inmediato a `https://aduana.vivaro.com/platforms?buscar=netbox-mon`, donde el catálogo precarga el filtro con la herramienta deseada. Si hace clic en "Ir al Dashboard", es dirigido a `https://aduana.vivaro.com/dashboard`.

### Impacto

Afecta a [deploy/errors/403.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/403.html), [deploy/errors/502.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/502.html), [deploy/errors/assets/js/error.js](file:///home/dtovar/bayblade/pokemon/deploy/errors/assets/js/error.js) y [frontend/src/components/platforms/platforms-shell.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/platforms/platforms-shell.tsx).


Botón Único de Acción en Página de Error 403

## Infraestructura y Páginas de Error Nginx

### Regla

La página de error 403 (`deploy/errors/403.html`) simplifica su zona de acciones presentando exclusivamente un único botón de acción principal: "Solicitar acceso en ADUANA". Se retira de forma definitiva el botón secundario "Ir al Dashboard" para enfocar la experiencia del usuario hacia el flujo de solicitud contextual directa en `https://aduana.vivaro.com/platforms?buscar={slug_plataforma}`.

### Ejemplo

Al acceder a `https://netbox-mon.vivaro.com/login` y resultar denegado con 403, la tarjeta muestra únicamente el botón "Solicitar acceso en ADUANA". Al pulsar dicho botón, el usuario es redirigido a `https://aduana.vivaro.com/platforms?buscar=netbox-mon`.

### Impacto

Afecta a [deploy/errors/403.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/403.html) y [deploy/errors/assets/js/error.js](file:///home/dtovar/bayblade/pokemon/deploy/errors/assets/js/error.js).


Pantalla de Acceso Denegado con Auto-Refresh y Correo de Soporte

## Autenticación y Control de Acceso (RBAC)

### Regla

1. **Pantalla Dedicada para Acceso Denegado**:
   Cuando un usuario autenticado ante Authelia no pertenece a ningún grupo autorizado (`acceso_denegado`), el portal despliega una pantalla de error dedicada (`AccesoDenegadoView` en `/acceso-denegado` y en `/login?error=acceso_denegado`), reemplazando el toast efímero por una experiencia explicativa y resolutiva.
2. **Instrucciones Claras de Gestión**:
   La pantalla indica explícitamente que la cuenta carece de permisos para ingresar a ADUANA y orienta al colaborador a comunicarse con su superior inmediato o a enviar un correo a la dirección de soporte configurada (`SUPPORT_EMAIL` / `NEXT_PUBLIC_SUPPORT_EMAIL`, por omisión `aduana-app@vivaro.com`).
3. **Mecanismo de Auto-Refresh Inteligente**:
   La pantalla implementa un temporizador regresivo de 15 segundos con barra animada de progreso y controles de pausa/reanudación. Al completarse el conteo, reintenta automáticamente la autenticación vía OIDC (`/api/v1/auth/oidc/login`), permitiendo el ingreso inmediato al Dashboard tan pronto como el superior o administrador asigne los grupos requeridos en el directorio, sin necesidad de recargas manuales.
4. **Controles de Interacción**:
   Dispone de un botón "Reintentar ahora", control de pausa/reanudación del temporizador, botón mailto preformateado y enlace de retorno al login.

### Ejemplo

Un colaborador sin grupo autorizado intenta ingresar a ADUANA y es rechazado. El portal despliega la pantalla "Sin acceso a la plataforma" con un contador de 15 segundos y la opción de enviar correo a `aduana-app@vivaro.com`. Mientras avisa a su superior, este le asigna el grupo `app-aduana-users`. Al finalizar el conteo regresivo, el portal reintenta la sesión con Authelia y el usuario ingresa de forma automática al Dashboard.

### Impacto

Afecta a [frontend/src/components/acceso-denegado-view.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/acceso-denegado-view.tsx), [frontend/src/app/acceso-denegado/page.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/app/acceso-denegado/page.tsx), [frontend/src/components/login-form.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/login-form.tsx), [app/modules/api/auth.py](file:///home/dtovar/bayblade/pokemon/app/modules/api/auth.py), [.env.example](file:///home/dtovar/bayblade/pokemon/.env.example) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Auto-creación de Grupos de Plataforma y Asignación de Grupo de Portal en LDAP

## Directorio y Aprovisionamiento (OpenLDAP & Worker)

### Regla

1. **Auto-creación de Grupos al Crear Plataformas**:
   Al dar de alta una plataforma con integración LDAP (`integration_type: 'ldap'`), el backend valida y asegura la existencia de los grupos de nivel usuario y administrador (`ldap_group_user_dn` y `ldap_group_admin_dn`, bajo la convención `app-{plataforma}-users` y `app-{plataforma}-admins`). Si los grupos no existen en OpenLDAP, el backend (`EscritorDirectorio.create_group`) los crea de forma automática bajo `LDAP_GROUPS_BASE_DN` con la clase `groupOfNames` (y miembro de relleno configurado), registrándose la plataforma con `groups_status: 'ok'` sin requerir aprovisionamiento manual previo en el directorio.
2. **Auto-recuperación y Creación de Grupos en Worker**:
   Cuando el worker de aprovisionamiento (`portal-worker`) procesa una operación de otorgamiento de acceso (`otorgar`) y el grupo de la plataforma no existe en OpenLDAP (`MOTIVO_GRUPO_INEXISTENTE`), el proveedor LDAP crea el grupo dinámicamente mediante `create_group` y reintenta la membresía, garantizando un aprovisionamiento auto-reparable y resiliente sin interrupción de tareas.
3. **Asignación Automática a app-aduana-users en Alta de Usuario**:
   Al crear una cuenta en el directorio desde el portal (`POST /users/directory`), el backend crea la entrada en `ou=users` y la agrega inmediatamente al grupo de usuarios regulares de ADUANA (`app-aduana-users` / `LDAP_APP_USERS`), creando el grupo si no existiera. Esto garantiza que el colaborador recién creado pueda autenticarse de inmediato en el portal vía Authelia OIDC sin ser bloqueado por ausencia de grupo.

### Ejemplo

1. Un administrador crea la plataforma «Netbox Mon» en el portal. El backend crea automáticamente en OpenLDAP los grupos `cn=app-netbox-mon-users,ou=groups,dc=vivaro,dc=local` y `cn=app-netbox-mon-admins,ou=groups,dc=vivaro,dc=local`.
2. Se da de alta al colaborador `juan.perez@vivaro.com` desde la pantalla de usuarios. El backend crea su entrada LDAP y lo añade de inmediato al grupo `app-aduana-users`. Al ingresar por primera vez con Authelia, se le concede acceso al portal sin error.

### Impacto

Afecta a [app/modules/directory/writer.py](file:///home/dtovar/bayblade/pokemon/app/modules/directory/writer.py), [app/modules/platforms/api.py](file:///home/dtovar/bayblade/pokemon/app/modules/platforms/api.py), [app/modules/provisioning/ldap_provider.py](file:///home/dtovar/bayblade/pokemon/app/modules/provisioning/ldap_provider.py), [app/modules/users/directory_accounts.py](file:///home/dtovar/bayblade/pokemon/app/modules/users/directory_accounts.py), [.env.example](file:///home/dtovar/bayblade/pokemon/.env.example) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Sincronización de Grupos OIDC por Rol de Usuario y Convención de Plataformas

## Autenticación, Usuarios y Directorio (OIDC & OpenLDAP)

### Regla

1. **Mapeo y Sincronización de Grupos OIDC según Rol en ADUANA**:
   Al crear un usuario desde ADUANA (`POST /users` o `POST /users/directory`), el backend determina su grupo OIDC en OpenLDAP según su rol:
   - Si el rol es de administración (`ROLE_AREA_ADMIN`, `admin_area`, `admin`, `administrador`), se agrega a `OIDC_GROUP_AREA_ADMIN` (por omisión: `app-aduana-admins`).
   - Si el rol es estándar (`ROLE_USER`, `usuario`, `user`), se agrega a `OIDC_GROUP_USER` (por omisión: `app-aduana-users`).
   Si el grupo no existe en el directorio, se crea automáticamente.
2. **Sincronización Dinámica al Cambiar de Rol**:
   Al modificar el rol de un usuario (`PUT /users/<id>`), si el directorio está activo, el backend actualiza atómicamente la pertenencia en LDAP, retirándolo del grupo anterior y agregándolo al nuevo grupo correspondiente (`app-aduana-admins` o `app-aduana-users`).
3. **Estandarización de Nombres de Grupos de Plataforma en Plural**:
   Para mantener compatibilidad estricta con Authelia y la nomenclatura institucional de Vivaro, los grupos generados para plataformas que utilicen el prefijo `app-` (o con `LDAP_GROUP_PLURAL=true`) derivan obligatoriamente los niveles en plural en inglés:
   - Nivel usuario: `app-{plataforma}-users`
   - Nivel administrador: `app-{plataforma}-admins`
4. **Manejo de Error 403 en Nginx bajo auth_request con Authelia**:
   En configuraciones de Nginx donde `location /` contiene la directiva `error_page 401 =302 $redirection_url;`, Nginx por diseño anula la herencia de las directivas `error_page` del bloque `server`. Para que el usuario vea la pantalla corporativa de ADUANA en lugar del error estándar en texto plano de Nginx (`403 Forbidden nginx/1.20.1`), se debe definir explícitamente `error_page 403 /errors/403.html;` dentro del bloque `location /` que invoca `auth_request`.

### Ejemplo

- Un administrador crea en ADUANA el usuario `operador@vivaro.com` con rol `usuario`. El sistema lo crea en OpenLDAP y lo añade a `cn=app-aduana-users,ou=groups,dc=vivaro,dc=com`. Cuando este usuario se autentica en Authelia e ingresa a ADUANA, Authelia emite el claim `groups: ["app-aduana-users"]` y ADUANA le otorga el rol de usuario sin rechazo.
- Para la plataforma `netbox-mon`, el sistema deriva y asegura los grupos `cn=app-netbox-mon-users,...` y `cn=app-netbox-mon-admins,...`.
- En `netbox.conf`, dentro de `location /`, se añade `error_page 403 /errors/403.html;`. Cuando un usuario sin permisos intenta acceder a Netbox, Authelia responde 403 y Nginx muestra la pantalla interactiva corporativa de ADUANA en lugar del error blanco por defecto.

### Impacto

Afecta a [app/modules/users/api.py](file:///home/dtovar/bayblade/pokemon/app/modules/users/api.py), [app/modules/users/directory_accounts.py](file:///home/dtovar/bayblade/pokemon/app/modules/users/directory_accounts.py), [app/modules/platforms/grupos.py](file:///home/dtovar/bayblade/pokemon/app/modules/platforms/grupos.py), [.env.example](file:///home/dtovar/bayblade/pokemon/.env.example), [tests/platforms/test_integracion_y_grupos.py](file:///home/dtovar/bayblade/pokemon/tests/platforms/test_integracion_y_grupos.py) y las configuraciones de Nginx para plataformas protegidas.


Personalización del Nombre de Plataforma e Independencia de Dominio en el Instalador

## Despliegue, Identidad e Instalación (deploy/install.sh)

### Regla

1. **Interacción y Desacoplamiento de Marca en la Instalación**:
   El instalador (`deploy/install.sh`) no asume de forma fija el nombre "Aduana" ni el dominio "vivaro.com". Al ejecutarse en una terminal interactiva (sin flags explícitos ni en modo `--actualizar`), solicita al operador:
   - El **nombre comercial / visible de la plataforma** (`APP_TITLE`, ej. `Aduana`, `Nexus`, `Portal TI`), permitiendo renombrar la interfaz completa del producto.
   - El **identificador técnico de despliegue** (`APP_NAME`, derivado de `APP_TITLE` o de la carpeta), usado para las unidades systemd (`<name>-backend`, `<name>-frontend`, `<name>-worker`), los registros (`/var/log/<name>`) y la configuración de Nginx (`/etc/nginx/conf.d/<name>.conf`).
   - El **dominio FQDN de instalación** (`DOMAIN`, ej. `aduana.tuempresa.com`, `portal.example.com`), eliminando cualquier amarre rígido a dominios institucionales predeterminados.
2. **Propagación Automática a Variables de Entorno y Metadatos**:
   Los valores configurados se registran de forma persistente en `.env` (`APP_NAME`, `APP_TITLE`, `NEXT_PUBLIC_APP_TITLE`, `DOMAIN`, `NEXT_PUBLIC_DOMAIN`) y se inyectan en:
   - Las unidades systemd mediante marcadores `@APP_NAME@`, `@APP_TITLE@`, `@DOMAIN@`.
   - La configuración de Nginx (`server_name @DOMAIN@`).
   - Las páginas corporativas de error (`deploy/errors/*.html`) en las etiquetas `<meta name="portal-domain">` y `<meta name="portal-title">`.
3. **Detección Dinámica de Origen en Scripts de Error**:
   El script de páginas de error de Nginx (`deploy/errors/assets/js/error.js`) resuelve dinámicamente el origen del portal a partir de la etiqueta `<meta name="portal-domain">` (o de `window.location.origin`), garantizando que los enlaces de retorno o solicitud de acceso redirijan con precisión al dominio donde se encuentra alojada la plataforma sin depender de URLs estáticas.
4. **Branding Dinámico en la Interfaz Web**:
   El frontend Next.js consume `NEXT_PUBLIC_APP_TITLE` y `NEXT_PUBLIC_DOMAIN` mediante `lib/branding.ts`, asegurando que la barra lateral, la barra superior, la pantalla de inicio de sesión, el acceso de contingencia y la vista de acceso denegado reflejen inmediatamente el nombre elegido por el administrador.

### Ejemplo

Durante la instalación en un servidor independiente, el operador indica `Nexus` como nombre de la plataforma y `seguridad.midominio.org` como dominio. El instalador configura las unidades `nexus-backend`, `nexus-frontend` y `nexus-worker`, registra `DOMAIN=seguridad.midominio.org` en `.env` y genera el virtualhost en `/etc/nginx/conf.d/nexus.conf`. La interfaz web completa se titula "Nexus" y los enlaces de solicitud de acceso dirigen a `https://seguridad.midominio.org/platforms`.

### Impacto

Afecta a [deploy/install.sh](file:///home/dtovar/bayblade/pokemon/deploy/install.sh), [deploy/errors/assets/js/error.js](file:///home/dtovar/bayblade/pokemon/deploy/errors/assets/js/error.js), [deploy/errors/*.html](file:///home/dtovar/bayblade/pokemon/deploy/errors/403.html), [frontend/next.config.ts](file:///home/dtovar/bayblade/pokemon/frontend/next.config.ts), [frontend/src/lib/branding.ts](file:///home/dtovar/bayblade/pokemon/frontend/src/lib/branding.ts), [app/modules/api/auth.py](file:///home/dtovar/bayblade/pokemon/app/modules/api/auth.py), [.env.example](file:///home/dtovar/bayblade/pokemon/.env.example) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Validación de Servicios Previos e Idempotencia en el Instalador

## Despliegue y Control de Servicios (deploy/install.sh & deploy/unidades.sh)

### Regla

1. **Introspección Directa de Servicios en Systemd**:
   El instalador no depende de archivos de bloqueo efímeros ni de registros volátiles en base de datos para determinar si existe una instalación previa en el host. En su lugar, consulta la fuente de verdad definitiva del sistema operativo mediante `unidad_systemd_existe` (`systemctl list-unit-files`) sobre `${APP_NAME}-backend.service`, `${APP_NAME}-frontend.service` y `${APP_NAME}-worker.service`.
2. **Protección Interactiva contra Sobrescrituras Accidentales**:
   Si se ejecuta `install.sh` en modo de instalación estándar (sin `--force` y sin `--actualizar`) en una terminal interactiva y el instalador detecta que la unidad `${APP_NAME}-backend.service` ya existe:
   - Alerta al operador indicando la presencia de servicios en ejecución.
   - Recomienda el uso de `sudo ./deploy/install.sh --actualizar` (para actualizar el código y dependencias sin alterar infraestructura ni configuración).
   - Recomienda el uso de `sudo ./deploy/install.sh --force` (para una reinstalación limpia desde cero que desmonte servicios previos).
   - Solicita confirmación explícita `[s/N]`. Si el usuario no confirma, la ejecución se cancela de forma inmediata sin alterar ningún servicio ni archivo del sistema.
3. **Comportamiento en Automatización / CI**:
   En entornos no interactivos (sin terminal TTY adjunta), el instalador conserva su naturaleza idempotente, emitiendo una notificación de advertencia y actualizando las definiciones de las unidades de forma segura.
4. **Protección a Nivel Base de Datos**:
   La integridad del esquema relacional está salvaguardada por el control transaccional de migraciones de Alembic (`alembic_version`), impidiendo la colisión o duplicidad de tablas si una base de datos ya fue aprovisionada previamente.

### Ejemplo

Un administrador ejecuta `sudo ./deploy/install.sh` habiendo instalado previamente la plataforma `aduana`. El script detecta de inmediato `aduana-backend.service` en `/etc/systemd/system/`, emite una alerta sugiriendo correr con `--actualizar` para una actualización limpia de código, y le pregunta si desea sobrescribir los servicios. Si el operador pulsa `N`, el proceso se detiene de forma segura sin interrumpir la operación actual.

### Impacto

Afecta a [deploy/install.sh](file:///home/dtovar/bayblade/pokemon/deploy/install.sh), [deploy/unidades.sh](file:///home/dtovar/bayblade/pokemon/deploy/unidades.sh), [tests/deploy/test_unidades_sh.py](file:///home/dtovar/bayblade/pokemon/tests/deploy/test_unidades_sh.py) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Integridad de Importaciones y Validación de Compilación en Frontend

## Compilación y Empaquetado (frontend/src)

### Regla

1. **Unicidad Estricta de Identificadores e Importaciones**:
   Todo módulo o componente React en `frontend/src` debe importar cada identificador o paquete una sola vez en el encabezado del archivo. La duplicación de declaraciones de importación (como `import Link from 'next/link'`) genera errores de análisis estático en Webpack/SWC durante `next build`, provocando fallos en la generación de artefactos estáticos de producción.
2. **Validación Previa al Despliegue**:
   Cualquier actualización en los componentes de autenticación o layouts debe compilar exitosamente vía `next build` y superar las pruebas unitarias de `vitest` antes de integrarse a las ramas productivas.

### Ejemplo

En `acceso-emergencia-form.tsx`, la inserción de tokens de marca no debe re-declarar la sentencia `import Link from 'next/link'`. El archivo conserva una única importación limpia del componente de enlace.

### Impacto

Afecta a [frontend/src/components/acceso-emergencia-form.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/acceso-emergencia-form.tsx) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Autoservicio de Contraseñas y Sincronización con JumpServer

## Autenticación y Autoservicio (app/modules/auth/autoservicio.py & frontend/src/app/autoservicio)

### Regla

1. **Centralización del Autoservicio en Aduana**:
   Para resolver la limitación de IdPs como Authelia (que no emiten webhooks de contraseñas tras reseteos de autoservicio), Aduana centraliza el flujo de actualización y recuperación de contraseñas de los usuarios corporativos en la ruta `/autoservicio` (y `/cambiar-contrasena`).
2. **Doble Modalidad de Autoservicio**:
   - **Cambio Directo con Contraseña Previa**: Si el usuario conoce su contraseña actual (o está expirada/marcada con `pwdReset: TRUE` en LDAP), se valida contra OpenLDAP y se actualiza atómicamente mediante Password Modify (RFC 3062).
   - **Recuperación con Token Temporal**: Si el usuario olvidó su contraseña, se genera un token criptográfico firmado (HMAC-SHA256 con TTL de 15 minutos) enviado por correo corporativo vía SMTP. Al confirmarlo, se actualiza la cuenta en el directorio sin requerir la contraseña anterior.
3. **Sincronización Inmediata con JumpServer**:
   En el mismo instante en que el backend de Aduana recibe la nueva contraseña en memoria, avisa a JumpServer (`integraciones/jumpserver.py`, oyente de `EscritorDirectorio`, FNC-190: lo mismo en cualquier cambio de contraseña en LDAP), garantizando que las credenciales para el autologeo a activos y bastiones nunca queden obsoletas ni desfasadas.
4. **Protección Anti-Enumeración y Fuerza Bruta**:
   - La solicitud de recuperación por correo responde siempre de forma genérica para no revelar qué identidades existen en el directorio.
   - Las solicitudes fallidas acumulan eventos en la bitácora de auditoría e interactúan con el mecanismo de bloqueo por IP y cuenta (`bloqueado`).

### Ejemplo

Un usuario corporativo que utiliza el JumpServer para acceder a switches de red cambia su contraseña expirada desde `https://aduana.vivaro.com/autoservicio`. El backend actualiza `userPassword` en OpenLDAP e inmediatamente sincroniza la credencial hacia JumpServer. Cuando el usuario abre una sesión RDP/SSH en JumpServer, el autologeo funciona de forma transparente sin que deba reconfigurar su cuenta.

### Impacto

Afecta a [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py), [app/modules/api/auth.py](file:///home/dtovar/bayblade/pokemon/app/modules/api/auth.py), [frontend/src/app/autoservicio/page.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/app/autoservicio/page.tsx), [frontend/src/app/cambiar-contrasena/page.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/app/cambiar-contrasena/page.tsx), [frontend/src/components/autoservicio-view.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/autoservicio-view.tsx), [frontend/src/lib/api.ts](file:///home/dtovar/bayblade/pokemon/frontend/src/lib/api.ts), [tests/test_autoservicio.py](file:///home/dtovar/bayblade/pokemon/tests/test_autoservicio.py) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Identidad Authelia y Factor de Autenticación Múltiple (MFA) en el Autoservicio

## Autenticación y Autoservicio (app/modules/auth/autoservicio.py & frontend/src/components/autoservicio-view.tsx)

### Regla

1. **Identidad Visual Branded como Authelia**:
   Para mantener la coherencia del flujo de seguridad cuando los usuarios son redirigidos desde el Single Sign-On de Authelia o requieren actualizar credenciales corporativas, la interfaz de autoservicio (`/autoservicio` y `/cambiar-contrasena`) se presenta bajo la identidad oficial y lenguaje de marca de **Authelia** (Single Sign-On & MFA), asegurando al usuario que la tarea forma parte del flujo corporativo legítimo sin confusión de sistemas.
2. **Autenticación Multifactor (MFA) Configurable**:
   El autoservicio soporta validación de segundo factor mediante la variable de entorno `AUTOSERVICIO_MFA_ENABLED`:
   - Si `AUTOSERVICIO_MFA_TIPO=email`: el usuario solicita un código numérico aleatorio de 6 dígitos que se despacha a su correo registrado mediante un token HMAC-SHA256 con TTL de 10 minutos y limitación de reenvíos por temporizador.
   - Si `AUTOSERVICIO_MFA_TIPO=authenticator`: el usuario valida un código TOTP de 6 dígitos basado en RFC 6238 generado por su aplicación de autenticación vinculada a Authelia.
   - Si `AUTOSERVICIO_MFA_TIPO=ambos`: la interfaz permite seleccionar cualquiera de ambos métodos de comprobación.
3. **Servidor SMTP Dedicado con Fallback**:
   El envío de correos de autoservicio (código MFA y enlace de recuperación) prioriza las variables específicas `AUTOSERVICIO_SMTP_*`. Si no están configuradas, utiliza como fallback la configuración global de correo `SMTP_*`, garantizando alta disponibilidad del servicio de mensajería transaccional de seguridad.
4. **Validación Criptográfica Stateless**:
   Los desafíos MFA se validan mediante tokens firmados con la `SECRET_KEY` de la plataforma, evitando almacenamiento volátil en memoria y permitiendo balanceo de carga sin pérdida de estado entre procesos workers.

### Ejemplo

Un usuario que olvida su contraseña accede a `/autoservicio`. Con `AUTOSERVICIO_MFA_ENABLED=true` y `AUTOSERVICIO_MFA_TIPO=email`, el usuario ingresa su correo institucional y presiona "Enviar código por correo". El backend despacha un correo firmado como "Authelia • Autoservicio de Identidad" con un código de 6 dígitos. Tras ingresar su código y su nueva contraseña de 16+ caracteres, la credencial se actualiza en OpenLDAP y se sincroniza automáticamente con JumpServer.

### Impacto

Afecta a [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py), [app/modules/api/auth.py](file:///home/dtovar/bayblade/pokemon/app/modules/api/auth.py), [frontend/src/components/autoservicio-view.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/autoservicio-view.tsx), [frontend/src/lib/api.ts](file:///home/dtovar/bayblade/pokemon/frontend/src/lib/api.ts), [.env.example](file:///home/dtovar/bayblade/pokemon/.env.example), [docs/configuracion/VARIABLES.md](file:///home/dtovar/bayblade/pokemon/docs/configuracion/VARIABLES.md), y [tests/test_autoservicio.py](file:///home/dtovar/bayblade/pokemon/tests/test_autoservicio.py).


Generador Criptográfico y Validación de Contraseñas en Autoservicio

## Autenticación y Autoservicio (frontend/src/components/autoservicio-view.tsx & app/modules/users/politica_contrasena.py)

### Regla

1. **Generador Criptográfico Incorporado**:
   La interfaz de autoservicio de contraseñas (`/autoservicio` y `/cambiar-contrasena`) incluye una acción directa "Generar contraseña" que invoca el generador criptográfico institucional (`generarContrasenaSegura`). El generador utiliza `crypto.getRandomValues` con muestreo por rechazo sin sesgo de módulo y barajado Fisher-Yates, produciendo una clave de 24 caracteres aleatorios.
2. **Cumplimiento Integral de Política en Generación**:
   La contraseña generada garantiza de forma determinista la presencia de todas las clases obligatorias:
   - Al menos 1 letra mayúscula (`A-Z`).
   - Al menos 1 letra minúscula (`a-z`).
   - Al menos 1 dígito numérico (`0-9`).
   - Al menos 1 símbolo especial permitido del conjunto corporativo (`!@#$%^&*()_+-=[]{}|;:,.<>?`).
   - Longitud estricta superior al mínimo de 16 caracteres (24 caracteres).
3. **Experiencia y Portapapeles**:
   Al pulsar el generador, se rellenan automáticamente los campos "Nueva Contraseña" y "Confirmar Nueva Contraseña", se activa la visibilidad de caracteres para verificación visual inmediata, se copia la clave al portapapeles del usuario y se satisfacen simultáneamente todos los indicadores del checklist de seguridad en tiempo real.
4. **Validación Simétrica en Servidor**:
   El backend valida nuevamente la clave enviada contra `PoliticaContrasena`, impidiendo caracteres prohibidos que pudieran comprometer la integración con LDAP (`"'\ `) o JumpServer.

### Ejemplo

Un usuario corporativo que necesita restablecer su acceso hace clic en "Generar contraseña". El sistema genera instantáneamente una clave de 24 caracteres con letras mayúsculas, minúsculas, números y símbolos (ej. `kM9#vL2$pQ8*wR1!xT7^yU3&`), la copia al portapapeles y marca en verde todos los requisitos de seguridad corporativa.

### Impacto

Afecta a [frontend/src/components/autoservicio-view.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/autoservicio-view.tsx), [frontend/src/lib/generador-contrasena.ts](file:///home/dtovar/bayblade/pokemon/frontend/src/lib/generador-contrasena.ts), [app/modules/users/politica_contrasena.py](file:///home/dtovar/bayblade/pokemon/app/modules/users/politica_contrasena.py) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).

Ámbito de Vaultwarden, Notificación de Cambio y Auditoría Diferenciada de Contraseñas

## Seguridad, Auditoría y Notificaciones (app/modules/auth/autoservicio.py & app/modules/users/api.py)

### Regla

1. **Ámbito Exclusivo de Vaultwarden (Sends Efímeros de Onboarding y Reset Administrativo)**:
   Vaultwarden no se utiliza como almacén permanente de contraseñas de usuarios corporativos ni interviene en el portal de autoservicio. Su función se limita estrictamente a la entrega segura y efímera de contraseñas iniciales (Bitwarden Send con expiración temporal) durante el proceso de onboarding (`alta`) o cuando un superadministrador realiza un reenvío/reset administrativo (`entrega_credenciales.py`). Las contraseñas gestionadas por autoservicio (`autoservicio.py`) son ingresadas o generadas directamente por el usuario en memoria, aplicadas a OpenLDAP y sincronizadas a JumpServer sin crear ítems ni Sends en Vaultwarden.
2. **Notificación de Confirmación de Cambio de Contraseña**:
   Al completarse exitosamente una actualización (`cambiar_contrasena`) o restablecimiento (`restablecer_con_token`) por autoservicio, el sistema despacha inmediatamente un correo de confirmación al usuario corporativo (`Authelia • Confirmación de actualización de contraseña`) con marca temporal y advertencia de seguridad. Si el usuario no reconoce la actividad, se le instruye reportarlo de inmediato a Seguridad de TI.
3. **Auditoría Diferenciada de Origen de Contraseña**:
   La bitácora de auditoría (`AuditLog`) distingue de forma inequívoca el origen y actor de cualquier modificación de contraseña:
   - **Autoservicio del Usuario**:
     * Evento: `AUTOSERVICIO: PASSWORD ACTUALIZADO POR USUARIO` (con credencial actual y MFA) o `AUTOSERVICIO: PASSWORD RESTABLECIDO POR USUARIO` (con enlace temporal firmado y MFA).
     * Actor / `user`: El identificador o correo del propio usuario.
     * Módulo: `Autoservicio`.
   - **Intervención del Administrador**:
     * Evento: `ADMIN: RESET PASSWORD` (desde edición de usuario) o `CREDENCIALES_REENVIADAS` (desde entrega por Send).
     * Actor / `user`: El correo del administrador que ejecutó la acción (`current_user.email`).
     * Módulo: `Usuarios`.

### Ejemplo

Si el operador `jdoe@vivaro.com` actualiza su clave en `/autoservicio`, recibe un correo de confirmación con fecha y hora, y en auditoría queda registrado `AUTOSERVICIO: PASSWORD ACTUALIZADO POR USUARIO` con actor `jdoe@vivaro.com`. Por el contrario, si el superadmin `admin@vivaro.com` resetea la contraseña de `jdoe` desde la consola de administración, en auditoría queda registrado `ADMIN: RESET PASSWORD` con actor `admin@vivaro.com`.

### Impacto

Afecta a [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py), [app/modules/users/api.py](file:///home/dtovar/bayblade/pokemon/app/modules/users/api.py), [app/modules/users/entrega_credenciales.py](file:///home/dtovar/bayblade/pokemon/app/modules/users/entrega_credenciales.py) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).

Control de Activación Explícita y Ámbito de Vaultwarden

## Módulo
Secretos / Vaultwarden

### Regla
1. **Interruptor Explícito (`VAULTWARDEN_ENABLED`)**:
   La integración con Vaultwarden puede ser activada o desactivada explícitamente mediante la variable de entorno `VAULTWARDEN_ENABLED` (o sus alias `VAULTWARDEN_HABILITADO` y `VAULTWARDEN_ENABLE`).
   - Si se define en `false`, `0`, `no`, `off`, `desactivado` o `disabled`, Vaultwarden queda totalmente inactivo; en el arranque del sistema (`validar_al_arrancar`) y en los scripts de despliegue (`deploy/secretos.sh`), no se exigen variables de conexión ni se interrumpe la ejecución fuera de desarrollo. Cualquier invocación a creación de Sends falla de manera controlada con `send_deshabilitado`.
   - Si se define en `true`, `1`, `si`, `yes` o se configuran variables de conexión sin desactivación explícita, Vaultwarden opera normalmente.
2. **Opcionalidad de `VAULTWARDEN_COLLECTION_ID` para Modo Sends**:
   Cuando Vaultwarden se utiliza exclusivamente para la emisión de enlaces efímeros de Bitwarden Send (onboarding inicial y reenvío administrativo) y no como almacén de contraseñas de conectores, la variable `VAULTWARDEN_COLLECTION_ID` es opcional. El sistema permite el arranque y la creación de Sends sin exigir una colección de organización; únicamente si se invoca la lectura de credenciales de bóveda (`leer(referencia)`), se exige `VAULTWARDEN_COLLECTION_ID`.

### Ejemplo
Un entorno que solo usa Vaultwarden para Sends de onboarding define `VAULTWARDEN_ENABLED=true` con URL y credenciales de la cuenta de servicio, omitiendo `VAULTWARDEN_COLLECTION_ID`. El sistema arranca sin advertencias críticas y entrega los Sends correctamente. Si el administrador desactiva el servicio configurando `VAULTWARDEN_ENABLED=false`, el portal omite las validaciones de Vaultwarden y no detiene el arranque.

### Impacto
Afecta a [app/modules/secretos/configuracion.py](file:///home/dtovar/bayblade/pokemon/app/modules/secretos/configuracion.py), [app/modules/secretos/vaultwarden.py](file:///home/dtovar/bayblade/pokemon/app/modules/secretos/vaultwarden.py), [app/modules/secretos/sends.py](file:///home/dtovar/bayblade/pokemon/app/modules/secretos/sends.py), [deploy/secretos.sh](file:///home/dtovar/bayblade/pokemon/deploy/secretos.sh), [.env.example](file:///home/dtovar/bayblade/pokemon/.env.example) y [docs/configuracion/VARIABLES.md](file:///home/dtovar/bayblade/pokemon/docs/configuracion/VARIABLES.md).

Acceso Público de Autoservicio y Desbloqueo de Cuentas Caducadas

## Módulo
Autenticación / Autoservicio

### Regla
1. **Naturaleza Pública e Inautenticada de Autoservicio**:
   Las rutas `/autoservicio` y `/cambiar-contrasena` son 100% públicas y no requieren ninguna sesión previa ni autenticación en Authelia o Aduana para acceder a ellas. Los usuarios pueden ingresar de forma directa para rotar o restablecer credenciales en cualquier momento.
2. **Desbloqueo de Contraseñas Caducadas o Sin Acceso Inicial**:
   Para resolver el bloqueo en que un usuario cuya contraseña ha caducado (o que no tiene contraseña previa) no puede iniciar sesión en Authelia ni consultar su correo corporativo:
   - **Tengo clave actual o caducada**: Si el usuario recuerda su contraseña caducada, el sistema la reconoce como válida en OpenLDAP (incluso si la directiva `ppolicy` rechaza el bind regular con `passwordExpired`) para autorizar la actualización inmediata.
   - **Restablecimiento Directo con MFA**: Si el usuario no conoce su clave o no tiene contraseña, puede restablecerla directamente en pantalla validando su segundo factor de autenticación (TOTP Authenticator o código OTP de correo) mediante el endpoint `/api/v1/auth/autoservicio/restablecer-mfa`, sin depender de enlaces por correo ni requerir contraseña anterior.
3. **Puntos de Entrada**:
   - En `/login`, se provee una tarjeta destacada de acceso al autoservicio sin necesidad de iniciar sesión.
   - En el menú de usuario de usuarios autenticados, se incluye la acción directa "Cambiar contraseña".

### Ejemplo
Un empleado cuya contraseña corporativa caducó no puede iniciar sesión en el SSO de Authelia ni abrir su correo de Vivaro. Entra directamente a `/autoservicio`, selecciona la pestaña "Restablecer con MFA", ingresa su usuario y su código de 6 dígitos de Google Authenticator, e ingresa su nueva contraseña generada. El sistema aplica el cambio en OpenLDAP y sincroniza JumpServer al instante, permitiéndole ingresar de inmediato.

### Impacto
Afecta a [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py), [app/modules/api/auth.py](file:///home/dtovar/bayblade/pokemon/app/modules/api/auth.py), [app/modules/directory/ldap_client.py](file:///home/dtovar/bayblade/pokemon/app/modules/directory/ldap_client.py), [frontend/src/components/autoservicio-view.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/autoservicio-view.tsx), [frontend/src/components/login-form.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/login-form.tsx), [frontend/src/components/marco/menu-usuario.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/marco/menu-usuario.tsx) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).

Asistente de Autoservicio de Contraseña por Pasos (Stepper) y Verificación MFA

## Módulo
Autenticación / Autoservicio

### Regla
1. **Flujo Guiado Secuencial en 3 Pasos (Stepper)**:
   La interfaz de autoservicio de contraseña se estructura en un asistente secuencial estricto de tres pasos sin pestañas concurrentes ni botones de bifurcación ambiguos:
   - **Paso 1 (Identificación)**: El usuario introduce su usuario o correo institucional. Si la autenticación multifactor configurada es por correo, el sistema despacha automáticamente el código de seguridad de 6 dígitos al correo registrado sin exponer información sensible.
   - **Paso 2 (Validación de Identidad MFA)**: Se valida el código numérico de 6 dígitos. El método de validación se rige estrictamente por la variable de entorno `AUTOSERVICIO_MFA_TIPO` (`email` para código enviado al buzón corporativo o `authenticator` para código temporal TOTP de aplicación móvil como Google Authenticator o Microsoft Authenticator). El usuario ingresa el código y el backend valida su autenticidad mediante `/api/v1/auth/autoservicio/mfa/verificar` antes de permitir el acceso al cambio de contraseña.
   - **Paso 3 (Nueva Contraseña)**: El usuario establece su nueva contraseña o utiliza el generador criptográfico integrado de 24 caracteres de alta entropía. La clave se valida contra la directiva corporativa (longitud mínima 16 caracteres, mayúsculas, minúsculas, dígitos y símbolos).
2. **Sincronización Atómica y Notificación de Confirmación**:
   Al enviar el formulario del Paso 3 mediante `/api/v1/auth/autoservicio/restablecer-mfa`, el backend actualiza de forma atómica la contraseña en OpenLDAP, sincroniza las credenciales autorizadas en JumpServer, genera un registro de auditoría (`AUTOSERVICIO: PASSWORD RESTABLECIDO POR USUARIO (MFA)`) y remite un correo electrónico de confirmación al usuario notificando el cambio exitoso de contraseña para alertarle ante cualquier actividad no autorizada.

### Ejemplo
Un empleado con contraseña vencida ingresa a `/autoservicio`. En el Paso 1 escribe su usuario `jdoe`. El sistema detecta `AUTOSERVICIO_MFA_TIPO=email`, despacha el código de 6 dígitos a su correo corporativo y avanza al Paso 2. El usuario introduce `482915` y presiona "Validar y Continuar al Paso 3". En el Paso 3, presiona "Generar contraseña segura", el sistema genera una clave de 24 caracteres que cumple con todos los requisitos, y al hacer clic en "Cambiar Contraseña", OpenLDAP y JumpServer se actualizan al instante, recibiendo el usuario un correo de notificación confirmando el cambio exitoso.

### Impacto
Afecta a [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py), [app/modules/api/auth.py](file:///home/dtovar/bayblade/pokemon/app/modules/api/auth.py), [frontend/src/components/autoservicio-view.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/autoservicio-view.tsx), [frontend/src/lib/api.ts](file:///home/dtovar/bayblade/pokemon/frontend/src/lib/api.ts), [tests/test_autoservicio.py](file:///home/dtovar/bayblade/pokemon/tests/test_autoservicio.py) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).

Tiempo de Vida y Expiración Criptográfica de Códigos MFA de Autoservicio

## Módulo
Autenticación / Autoservicio

### Regla
1. **Tiempo de Vida de Códigos OTP por Correo**:
   El código numérico de seguridad de 6 dígitos despachado por correo electrónico posee una vigencia temporal estricta controlada criptográficamente mediante firma HMAC con marca de tiempo (`URLSafeTimedSerializer`).
   - Por defecto, el tiempo de vida (TTL) es de **10 minutos (600 segundos)**.
   - Es configurable mediante la variable de entorno `AUTOSERVICIO_MFA_TTL_MINUTOS` (o `AUTOSERVICIO_MFA_EXPIRACION_SEGUNDOS`).
   - Una vez transcurrido este plazo, cualquier intento de validación es rechazado automáticamente por el backend con error HTTP 401 (`SignatureExpired`), impidiendo el uso de códigos obsoletos o interceptados.
2. **Tiempo de Vida de Códigos TOTP (Authenticator)**:
   Los códigos generados por aplicaciones Authenticator (Google Authenticator, Microsoft Authenticator) operan bajo el estándar RFC 6238 en intervalos de **30 segundos**. El backend valida una ventana estricta de tiempo de ±30 segundos para tolerancia de desfase de reloj, garantizando que el código expire automáticamente fuera de esa ventana.

### Ejemplo
Un usuario solicita un código MFA a las 10:00 AM recibiendo el número `482915`. Si intenta introducirlo a las 10:12 AM (después de los 10 minutos por defecto), el backend rechaza la petición con "El código de verificación ha expirado. Solicita uno nuevo." y el usuario debe solicitar un reenvío para continuar con el Paso 2 del autoservicio.

### Impacto
Afecta a [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py), [frontend/src/lib/api.ts](file:///home/dtovar/bayblade/pokemon/frontend/src/lib/api.ts), [frontend/src/components/autoservicio-view.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/autoservicio-view.tsx), [.env.example](file:///home/dtovar/bayblade/pokemon/.env.example), [docs/configuracion/VARIABLES.md](file:///home/dtovar/bayblade/pokemon/docs/configuracion/VARIABLES.md), [tests/test_autoservicio.py](file:///home/dtovar/bayblade/pokemon/tests/test_autoservicio.py) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).

Botón de Acceso a Authelia SSO y Redirección Directa desde Autoservicio y Login

## Módulo
Autenticación / Login / Autoservicio

### Regla
1. **Disponibilidad Permanente del Botón de Inicio de Sesión con Authelia**:
   En la pantalla de acceso `/login`, el botón principal **"Iniciar Sesión con Authelia"** se muestra siempre activo e interactivo, eliminando cualquier bloqueo o pantalla muerta que indique que el servicio no está disponible.
   - Si la federación OIDC está activa (`oidc_enabled`), el botón inicia el flujo de autorización estándar hacia `/api/v1/auth/oidc/login`.
   - Si OIDC está en proceso de arranque o la URL de Authelia está configurada (`AUTHELIA_URL`), el botón redirige directamente al portal de Authelia SSO.
   - Adicionalmente, se provee un enlace directo para abrir el portal de Authelia en caso de requerir acceso manual.
2. **Acceso Sin Bloqueos al Autoservicio de Contraseña**:
   La tarjeta informativa de Autoservicio de Contraseña permanece siempre visible en `/login`, garantizando que cualquier usuario con credenciales caducadas o sin sesión activa pueda acceder a `/autoservicio` sin depender del inicio de sesión.
3. **Navegación Fluida hacia Authelia desde Autoservicio**:
   En la pantalla de Autoservicio (`/autoservicio`), tanto el enlace de retorno en el pie de página como el botón final del Paso 4 dirigen al usuario directamente al portal de Authelia configurado vía `AUTHELIA_URL` (o a `/login`), permitiéndole autenticarse de inmediato tras renovar su clave.

### Ejemplo
Un usuario finaliza la actualización de su contraseña en el Paso 3 del Autoservicio. En la pantalla de éxito, presiona "Iniciar Sesión en Authelia →" y es enviado directamente al portal corporativo de Authelia SSO (o a la pantalla de acceso con el botón de entrada listo). Si visita `/login` mientras el backend se reinicia, ya no observa un mensaje de error restrictivo, sino el botón para entrar con Authelia y el acceso directo a recuperar su cuenta.

### Impacto
Afecta a [frontend/src/components/login-form.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/login-form.tsx), [frontend/src/components/autoservicio-view.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/autoservicio-view.tsx), [app/modules/api/auth.py](file:///home/dtovar/bayblade/pokemon/app/modules/api/auth.py), [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py), [.env.example](file:///home/dtovar/bayblade/pokemon/.env.example), [docs/configuracion/VARIABLES.md](file:///home/dtovar/bayblade/pokemon/docs/configuracion/VARIABLES.md) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Resolución Unificada de SMTP y Diagnóstico Explícito de Entrega de Códigos MFA

## Módulo
Autenticación / Autoservicio / Notificaciones SMTP

### Regla
1. **Resolución Unificada de Servidor SMTP**:
   El módulo de autoservicio (`autoservicio.py`) resuelve el servidor de correo saliente mediante una cascada de configuración:
   - **Prioridad 1**: Configuración dedicada en variables de entorno `AUTOSERVICIO_SMTP_*` (si `AUTOSERVICIO_SMTP_SERVER` está definido).
   - **Prioridad 2**: Configuración global unificada de Aduana mediante `resolve_smtp_settings()`, reutilizando las variables `SMTP_*` del entorno o la configuración almacenada en la base de datos (`SMTPConfig`), con soporte para remitente personalizado `AUTOSERVICIO_SMTP_SENDER_NAME` y `AUTOSERVICIO_SMTP_SENDER_EMAIL`.
   - **Prioridad 3**: Variables de entorno globales `SMTP_*`.
2. **Diagnóstico y Retroalimentación Explícita en Entrega de Códigos**:
   El envío de códigos MFA y notificaciones no debe fallar silenciosamente. Si no existe ningún servidor SMTP configurado o si ocurre un error de conexión, autenticación o tiempo de espera con el servidor de correo:
   - El sistema registra en logs el detalle completo del intento de conexión (`host`, `port`, cifrado y causa del fallo con traza de excepción).
   - En ejecución de producción, la API responde con un error HTTP 503 explicativo (`ErrorAutoservicio`), notificando al usuario en la interfaz la razón exacta (ej. falta de configuración de SMTP o fallo de conexión al host de correo) en lugar de retornar un falso positivo de éxito.
3. **Búsqueda Resiliente de Identidad en Directorio LDAP**:
   Al solicitar código MFA, si el usuario introduce una dirección de correo corporativa (`usuario@dominio.com`) y la búsqueda por atributo `mail` no retorna coincidencia directa en LDAP, el sistema realiza una búsqueda secundaria por el identificador de cuenta (`uid`), garantizando la entrega en infraestructuras donde el buzón y el UID difieren o no comparten atributos idénticos.

### Ejemplo
Un administrador despliega el portal habiendo definido únicamente el remitente institucional en `.env` pero sin servidor SMTP activo. Al solicitar el código MFA en el Paso 1, el backend detecta la ausencia de servidor configurado y devuelve un error 503 claro: "No hay un servidor de correo (SMTP) configurado en el sistema. Configura SMTP_SERVER o AUTOSERVICIO_SMTP_SERVER en el archivo .env". La interfaz muestra de inmediato una notificación toast descriptiva, impidiendo que el usuario quede en espera indefinida de un correo no despachado.

### Impacto
Afecta a [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py), [.env.example](file:///home/dtovar/bayblade/pokemon/.env.example), [docs/configuracion/VARIABLES.md](file:///home/dtovar/bayblade/pokemon/docs/configuracion/VARIABLES.md) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Plantillas Visuales HTML, Cumplimiento de Cabeceras RFC 5322/2047 y Búsqueda Canónica en Directorio LDAP

## Módulo
Autenticación / Autoservicio / Notificaciones y Directorio

### Regla
1. **Cumplimiento Estricto de Cabeceras de Correo RFC 5322 y RFC 2047**:
   Para evitar que servidores de correo corporativo (como Microsoft Exchange / Outlook) cataloguen los mensajes salientes como `<no sender address>` o adviertan riesgos de remitente:
   - Toda cabecera `From:` con caracteres especiales o no-ASCII (como viñetas `•`) debe codificarse obligatoriamente mediante `formataddr((Header(sender_name, 'utf-8'), sender_email))`.
   - Se debe definir explícitamente la cabecera `Sender: {sender_email}` y `Reply-To: {sender_email}` en el objeto MIME.
   - La llamada de transmisión SMTP `smtp.send_message(msg, from_addr=sender_email)` debe pasar de manera explícita la dirección de envolvente `from_addr` (comando `MAIL FROM:<...>`), garantizando que la dirección del remitente sea canónica y RFC-válida.
2. **Plantillas Institucionales Multipart (HTML + Texto Plano)**:
   Los correos de verificación MFA, confirmación de cambio de contraseña y restablecimiento por enlace deben generarse con estructura `multipart/alternative`:
   - Versión en texto plano para clientes de consola o lectores accesibles.
   - Versión en HTML enriquecido con diseño institucional limpio: encabezado con degradado distintivo, tarjeta central con borde suave, caja destacada para el código de 6 dígitos con tipografía monoespaciada de gran visibilidad y aviso de expiración y advertencias de seguridad.
3. **Búsqueda Canónica en `ClienteDirectorio`**:
   Las consultas de usuario contra OpenLDAP deben utilizar exclusivamente el método nativo `buscar_usuario(identificador)` (que filtra por el atributo `cfg.atributo_usuario` / `uid`), eliminando cualquier invocación a métodos inexistentes como `buscar_por_uid`. En búsquedas que reciban correo electrónico, si la consulta por `buscar_por_correo` no produce resultados, se debe intentar secundariamente `buscar_usuario` extrayendo el nombre de cuenta previo al carácter `@`.

### Ejemplo
Un usuario `dtovar` solicita un código MFA de recuperación. El backend busca a `dtovar` llamando a `cliente.buscar_usuario('dtovar')` en LDAP sin generar errores de atributo. Al despachar el correo, el servidor SMTP envía el mensaje con cabecera `From: =?utf-8?...?= <authelia@vivaro.com>` y `Sender: authelia@vivaro.com`. En la bandeja de entrada de Outlook, el correo se muestra impecablemente firmado por "Authelia • Autoservicio de Identidad <authelia@vivaro.com>", sin la etiqueta `<no sender address>`, presentando una tarjeta HTML profesional con el código de 6 dígitos claramente visible.

### Impacto
Afecta a [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py), [tests/test_autoservicio.py](file:///home/dtovar/bayblade/pokemon/tests/test_autoservicio.py) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Optimización Visual y Desaturación del Asistente de Autoservicio de Contraseña

## Módulo
Frontend / Autoservicio / UI & UX

### Regla
1. **Concisión y Claridad en Botones de Acción**:
   Dado que el indicador superior (Stepper) ya informa de manera permanente el número y nombre del paso en el que se encuentra el usuario, los botones de avance deben emplear la etiqueta concisa **"Continuar →"** (o "Guardar Contraseña →" en el paso final), suprimiendo textos extensos y redundantes como "Validar y Continuar al Paso 3 →" o "Continuar al Paso 2 →".
2. **Jerarquía Visual y Botones Secundarios Desaturados**:
   El botón de retorno ("← Volver") se presenta con estilo secundario limpio y estilizado (borde tenue, fondo transparente y texto secundario con feedback en hover), evitando competir cromáticamente o en peso visual con el botón primario de acción (CTA en color institucional `aduana-cyan`).
3. **Consolidación de Información en Tarjeta Única**:
   En el Paso 2 (Validación MFA), se prohíbe la acumulación de cajas de información duplicadas que repitan el correo o usuario. Toda la metadata relevante (correo destinatario, opción de cambiar cuenta, tiempo de caducidad en minutos y botón de reenvío con temporizador cooldown) se unifica en una sola tarjeta compacta y accesible.
4. **Legibilidad y Enfoque en Código de 6 Dígitos**:
   El campo numérico de código de seguridad presenta un diseño de alta legibilidad, centrado, con tipografía monoespaciada, espaciado de dígitos amplio y altura táctil accesible.
5. **Alivio de Carga Cognitiva**:
   En el Paso 1 se suprimen banners pesados de advertencia en favor de textos de ayuda discretos e integrados, y en el Paso 3 el checklist de políticas de contraseñas se organiza en cuadrícula balanceada y compacta para evitar desplazamientos verticales excesivos en pantalla.

### Ejemplo
Al pasar al Paso 2 tras ingresar `dtovar@vivaro.com`, la pantalla ya no muestra dos cajas rectangulares independientes con el mismo correo, sino una tarjeta limpia consolidada que indica "Código enviado a dtovar@vivaro.com · Cambiar" y en la parte inferior "Válido por 10 min · Reenviar código". El botón principal indica claramente "Continuar →" y el botón secundario "← Volver" tiene un tratamiento visual ligero que no satura la interfaz.

### Impacto
Afecta a [frontend/src/components/autoservicio-view.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/autoservicio-view.tsx) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Estandarización de Contraseñas a 16 Caracteres y Unificación de Diseño de Plantillas de Correo

## Módulo
Seguridad / Autoservicio / Notificaciones y Políticas de Contraseña

### Regla
1. **Longitud Generada Estandarizada a 16 Caracteres**:
   La longitud por omisión de las contraseñas autogeneradas por el generador seguro del servidor (`LARGO_GENERADO` en `politica_contrasena.py`) y por el asistente de autoservicio en el frontend (`generarContrasenaSegura(16)`) se establece de forma homogénea en 16 caracteres (alineado al límite mínimo de la política corporativa `PASSWORD_POLICY_MIN_LENGTH=16`). Se actualizan todas las etiquetas, avisos de copiado al portapapeles y textos descriptivos para reflejar 16 caracteres.
2. **Unificación y Compatibilidad de Plantillas de Correo Institucionales**:
   Los correos de envío de código de verificación MFA, confirmación de actualización de contraseña y restablecimiento por enlace seguro adoptan la misma estructura y diseño institucional que la plantilla de entrega de credenciales iniciales:
   - Contenedor de tarjeta limpia y accesible con ancho máximo de 540 px, bordes tenues `#e2e8f0` y tipografía corporativa legible (`-apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif`).
   - Encabezado con color de fondo sólido de respaldo (`background-color: #0284c7` en azul o `#059669` en verde) para garantizar que clientes de correo que no soportan degradados CSS (como Microsoft Outlook Desktop) nunca muestren el encabezado en blanco ni oculten el texto del título.
   - Remitente y firma dinámica basada en la marca configurada (`AUTOSERVICIO_SMTP_SENDER_NAME` o fallback institucional).
   - Bloque central destacado con el código de seguridad de 6 dígitos o confirmación de sincronización con el directorio corporativo (OpenLDAP y plataformas asociadas).
   - Aviso de seguridad visible indicando las acciones preventivas si el usuario no originó la solicitud.
   - Cabeceras RFC 5322 y RFC 2047 (`From`, `Sender`, `Reply-To`, `Subject`) y envío con `from_addr` canónico para prevenir etiquetas de `<no sender address>` en Outlook.

### Ejemplo
Al pulsar "Generar contraseña segura" en el paso 3 de recuperación o al crear un usuario en el portal, el sistema genera automáticamente una clave alfanumérica con símbolos de exactamente 16 caracteres y notifica "Contraseña de 16 caracteres generada y copiada al portapapeles". Al despachar el código MFA o la confirmación de cambio, el usuario recibe en Outlook un correo con diseño corporativo idéntico al de bienvenida/credenciales iniciales, con fondo sólido visible en el banner superior y firma de "Authelia • Autoservicio de Identidad".

### Impacto
Afecta a [app/modules/users/politica_contrasena.py](file:///home/dtovar/bayblade/pokemon/app/modules/users/politica_contrasena.py), [frontend/src/components/autoservicio-view.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/autoservicio-view.tsx), [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Configuración de Longitud Generada en .env y Reactividad Dinámica en Autoservicio

## Módulo
Seguridad / Configuración / Autoservicio y Políticas de Contraseña

### Regla
1. **Configuración de Longitud Generada en Entorno**:
   Se habilita la variable de entorno `PASSWORD_POLICY_GENERATED_LENGTH` (con fallback opcional en `AUTOSERVICIO_PASSWORD_LENGTH`), permitiendo definir en el archivo `.env` la longitud de caracteres para contraseñas generadas automáticamente tanto en el backend (`generar()` en `politica_contrasena.py`) como en el frontend de Autoservicio (`/autoservicio`).
2. **Reactividad Dinámica en el Asistente**:
   El endpoint `/auth/autoservicio/configuracion` expone la propiedad `password_length` calculada a partir de las variables de entorno (`PASSWORD_POLICY_GENERATED_LENGTH` o `PASSWORD_POLICY_MIN_LENGTH`, por defecto 16). El componente `AutoservicioView` se vincula de manera reactiva a esta configuración:
   - Al pulsar "Generar contraseña segura", genera una clave con exactamente `password_length` caracteres.
   - Los textos descriptivos, placeholders del campo de entrada y tooltips adaptan su redacción dinámicamente al valor recibido.
   - El checklist de validación en tiempo real evalúa la longitud contra `config.politica.min_length`.

### Ejemplo
Un administrador define en su `.env` la directiva `PASSWORD_POLICY_GENERATED_LENGTH=16` (o `20`). Al ingresar al paso 3 de recuperación de contraseña, el asistente muestra automáticamente «Ingresa tu nueva clave institucional o genera una automáticamente de 16 caracteres» y genera una clave de 16 caracteres sin requerir recompilaciones manuales fijas en el código de la vista.

### Impacto
Afecta a [app/modules/users/politica_contrasena.py](file:///home/dtovar/bayblade/pokemon/app/modules/users/politica_contrasena.py), [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py), [frontend/src/lib/api.ts](file:///home/dtovar/bayblade/pokemon/frontend/src/lib/api.ts), [frontend/src/components/autoservicio-view.tsx](file:///home/dtovar/bayblade/pokemon/frontend/src/components/autoservicio-view.tsx), [.env.example](file:///home/dtovar/bayblade/pokemon/.env.example) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Sincronización Transaccional Obligatoria y Manejo de Errores en Cambio de Contraseñas LDAP

## Módulo
Autoservicio / Directorio OpenLDAP / Autenticación y Seguridad

### Regla
1. **Consistencia Transaccional con el Directorio Corporativo (LDAP)**:
   Cuando el directorio LDAP se encuentra activo (`directorio_activo() == True`), OpenLDAP constituye la fuente canónica de verdad para la autenticación en Authelia SSO (1FA). Si un usuario realiza un restablecimiento o cambio de contraseña en Autoservicio:
   - La nueva contraseña se debe aplicar imperativamente en OpenLDAP mediante `EscritorDirectorio.change_password`.
   - Si la operación de escritura en LDAP falla, es rechazada por directivas de política (`ppolicy`) o se interrumpe la comunicación, el sistema DEBE interrumpir el flujo inmediatamente y responder con un error HTTP 500 (`ErrorAutoservicio`).
   - Queda estrictamente prohibido silenciar fallos de LDAP o simular un restablecimiento exitoso actualizando únicamente la base de datos local relacional.
   - Tras la aplicación exitosa en LDAP, el sistema sincroniza de forma atómica el registro en la base de datos local (si existe) para garantizar consistencia entre Authelia SSO y el portal Aduana.
2. **Propiedades de Acceso Robustas en Clases del Directorio**:
   - `ResultadoEscritura` expone la propiedad `exitoso` como alias canónico de `exito` (`self.resultado.exito`), previniendo errores de tipo `AttributeError` al verificar el estado de las transacciones.
   - `UsuarioDirectorio` expone las propiedades seguras `nombre` (resolviendo `cn` o `displayName`) y `correo` (resolviendo `mail`), evitando excepciones al consultar el perfil de la cuenta.

### Ejemplo
Un usuario con cuenta corporativa en OpenLDAP utiliza el asistente de recuperación con MFA en el portal de autoservicio. El servidor localiza la cuenta en OpenLDAP, invoca `change_password` y verifica `resultado.exito`. Si OpenLDAP actualiza la contraseña exitosamente, se sincroniza la base de datos local y el usuario puede iniciar sesión de inmediato en Authelia con la nueva contraseña. Si OpenLDAP rechazara el cambio por políticas de contraseña, el portal notifica el error de forma transparente en lugar de emitir un falso positivo.

### Impacto
Afecta a [app/modules/directory/errors.py](file:///home/dtovar/bayblade/pokemon/app/modules/directory/errors.py), [app/modules/directory/ldap_client.py](file:///home/dtovar/bayblade/pokemon/app/modules/directory/ldap_client.py), [app/modules/auth/autoservicio.py](file:///home/dtovar/bayblade/pokemon/app/modules/auth/autoservicio.py), [tests/test_autoservicio.py](file:///home/dtovar/bayblade/pokemon/tests/test_autoservicio.py) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Directorio Canónico de Logs y Persistencia de Trazas en Modo Debug

## Módulo
Infraestructura / Observabilidad / Directorio OpenLDAP

### Regla
1. **Preservación y Creación Automática del Directorio de Logs**:
   El proyecto versiona el directorio `logs/` mediante un archivo centinela `logs/.gitkeep`, configurando `.gitignore` para ignorar archivos generados (`logs/*`) sin suprimir el directorio base (`!logs/.gitkeep`). En tiempo de ejecución, la función `resolver_carpeta_logs()` asegura la existencia física de la carpeta `logs/` en la raíz del proyecto o en la ruta definida por `LOG_DIR`/`LOGDIR`.
2. **Persistencia Unificada de Registros de Depuración**:
   Al habilitar `DEBUG_LDAP=true`:
   - El sistema inicializa automáticamente la carpeta `logs/` y crea el archivo `logs/ldap_debug.log`.
   - Se canalizan simultáneamente las operaciones de bajo nivel del protocolo (`ldap3`) y los registros de aplicación de alto nivel (`app.modules.directory`, `app.modules.auth.autoservicio`, `app.modules.users.entrega_credenciales`) hacia `logs/ldap_debug.log` con nivel `DEBUG`.
   - La inicialización se ejecuta tanto en la importación de clientes LDAP como en el arranque de la aplicación Flask (`create_app`), garantizando que las trazas de autoservicio y cambios de contraseña se persistan de inmediato en disco.

### Ejemplo
Al configurar `DEBUG_LDAP=true` en `.env` y reiniciar el servicio, cualquier intento de recuperación de contraseña o consulta en OpenLDAP escribe en `logs/ldap_debug.log` tanto los mensajes de negocio ("Autoservicio MFA: Restablecimiento en LDAP para dtovar -> exito=True") como las tramas de la librería ldap3 (BIND, MODIFY PASSWORD, RESULT), permitiendo auditar la interacción completa sin depender exclusivamente de journald.

### Impacto
Afecta a [.gitignore](file:///home/dtovar/bayblade/pokemon/.gitignore), [app/modules/directory/depuracion.py](file:///home/dtovar/bayblade/pokemon/app/modules/directory/depuracion.py), [app/__init__.py](file:///home/dtovar/bayblade/pokemon/app/__init__.py), [tests/test_depuracion_ldap.py](file:///home/dtovar/bayblade/pokemon/tests/test_depuracion_ldap.py) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).


Resiliencia de Registro de Logs ante Sistemas de Archivos de Solo Lectura (Systemd ProtectSystem)

## Módulo
Infraestructura / Observabilidad / Despliegue y Hardening

### Regla
1. **Detección Dinámica de Permisos de Escritura de Logs**:
   En entornos de producción protegidos por directivas de endurecimiento de systemd (`ProtectSystem=strict` o `ProtectSystem=full`), el árbol del proyecto (`/opt/portal` o `@PREFIX@`) se monta en modo de solo lectura (`[Errno 30] Read-only file system`).
   - La resolución del directorio de registros (`resolver_carpeta_logs`) realiza una prueba activa de escritura antes de seleccionar un destino.
   - Si la carpeta local `logs/` del proyecto es de solo lectura, el sistema busca de forma transparente el directorio autorizado por systemd (`/var/log/portal`, configurado en `ReadWritePaths`), o en su defecto `/tmp/portal_logs` (`PrivateTmp=true`).
2. **Inmunidad ante Caídas por Fallos de E/S**:
   - `activar_si_se_pide()` captura de forma preventiva cualquier excepción `OSError` o `PermissionError` al crear `FileHandler`.
   - Bajo ninguna circunstancia se interrumpe el arranque del servidor web (Gunicorn) o del worker si el sistema de archivos prohíbe crear archivos de log.
   - En caso de indisponibilidad de escritura en disco, las trazas continúan fluyendo a la consola estándar (`StreamHandler`) para su consumo mediante `journalctl`.

### Ejemplo
Un servidor Linux Rocky 9 despliega el backend bajo `/opt/portal` con `ProtectSystem=strict` en su unidad de systemd. Al habilitar `DEBUG_LDAP=true` e iniciar Gunicorn, el sistema detecta que `/opt/portal/logs` es de solo lectura y redirige automáticamente `ldap_debug.log` hacia `/var/log/portal/ldap_debug.log` (o `/tmp/portal_logs/ldap_debug.log`) sin arrojar `[Errno 30]` ni abortar los procesos trabajadores de Gunicorn.

### Impacto
Afecta a [app/modules/directory/depuracion.py](file:///home/dtovar/bayblade/pokemon/app/modules/directory/depuracion.py), [tests/test_depuracion_ldap.py](file:///home/dtovar/bayblade/pokemon/tests/test_depuracion_ldap.py) y [docs/business_rules.md](file:///home/dtovar/bayblade/pokemon/docs/business_rules.md).

## Autoservicio de Contraseña Solo para Cuentas Dadas de Alta en el Portal

### Regla

Solo una persona con cuenta **activa** en el portal (tabla `users`) puede cambiar o recuperar su contraseña de LDAP desde el autoservicio (código MFA, enlace por correo o cambio con contraseña actual). Quien existe solo en LDAP no recibe código ni enlace (misma respuesta genérica, sin revelar si existe) y, si llegara a pasar la verificación, se rechaza con `403` sin tocar LDAP. Decisión del dueño, 2026-11-24 (FNC-181).

### Ejemplo

`uid=lacid,ou=users,dc=vivaro,dc=local` existe en LDAP pero no en el portal: al pedir el código en `/autoservicio` ve «Si la cuenta existe…» y no le llega nada. Cuando un administrador lo da de alta (activo), ya puede restablecer y el cambio se aplica en LDAP.

### Impacto

Afecta a [autoservicio.py](../app/modules/auth/autoservicio.py), [autoservicio_mfa.py](../app/modules/auth/autoservicio_mfa.py) y [autoservicio_cuentas.py](../app/modules/auth/autoservicio_cuentas.py); pruebas en [test_autoservicio_solo_ldap.py](../tests/test_autoservicio_solo_ldap.py).

## Toda Plataforma Da Acceso por Grupo LDAP; el Conector Es un Paso Adicional

### Regla

Cuando se acepta una solicitud (o el admin otorga, o el sistema da el acceso automático al admin de área) se agrega a la persona al grupo LDAP de su nivel, `app-{plataforma}-users` o `app-{plataforma}-admins`, sin importar si la plataforma tiene conector. Después, **solo si** la plataforma tiene un conector configurado y disponible, se ejecuta su alta (crear la cuenta local por API), para plataformas cuyo backend de autenticación es LDAP pero que no crean el usuario por sí solas. Al revocar (revocación, salida del área, regreso de admin) se quita del grupo y, si hay conector, se ejecuta su baja. Subir o bajar de nivel solo cambia el grupo. Toda plataforma activa de un área activa es solicitable en ambos niveles. Si no se indican los DN de grupo, se derivan de `LDAP_PLATFORM_GROUP_TEMPLATE` (por omisión `cn=app-{plataforma}-{nivel}`) y el grupo inexistente se crea al otorgar. Si el conector falla, el acceso queda `fallido` (o `fallo_revocacion`) con su error y la pertenencia al grupo no se revierte.

### Ejemplo

`tacacs` no tiene DN ni conector: al aprobar la solicitud de la persona se crea `cn=app-tacacs-users` si no existe y se la agrega; el acceso pasa a `activo`. `zabbix` además tiene un conector `api`: tras agregarla a `app-zabbix-users` se crea su usuario en Zabbix; si esa llamada falla, el acceso queda `fallido`, sigue en el grupo y el reintento repite ambos pasos.

### Impacto

Afecta a [compuesto.py](../app/modules/provisioning/compuesto.py), [ldap_provider.py](../app/modules/provisioning/ldap_provider.py), [grupos.py](../app/modules/platforms/grupos.py), [catalogo.py](../app/modules/access_requests/catalogo.py), [area_admin_sync.py](../app/modules/access/area_admin_sync.py) y [services.py](../app/modules/access/services.py); migración `0021`; pruebas en [test_grupos_y_conector.py](../tests/access/test_grupos_y_conector.py).

## Solicitudes Solo de Nivel Usuario

### Regla

El usuario solo solicita acceso de nivel **usuario**. El nivel **admin** de una plataforma lo otorga un administrador desde el panel de administración; no se pide por solicitud. La justificación no se pide (son herramientas de trabajo). Decisión del dueño, 2026-11-24 (FNC-199, DIS-125).

### Ejemplo

Un miembro de Packet ve `tacacs` «Sin acceso», pulsa «Solicitar acceso» y la solicitud nace de nivel usuario; si alguien manda `level: admin` por la API, recibe `422`.

### Impacto

Afecta a [catalogo.py](../app/modules/access_requests/catalogo.py) (`NIVELES_SOLICITABLES`) y [services.py](../app/modules/access_requests/services.py).

## Un área no se activa sin administrador

### Regla

Un área no puede estar activa sin al menos un admin de área. Crearla activa o pasarla de `Inactivo` a `Activo` sin admin responde `409 area_sin_admin` («Asigna al menos un administrador antes de activar el área.»). El admin de área que crea un área queda como su admin, así que sí puede crearla activa. Las áreas de la importación masiva (CSV, `flask alta areas`) nacen `Inactivo`. Quitar el último admin de un área activa no se bloquea (decisión del dueño, 2026-11-28, para no frenar las bajas de usuarios).

### Ejemplo

El superadmin crea «Legal» sin enviar `status`: recibe `409`. La crea `Inactivo`, asigna un admin y la activa con `PUT`: pasa.

### Impacto

Afecta a [api.py](../app/modules/areas/api.py), [services.py](../app/modules/bulk_import/services.py) y [areas-y-roles.md](contratos/areas-y-roles.md).
