"""Conector tipo base de datos (FNC-053, SEC-CON-05, ADR-005).

Otorga, revoca y consulta con **sentencias parametrizadas predefinidas** en la
configuración de la plataforma (sin SQL libre). Lo específico de cada
plataforma va en `params` (sin secretos); el código es genérico.

Esquema de `params` (cerrado: una clave desconocida se rechaza):
- `motor` (obligatorio): `mysql` (MySQL y MariaDB, PyMySQL) o `postgresql`
  (psycopg2).
- `base_datos` (obligatorio): nombre de la base (`[A-Za-z0-9_-]`, ≤ 64).
- `otorgar`, `revocar` (obligatorios) y `consultar` (opcional): `{"sentencia":
  "INSERT INTO usuarios (email, rol) VALUES (%s, %s)", "parametros":
  ["correo", "nivel"], "max_filas": 1}`. Las reglas de la sentencia están en
  `bd_sentencias.py`; `parametros` lista, en orden, las marcas (`correo`,
  `nivel`, `plataforma`) que ocupan cada `%s`; `max_filas` (1–10, por defecto
  1; no aplica a `consultar`) es el máximo de filas que puede afectar.

Garantías:
- Host, puerto y base salen de `Destino`/`params` validados; el host de la
  lista blanca se resuelve y se conecta a la **IP validada** (`destino_seguro`).
- TLS siempre obligatorio y verificado (certificado y nombre del host; CA del
  sistema o `CONNECTOR_DB_CA_FILE`). Sin opción para desactivarlo; si el servidor
  MySQL no ofrece TLS la conexión se aborta (`tls_no_valido`).
- Los valores viajan como parámetros del driver. Transacción explícita: se
  confirma solo si la sentencia terminó bien y no afectó más de `max_filas`;
  ante cualquier error, `rollback`. Una consulta nunca confirma.
- `otorgar`/`revocar`: filas afectadas > 0 → éxito; 0 → `sin_cambios`
  (idempotente: use `ON DUPLICATE KEY UPDATE`, `ON CONFLICT DO NOTHING` o un
  `DELETE`/`UPDATE` con `WHERE`). Más de `max_filas` → se deshace
  (`bd_filas_excesivas`, permanente).
- Los `params` guardados se revalidan en cada operación.
- Errores del driver: nunca su mensaje, solo un código (`MySQL 1062`,
  `SQLSTATE 23505`). Red, bloqueos, interbloqueos, tiempo agotado y servidor
  no disponible son transitorios; credencial, certificado y sentencia
  rechazada, permanentes. Si la confirmación falla no se sabe si se aplicó:
  es transitorio y el reintento es seguro porque las operaciones son
  idempotentes.
"""
import re
import socket

from app.modules.connectors.api_http import _con_control, _valores_seguros
from app.modules.connectors.base import Conector
from app.modules.connectors.bd_configuracion import cargar_configuracion_bd
from app.modules.connectors.bd_motores import (MOTORES, ErrorConexion,
                                               ParametrosConexion)
from app.modules.connectors.bd_sentencias import (MARCAS, MAXIMO_PARAMETROS,
                                                  contar_marcadores,
                                                  error_sentencia)
from app.modules.connectors.destino_seguro import (DestinoNoPermitido,
                                                   ErrorResolucion,
                                                   resolver_seguro)
from app.modules.connectors.registry import TipoConector
from app.modules.connectors.tipos import TIPO_BD
from app.modules.provisioning.providers import (ResultadoProveedor,
                                                permanente, transitorio)
from app.modules.provisioning.saneo import (MOTIVO_BD_FILAS,
                                            MOTIVO_CONFIGURACION_INVALIDA,
                                            MOTIVO_CREDENCIAL_NO_ENCONTRADA,
                                            MOTIVO_DESTINO_NO_PERMITIDO,
                                            MOTIVO_RED, MOTIVO_TLS,
                                            MOTIVO_VALOR_NO_VALIDO)
from app.modules.provisioning.tipos import (OPERACION_OTORGAR,
                                            OPERACION_REVOCAR,
                                            RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)

OPERACIONES_OBLIGATORIAS = ('otorgar', 'revocar')
OPERACION_CONSULTAR = 'consultar'
CAMPOS_PARAMS = ('motor', 'base_datos') + OPERACIONES_OBLIGATORIAS + (
    OPERACION_CONSULTAR,)
CAMPOS_OPERACION = ('sentencia', 'parametros', 'max_filas')
_NOMBRE_BASE = re.compile(r'[A-Za-z0-9_-]{1,64}')

MAXIMO_FILAS = (1, 1, 10)  # (por defecto, mínimo, máximo) de `max_filas`
MAXIMO_DIRECCIONES = 3  # IP validadas que se prueban si una no conecta

