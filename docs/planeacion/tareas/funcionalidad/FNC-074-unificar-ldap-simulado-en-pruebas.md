# FNC-074 — Unificar el LDAP simulado de las pruebas

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | pruebas |
| **Prioridad** | Baja |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |

## Contexto
- `tests/matriz_proteccion.py:132-155` (`_ConexionLdapFalsa`, `_con_directorio_simulado`) se solapa con `tests/directorio_falso.py` (FNC-022).
- `'dc=pruebas,dc=local'` está escrito tal cual en `matriz_proteccion.py:152` en vez de usar `BASE_DN`.
- Origen: revisión de FNC-022.

## Criterios de aceptación
- [x] Un solo doble de `ldap3` usado por todas las pruebas
- [x] Sin cambio en el resultado de la suite

## Verificación
- Antes: `pytest tests` código 0, 2397 passed, 15 xfailed. Después: `pytest tests` código 0, 2397 passed, 15 xfailed (igual).

## Bitácora
- 2026-10-27: decisión del orquestador (pendiente de validar en la prueba de concepto): `_ConexionLdapFalsa` ya no existía en `matriz_proteccion.py` (usa `instalar_directorio` desde FNC-042). El solapamiento real era `DirectorioFalso` vs `DirectorioMock`.
- Base `ServidorSimulado` en `tests/directorio_falso.py` (siembra, `BASE_DN`, `dn_persona`, `dn_grupo`, `ENTORNO_VALIDO`); ambos dobles la extienden; `tests/directory/conftest.py` reexporta las constantes. Sin cambios en `app/` ni en aserciones.

## Impacto en elementos compartidos
- `tests/directory/conftest.py` y `tests/directorio_falso.py`: lo usan las pruebas de `tests/directory/`, login, usuarios, plataformas, accesos y secretos; todas pasan.

- 2026-10-27: verificado por el orquestador: sin cambios en `app/`; pytest antes y después 2397 passed, 15 xfailed, código 0 en ambos. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto).
