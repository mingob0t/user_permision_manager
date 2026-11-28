"""Pruebas de la API de importación masiva (Bulk Import, /api/v1/import/bulk).
Verifica autenticación, autorización (solo superadmin), validaciones y asignaciones.
"""

from app.authz import ROLE_USER
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform
from tests import fabricas


def test_import_requiere_autenticacion(client):
    res = client.post('/api/v1/import/bulk', json={'entity': 'users', 'records': []})
    assert res.status_code in (401, 302)


def test_import_requiere_superadmin(app, cliente_como):
    user = fabricas.crear_usuario(rol=ROLE_USER)
    cliente = cliente_como(user)
    res = cliente.post('/api/v1/import/bulk', json={'entity': 'users', 'records': []})
    assert res.status_code == 403


def test_import_usuarios_dry_run_y_real(app, cliente_admin, crear_area):
    area_finanzas = crear_area('Finanzas')

    registros = [
        {
            'email': 'maria.lopez@ejemplo.com',
            'nombre': 'María López',
            'rol': 'usuario',
            'areas': 'Finanzas',
        },
        {
            'email': 'carlos.admin@ejemplo.com',
            'nombre': 'Carlos Admin',
            'rol': 'admin_area',
            'areas': 'Finanzas',
        },
    ]

    # 1. Dry run
    res_dry = cliente_admin.post(
        '/api/v1/import/bulk',
        json={'entity': 'users', 'records': registros, 'dry_run': True},
    )
    assert res_dry.status_code == 200
    data_dry = res_dry.get_json()
    assert data_dry['status'] == 'success'
    assert data_dry['total'] == 2
    assert data_dry['valid'] == 2
    assert data_dry['created'] == 0
    assert len(data_dry['errors']) == 0

    assert User.query.filter_by(email='maria.lopez@ejemplo.com').first() is None

    # 2. Ejecución real
    res_real = cliente_admin.post(
        '/api/v1/import/bulk',
        json={'entity': 'users', 'records': registros, 'dry_run': False},
    )
    assert res_real.status_code == 200
    data_real = res_real.get_json()
    assert data_real['status'] == 'success'
    assert data_real['created'] == 2

    u = User.query.filter_by(email='maria.lopez@ejemplo.com').first()
    assert u is not None
    assert u.nombre == 'María López'
    assert u.role == 'usuario'
    assert any(a.name == 'Finanzas' for a in u.areas)


