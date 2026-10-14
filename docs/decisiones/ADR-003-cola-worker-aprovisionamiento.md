# ADR-003 — Cola y worker de aprovisionamiento

- **Estatus:** Propuesta · **Fecha:** 2026-10-13 · **Tarea:** FNC-037 → FNC-049, FNC-067

## Contexto
- Otorgar y revocar (LDAP o conector) va en segundo plano con reintentos y bitácora
- Redis existe, opcional y sin uso; sin contraseña por defecto (SEG-29)

## Alternativas
- **A. Tabla MySQL como cola** + worker systemd con polling (`SKIP LOCKED`): sin infraestructura nueva, transaccional con el acceso
- **B. RQ sobre Redis** + tabla *outbox*: menor latencia; Redis pasa a obligatorio con contraseña
- **C. Celery** sobre Redis: más funciones, más complejidad

## Recomendación
- A (volumen bajo; latencia de segundos tolerable); B si se requiere latencia menor a 1 s

## Consecuencias
- Nueva unidad `<nombre>-worker` (FNC-067)
- Variables `PROVISIONING_*` registradas
