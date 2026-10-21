# FNC-106 — Conectores: permitir redes internas autorizadas por despliegue (CIDR)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | conectores |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |
| **Estatus Git** | — |
| **Rama** | — |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (ejecución remota, SSRF) |

## Contexto
- FNC-051 rechaza todo host que resuelva a una IP no pública (DNS *rebinding*, SEC-CON-06): una plataforma interna con IP privada no se alcanza
- Origen: decisión del orquestador en FNC-051 (lo más seguro); la PoC dirá si las plataformas piloto son internas

## Objetivo
- Una variable del despliegue con las redes (CIDR) que SÍ se permiten como destino, vacía por defecto; solo esas IP privadas pasan `ip_permitida`

## Alcance
- **Incluye:** variable `CONNECTOR_ALLOWED_NETWORKS` (CIDR, validada al arrancar, nunca `0.0.0.0/0` ni loopback ni *link-local*), uso en `destino_seguro.py`, registro y pruebas
- **No incluye:** permitir loopback, *link-local* ni metadatos de nube en ningún caso

## Archivos previstos
- `app/modules/connectors/destino_seguro.py`, `configuracion.py`, `tests/connectors/`, `docs/configuracion/`

## Reutilización
- `destino_seguro.ip_permitida`, `configuracion.cargar_configuracion`

## Criterios de aceptación
- [ ] Vacía = comportamiento actual (prueba)
- [ ] Una IP privada dentro del CIDR configurado pasa; fuera, no (prueba)
- [ ] CIDR amplio, loopback o *link-local* detienen el arranque (prueba)

## Impacto cruzado
- Origen ← FNC-051; la reutilizan FNC-052 y FNC-053

## Riesgos y reversión
- Ampliar la superficie SSRF: solo con la lista del despliegue. Reversión: vaciar la variable.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta (FNC-051) |
