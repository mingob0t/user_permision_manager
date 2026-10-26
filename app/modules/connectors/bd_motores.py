"""Motores de base de datos del conector `bd` (FNC-053, SEC-CON-05).

Cada motor sabe (1) abrir la conexión **a la IP ya validada**, con TLS
obligatorio y verificado contra el **nombre del host**, transacción explícita
(sin *autocommit*) y tiempos de conexión y de consulta, y (2) clasificar los
errores de su driver en transitorios o permanentes, sin devolver nunca el
mensaje del driver (puede traer datos del servidor): solo un código numérico.

- `mysql` (MySQL y MariaDB): PyMySQL. Se abre el socket a la IP validada y se
  entrega al driver (`connect(sock)`); el driver verifica el certificado contra
  `host` (contexto con `CERT_REQUIRED` y `check_hostname`, TLS ≥ 1.2).
- `postgresql`: psycopg2 (libpq) con `hostaddr` (IP validada) y `host` (nombre
  para el certificado), `sslmode=verify-full`, `gssencmode=disable` (la
  encriptación GSS no verifica el certificado) y `statement_timeout`.
Ninguno desactiva la verificación.
"""
import socket
import ssl
from dataclasses import dataclass, field

import psycopg2
import pymysql

from app.modules.connectors.http_transporte import crear_contexto
from app.modules.provisioning.saneo import (MOTIVO_BD_AUTENTICACION,
                                            MOTIVO_BD_RECHAZADA,
                                            MOTIVO_BD_TRANSITORIA, MOTIVO_RED,
                                            MOTIVO_TLS)

MOTOR_MYSQL = 'mysql'
MOTOR_POSTGRESQL = 'postgresql'
MILISEGUNDOS = 1000
CODIFICACION_MYSQL = 'utf8mb4'
SSLMODE_PG = 'verify-full'
CA_DEL_SISTEMA_PG = 'system'

# MySQL / MariaDB: códigos de error del servidor y del cliente.
MYSQL_AUTENTICACION = frozenset({1044, 1045})
MYSQL_TLS_CODIGO = 2026
MYSQL_TLS = frozenset({MYSQL_TLS_CODIGO})
MYSQL_TRANSITORIOS = frozenset({1040, 1053, 1203, 1205, 1213, 1317, 2002,
                                2003, 2006, 2013, 3024})
# PostgreSQL: clase (2 primeros caracteres) o código SQLSTATE completo.
PG_CLASES_TRANSITORIAS = frozenset({'08', '40', '53', '57', '58'})
PG_CODIGOS_TRANSITORIOS = frozenset({'55P03'})
PG_CLASE_AUTENTICACION = '28'


class ErrorConexion(OSError):
    """No se pudo abrir la conexión de red (aún no se envió nada): único caso
    en que el conector prueba otra IP validada."""


@dataclass(frozen=True)
class Clasificacion:
    transitorio: bool
    motivo: str
    detalle: str | None = None


@dataclass(frozen=True)
class ParametrosConexion:
    host: str
    ip: str
    puerto: int
    base_datos: str
    usuario: str
    secreto: str = field(repr=False)
    tiempo: int = 10
    archivo_ca: str | None = None


def _cadena_de_causas(exc):
    visto = []
    while exc is not None and exc not in visto and len(visto) < 8:
        visto.append(exc)
        exc = exc.__cause__ or exc.__context__
    return visto


def _falla_tls(exc):
    """Una falla de certificado o de saludo TLS en la cadena de causas."""
    return any(isinstance(e, ssl.SSLError)
               and not isinstance(e, (ssl.SSLEOFError, ssl.SSLZeroReturnError))
               for e in _cadena_de_causas(exc))


class Motor:
    nombre = ''

    def conectar(self, parametros):
        raise NotImplementedError

    def clasificar(self, exc):
        """`Clasificacion` de un error del driver o `None` si no es suyo."""
        raise NotImplementedError


