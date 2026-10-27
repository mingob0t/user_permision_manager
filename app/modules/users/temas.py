"""Temas de la interfaz que una cuenta puede guardar (FNC-122).

Misma lista que `frontend/src/lib/tema.ts` (`TEMAS`, ids): si el frontend agrega
o quita un tema, se cambia aquí en la misma tarea.
"""

TEMA_POR_DEFECTO = 'sistema'
TEMAS_VALIDOS = frozenset({
    TEMA_POR_DEFECTO, 'claro', 'oscuro', 'esmeralda', 'obsidiana', 'rosa',
    'violeta',
})
