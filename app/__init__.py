from flask import Flask, jsonify, send_from_directory
from flask_compress import Compress
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configurar Zona Horaria del Sistema
tz = os.getenv('TZ_APP', os.getenv('TZ', 'America/Mexico_City'))
os.environ['TZ'] = tz
try:
    import time
    time.tzset()
except AttributeError:
    pass # Windows fallback

# Instancias globales
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def _configurar(app, config_overrides):
    """Configuración de base de datos, sesión y seguridad; luego los
    reemplazos (pruebas)."""
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'nexus-premium-secret-key')
    # La misma regla la usan las migraciones (migrations/env.py).
    from app.utils.uri_bd import construir_uri_bd
    app.config['SQLALCHEMY_DATABASE_URI'] = construir_uri_bd()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configuración de Sesiones para evitar cierres inesperados
    from datetime import timedelta
    from flask import session
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SESSION_COOKIE_NAME'] = 'nexus_session'
    app.config['WTF_CSRF_TIME_LIMIT'] = None # Evita expiración de tokens por tiempo en dev

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    # Prevención de pérdida de conexión (Recomendado para MySQL)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    if config_overrides:
        app.config.update(config_overrides)


def _validar_configuracion():
    """Variables inválidas detienen el arranque."""
    # Con LDAP_URL definida, sin TLS o con configuración incompleta del
    # directorio la app no arranca (FNC-040, SEC-LDAP-02).
    from app.modules.directory.configuracion import validar_al_arrancar
    validar_al_arrancar()
    # Variables PROVISIONING_* inválidas detienen el arranque (FNC-049).
    from app.modules.provisioning.configuracion import (
        validar_al_arrancar as validar_aprovisionamiento)
    validar_aprovisionamiento()
    # Variables CONNECTOR_* inválidas (p. ej. una IP en la lista blanca)
    # detienen el arranque (FNC-050).
    from app.modules.connectors.configuracion import (
        validar_al_arrancar as validar_conectores)
    validar_conectores()
    # Fuera de dev, `VAULTWARDEN_*` incompleta o insegura detiene el arranque
    # (FNC-068); no se conecta a Vaultwarden al arrancar.
    from app.modules.secretos.configuracion import (
        validar_al_arrancar as validar_secretos)
    validar_secretos()


