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

def create_app(config_overrides=None):
    """Crea la aplicación.

    `config_overrides` (opcional) reemplaza claves de configuración antes de
    iniciar las extensiones; lo usan las pruebas para apuntar a una BD
    temporal. Sin él (producción, `run.py`), el comportamiento no cambia.
    """
    # Flask es solo API: no sirve frontend. `static_folder=None` desactiva la
    # ruta /static, que ya no tiene contenido. Las plantillas se conservan
    # únicamente para las páginas de error.
    # Flask es solo API: ni plantillas ni estáticos.
    app = Flask(__name__, template_folder=None, static_folder=None)

    # Configuración de base de datos y seguridad
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'nexus-premium-secret-key')
    db_engine = os.getenv('DB_ENGINE', 'sqlite')
    if db_engine == 'mysql':
        db_uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    else:
        db_uri = 'sqlite:///nexus.db'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
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



    # Inicializar Extensiones
    Compress(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    # La pantalla de acceso vive en el frontend; sin esto, Flask redirigiría a
    # su ruta heredada y el navegador daría un salto de más.
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, inicie sesión para acceder."
    login_manager.login_message_category = "info"

    @login_manager.unauthorized_handler
    def unauthorized():
        """Sin sesión: JSON para las llamadas de API, redirección para el resto."""
        from flask import redirect, request as req
        wants_json = (
            req.is_json
            or '/api/' in req.path
            or req.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or req.accept_mimetypes['application/json']
            >= req.accept_mimetypes['text/html']
        )
        if wants_json:
            return jsonify({'status': 'error',
                            'message': 'Sesión no válida.'}), 401
        target = (os.getenv('FRONTEND_URL', '') or '') + '/login'
        return redirect(target)

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

    # Registro de Blueprints
    from app.modules.core.routes import core_bp
    from app.modules.settings.routes import settings_bp
    from app.modules.audit.routes import audit_bp
    from app.modules.notifications.routes import notifications_bp
    from app.modules.auth.routes import auth_bp
    from app.modules.users.routes import users_bp
    from app.modules.areas.routes import areas_bp
    from app.modules.api.routes import api_bp
    from app.modules.api.crud import crud_bp
    from app.modules.api.admin import admin_bp
    from app.modules.api.auth import auth_api_bp






    
    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(areas_bp)
    # La API v1 usa la cookie de sesión y no formularios, así que no
    # participa del CSRF de Flask-WTF.
    for bp in (api_bp, crud_bp, admin_bp, auth_api_bp):
        csrf.exempt(bp)
        app.register_blueprint(bp)

    # Los blueprints heredados ya no procesan datos: solo redirigen o devuelven
    # 410. Sin exentarlos, el CSRF los intercepta antes y responde un 400 en
    # HTML, ocultando la indicación del endpoint que los reemplaza.
    for bp in (auth_bp, users_bp, areas_bp, audit_bp, notifications_bp,
               settings_bp, core_bp):
        csrf.exempt(bp)



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
            from app.modules.auth.models import User
            if not User.query.first():
                admin = User(email='admin', nombre='admin', role='administrador')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("👤 Usuario Maestro Creado: admin / admin123")
            print("🚀 Base de Datos Sincronizada Correctamente")
        except Exception as e:
            print(f"❌ Error al sincronizar base de datos: {e}")


    # Flask es API: los errores se responden en JSON. Las páginas de error de
    # la interfaz las sirve el frontend.
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

    return app
