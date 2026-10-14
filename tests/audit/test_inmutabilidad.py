"""Inmutabilidad del registro de auditoría (FNC-047, SEC-AUD-03).

- El ORM rechaza `UPDATE` y `DELETE` de `AuditLog`, por objeto y masivos.
- Ninguna ruta de la app modifica ni borra registros (solo `GET`).
- Borrar un usuario no borra su auditoría (sin cascada).
"""

import pytest
from sqlalchemy import delete, update

from app import db
from app.authz import ROLE_USER
from app.modules.audit.inmutabilidad import RegistroInmutable
from app.modules.audit.models import AuditLog
from app.modules.audit.services import add_audit_log
from tests import fabricas

A = '/api/v1'
METODOS_DE_LECTURA = {'GET', 'HEAD', 'OPTIONS'}
FRAGMENTO_RUTA = 'audit'


@pytest.fixture
def registro(app):
    add_audit_log('ORIGINAL', 'info')
    return AuditLog.query.one()


def _sigue_igual(registro_id):
    db.session.rollback()
    db.session.expire_all()
    assert db.session.get(AuditLog, registro_id).action == 'ORIGINAL'


def test_editar_un_registro_se_rechaza(registro):
    registro_id = registro.id
    registro.action = 'CAMBIADO'

    with pytest.raises(RegistroInmutable):
        db.session.commit()
    _sigue_igual(registro_id)


def test_borrar_un_registro_se_rechaza(registro):
    registro_id = registro.id
    db.session.delete(registro)

    with pytest.raises(RegistroInmutable):
        db.session.commit()
    _sigue_igual(registro_id)


@pytest.mark.parametrize('operacion', [
    lambda: AuditLog.query.update({'action': 'CAMBIADO'}),
    lambda: AuditLog.query.delete(),
    lambda: db.session.execute(update(AuditLog).values(action='CAMBIADO')),
    lambda: db.session.execute(delete(AuditLog)),
    lambda: db.session.execute(
        AuditLog.__table__.update().values(action='CAMBIADO')),
    lambda: db.session.execute(AuditLog.__table__.delete()),
], ids=['query.update', 'query.delete', 'orm update', 'orm delete',
        'tabla update', 'tabla delete'])
def test_operaciones_masivas_se_rechazan(registro, operacion):
    registro_id = registro.id
    with pytest.raises(RegistroInmutable):
        operacion()
    _sigue_igual(registro_id)


def test_otras_tablas_se_siguen_editando(app):
    usuario = fabricas.crear_usuario(ROLE_USER)

    usuario.nombre = 'Editado'
    db.session.commit()

    assert db.session.get(type(usuario), usuario.id).nombre == 'Editado'


def test_ninguna_ruta_modifica_ni_borra_auditoria(app):
    escrituras = sorted(
        (regla.rule, sorted(regla.methods - METODOS_DE_LECTURA))
        for regla in app.url_map.iter_rules()
        if FRAGMENTO_RUTA in regla.rule and regla.methods - METODOS_DE_LECTURA)

    assert escrituras == []


def test_borrar_un_usuario_conserva_su_auditoria(app, cliente_admin):
    usuario = fabricas.crear_usuario(ROLE_USER, email='borrable@pruebas.local')
    add_audit_log('EVENTO PREVIO', target=usuario.email,
                  target_user_id=usuario.id)

    respuesta = cliente_admin.delete(f'{A}/users/{usuario.id}')

    assert respuesta.status_code == 200
    previo = AuditLog.query.filter_by(action='EVENTO PREVIO').one()
    assert previo.target == 'borrable@pruebas.local'