MENSAJE_OBLIGATORIO = 'Es obligatorio.'
MENSAJE_DESCONOCIDO = 'Campo no admitido.'
MENSAJE_OBJETO = 'Debe ser un objeto.'
MENSAJE_MOTOR = f'Usa uno de: {", ".join(sorted(MOTORES))}.'
MENSAJE_BASE = 'Usa letras, dígitos, "_" y "-" (máximo 64).'
MENSAJE_PARAMETROS = (f'Debe ser una lista de hasta {MAXIMO_PARAMETROS} marcas '
                      f'({", ".join(MARCAS)}), una por cada %s de la sentencia.')
MENSAJE_MAX_FILAS = (f'Debe ser un entero entre {MAXIMO_FILAS[1]} y '
                     f'{MAXIMO_FILAS[2]}.')
MENSAJE_MAX_FILAS_CONSULTA = 'No aplica a consultar.'


def _es_entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


# --------------------------------------------------------------------------- #
# Esquema de params
# --------------------------------------------------------------------------- #

def _errores_operacion(nombre, spec, errores):
    if not isinstance(spec, dict):
        errores[nombre] = MENSAJE_OBJETO
        return
    for clave in spec:
        if clave not in CAMPOS_OPERACION:
            errores[f'{nombre}.{clave}'] = MENSAJE_DESCONOCIDO
    sentencia = spec.get('sentencia')
    motivo = error_sentencia(sentencia, nombre)
    if motivo is not None:
        errores[f'{nombre}.sentencia'] = motivo
    parametros = spec.get('parametros', [])
    if (not isinstance(parametros, list) or len(parametros) > MAXIMO_PARAMETROS
            or any(p not in MARCAS for p in parametros)
            or (motivo is None
                and contar_marcadores(sentencia) != len(parametros))):
        errores[f'{nombre}.parametros'] = MENSAJE_PARAMETROS
    if 'max_filas' in spec:
        if nombre == OPERACION_CONSULTAR:
            errores[f'{nombre}.max_filas'] = MENSAJE_MAX_FILAS_CONSULTA
        elif (not _es_entero(spec['max_filas'])
              or not MAXIMO_FILAS[1] <= spec['max_filas'] <= MAXIMO_FILAS[2]):
            errores[f'{nombre}.max_filas'] = MENSAJE_MAX_FILAS


def validar_params(params):
    """`{campo: mensaje}` del esquema; vacío si `params` es válido."""
    errores = {}
    if not isinstance(params, dict):
        return {'params': MENSAJE_OBJETO}
    for clave in params:
        if clave not in CAMPOS_PARAMS:
            errores[str(clave)] = MENSAJE_DESCONOCIDO
    if params.get('motor') not in MOTORES:
        errores['motor'] = MENSAJE_MOTOR
    base = params.get('base_datos')
    if not isinstance(base, str) or not _NOMBRE_BASE.fullmatch(base):
        errores['base_datos'] = MENSAJE_BASE
    for nombre in OPERACIONES_OBLIGATORIAS:
        if params.get(nombre) is None:
            errores[nombre] = MENSAJE_OBLIGATORIO
        else:
            _errores_operacion(nombre, params[nombre], errores)
    if OPERACION_CONSULTAR in params:
        _errores_operacion(OPERACION_CONSULTAR, params[OPERACION_CONSULTAR],
                           errores)
    return errores


# --------------------------------------------------------------------------- #
# Conector
# --------------------------------------------------------------------------- #

