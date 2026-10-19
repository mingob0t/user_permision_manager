from app import db
from app.modules.platforms.estado import accesos_vigentes, tiene_conector
from app.modules.platforms.validacion import url_segura
from app.modules.platforms.tipos import (GRUPOS_SIN_VERIFICAR, LARGO_DN,
                                         LARGO_ESTADO_GRUPOS, LARGO_TIPO,
                                         TIPO_LDAP)

class Area(db.Model):
    __tablename__ = 'areas'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), default='box')
    color = db.Column(db.String(100), default='#6366f1')
    status = db.Column(db.String(20), default='Activo')

    @property
    def color_rgb(self):
        """Converts hex color to RGB comma-separated string for CSS variables."""
        hex_color = self.color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}"
        except:
            return "99, 102, 241" # Default Indigo-500

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'status': self.status
        }

class Platform(db.Model):
    __tablename__ = 'platforms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=False)
    direct_link = db.Column(db.String(255))
    icon = db.Column(db.String(50), default='box')
    logo_url = db.Column(db.String(255), nullable=True)
    bg_color = db.Column(db.String(20), default='#6366f1')
    text_color = db.Column(db.String(20), default='#ffffff')
    status = db.Column(db.String(20), default='Activo')
    visits = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.now())
    # Integración y grupos por nivel (FNC-046, migración 0005). Las plataformas
    # anteriores quedan `ldap` sin grupos hasta que el superadmin los complete.
    integration_type = db.Column(db.String(LARGO_TIPO), nullable=False,
                                 default=TIPO_LDAP, server_default=TIPO_LDAP)
    ldap_group_user_dn = db.Column(db.String(LARGO_DN), nullable=True)
    ldap_group_admin_dn = db.Column(db.String(LARGO_DN), nullable=True)
    groups_status = db.Column(db.String(LARGO_ESTADO_GRUPOS), nullable=False,
                              default=GRUPOS_SIN_VERIFICAR,
                              server_default=GRUPOS_SIN_VERIFICAR)

    # Relationships
    area = db.relationship('Area', backref=db.backref('platforms', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'area_id': self.area_id,
            'icon': self.icon,
            'direct_link': url_segura(self.direct_link),
            'logo_url': url_segura(self.logo_url),
            'bg_color': self.bg_color,
            'text_color': self.text_color,
            'status': self.status,
            'area_name': self.area.name if self.area else 'Sin Área',
            'area_color': self.area.color if self.area else '#6366f1',
            'area_icon': self.area.icon if self.area else 'box',
            'integration_type': self.integration_type,
            'ldap_group_user_dn': self.ldap_group_user_dn,
            'ldap_group_admin_dn': self.ldap_group_admin_dn,
            'groups_status': self.groups_status,
            'has_connector': tiene_conector(self),
            'active_grants': accesos_vigentes(self),
            # `user_ids` ya no se expone (contrato plataformas-integracion v1).
        }
