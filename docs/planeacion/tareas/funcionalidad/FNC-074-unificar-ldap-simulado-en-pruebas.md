# FNC-074 — Unificar el LDAP simulado de las pruebas

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | pruebas |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |

## Contexto
- `tests/matriz_proteccion.py:132-155` (`_ConexionLdapFalsa`, `_con_directorio_simulado`) se solapa con `tests/directorio_falso.py` (FNC-022).
- `'dc=pruebas,dc=local'` está escrito tal cual en `matriz_proteccion.py:152` en vez de usar `BASE_DN`.
- Origen: revisión de FNC-022.

## Criterios de aceptación
- [ ] Un solo doble de `ldap3` usado por todas las pruebas
- [ ] Sin cambio en el resultado de la suite
