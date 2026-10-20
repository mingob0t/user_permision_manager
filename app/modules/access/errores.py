"""Errores del servicio de accesos con su código y HTTP de contrato.

Los endpoints (FNC-057, FNC-058) los traducen con `error_response(*e.respuesta)`.
"""
from app.modules.api.helpers import MENSAJE_VALIDACION


class ErrorDeAcceso(Exception):
    """Regla de accesos incumplida; no se encoló ni cambió nada."""

    def __init__(self, mensaje, http, codigo, campos=None):
        super().__init__(mensaje)
        self.mensaje, self.http, self.codigo = mensaje, http, codigo
        self.campos = campos

    @property
    def respuesta(self):
        return self.mensaje, self.http, self.codigo, self.campos


def fuera_de_alcance():
    """SEC-AUTHZ-03/04/06: igual que inexistente."""
    return ErrorDeAcceso('Recurso no encontrado.', 404, 'no_encontrado')


def operacion_propia(revocar=True):
    """SEC-AUTHZ-08."""
    mensaje = ('No puedes revocar tu propio acceso.' if revocar
               else 'No puedes otorgarte un acceso.')
    return ErrorDeAcceso(mensaje, 403, 'operacion_propia')


def estado_invalido(mensaje='Solo se revoca un acceso activo.'):
    return ErrorDeAcceso(mensaje, 409, 'estado_invalido')


def nivel_vigente():
    """P5: ya tiene ese nivel o uno superior (solicitudes.md)."""
    return ErrorDeAcceso('Ya tienes ese nivel o uno superior.', 409,
                         'nivel_vigente')


def acceso_por_defecto():
    """El superadmin tiene acceso por defecto: no se le otorga nada (P6)."""
    return ErrorDeAcceso('El superadmin tiene acceso por defecto.', 409,
                         'acceso_por_defecto')


def validacion(campo, mensaje):
    return ErrorDeAcceso(MENSAJE_VALIDACION, 422, 'validacion',
                         {campo: mensaje})
