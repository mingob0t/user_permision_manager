"""Grupos LDAP de áreas y plataformas inactivas (FNC-163).

Al pasar a `Inactivo` los grupos se mueven (ModifyDN con `new_superior`) a
`LDAP_GROUPS_INACTIVE_BASE_DN`; al reactivar regresan. Lo hace el worker
(`ejecutar_traslado`); la API solo deja el traslado `pendiente`. El directorio
es el simulado `MOCK_SYNC` (`tests/directorio_falso.py`), sin red.
"""
import ldap3
import pytest
from ldap3.core.exceptions import LDAPSocketOpenError

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN
from app.modules.audit.models import AuditLog
from app.modules.core.models import Platform
from app.modules.directory.configuracion import (ErrorConfiguracionDirectorio,
                                                 cargar_configuracion)
from app.modules.directory.dn import separar_dn
from app.modules.directory.errors import Resultado
from app.modules.directory.writer import EscritorDirectorio
from app.modules.platforms import traslado_grupos
from app.modules.platforms.models import TrasladoGrupos
from app.modules.platforms.tipos import NIVEL_USUARIO
from app.modules.provisioning.ldap_provider import ProveedorLdap
from app.modules.provisioning.providers import Operacion
from app.modules.provisioning.tipos import RESULTADO_EXITOSO
from tests import fabricas
from tests.directorio_falso import (BASE_DN, ENTORNO_VALIDO, GRUPOS_BASE_DN,
                                    instalar_directorio)

A = '/api/v1'
INACTIVOS = f'ou=inactivos,{BASE_DN}'
VARIABLE = 'LDAP_GROUPS_INACTIVE_BASE_DN'


def _dn(nombre, base=GRUPOS_BASE_DN):
    return f'cn={nombre},{base}'


@pytest.fixture
def despertados(monkeypatch):
    """Registra los ids con que se despierta al worker (sin Redis)."""
    ids = []
    monkeypatch.setattr(traslado_grupos, 'despertar', ids.extend)
    return ids


@pytest.fixture
def directorio(app, monkeypatch, despertados):
    servidor = instalar_directorio(monkeypatch,
                                   variables={VARIABLE: INACTIVOS})
    servidor._agregar(INACTIVOS, objectClass='organizationalUnit',
                      ou='inactivos')
    return servidor


@pytest.fixture
def superadmin(cliente_como):
    return cliente_como(fabricas.crear_usuario(ROLE_ADMIN,
                                               email='super@pruebas.local'))


def _grupo(directorio, nombre):
    directorio._agregar(_dn(nombre), objectClass='groupOfNames', cn=nombre,
                        member=['cn=relleno,dc=pruebas,dc=local'])


def _miembros(entrada):
    return [v.decode() if isinstance(v, bytes) else str(v)
            for v in entrada['member']]


def _plataforma(directorio, area, nombre='wiki', **campos):
    _grupo(directorio, f'{nombre}-usuario')
    _grupo(directorio, f'{nombre}-admin')
    return fabricas.crear_plataforma(
        area, nombre=nombre, integration_type='ldap',
        ldap_group_user_dn=_dn(f'{nombre}-usuario'),
        ldap_group_admin_dn=_dn(f'{nombre}-admin'), **campos)


def _en(directorio, dn):
    return dn in directorio.servidor.dit


def _ubicacion(directorio, nombre):
    """`activos`, `inactivos` o `ninguna` según dónde esté el grupo `nombre`."""
    if _en(directorio, _dn(nombre)):
        return 'activos'
    if _en(directorio, _dn(nombre, INACTIVOS)):
        return 'inactivos'
    return 'ninguna'


def _traslado(plataforma_id):
    db.session.expire_all()
    return TrasladoGrupos.query.filter_by(platform_id=plataforma_id).first()


def _ejecutar(plataforma_id):
    traslado = _traslado(plataforma_id)
    return traslado_grupos.ejecutar_traslado(traslado.id)


def _cambiar(cliente, ruta, **campos):
    respuesta = cliente.put(f'{A}{ruta}', json=campos)
    assert respuesta.status_code == 200, respuesta.get_json()
    return respuesta.get_json()


def _eventos(accion):
    return AuditLog.query.filter_by(action=accion).all()


# --------------------------------------------------------------------------- #
# Plataforma: desactivar mueve, reactivar regresa
# --------------------------------------------------------------------------- #

