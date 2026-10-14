"""Servidor SMTP simulado para las pruebas de notificaciones (FNC-023).

Sustituye a `smtplib.SMTP` y `smtplib.SMTP_SSL` sin red. Guarda los mensajes
enviados, el servidor al que se conectó y el usuario con que inició sesión.

Uso:
    correo = instalar_smtp(monkeypatch)
    ...
    assert correo.enviados[0]['Subject'] == 'Asunto'
"""

import smtplib


class SmtpFalso:
    """Registro de lo que el servicio pidió al servidor de correo."""

    def __init__(self):
        self.enviados = []       # mensajes (email.message.Message), en orden
        self.conexiones = []     # (clase, servidor, puerto)
        self.logins = []         # (usuario, contraseña)
        self.error = None        # excepción a lanzar al enviar, si se define

    def clase(self, nombre):
        """Clase que reemplaza a `smtplib.<nombre>`, ligada a este registro."""
        registro = self

        class ConexionFalsa:
            def __init__(self, servidor, puerto, timeout=None):
                registro.conexiones.append((nombre, servidor, puerto))

            def starttls(self):
                return None

            def set_debuglevel(self, nivel):
                return None

            def login(self, usuario, contrasena):
                registro.logins.append((usuario, contrasena))

            def send_message(self, mensaje):
                if registro.error:
                    raise registro.error
                registro.enviados.append(mensaje)

            def quit(self):
                return None

        return ConexionFalsa


def instalar_smtp(monkeypatch):
    """Simula `smtplib` (sobrescribe el bloqueo de `conftest.py`)."""
    correo = SmtpFalso()
    monkeypatch.setattr(smtplib, 'SMTP', correo.clase('SMTP'))
    monkeypatch.setattr(smtplib, 'SMTP_SSL', correo.clase('SMTP_SSL'))
    return correo