class ConectorBd(Conector):
    """`getaddrinfo`, `conectar` y `archivo_ca` se inyectan en las pruebas;
    sin ellos: DNS del sistema, el driver real y `CONNECTOR_DB_CA_FILE`.
    `conectar(motor, parametros)` devuelve una conexión DB-API."""

    def __init__(self, destino, credencial, getaddrinfo=None, conectar=None,
                 archivo_ca=None, tiempo=None):
        super().__init__(destino, credencial)
        self._getaddrinfo = getaddrinfo or socket.getaddrinfo
        self._conectar = conectar or (lambda motor, p: motor.conectar(p))
        self._archivo_ca = archivo_ca
        self._tiempo = tiempo

    # -- preparación ------------------------------------------------------ #

    def _credencial_valida(self):
        usuario = self.credencial.usuario or ''
        secreto = self.credencial.secreto or ''
        return bool(usuario and secreto and not _con_control(usuario)
                    and not _con_control(secreto))

    @staticmethod
    def _valores(solicitud):
        return {'correo': solicitud.cuenta, 'nivel': solicitud.nivel,
                'plataforma': str(solicitud.plataforma_id)}

    def _abrir(self, motor, params, ips, configuracion):
        """Conexión abierta o un `ResultadoProveedor` de error."""
        for ip in ips[:MAXIMO_DIRECCIONES]:
            parametros = ParametrosConexion(
                host=self.destino.host, ip=ip, puerto=self.destino.puerto,
                base_datos=params['base_datos'],
                usuario=self.credencial.usuario,
                secreto=self.credencial.secreto,
                tiempo=self._tiempo or configuracion.tiempo,
                archivo_ca=self._archivo_ca or configuracion.archivo_ca
                or None)
            try:
                return self._conectar(motor, parametros)
            except ErrorConexion:
                continue  # la red falló antes de enviar nada: otra IP
            except Exception as exc:  # noqa: BLE001 - se clasifica o se relanza
                return self._error(motor, exc)
        return transitorio(MOTIVO_RED)

    @staticmethod
    def _error(motor, exc):
        clase = motor.clasificar(exc)
        if clase is None:
            raise exc
        fabrica = transitorio if clase.transitorio else permanente
        return fabrica(clase.motivo, clase.detalle)

    # -- ejecución -------------------------------------------------------- #

    def _correr(self, conexion, spec, valores, consulta):
        """`True`/`False` (presente), `int` (filas) o `ResultadoProveedor`."""
        cursor = conexion.cursor()
        try:
            cursor.execute(spec['sentencia'],
                           tuple(valores[m] for m in spec['parametros']))
            if consulta:
                fila = cursor.fetchone()
                conexion.rollback()  # una consulta nunca confirma
                return fila is not None
            filas = cursor.rowcount
            if filas > spec.get('max_filas', MAXIMO_FILAS[0]):
                conexion.rollback()
                return permanente(MOTIVO_BD_FILAS, f'{filas} filas')
            conexion.commit()
            return filas
        finally:
            cursor.close()

    def _operar(self, nombre, solicitud):
        """Resultado del proveedor para `nombre` (con `presente` al consultar)."""
        params = dict(self.destino.params)
        if validar_params(params):
            return permanente(MOTIVO_CONFIGURACION_INVALIDA)
        if (not _valores_seguros(solicitud)
                or any(_con_control(v) for v in self._valores(solicitud).values())):
            return permanente(MOTIVO_VALOR_NO_VALIDO)
        if not self._credencial_valida():
            return permanente(MOTIVO_CREDENCIAL_NO_ENCONTRADA)
        try:
            configuracion = cargar_configuracion_bd()
        except Exception:  # noqa: BLE001 - valor inválido tras el arranque
            return permanente(MOTIVO_CONFIGURACION_INVALIDA)
        try:
            ips = resolver_seguro(self.destino.host, self.destino.puerto,
                                  self._getaddrinfo)
        except DestinoNoPermitido:
            return permanente(MOTIVO_DESTINO_NO_PERMITIDO)
        except ErrorResolucion:
            return transitorio(MOTIVO_RED)
        motor = MOTORES[params['motor']]
        conexion = self._abrir(motor, params, ips, configuracion)
        if isinstance(conexion, ResultadoProveedor):
            return conexion
        consulta = nombre == OPERACION_CONSULTAR
        try:
            salida = self._correr(conexion, params[nombre],
                                  self._valores(solicitud), consulta)
        except Exception as exc:  # noqa: BLE001 - se clasifica o se relanza
            self._deshacer(conexion)
            return self._error(motor, exc)
        finally:
            self._cerrar(conexion)
        if isinstance(salida, ResultadoProveedor):
            return salida
        if consulta:
            return ResultadoProveedor(RESULTADO_EXITOSO, presente=salida)
        if salida == 0:
            return ResultadoProveedor(RESULTADO_SIN_CAMBIOS)
        return ResultadoProveedor(RESULTADO_EXITOSO)

    @staticmethod
    def _deshacer(conexion):
        try:
            conexion.rollback()
        except Exception:  # noqa: BLE001 - la conexión ya estaba rota
            pass

    @staticmethod
    def _cerrar(conexion):
        try:
            conexion.close()
        except Exception:  # noqa: BLE001
            pass

    def otorgar(self, solicitud):
        return self._operar(OPERACION_OTORGAR, solicitud)

    def revocar(self, solicitud):
        return self._operar(OPERACION_REVOCAR, solicitud)

    def consultar(self, solicitud):
        if OPERACION_CONSULTAR not in self.destino.params:
            return super().consultar(solicitud)
        return self._operar(OPERACION_CONSULTAR, solicitud)


TIPO = TipoConector(TIPO_BD, ConectorBd, validar_params)