def test_desactivar_plataforma_mueve_sus_grupos_y_reactivar_los_regresa(
        directorio, superadmin, despertados):
    plataforma = _plataforma(directorio, fabricas.crear_area())

    respuesta = _cambiar(superadmin, f'/platforms/{plataforma.id}',
                         status='Inactivo')

    # La petición solo deja el pendiente: el directorio no se toca.
    assert _ubicacion(directorio, 'wiki-usuario') == 'activos'
    assert respuesta['platform']['groups_move_status'] == 'pendiente'
    assert despertados == [_traslado(plataforma.id).id]

    assert _ejecutar(plataforma.id) == 'hecho'
    assert _ubicacion(directorio, 'wiki-usuario') == 'inactivos'
    assert _ubicacion(directorio, 'wiki-admin') == 'inactivos'
    # El `cn` no cambia y la plataforma conserva su DN original.
    assert db.session.get(Platform, plataforma.id).ldap_group_user_dn == \
        _dn('wiki-usuario')
    assert db.session.get(Platform, plataforma.id).to_dict()[
        'groups_location'] == 'inactivos'

    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Activo')
    assert _ejecutar(plataforma.id) == 'hecho'
    assert _ubicacion(directorio, 'wiki-usuario') == 'activos'
    assert _ubicacion(directorio, 'wiki-admin') == 'activos'
    assert db.session.get(Platform, plataforma.id).to_dict()[
        'groups_location'] == 'activos'


def test_los_miembros_no_se_tocan_al_mover(directorio, superadmin):
    area = fabricas.crear_area()
    directorio.agregar('ana', 'clave')
    plataforma = _plataforma(directorio, area)
    EscritorDirectorio().add_member(
        _dn('wiki-usuario'), 'uid=ana,ou=personas,dc=pruebas,dc=local')

    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')
    _ejecutar(plataforma.id)

    miembros = _miembros(
        directorio.servidor.dit[_dn('wiki-usuario', INACTIVOS)])
    assert any('uid=ana' in m for m in miembros)


def test_cada_movimiento_se_audita_como_sistema(directorio, superadmin):
    plataforma = _plataforma(directorio, fabricas.crear_area())
    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')
    _ejecutar(plataforma.id)

    (evento,) = _eventos('grupos_movidos')
    assert evento.user == 'sistema'
    assert evento.platform_id == plataforma.id
    assert evento.status == 'success'
    assert 'inactivos' in evento.detail


# --------------------------------------------------------------------------- #
# Área: desactivar mueve todas sus plataformas; reactivar respeta las inactivas
# --------------------------------------------------------------------------- #

def test_area_inactiva_mueve_los_grupos_de_todas_sus_plataformas(
        directorio, superadmin):
    area = fabricas.crear_area()
    una = _plataforma(directorio, area, 'wiki')
    otra = _plataforma(directorio, area, 'crm')

    _cambiar(superadmin, f'/areas/{area.id}', status='Inactivo')
    for plataforma in (una, otra):
        assert _ejecutar(plataforma.id) == 'hecho'

    for nombre in ('wiki-usuario', 'wiki-admin', 'crm-usuario', 'crm-admin'):
        assert _ubicacion(directorio, nombre) == 'inactivos'


def test_reactivar_el_area_respeta_la_plataforma_inactiva_por_si_misma(
        directorio, superadmin, despertados):
    area = fabricas.crear_area()
    fabricas.crear_usuario(ROLE_AREA_ADMIN, areas_administradas=[area])  # FNC-220
    una = _plataforma(directorio, area, 'wiki')
    otra = _plataforma(directorio, area, 'crm', status='Inactivo')
    _cambiar(superadmin, f'/areas/{area.id}', status='Inactivo')
    _ejecutar(una.id)
    _ejecutar(otra.id)

    despertados.clear()
    _cambiar(superadmin, f'/areas/{area.id}', status='Activo')
    # Solo la plataforma activa por sí misma vuelve; la otra no se pide.
    assert despertados == [_traslado(una.id).id]
    _ejecutar(una.id)
    assert _traslado(otra.id).status == 'hecho'

    assert _ubicacion(directorio, 'wiki-usuario') == 'activos'
    assert _ubicacion(directorio, 'crm-usuario') == 'inactivos'
    assert _ubicacion(directorio, 'crm-admin') == 'inactivos'


def test_reactivar_la_plataforma_con_el_area_inactiva_no_los_regresa(
        directorio, superadmin, despertados):
    area = fabricas.crear_area()
    plataforma = _plataforma(directorio, area)
    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')
    _ejecutar(plataforma.id)
    area.status = 'Inactivo'
    db.session.commit()

    despertados.clear()
    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Activo')

    assert despertados == []  # el área sigue inactiva: nada que regresar
    assert _ubicacion(directorio, 'wiki-usuario') == 'inactivos'
    assert _ubicacion(directorio, 'wiki-admin') == 'inactivos'