def _iniciar_extensiones(app):
    """Extensiones de Flask, inicio de sesión y Redis."""
    Compress(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_message = "Por favor, inicie sesión para acceder."
    login_manager.login_message_category = "info"

    @login_manager.unauthorized_handler
    def unauthorized():
        """Sin sesión: 401 JSON (toda ruta protegida es de `/api/v1`)."""
        return jsonify({'status': 'error',
                        'message': 'Sesión no válida.'}), 401

    # Configuración de Redis
    from app.utils.redis_client import registry as redis_registry
    redis_registry.host = os.getenv('REDIS_HOST', 'localhost')
    redis_registry.port = int(os.getenv('REDIS_PORT', 6379))
    redis_registry.password = os.getenv('REDIS_PASS', None)
    redis_registry.connect() # Intento de conexión inicial

    @login_manager.user_loader
    def load_user(user_id):
        if user_id is None or user_id == "None":
            return None
        from app.modules.auth.models import User
        try:
            return User.query.get(int(user_id))
        except ValueError:
            return None


def _registrar_blueprints(app):
    """Registra la API v1. Ya no participa del CSRF de Flask-WTF: usa la
    cookie de sesión y no formularios."""
    from app.modules.api.routes import api_bp
    from app.modules.api.auth import auth_api_bp
    from app.modules.users.api import users_api_bp
    from app.modules.users.preferencias_api import preferences_api_bp
    from app.modules.users.higiene_api import hygiene_api_bp
    from app.modules.areas.api import areas_api_bp
    from app.modules.settings.api import settings_api_bp
    from app.modules.settings.respaldo_api import respaldo_api_bp
    from app.modules.notifications.api import notifications_api_bp
    from app.modules.directory.api import directory_api_bp
    from app.modules.platforms.api import platforms_api_bp
    from app.modules.audit.api import audit_api_bp
    from app.modules.access.api import access_api_bp
    from app.modules.access_requests.api import access_requests_api_bp
    from app.modules.access.inventario_api import access_inventory_api_bp
    from app.modules.provisioning.api import provisioning_api_bp
    from app.modules.connectors.api import connectors_api_bp
    from app.modules.home.api import home_api_bp

    for bp in (api_bp, preferences_api_bp, hygiene_api_bp, settings_api_bp,
               notifications_api_bp, respaldo_api_bp, auth_api_bp,
               users_api_bp, areas_api_bp, directory_api_bp,
               platforms_api_bp, audit_api_bp, access_requests_api_bp,
               access_api_bp, access_inventory_api_bp, provisioning_api_bp,
               connectors_api_bp, home_api_bp):
        csrf.exempt(bp)
        app.register_blueprint(bp)


def _registrar_cli_y_manejadores(app):
    """Comando del worker y manejadores de eventos entre módulos."""
    # Worker de aprovisionamiento: `flask provisioning worker` (FNC-049).
    from app.modules.provisioning.cli import provisioning_cli
    app.cli.add_command(provisioning_cli)
    # El resultado de cada trabajo actualiza el acceso otorgado (FNC-054).
    from app.modules.access.manejadores import registrar as registrar_accesos
    registrar_accesos()
    # Proveedor `conector` del ejecutor y tipo `noop` en dev/pruebas (FNC-050).
    from app.modules.connectors import registrar as registrar_conectores
    registrar_conectores(app)


def _crear_tablas(app):
    """Importa los modelos y crea las tablas y el usuario inicial."""
    # Sincronizar Modelos (Importar antes de crear tablas)
    from app.modules.settings.models import SystemConfig
    from app.modules.audit.models import AuditLog
    from app.modules.notifications.models import SMTPConfig, NotificationTemplate
    from app.modules.auth.models import AuthConfig, User

    # Crear tablas automáticamente dentro del contexto de la app
    with app.app_context():
        try:
            db.create_all()
            # Crear usuario inicial si no existe ninguno
            if not User.query.first():
                admin = User(email='admin', nombre='admin', role='administrador')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("👤 Usuario Maestro Creado: admin / admin123")
            print("🚀 Base de Datos Sincronizada Correctamente")
        except Exception as e:
            print(f"❌ Error al sincronizar base de datos: {e}")


def _registrar_manejadores_de_error(app):
    """Flask es API: los errores se responden en JSON. Las páginas de error
    de la interfaz las sirve el frontend."""
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return jsonify({'status': 'error',
                        'message': 'Token CSRF ausente o no válido.'}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'status': 'error', 'message': 'Recurso no encontrado.'}), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(f"Error interno: {error}")
        return jsonify({'status': 'error', 'message': 'Error interno del servidor.'}), 500

    @app.context_processor
    def inject_global_data():
        from app.modules.settings.models import SystemConfig
        try:
            config = SystemConfig.query.first()
            return dict(
                sys_config=config,
                portal_settings=config,
                csp_nonce=lambda: ""
            )
        except Exception as e:
            return dict(
                sys_config=None,
                portal_settings=None,
                csp_nonce=lambda: ""
            )


def create_app(config_overrides=None):
    """Crea la aplicación.

    `config_overrides` (opcional) reemplaza claves de configuración antes de
    iniciar las extensiones; lo usan las pruebas para apuntar a una BD
    temporal. Sin él (producción, `run.py`), el comportamiento no cambia.

    Flask es solo API: ni plantillas ni estáticos. El orden de los pasos
    importa: la configuración se valida antes de iniciar extensiones y las
    tablas se crean después de registrar los manejadores de eventos.
    """
    app = Flask(__name__, template_folder=None, static_folder=None)
    _configurar(app, config_overrides)
    _validar_configuracion()
    _iniciar_extensiones(app)
    _registrar_blueprints(app)
    _registrar_cli_y_manejadores(app)
    _crear_tablas(app)
    _registrar_manejadores_de_error(app)
    return app
