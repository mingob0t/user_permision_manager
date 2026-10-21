"""Descifrado del lado del cliente del protocolo Bitwarden (FNC-068, ADR-005).

Vaultwarden guarda la bóveda cifrada de extremo a extremo: el servidor nunca
ve los valores. Para leer un ítem, la app hace lo mismo que el cliente
oficial, solo con `cryptography` (ya era dependencia):

1. Clave maestra = KDF(contraseña maestra, correo): PBKDF2-SHA256 (`kdf=0`) o
   Argon2id (`kdf=1`), con los parámetros que publica el servidor dentro de
   `LIMITES_KDF` (un servidor hostil no puede pedir un KDF débil ni uno que
   agote la memoria).
2. Clave estirada = HKDF-Expand(clave maestra, `enc`/`mac`).
3. Clave de usuario = descifrar `Key` (tipo 2) con la clave estirada.
4. Llave privada RSA = descifrar `PrivateKey` (tipo 2) con la clave de usuario.
5. Clave de la organización = descifrar su `key` (tipo 4 o 3, RSA-OAEP).
6. Campos del ítem = tipo 2 con la clave del ítem o la de la organización.

Solo se aceptan los tipos autenticados (2: AES-256-CBC + HMAC-SHA256, y 3/4:
RSA-OAEP); el tipo 0 (sin MAC) y los RSA con HMAC (5/6, obsoletos) se
rechazan. El MAC se compara en tiempo constante antes de descifrar.

Ninguna clave aparece en `repr` ni en el texto de los errores.
"""
import base64
import binascii
import hashlib
import hmac

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.asymmetric import padding as padding_rsa
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand
from cryptography.hazmat.primitives.serialization import load_der_private_key

KDF_PBKDF2 = 0
KDF_ARGON2ID = 1

# (mínimo, máximo) aceptados de cada parámetro del KDF. Mínimos: los de
# Bitwarden; máximos: tope para que un servidor no agote CPU o memoria.
LIMITES_KDF = {
    'pbkdf2_iteraciones': (100_000, 2_000_000),
    'argon2_iteraciones': (2, 10),
    'argon2_memoria_mib': (15, 1024),
    'argon2_paralelismo': (1, 16),
}

TIPO_AES_HMAC = 2
TIPO_RSA_OAEP_SHA256 = 3
TIPO_RSA_OAEP_SHA1 = 4

LARGO_CLAVE = 32           # AES-256 y HMAC-SHA256
LARGO_CLAVE_SIMETRICA = 64  # enc (32) + mac (32)
LARGO_IV = 16
LARGO_MAC = 32
KIB_POR_MIB = 1024
INFO_ENC = b'enc'
INFO_MAC = b'mac'
CODIFICACION = 'utf-8'


class ErrorDeCifrado(Exception):
    """Dato cifrado inválido, MAC incorrecto o clave equivocada (sin detalle)."""


class ClaveSimetrica:
    """Par AES/HMAC de 32 + 32 bytes. Nunca se representa su contenido."""

    __slots__ = ('_enc', '_mac')

    def __init__(self, enc, mac):
        if len(enc) != LARGO_CLAVE or len(mac) != LARGO_CLAVE:
            raise ErrorDeCifrado('Largo de clave inválido.')
        self._enc = bytes(enc)
        self._mac = bytes(mac)

    @classmethod
    def desde_bytes(cls, datos):
        if len(datos) != LARGO_CLAVE_SIMETRICA:
            raise ErrorDeCifrado('Largo de clave inválido.')
        return cls(datos[:LARGO_CLAVE], datos[LARGO_CLAVE:])

    def __repr__(self):
        return '<ClaveSimetrica oculta>'

    __str__ = __repr__


def _en_rango(nombre, valor):
    minimo, maximo = LIMITES_KDF[nombre]
    if not isinstance(valor, int) or isinstance(valor, bool) \
            or not minimo <= valor <= maximo:
        raise ErrorDeCifrado('Parámetros del KDF fuera de los límites.')
    return valor