# --------------------------------------------------------------------------- #
# Apagado y casos que no aplican
# --------------------------------------------------------------------------- #

def test_con_la_variable_vacia_no_se_hace_nada(app, monkeypatch, despertados,
                                               cliente_como):
    directorio = instalar_directorio(monkeypatch)  # sin la variable
    plataforma = _plataforma(directorio, fabricas.crear_area())
    cliente = cliente_como(fabricas.crear_usuario(ROLE_ADMIN,
                                                  email='s@pruebas.local'))

    respuesta = _cambiar(cliente, f'/platforms/{plataforma.id}',
                         status='Inactivo')

    assert _traslado(plataforma.id) is None
    assert despertados == []
    assert respuesta['platform']['status'] == 'Inactivo'
    assert respuesta['platform']['groups_location'] == 'activos'
    assert respuesta['platform']['groups_move_status'] is None
    assert _ubicacion(directorio, 'wiki-usuario') == 'activos'


def test_plataforma_sin_grupo_ldap_no_aplica(directorio, superadmin):
    area = fabricas.crear_area()
    conector = fabricas.crear_plataforma(area, integration_type='conector')
    manual = fabricas.crear_plataforma(area, integration_type='ldap')

    _cambiar(superadmin, f'/areas/{area.id}', status='Inactivo')
    _cambiar(superadmin, f'/platforms/{conector.id}', status='Inactivo')

    assert _traslado(conector.id) is None
    assert _traslado(manual.id) is None


# --------------------------------------------------------------------------- #
# Idempotencia y fallos
# --------------------------------------------------------------------------- #

def test_si_el_grupo_ya_esta_donde_debe_no_falla(directorio):
    _grupo(directorio, 'g1')
    escritor = EscritorDirectorio()
    assert escritor.mover_grupo(_dn('g1'), INACTIVOS).resultado is Resultado.HECHO
    # Pedir lo mismo con el grupo ya en su lugar es idempotente.
    repetido = escritor.mover_grupo(_dn('g1', INACTIVOS), INACTIVOS)
    assert repetido.resultado is Resultado.YA_ESTABA


def test_un_traslado_hecho_no_se_vuelve_a_ejecutar(directorio, superadmin):
    plataforma = _plataforma(directorio, fabricas.crear_area())
    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')
    assert _ejecutar(plataforma.id) == 'hecho'
    # Un traslado ya hecho no se vuelve a ejecutar.
    assert traslado_grupos.ejecutar_traslado(
        _traslado(plataforma.id).id) is None


def test_guardar_sin_cambios_no_vuelve_a_pedir_el_traslado(directorio,
                                                           superadmin,
                                                           despertados):
    plataforma = _plataforma(directorio, fabricas.crear_area())
    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')
    _ejecutar(plataforma.id)
    despertados.clear()

    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')

    assert despertados == []
    assert _traslado(plataforma.id).status == 'hecho'


def test_fallo_del_directorio_se_reintenta_con_espera(directorio, superadmin,
                                                      monkeypatch):
    plataforma = _plataforma(directorio, fabricas.crear_area())
    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')

    def caido(self, *args, **kwargs):
        raise LDAPSocketOpenError('sin red')

    with monkeypatch.context() as parche:
        parche.setattr(ldap3.Connection, 'modify_dn', caido)
        assert _ejecutar(plataforma.id) == 'pendiente'

    traslado = _traslado(plataforma.id)
    assert traslado.attempts_count == 1
    assert traslado.last_error == 'directorio'
    assert traslado.next_attempt_at is not None
    assert _ubicacion(directorio, 'wiki-usuario') == 'activos'
    assert _eventos('grupos_traslado_fallido') == []
    # Aún no le toca: no se reserva.
    assert traslado_grupos.ejecutar_traslado(traslado.id) is None

    traslado.next_attempt_at = None
    db.session.commit()
    assert _ejecutar(plataforma.id) == 'hecho'
    assert _ubicacion(directorio, 'wiki-usuario') == 'inactivos'


def test_intentos_agotados_dejan_fallido_con_auditoria(directorio, superadmin,
                                                       monkeypatch):
    monkeypatch.setenv('PROVISIONING_MAX_ATTEMPTS', '1')
    plataforma = _plataforma(directorio, fabricas.crear_area())
    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')

    def caido(self, *args, **kwargs):
        raise LDAPSocketOpenError('sin red')

    monkeypatch.setattr(ldap3.Connection, 'modify_dn', caido)
    assert _ejecutar(plataforma.id) == 'fallido'

    (evento,) = _eventos('grupos_traslado_fallido')
    assert evento.status == 'error' and evento.user == 'sistema'
    assert 'directorio' in evento.detail
    assert _traslado(plataforma.id).next_attempt_at is None


