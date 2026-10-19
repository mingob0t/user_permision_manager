from app import db
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash

# Helper Table for Area-User Relationship
user_areas = db.Table('user_areas',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('area_id', db.Integer, db.ForeignKey('areas.id'), primary_key=True)
)

# Helper Table for Platform-User Relationship (Favs/Access)
user_platforms = db.Table('user_platforms',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('platform_id', db.Integer, db.ForeignKey('platforms.id'), primary_key=True)
)

# Helper Table for User Favorites
user_favorites = db.Table('user_favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('platform_id', db.Integer, db.ForeignKey('platforms.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=True) # Nombre visible del usuario
    password_hash = db.Column(db.String(255), nullable=True) # Nulo para usuarios LDAP
    role = db.Column(db.String(20), default='usuario') # administrador, admin_area, usuario
    auth_source = db.Column(db.String(10), default='local') # local, ldap
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    areas = db.relationship('Area', secondary='user_areas', backref=db.backref('area_users', lazy=True))
    platforms = db.relationship('Platform', secondary='user_platforms', backref=db.backref('platform_users', lazy='dynamic'))
    favorites = db.relationship('Platform', secondary='user_favorites', backref=db.backref('favorited_by', lazy='dynamic'))
    # Áreas que este usuario administra (rol admin_area)
    managed_areas = db.relationship('Area', secondary='area_admins', backref=db.backref('admins', lazy=True))

    # User Interface Preferences
    pref_notifications = db.Column(db.Boolean, default=True)
    pref_email_notifications = db.Column(db.Boolean, default=True)
    pref_refresh_interval = db.Column(db.Integer, default=60)
    pref_tour_enabled = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AuthConfig(db.Model):
    """Configuración LDAP heredada: OBSOLETA desde FNC-043.

    El directorio se configura solo con las variables `LDAP_*` (ADR-004,
    `app/modules/directory/configuracion.py`); nada lee estas columnas, que
    se conservan para el respaldo y la reversión (migración 0004).
    """
    __tablename__ = 'auth_config'
    
    id = db.Column(db.Integer, primary_key=True)
    ldap_host = db.Column(db.String(100), nullable=True)
    ldap_port = db.Column(db.Integer, default=389)
    ldap_ssl = db.Column(db.Boolean, default=False)
    ldap_base_dn = db.Column(db.String(200), nullable=True)
    ldap_user = db.Column(db.String(100), nullable=True)
    # Obsoleta (FNC-043, SEG-08): la migración 0004 la vacía y no se escribe
    # más; la credencial de bind es `LDAP_BIND_PASSWORD` (SEC-LDAP-11).
    ldap_pass = db.Column(db.String(100), nullable=True)
    ldap_user_attr = db.Column(db.String(50), default='sAMAccountName')
    
    # Mapeo de roles por grupos: obsoleto (FNC-042, RF-04); nada lo lee.
    ldap_group_admin = db.Column(db.String(200), nullable=True)
    ldap_group_user = db.Column(db.String(200), nullable=True)
    ldap_role_mappings = db.Column(db.Text, nullable=True) # JSON string for dynamic mappings
    
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @validates('ldap_pass')
    def _sin_credencial_en_bd(self, clave, valor):
        """La credencial de bind nunca vuelve a la BD (SEC-CFG-03)."""
        if valor:
            raise ValueError('auth_config.ldap_pass es obsoleta: la credencial '
                             'de bind va en LDAP_BIND_PASSWORD.')
        return None

    def to_dict(self):
        return {
            "ldap_host": self.ldap_host,
            "ldap_port": self.ldap_port,
            "ldap_ssl": self.ldap_ssl,
            "ldap_base_dn": self.ldap_base_dn,
            "ldap_user": self.ldap_user,
            "ldap_user_attr": self.ldap_user_attr,
            "ldap_group_admin": self.ldap_group_admin,
            "ldap_group_user": self.ldap_group_user,
            "ldap_role_mappings": self.ldap_role_mappings
        }


# Helper Table for Area Administrators (Multitenant)
# Un usuario con rol 'admin_area' administra las áreas listadas aquí.
area_admins = db.Table('area_admins',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('area_id', db.Integer, db.ForeignKey('areas.id'), primary_key=True)
)
