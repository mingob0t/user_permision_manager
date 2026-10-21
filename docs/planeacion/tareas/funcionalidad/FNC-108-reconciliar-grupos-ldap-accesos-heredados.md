# FNC-108 — Reconciliar los grupos LDAP con los accesos `heredado`

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |
| **Estatus Git** | — |
| **Rama** | — |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (membresía de grupos) |

## Contexto
- La migración 0010 de FNC-065 crea accesos `heredado` `activo` sin escribir en LDAP ni encolar trabajos: el portal dice que la cuenta tiene acceso, pero su membresía en el grupo de la plataforma no está comprobada
- Relacionada con FNC-086 (sincronización inicial de accesos automáticos)

## Objetivo
- Comando o trabajo que compare cada acceso `heredado` con el grupo de su plataforma y, con confirmación, agregue a quien falte o marque el acceso para revisión

## Alcance
- **Incluye:** reporte de diferencias (solo lectura por defecto), corrección explícita y auditoría
- **No incluye:** cambiar la migración 0010

## Impacto cruzado
- Origen ← FNC-065; depende de FNC-049 y FNC-041

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta (FNC-065) |
