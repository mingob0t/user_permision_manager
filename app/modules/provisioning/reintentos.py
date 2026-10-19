"""Espera entre intentos: *backoff* exponencial con *jitter* (SEC-CON-08)."""
import random

# Base del crecimiento exponencial.
FACTOR_BACKOFF = 2


def segundos_de_espera(intentos_hechos, base, maximo, aleatorio=random.random):
    """Espera antes del siguiente intento tras `intentos_hechos` (≥ 1).

    `min(maximo, base · 2^(n-1))`, con la mitad fija y la otra mitad al azar
    (*equal jitter*): dos workers no reintentan a la vez y la espera nunca
    baja de la mitad del escalón.
    """
    escalon = min(maximo, base * FACTOR_BACKOFF ** max(intentos_hechos - 1, 0))
    return escalon / 2 + aleatorio() * escalon / 2