class MotorMysql(Motor):
    nombre = MOTOR_MYSQL

    def conectar(self, p):
        try:
            contexto = crear_contexto(p.archivo_ca)
        except (OSError, ssl.SSLError):
            raise pymysql.err.OperationalError(MYSQL_TLS_CODIGO, '') from None
        try:
            enchufe = socket.create_connection((p.ip, p.puerto), p.tiempo)
        except OSError:
            raise ErrorConexion() from None
        enchufe.settimeout(p.tiempo)
        conexion = pymysql.connections.Connection(
            host=p.host, port=p.puerto, user=p.usuario,
            password=p.secreto.encode('utf-8'), database=p.base_datos,
            charset=CODIFICACION_MYSQL, ssl=contexto, autocommit=False,
            connect_timeout=p.tiempo, read_timeout=p.tiempo,
            write_timeout=p.tiempo, defer_connect=True)
        conexion.connect(enchufe)
        return conexion

    def clasificar(self, exc):
        if _falla_tls(exc):
            return Clasificacion(False, MOTIVO_TLS)
        if not isinstance(exc, pymysql.err.MySQLError):
            return None
        codigo = exc.args[0] if exc.args and isinstance(exc.args[0], int) else None
        detalle = f'MySQL {codigo}' if codigo is not None else None
        if codigo in MYSQL_TLS:
            return Clasificacion(False, MOTIVO_TLS, detalle)
        if codigo in MYSQL_AUTENTICACION:
            return Clasificacion(False, MOTIVO_BD_AUTENTICACION, detalle)
        if codigo in MYSQL_TRANSITORIOS:
            return Clasificacion(True, MOTIVO_BD_TRANSITORIA, detalle)
        if isinstance(exc, (pymysql.err.OperationalError,
                            pymysql.err.InterfaceError,
                            pymysql.err.InternalError)):
            return Clasificacion(True, MOTIVO_BD_TRANSITORIA, detalle)
        return Clasificacion(False, MOTIVO_BD_RECHAZADA, detalle)


class MotorPostgresql(Motor):
    nombre = MOTOR_POSTGRESQL

    def conectar(self, p):
        try:
            return psycopg2.connect(
                host=p.host, hostaddr=p.ip, port=p.puerto,
                dbname=p.base_datos, user=p.usuario, password=p.secreto,
                sslmode=SSLMODE_PG, gssencmode='disable',
                sslrootcert=p.archivo_ca or CA_DEL_SISTEMA_PG,
                connect_timeout=p.tiempo,
                options=f'-c statement_timeout={p.tiempo * MILISEGUNDOS}')
        except psycopg2.OperationalError as exc:
            if exc.pgcode is not None:
                raise
            texto = str(exc).lower()
            if 'ssl' in texto or 'certificate' in texto:
                raise psycopg2.OperationalError('tls') from None
            if 'authentication' in texto or 'password' in texto:
                raise
            raise ErrorConexion() from None

    def clasificar(self, exc):
        if not isinstance(exc, psycopg2.Error):
            return None
        estado = getattr(exc, 'pgcode', None)
        if estado is None:
            texto = str(exc).lower()
            if texto == 'tls' or 'ssl' in texto or 'certificate' in texto:
                return Clasificacion(False, MOTIVO_TLS)
            if 'authentication' in texto or 'password' in texto:
                return Clasificacion(False, MOTIVO_BD_AUTENTICACION)
            if isinstance(exc, (psycopg2.OperationalError,
                                psycopg2.InterfaceError)):
                return Clasificacion(True, MOTIVO_RED)
            return Clasificacion(False, MOTIVO_BD_RECHAZADA)
        detalle = f'SQLSTATE {estado}'
        if estado[:2] == PG_CLASE_AUTENTICACION:
            return Clasificacion(False, MOTIVO_BD_AUTENTICACION, detalle)
        if (estado[:2] in PG_CLASES_TRANSITORIAS
                or estado in PG_CODIGOS_TRANSITORIOS):
            return Clasificacion(True, MOTIVO_BD_TRANSITORIA, detalle)
        return Clasificacion(False, MOTIVO_BD_RECHAZADA, detalle)


MOTORES = {MOTOR_MYSQL: MotorMysql(), MOTOR_POSTGRESQL: MotorPostgresql()}