def test_import_usuarios_seguridad_rechaza_administrador(cliente_admin):
    registros = [
        {
            'email': 'hacker@ejemplo.com',
            'nombre': 'Hacker Escalamiento',
            'rol': 'administrador',
        }
    ]
    res = cliente_admin.post(
        '/api/v1/import/bulk',
        json={'entity': 'users', 'records': registros, 'dry_run': False},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert len(data['errors']) == 1
    assert 'No se permite asignar el rol de administrador' in data['errors'][0]['error']


def test_import_areas_y_plataformas(cliente_admin):
    # 1. Crear áreas
    areas_payload = [
        {
            'nombre': 'Logística y Almacén',
            'descripcion': 'Gestión de envíos e inventario',
            'color': '#10b981',
            'icono': 'inventario',
        }
    ]
    res_areas = cliente_admin.post(
        '/api/v1/import/bulk',
        json={'entity': 'areas', 'records': areas_payload, 'dry_run': False},
    )
    assert res_areas.status_code == 200
    assert res_areas.get_json()['created'] == 1

    # 2. Crear plataforma en el área nueva
    plat_payload = [
        {
            'nombre': 'WMS Central',
            'descripcion': 'Sistema de almacenes',
            'area': 'Logística y Almacén',
            'enlace': 'https://wms.empresa.com',
        }
    ]
    res_plat = cliente_admin.post(
        '/api/v1/import/bulk',
        json={'entity': 'platforms', 'records': plat_payload, 'dry_run': False},
    )
    assert res_plat.status_code == 200
    assert res_plat.get_json()['created'] == 1

    p = Platform.query.filter_by(name='WMS Central').first()
    assert p is not None
    assert p.area.name == 'Logística y Almacén'


def test_descargar_plantilla(cliente_admin):
    res = cliente_admin.get('/api/v1/import/template/users')
    assert res.status_code == 200
    assert res.headers['Content-Type'].startswith('text/csv')
    assert 'nombre,correo,rol,areas' in res.get_data(as_text=True)


# --- Regresiones de la revisión (mismas reglas que las altas normales) -------

A = '/api/v1/import/bulk'


def test_lista_vacia_es_valida(cliente_admin):
    res = cliente_admin.post(A, json={'entity': 'areas', 'records': [], 'dry_run': True})
    assert res.status_code == 200
    assert res.get_json()['total'] == 0


def test_registro_que_no_es_objeto_da_400_y_no_500(cliente_admin):
    res = cliente_admin.post(A, json={'entity': 'areas', 'records': ['Finanzas']})
    assert res.status_code == 400
    assert res.get_json()['code'] == 'cuerpo_invalido'


def test_plataforma_con_enlace_no_https_se_rechaza(cliente_admin):
    area = fabricas.crear_area('Finanzas Enlaces')
    for enlace in ('javascript:alert(1)', 'http://sap.empresa.com'):
        res = cliente_admin.post(A, json={'entity': 'platforms', 'records': [
            {'nombre': 'SAP', 'descripcion': 'ERP', 'area': area.name, 'enlace': enlace}]})
        cuerpo = res.get_json()
        assert res.status_code == 200
        assert cuerpo['created'] == 0
        assert 'https' in cuerpo['errors'][0]['error']
    assert Platform.query.filter_by(name='SAP').count() == 0


def test_area_con_icono_o_color_invalido_se_rechaza(cliente_admin):
    res = cliente_admin.post(A, json={'entity': 'areas', 'records': [
        {'nombre': 'Ventas', 'icono': '<script>'},
        {'nombre': 'Compras', 'color': 'rojo'},
    ]})
    cuerpo = res.get_json()
    assert cuerpo['created'] == 0
    assert len(cuerpo['errors']) == 2
    assert Area.query.filter(Area.name.in_(['Ventas', 'Compras'])).count() == 0


def test_identificador_reservado_no_se_importa(cliente_admin):
    res = cliente_admin.post(A, json={'entity': 'users', 'records': [{'email': 'admin'}]})
    assert res.get_json()['created'] == 0


def test_is_active_texto_falso_crea_cuenta_inactiva(cliente_admin):
    cliente_admin.post(A, json={'entity': 'users', 'records': [
        {'email': 'inactiva@ejemplo.com', 'is_active': 'false'}]})
    assert User.query.filter_by(email='inactiva@ejemplo.com').one().is_active is False


def test_error_interno_no_filtra_el_detalle(cliente_admin, monkeypatch):
    from app.modules.bulk_import import services

    def falla(registros, dry_run=False):
        raise RuntimeError('detalle-interno-secreto')

    monkeypatch.setitem(services.ejecutar_importacion_masiva.__globals__, 'procesar_areas', falla)
    res = cliente_admin.post(A, json={'entity': 'areas', 'records': [{'nombre': 'X1'}]})
    assert res.status_code == 500
    assert 'detalle-interno-secreto' not in res.get_data(as_text=True)


def test_alta_de_plataforma_queda_auditada(cliente_admin):
    from app.modules.audit.models import AuditLog
    area = fabricas.crear_area('Finanzas Auditoría')
    cliente_admin.post(A, json={'entity': 'platforms', 'records': [
        {'nombre': 'Nómina', 'descripcion': 'Pagos', 'area': area.name}]})
    assert AuditLog.query.filter_by(action='plataforma_creada', target='Nómina').count() == 1


def test_areas_importadas_nacen_inactivas_sin_admin(cliente_admin):
    """FNC-220: una área no se activa sin admin; la importación no lo tiene."""
    res = cliente_admin.post('/api/v1/import/bulk', json={
        'entity': 'areas', 'dry_run': False,
        'records': [{'nombre': 'Importada', 'descripcion': 'x'}]})

    assert res.status_code == 200
    assert Area.query.filter_by(name='Importada').one().status == 'Inactivo'