def test_error_permanente_no_se_reintenta_y_guardar_de_nuevo_lo_rearma(
        directorio, superadmin):
    plataforma = _plataforma(directorio, fabricas.crear_area())
    del directorio.servidor.dit[INACTIVOS]  # la OU destino no existe
    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')

    assert _ejecutar(plataforma.id) == 'fallido'
    assert _traslado(plataforma.id).last_error == 'ou_destino_inexistente'
    assert _ubicacion(directorio, 'wiki-usuario') == 'activos'

    directorio._agregar(INACTIVOS, objectClass='organizationalUnit',
                        ou='inactivos')
    respuesta = _cambiar(superadmin, f'/platforms/{plataforma.id}',
                         status='Inactivo')
    assert respuesta['platform']['groups_move_status'] == 'pendiente'
    assert _ejecutar(plataforma.id) == 'hecho'
    assert _ubicacion(directorio, 'wiki-usuario') == 'inactivos'


def test_grupo_inexistente_queda_fallido_sin_adivinar(directorio, superadmin):
    area = fabricas.crear_area()
    plataforma = fabricas.crear_plataforma(
        area, integration_type='ldap',
        ldap_group_user_dn=_dn('no-existe'),
        ldap_group_admin_dn=_dn('tampoco'))

    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')

    assert _ejecutar(plataforma.id) == 'fallido'
    assert _traslado(plataforma.id).last_error == 'grupo_inexistente'


def test_no_se_cambian_los_grupos_mientras_estan_en_inactivos(directorio,
                                                              superadmin):
    plataforma = _plataforma(directorio, fabricas.crear_area())
    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')
    _ejecutar(plataforma.id)

    respuesta = superadmin.put(f'{A}/platforms/{plataforma.id}', json={
        'ldap_group_user_dn': _dn('otro-usuario'),
        'ldap_group_admin_dn': _dn('otro-admin')})

    assert respuesta.status_code == 409
    assert respuesta.get_json()['code'] == 'grupos_en_inactivos'


# --------------------------------------------------------------------------- #
# Accesos con la plataforma inactiva
# --------------------------------------------------------------------------- #

def test_otorgar_y_revocar_operan_sobre_el_grupo_en_inactivos(directorio,
                                                              superadmin):
    area = fabricas.crear_area()
    dn_ana = directorio.agregar('ana', 'clave', correo='ana@pruebas.local')
    plataforma = _plataforma(directorio, area)
    usuario = fabricas.crear_usuario(email='ana@pruebas.local')
    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')
    _ejecutar(plataforma.id)
    operacion = Operacion(id_operacion='1', clave_idempotencia='k',
                          operacion='otorgar', nivel=NIVEL_USUARIO,
                          plataforma_id=plataforma.id, usuario_id=usuario.id)
    proveedor = ProveedorLdap()

    assert proveedor.otorgar(operacion).resultado == RESULTADO_EXITOSO
    movido = directorio.servidor.dit[_dn('wiki-usuario', INACTIVOS)]
    assert dn_ana in _miembros(movido)
    assert _ubicacion(directorio, 'wiki-usuario') == 'inactivos'

    assert proveedor.revocar(operacion).resultado == RESULTADO_EXITOSO
    assert dn_ana not in _miembros(movido)


# --------------------------------------------------------------------------- #
# Escritor: mover_grupo
# --------------------------------------------------------------------------- #

def test_mover_grupo_solo_dentro_de_las_bases(directorio):
    escritor = EscritorDirectorio()
    _grupo(directorio, 'g1')

    fuera = escritor.mover_grupo(f'cn=g1,{BASE_DN}', INACTIVOS)
    assert fuera.resultado is Resultado.ERROR_PERMANENTE
    assert fuera.motivo == 'fuera_de_base'
    # El destino tampoco puede ser cualquier parte del árbol.
    otro = escritor.mover_grupo(_dn('g1'), f'ou=personas,{BASE_DN}')
    assert otro.motivo == 'fuera_de_base'
    assert _ubicacion(directorio, 'g1') == 'activos'


