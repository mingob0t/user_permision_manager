"""Vaultwarden simulado en memoria, sin red (FNC-068).

Arma una bóveda cifrada de verdad (mismo formato que Bitwarden: claves
derivadas con el KDF, `Key` y `PrivateKey` tipo 2, clave de organización
tipo 4 y campos tipo 2), de modo que el cliente real la descifre de extremo
a extremo. Se inyecta como `transporte` del `ClienteVaultwarden`.

Todos los valores son ficticios de prueba (no son secretos).
"""
import base64
import hashlib
import hmac
import json
import os
from functools import lru_cache
from urllib.parse import parse_qs

from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding as padding_rsa
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.modules.secretos import cifrado
from app.modules.secretos.vaultwarden import (RUTA_PRELOGIN, RUTA_SYNC,
                                              RUTA_TOKEN, Respuesta)

URL = 'https://vault.pruebas.invalid'
CLIENT_ID = 'user.11111111-2222-4333-8444-555555555555'
CLIENT_SECRET = 'secreto-de-api-ficticio'
CORREO = 'Servicio.Portal@Pruebas.Invalid'
CONTRASENA_MAESTRA = 'maestra-ficticia-de-prueba'
ORGANIZACION = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'
COLECCION = '99999999-8888-4777-8666-555555555555'
OTRA_COLECCION = '12345678-1234-4123-8123-123456789012'
TOKEN = 'token-de-acceso-ficticio'
PBKDF2_PRUEBA = 100_000

ENTORNO = {
    'VAULTWARDEN_URL': URL,
    'VAULTWARDEN_CLIENT_ID': CLIENT_ID,
    'VAULTWARDEN_CLIENT_SECRET': CLIENT_SECRET,
    'VAULTWARDEN_EMAIL': CORREO,
    'VAULTWARDEN_MASTER_PASSWORD': CONTRASENA_MAESTRA,
    'VAULTWARDEN_COLLECTION_ID': COLECCION,
}


@lru_cache(maxsize=1)
def _llave_rsa():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def cifrar(datos, clave):
    """Valor tipo 2 (`2.iv|datos|mac`) con una `ClaveSimetrica`."""
    if isinstance(datos, str):
        datos = datos.encode()
    iv = os.urandom(cifrado.LARGO_IV)
    relleno = padding.PKCS7(128).padder()
    plano = relleno.update(datos) + relleno.finalize()
    cifrador = Cipher(algorithms.AES(clave._enc), modes.CBC(iv)).encryptor()
    texto = cifrador.update(plano) + cifrador.finalize()
    mac = hmac.new(clave._mac, iv + texto, hashlib.sha256).digest()
    b = base64.b64encode
    return f'2.{b(iv).decode()}|{b(texto).decode()}|{b(mac).decode()}'


def cifrar_rsa(datos, publica):
    texto = publica.encrypt(datos, padding_rsa.OAEP(
        mgf=padding_rsa.MGF1(algorithm=hashes.SHA1()),
        algorithm=hashes.SHA1(), label=None))
    return '4.' + base64.b64encode(texto).decode()


def clave_aleatoria():
    return cifrado.ClaveSimetrica.desde_bytes(os.urandom(64))


