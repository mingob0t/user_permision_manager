"""Dobles del ejecutor de aprovisionamiento (FNC-049).

- `cola_falsa`: reemplaza la cola RQ; guarda los mensajes y permite
  procesarlos en el mismo proceso, como `Queue(is_async=False)`, sin Redis.
- `proveedor_simulado`: proveedor registrado para `ldap` y `conector` que
  devuelve los resultados que se le indiquen y cuenta las llamadas.
- `avisos`: registra las llamadas a `notificar_aprovisionamiento_fallido`.
"""
import pytest
from rq.utils import import_attribute

from app import db
from app.modules.platforms.tipos import NIVEL_USUARIO, TIPO_LDAP
from app.modules.provisioning import ejecucion, manejadores, providers, queue
from app.modules.provisioning.ldap_provider import ProveedorLdap
from app.modules.provisioning.providers import Provisioner, ResultadoProveedor
from app.modules.provisioning.tipos import (OPERACION_OTORGAR,
                                            PROVEEDOR_CONECTOR,
                                            PROVEEDOR_LDAP, RESULTADO_EXITOSO)
from tests import fabricas

GRUPO_USUARIO = 'cn=wiki-usuario,ou=grupos,dc=pruebas,dc=local'
GRUPO_ADMIN = 'cn=wiki-admin,ou=grupos,dc=pruebas,dc=local'


class MensajeRq:
    def __init__(self, funcion, args, kwargs):
        self.funcion, self.args, self.kwargs = funcion, args, kwargs


class ColaFalsa:
    """Cola RQ simulada: `enqueue` guarda; `procesar` ejecuta en orden."""

    def __init__(self):
        self.mensajes = []
        self.connection = object()

    def enqueue(self, funcion, *args, **kwargs):
        self.mensajes.append(MensajeRq(funcion, args, kwargs))

    def ids(self):
        return [m.args[0] for m in self.mensajes]

    def procesar(self):
        pendientes, self.mensajes = self.mensajes, []
        return [import_attribute(m.funcion)(*m.args) for m in pendientes]


@pytest.fixture
def cola_falsa(monkeypatch):
    falsa = ColaFalsa()
    monkeypatch.setattr(queue, 'cola', lambda conexion=None: falsa)
    return falsa


class ProveedorSimulado(Provisioner):
    def __init__(self):
        self.resultados = []
        self.llamadas = []

    def _siguiente(self, nombre, operacion):
        self.llamadas.append((nombre, operacion))
        siguiente = (self.resultados.pop(0) if self.resultados
                     else ResultadoProveedor(RESULTADO_EXITOSO))
        if isinstance(siguiente, BaseException):
            raise siguiente
        return siguiente

    def otorgar(self, operacion):
        return self._siguiente('otorgar', operacion)

    def revocar(self, operacion):
        return self._siguiente('revocar', operacion)

    def consultar(self, operacion):
        return self._siguiente('consultar', operacion)


@pytest.fixture
def proveedor_simulado():
    simulado = ProveedorSimulado()
    for tipo in (PROVEEDOR_LDAP, PROVEEDOR_CONECTOR):
        providers.registrar_proveedor(tipo, lambda: simulado)
    yield simulado
    providers.quitar_proveedor(PROVEEDOR_CONECTOR)
    providers.registrar_proveedor(PROVEEDOR_LDAP, ProveedorLdap)


@pytest.fixture(autouse=True)
def sin_manejadores():
    manejadores.quitar_manejadores()
    yield
    manejadores.quitar_manejadores()


@pytest.fixture
def avisos(monkeypatch):
    llamadas = []

    def _registrar(usuario, plataforma, nivel, operacion):
        llamadas.append((usuario.id, plataforma.id, nivel, operacion))
        return {'status': 'success', 'recipients': 1}

    monkeypatch.setattr(ejecucion, 'notificar_aprovisionamiento_fallido',
                        _registrar)
    return llamadas


@pytest.fixture
def datos(app):
    """Área, plataforma LDAP con grupos y un usuario."""
    area = fabricas.crear_area()
    plataforma = fabricas.crear_plataforma(
        area, integration_type=TIPO_LDAP, ldap_group_user_dn=GRUPO_USUARIO,
        ldap_group_admin_dn=GRUPO_ADMIN)
    usuario = fabricas.crear_usuario(areas=[area])
    return area, plataforma, usuario


@pytest.fixture
def nuevo_trabajo(datos):
    """`nuevo_trabajo(clave, operacion=…, nivel=…)` encola y hace commit."""
    _, plataforma, usuario = datos

    def _nuevo(clave='clave-1', operacion=OPERACION_OTORGAR,
               nivel=NIVEL_USUARIO, plataforma_=None):
        trabajo = queue.encolar(operacion, usuario.id, plataforma_ or plataforma,
                                nivel, clave, access_id=77)
        db.session.commit()
        return trabajo.id

    return _nuevo
