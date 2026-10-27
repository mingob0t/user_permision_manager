# DIS-048 — Chips de plataforma y área: texto con contraste garantizado

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Rama** | `dis/DIS-048-chips-con-color-libre-contraste` |
| **Creada** | 2026-10-27 |

## Contexto
- `.nx-chip-tint` (área en `PlatformCard`, monograma de `AreasList`) y `.nx-chip-solid` (icono de plataforma) pintan el texto con el color libre del dato (`area.color`, `platform.text_color`) sin garantizar contraste. El color por defecto `#6366f1` sobre su propio tinte da 3,5–3,8:1 (< 4,5:1).
- `Platform.bg_color`/`text_color` los elige el usuario; FNC-033 (validar contraste de colores elegidos) sigue en Propuesta.

## Objetivo
- Opción A: texto con token del tema (`--color-body-text` o `--color-primary-text`) y el color del dato solo en fondo y borde.
- Opción B: validar el contraste al guardar (con FNC-033).
- Medir con `auditor-accesibilidad` en los 7 temas.

## Impacto cruzado
- Origen ← DIS-012
- Depende de → decisión del dueño (A o B); B genera FNC (backend)
- Relacionada: FNC-033, FNC-017
