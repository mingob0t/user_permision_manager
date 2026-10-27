from app import db
from datetime import datetime

from app.modules.settings import valores_por_defecto as vpd

class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    portal_name = db.Column(db.String(100), default=vpd.PORTAL_NAME_POR_DEFECTO)
    portal_identity_type = db.Column(db.String(10), default=vpd.PORTAL_IDENTITY_TYPE_POR_DEFECTO) # 'icon' or 'image'
    portal_icon = db.Column(db.Text, nullable=True) # Storing SVG code or Image DataURL/Path
    bg_color = db.Column(db.String(20), default=vpd.BG_COLOR_POR_DEFECTO)
    text_color = db.Column(db.String(20), default=vpd.TEXT_COLOR_POR_DEFECTO)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @classmethod
    def por_defecto(cls):
        """Instancia sin guardar con los valores por defecto ya asignados
        (los `default=` de columna solo se aplican al insertar)."""
        return cls(portal_name=vpd.PORTAL_NAME_POR_DEFECTO,
                   portal_identity_type=vpd.PORTAL_IDENTITY_TYPE_POR_DEFECTO,
                   bg_color=vpd.BG_COLOR_POR_DEFECTO,
                   text_color=vpd.TEXT_COLOR_POR_DEFECTO)

    def to_dict(self):
        return {
            "portal_name": self.portal_name,
            "portal_identity_type": self.portal_identity_type,
            "portal_icon": self.portal_icon,
            "bg_color": self.bg_color,
            "text_color": self.text_color
        }
