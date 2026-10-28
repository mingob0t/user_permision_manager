# Estándares de Comportamiento e Interacción (02-comportamiento.md)

Basado en **ADR-007**, **PLAN-FASE-7** y la regla arquitectónica **«Un patrón, un componente» (DIS-068)**.

## 1. Principio Fundamental: «Un patrón, un componente»

Ninguna pantalla, vista o módulo debe implementar marcado ad hoc para componentes de diseño que ya cuentan con una implementación estándar en la biblioteca compartida.

### Matriz de Patrones y Componentes Canónicos

| Patrón Funcional | Prohibición en Vistas / Marcado Ad Hoc | Componente Canónico Único | Tarea de Consolidación |
|---|---|---|---|
| **Botones y Enlaces de Acción** | Prohibido `<button className="nexus-btn">` o `<Link className="nexus-btn">` sueltos | `<Button>` y `<ButtonLink>` (`components/form.tsx` / `button.tsx`) | DIS-058 |
| **Campos de Entrada** | Prohibidos `<input>`, `<select>`, `<textarea>` directos con estilos arbitrarios | `<TextInput>`, `<Select>`, `<TextArea>` (`components/form.tsx`) | DIS-059 |
| **Pestañas de Navegación** | Prohibido marcar `role="tablist"`, `role="tab"` manualmente | `<Tabs>` y `<ToggleChip>` (`components/tabs.tsx`) | DIS-060 |
| **Contenedores y Paneles** | Prohibido reimplementar estructuras de tarjetas o modales de cristal | `<Card>`, `<PanelHeader>`, `<Modal>`, `<Drawer>` (`components/ui.tsx`, `components/form.tsx`) | DIS-061 |
| **Mensajes y Estados** | Prohibidas cajas con `bg-<estado>/NN` ad hoc | `<Note>`, insignias (`Badge`) y alertas | DIS-062 |
| **Tablas y Listados de Datos** | Prohibido `<table>` o `<thead>`/`<tbody>` fuera del componente canónico | `<DataTable>` (`components/data-table.tsx`) | DIS-071 |
| **Barras de Filtros** | Prohibidas barras de búsqueda y filtros duplicadas | `<FilterBar>` (`components/filter-bar.tsx`) | DIS-069 |
| **Encabezados de Página** | Prohibido `<h1>` fuera del encabezado canónico de pantalla | `<PageHeader>` (`components/page-header.tsx`) | DIS-070 |
| **Diálogos de Confirmación** | Prohibido `window.confirm`, alert nativo o modales ad hoc para avisos | `<AlertDialog>` (`components/alert-dialog.tsx`) | DIS-074 |

---

## 2. Validación Automatizada
La prueba `frontend/tests/accesibilidad/patrones-unicos.test.ts` valida en tiempo de compilación y pruebas:
1. No se permite la inclusión de ningún nuevo `<table>`, `<h1>`, `role="tablist"` o clases `.nexus-btn` fuera de los componentes autorizados.
2. Toda excepción heredada existente está cuantificada estrictamente en `patrones-unicos.excepciones.ts` y disminuye con cada iteración de los bloques C y D.

---

## 3. Estabilidad Visual (Sin saltos de diseño / CLS < 0.01) y Movimiento Reducido (DIS-073)

### Reglas de Estabilidad:
1. **Canales de desplazamiento estables:** Todo contenedor desplazable (`[data-desplazable]`) declara `scrollbar-gutter: stable` en CSS para evitar que al activar el bloqueo de scroll (`useScrollLock`) o al alternar diálogos el contenido salte lateralmente.
2. **Cargas asíncronas con esqueletos:** Las operaciones de carga deben reservar el espacio final mediante `<Skeleton variant="fila" | "tarjeta" | "contador">` para evitar el desplazamiento vertical del contenido.
3. **Zonas reservadas para avisos:** Los formularios y cabeceras de listado usan `<RegionDeAviso minHeight="...">` para evitar que la aparición de un mensaje de error o éxito empuje los controles inferiores.
4. **Animaciones respetuosas:**
   - Toda transición se restringe estrictamente a `opacity` y `transform`.
   - Con `prefers-reduced-motion: reduce`, las animaciones y transiciones se anulan (`animation: none`, `motion-reduce:transition-none`).