def test_mover_grupo_con_nombre_ocupado_en_destino(directorio):
    _grupo(directorio, 'g1')
    directorio._agregar(_dn('g1', INACTIVOS), objectClass='groupOfNames',
                        cn='g1', member=['cn=relleno,dc=pruebas,dc=local'])

    resultado = EscritorDirectorio().mover_grupo(_dn('g1'), INACTIVOS)

    assert resultado.resultado is Resultado.ERROR_PERMANENTE
    assert resultado.motivo == 'destino_ocupado'


def test_mover_grupo_sin_la_variable_no_hace_nada(app, monkeypatch):
    directorio = instalar_directorio(monkeypatch)
    _grupo(directorio, 'g1')

    resultado = EscritorDirectorio().mover_grupo(_dn('g1'), INACTIVOS)

    assert resultado.motivo == 'inactivos_no_configurado'
    assert _en(directorio, _dn('g1'))


# --------------------------------------------------------------------------- #
# Configuración y utilidades
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('valor', [
    GRUPOS_BASE_DN,                    # igual a la base de activos
    f'ou=viejos,{GRUPOS_BASE_DN}',     # dentro de la base de activos
    BASE_DN,                           # contiene la base de activos
    'esto no es un dn',
])
def test_la_ou_de_inactivos_invalida_impide_arrancar(valor):
    with pytest.raises(ErrorConfiguracionDirectorio) as error:
        cargar_configuracion({**ENTORNO_VALIDO, VARIABLE: valor})
    assert VARIABLE in str(error.value)


def test_la_ou_de_inactivos_es_opcional_y_valida():
    assert cargar_configuracion(ENTORNO_VALIDO).grupos_inactivos_base_dn == ''
    cfg = cargar_configuracion({**ENTORNO_VALIDO, VARIABLE: INACTIVOS})
    assert cfg.grupos_inactivos_base_dn == INACTIVOS


def test_separar_dn_conserva_el_rdn_con_escapes():
    assert separar_dn('cn=a\\,b,ou=g,dc=x') == ('cn=a\\,b', 'ou=g,dc=x')
    assert separar_dn('cn=a+uid=1,ou=g,dc=x') == ('cn=a+uid=1', 'ou=g,dc=x')
    assert separar_dn('dc=x') is None
    assert separar_dn('no es dn') is None


def test_el_tipo_de_trabajo_esta_registrado_en_el_worker(app):
    from app.modules.provisioning.tipos_de_trabajo import funciones_permitidas
    assert traslado_grupos.FUNCION_TRASLADO in funciones_permitidas()


def test_destino_con_el_mismo_cn_de_otra_plataforma_no_se_adopta(directorio):
    """Auditor-seguridad: con el origen inexistente, un grupo homónimo en la
    OU de inactivos (de otra plataforma) no se da por movido ni se mueve."""
    _grupo(directorio, 'g1')
    escritor = EscritorDirectorio()
    escritor.mover_grupo(_dn('g1'), INACTIVOS)       # el grupo de la plataforma A
    ou_b = f'ou=b,{GRUPOS_BASE_DN}'
    directorio._agregar(ou_b, objectClass='organizationalUnit', ou='b')

    resultado = escritor.mover_grupo(f'cn=g1,{ou_b}', INACTIVOS)  # B sin grupo

    assert resultado.resultado is Resultado.NO_EXISTE
    assert _en(directorio, _dn('g1', INACTIVOS))     # el de A sigue en su sitio


def test_el_rdn_de_grupo_debe_ser_unico_con_la_funcion_encendida(directorio,
                                                                 superadmin):
    area = fabricas.crear_area()
    _plataforma(directorio, area, 'wiki')
    ou = f'ou=otra,{GRUPOS_BASE_DN}'
    otra = fabricas.crear_plataforma(area, nombre='otra')

    respuesta = superadmin.put(f'{A}/platforms/{otra.id}', json={
        'integration_type': 'ldap',
        'ldap_group_user_dn': f'cn=wiki-usuario,{ou}',
        'ldap_group_admin_dn': f'cn=otra-admin,{ou}'})

    assert respuesta.status_code == 409
    assert respuesta.get_json()['code'] == 'grupo_en_uso'


def test_un_pendiente_con_intentos_agotados_sin_reserva_se_rearma(
        directorio, superadmin):
    plataforma = _plataforma(directorio, fabricas.crear_area())
    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')
    traslado = _traslado(plataforma.id)
    traslado.attempts_count = traslado.max_attempts  # el worker cayó al cerrar
    db.session.commit()
    assert _ejecutar(plataforma.id) is None  # nadie lo toma

    _cambiar(superadmin, f'/platforms/{plataforma.id}', status='Inactivo')

    assert _traslado(plataforma.id).attempts_count == 0
    assert _ejecutar(plataforma.id) == 'hecho'