def derivar_clave_maestra(contrasena, correo, kdf, iteraciones,
                          memoria_mib=None, paralelismo=None):
    """Clave maestra de 32 bytes (PBKDF2-SHA256 o Argon2id)."""
    secreto = contrasena.encode(CODIFICACION)
    sal = correo.strip().lower().encode(CODIFICACION)
    if kdf == KDF_PBKDF2:
        vueltas = _en_rango('pbkdf2_iteraciones', iteraciones)
        return hashlib.pbkdf2_hmac('sha256', secreto, sal, vueltas, LARGO_CLAVE)
    if kdf == KDF_ARGON2ID:
        try:
            return Argon2id(
                salt=hashlib.sha256(sal).digest(), length=LARGO_CLAVE,
                iterations=_en_rango('argon2_iteraciones', iteraciones),
                lanes=_en_rango('argon2_paralelismo', paralelismo),
                memory_cost=_en_rango('argon2_memoria_mib', memoria_mib)
                * KIB_POR_MIB).derive(secreto)
        except UnsupportedAlgorithm:
            # OpenSSL sin Argon2 (B1): permanente, como un KDF no soportado.
            raise ErrorDeCifrado('Argon2id no disponible.') from None
    raise ErrorDeCifrado('KDF no soportado.')


def estirar(clave_maestra):
    """Clave estirada (HKDF-Expand con `enc` y `mac`) de la clave maestra."""
    def expandir(info):
        return HKDFExpand(algorithm=hashes.SHA256(), length=LARGO_CLAVE,
                          info=info).derive(clave_maestra)
    return ClaveSimetrica(expandir(INFO_ENC), expandir(INFO_MAC))


def _b64(texto):
    try:
        return base64.b64decode(texto, validate=True)
    except (binascii.Error, ValueError):
        raise ErrorDeCifrado('Base64 inválido.') from None


def _partir(cifrado):
    if not isinstance(cifrado, str) or '.' not in cifrado:
        raise ErrorDeCifrado('Formato cifrado inválido.')
    tipo, _, resto = cifrado.partition('.')
    try:
        return int(tipo), resto.split('|')
    except ValueError:
        raise ErrorDeCifrado('Formato cifrado inválido.') from None


def descifrar_simetrico(cifrado, clave):
    """Bytes de un valor tipo 2 (`2.iv|datos|mac`), tras validar el MAC."""
    tipo, partes = _partir(cifrado)
    if tipo != TIPO_AES_HMAC or len(partes) != 3:
        raise ErrorDeCifrado('Tipo de cifrado no admitido.')
    iv, datos, mac = (_b64(p) for p in partes)
    if len(iv) != LARGO_IV or len(mac) != LARGO_MAC or not datos \
            or len(datos) % LARGO_IV:
        raise ErrorDeCifrado('Formato cifrado inválido.')
    esperado = hmac.new(clave._mac, iv + datos, hashlib.sha256).digest()
    if not hmac.compare_digest(esperado, mac):
        raise ErrorDeCifrado('MAC incorrecto.')
    descifrador = Cipher(algorithms.AES(clave._enc), modes.CBC(iv)).decryptor()
    relleno = descifrador.update(datos) + descifrador.finalize()
    quitar = padding.PKCS7(algorithms.AES.block_size).unpadder()
    try:
        return quitar.update(relleno) + quitar.finalize()
    except ValueError:
        raise ErrorDeCifrado('Relleno inválido.') from None


def descifrar_texto(cifrado, clave):
    try:
        return descifrar_simetrico(cifrado, clave).decode(CODIFICACION)
    except UnicodeDecodeError:
        raise ErrorDeCifrado('Texto inválido.') from None


def cargar_llave_privada(der):
    """Llave privada RSA (PKCS#8 DER) de la cuenta."""
    try:
        llave = load_der_private_key(der, password=None)
    except (ValueError, TypeError, UnsupportedAlgorithm):
        raise ErrorDeCifrado('Llave privada inválida.') from None
    if not isinstance(llave, rsa.RSAPrivateKey):
        raise ErrorDeCifrado('Llave privada inválida.')
    return llave


def descifrar_rsa(cifrado, llave_privada):
    """Bytes de un valor tipo 4 (RSA-OAEP SHA-1) o 3 (RSA-OAEP SHA-256)."""
    tipo, partes = _partir(cifrado)
    algoritmos = {TIPO_RSA_OAEP_SHA1: hashes.SHA1,
                  TIPO_RSA_OAEP_SHA256: hashes.SHA256}
    if tipo not in algoritmos or len(partes) != 1:
        raise ErrorDeCifrado('Tipo de cifrado no admitido.')
    algoritmo = algoritmos[tipo]()
    try:
        return llave_privada.decrypt(_b64(partes[0]), padding_rsa.OAEP(
            mgf=padding_rsa.MGF1(algorithm=algoritmo), algorithm=algoritmo,
            label=None))
    except ValueError:
        raise ErrorDeCifrado('No se pudo descifrar.') from None
