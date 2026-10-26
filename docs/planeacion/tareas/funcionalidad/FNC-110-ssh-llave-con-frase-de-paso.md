# FNC-110 — Conector SSH: llave privada con frase de paso

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | conectores |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |
| **Estatus Git** | — |
| **Rama** | — |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (credenciales) |

## Contexto
- FNC-052 solo acepta llaves privadas sin frase de paso (`cargar_llave` rechaza una cifrada)
- Origen: decisión del orquestador en FNC-052; depende de cómo FNC-068 guarde campos adicionales de la credencial

## Objetivo
- Aceptar una llave cifrada con la frase de paso tomada del gestor (campo aparte de la credencial), sin guardarla ni registrarla

## Alcance
- **Incluye:** lectura de la frase de paso desde la credencial, `cargar_llave(texto, frase)`, pruebas con llave cifrada (correcta, incorrecta, ausente) y registro en la documentación
- **No incluye:** otros métodos de autenticación, agente SSH

## Archivos previstos
- `app/modules/connectors/ssh_transporte.py`, `credenciales.py` (según FNC-068), `tests/connectors/`, `docs/backend/README.md`

## Reutilización
- `ssh_transporte.cargar_llave`, `Credencial`

## Criterios de aceptación
- [ ] Llave cifrada con la frase correcta autentica; con otra o sin ella, error permanente `ssh_autenticacion_rechazada` (prueba)
- [ ] La frase nunca aparece en logs, bitácora ni `repr` (prueba)

## Impacto cruzado
- Origen ← FNC-052; depende de FNC-068

## Riesgos y reversión
- Amplía lo que maneja la credencial en memoria. Reversión: volver a exigir llaves sin frase.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta (FNC-052) |