class VaultwardenFalso:
    """Servidor simulado; `peticiones` registra (método, ruta)."""

    def __init__(self, kdf=cifrado.KDF_PBKDF2, iteraciones=PBKDF2_PRUEBA,
                 memoria=None, paralelismo=None, kdf_en_token=True,
                 contrasena_maestra=CONTRASENA_MAESTRA):
        self.kdf = (kdf, iteraciones, memoria, paralelismo)
        self.kdf_en_token = kdf_en_token
        self.peticiones = []
        self.estado_forzado = {}   # ruta → estado HTTP
        self.excepcion = None      # se lanza en la siguiente petición
        self.token_vigente = TOKEN
        self.expira = 3600
        maestra = cifrado.derivar_clave_maestra(
            contrasena_maestra, CORREO, kdf, iteraciones, memoria, paralelismo)
        self.clave_usuario = clave_aleatoria()
        self.key = cifrar(self.clave_usuario._enc + self.clave_usuario._mac,
                          cifrado.estirar(maestra))
        der = _llave_rsa().private_bytes(
            serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption())
        self.private_key = cifrar(der, self.clave_usuario)
        self.clave_org = clave_aleatoria()
        self.org_key = cifrar_rsa(self.clave_org._enc + self.clave_org._mac,
                                  _llave_rsa().public_key())
        self.ciphers = []

    # ------------------------------------------------------------ bóveda

    def item(self, nombre, contrasena, usuario=None, coleccion=COLECCION,
             organizacion=ORGANIZACION, tipo=1, borrado=False,
             clave_propia=False):
        clave = self.clave_org
        extra = {}
        if clave_propia:
            clave = clave_aleatoria()
            extra['key'] = cifrar(clave._enc + clave._mac, self.clave_org)
        self.ciphers.append({
            'id': f'item-{len(self.ciphers)}', 'type': tipo,
            'organizationId': organizacion, 'collectionIds': [coleccion],
            'deletedDate': '2026-10-01T00:00:00Z' if borrado else None,
            'name': cifrar(nombre, clave),
            'login': {'username': cifrar(usuario, clave) if usuario else None,
                      'password': cifrar(contrasena, clave)},
            **extra})
        return self.ciphers[-1]

    def cambiar_contrasena(self, indice, nueva):
        item = self.ciphers[indice]
        clave = self.clave_org
        if item.get('key'):
            clave = cifrado.ClaveSimetrica.desde_bytes(
                cifrado.descifrar_simetrico(item['key'], self.clave_org))
        item['login']['password'] = cifrar(nueva, clave)

    # ------------------------------------------------------------ HTTP

    def _json(self, datos, estado=200):
        return Respuesta(estado, json.dumps(datos).encode())

    def __call__(self, metodo, url, cabeceras, cuerpo=None):
        assert url.startswith(URL), url
        ruta = url[len(URL):]
        self.peticiones.append((metodo, ruta))
        if self.excepcion is not None:
            excepcion, self.excepcion = self.excepcion, None
            raise excepcion
        if ruta in self.estado_forzado:
            return Respuesta(self.estado_forzado[ruta], b'{}')
        if metodo == 'POST' and ruta == RUTA_TOKEN:
            return self._token(cuerpo)
        if metodo == 'POST' and ruta == RUTA_PRELOGIN:
            kdf, iteraciones, memoria, paralelismo = self.kdf
            return self._json({'kdf': kdf, 'kdfIterations': iteraciones,
                               'kdfMemory': memoria,
                               'kdfParallelism': paralelismo})
        if metodo == 'GET' and ruta == RUTA_SYNC:
            if cabeceras.get('Authorization') != f'Bearer {self.token_vigente}':
                return Respuesta(401, b'')
            return self._json(self._sync())
        return Respuesta(404, b'')

    def _token(self, cuerpo):
        datos = {k: v[0] for k, v in parse_qs(cuerpo.decode()).items()}
        if (datos.get('grant_type') != 'client_credentials'
                or datos.get('client_id') != CLIENT_ID
                or datos.get('client_secret') != CLIENT_SECRET
                or not datos.get('deviceIdentifier')):
            return self._json({'error': 'invalid_client'}, 400)
        respuesta = {'access_token': self.token_vigente,
                     'expires_in': self.expira, 'token_type': 'Bearer',
                     'Key': self.key, 'PrivateKey': self.private_key}
        if self.kdf_en_token:
            kdf, iteraciones, memoria, paralelismo = self.kdf
            respuesta.update({'Kdf': kdf, 'KdfIterations': iteraciones,
                              'KdfMemory': memoria,
                              'KdfParallelism': paralelismo})
        return self._json(respuesta)

    def _sync(self):
        return {
            'profile': {'organizations': [
                {'id': ORGANIZACION, 'key': self.org_key}]},
            'collections': [
                {'id': COLECCION, 'organizationId': ORGANIZACION},
                {'id': OTRA_COLECCION, 'organizationId': ORGANIZACION}],
            'ciphers': self.ciphers,
        }
