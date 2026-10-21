"""Cliente de Vaultwarden contra un servidor simulado, sin red (FNC-068)."""
import logging
import ssl
import urllib.error

import pytest

from app.modules.secretos import cifrado, vaultwarden
from app.modules.secretos.configuracion import cargar_configuracion
from app.modules.secretos.vaultwarden import (ClienteVaultwarden, GestorCaido,
                                              GestorMalConfigurado,
                                              RUTA_PRELOGIN, RUTA_SYNC,
                                              RUTA_TOKEN, SecretoAmbiguo,
                                              SecretoNoEncontrado,
                                              TransporteHttps)
from tests.secretos import vaultwarden_falso as vf

REFERENCIA = 'pokemon/contabilidad-api'
SECRETO = 'Valor-Ficticio-Del-Item'


class Reloj:
    def __init__(self):
        self.ahora = 1000.0

    def __call__(self):
        return self.ahora


def _cliente(servidor, reloj=None, **variables):
    cfg = cargar_configuracion({**vf.ENTORNO, **variables})
    return ClienteVaultwarden(cfg, transporte=servidor,
                              reloj=reloj or Reloj())


@pytest.fixture
def servidor():
    return vf.VaultwardenFalso()


def test_lee_secreto_y_usuario_del_item_de_la_coleccion(servidor):
    servidor.item(REFERENCIA, SECRETO, usuario='svc-portal')
    item = _cliente(servidor).leer(REFERENCIA)
    assert (item.secreto, item.usuario) == (SECRETO, 'svc-portal')


def test_item_con_clave_propia(servidor):
    servidor.item(REFERENCIA, SECRETO, clave_propia=True)
    assert _cliente(servidor).leer(REFERENCIA).secreto == SECRETO


def test_argon2id_y_kdf_desde_prelogin():
    servidor = vf.VaultwardenFalso(kdf=cifrado.KDF_ARGON2ID, iteraciones=2,
                                   memoria=16, paralelismo=1,
                                   kdf_en_token=False)
    servidor.item(REFERENCIA, SECRETO)
    assert _cliente(servidor).leer(REFERENCIA).secreto == SECRETO
    assert ('POST', RUTA_PRELOGIN) in servidor.peticiones


@pytest.mark.parametrize('variacion', [
    {'coleccion': vf.OTRA_COLECCION},
    {'organizacion': '00000000-0000-4000-8000-000000000000'},
    {'borrado': True},
    {'tipo': 2},
])
def test_ignora_items_fuera_de_la_coleccion_borrados_o_no_login(servidor,
                                                                 variacion):
    servidor.item(REFERENCIA, SECRETO, **variacion)
    with pytest.raises(SecretoNoEncontrado):
        _cliente(servidor).leer(REFERENCIA)


def test_nombre_exacto_sin_coincidencias_parciales(servidor):
    servidor.item(REFERENCIA + '-viejo', SECRETO)
    with pytest.raises(SecretoNoEncontrado):
        _cliente(servidor).leer(REFERENCIA)


def test_dos_items_con_el_mismo_nombre_es_ambiguo(servidor):
    servidor.item(REFERENCIA, SECRETO)
    servidor.item(REFERENCIA, 'otro-valor-ficticio')
    with pytest.raises(SecretoAmbiguo):
        _cliente(servidor).leer(REFERENCIA)


def test_item_sin_contrasena_no_se_acepta(servidor):
    servidor.item(REFERENCIA, '')
    with pytest.raises(SecretoNoEncontrado):
        _cliente(servidor).leer(REFERENCIA)


def test_mac_alterado_se_ignora_y_no_se_usa(servidor):
    item = servidor.item(REFERENCIA, SECRETO)
    iv, datos, mac = item['name'][2:].split('|')
    item['name'] = f'2.{iv}|{datos}|{"A" * 43}='
    with pytest.raises(SecretoNoEncontrado):
        _cliente(servidor).leer(REFERENCIA)


def test_tipo_sin_mac_se_rechaza():
    with pytest.raises(cifrado.ErrorDeCifrado):
        cifrado.descifrar_simetrico('0.AAAA|BBBB', vf.clave_aleatoria())


def test_contrasena_maestra_equivocada_falla_cerrado(servidor, caplog):
    servidor.item(REFERENCIA, SECRETO)
    caplog.set_level(logging.DEBUG)
    with pytest.raises(GestorMalConfigurado) as error:
        _cliente(servidor,
                 VAULTWARDEN_MASTER_PASSWORD='otra-maestra').leer(REFERENCIA)
    for valor in ('otra-maestra', vf.CONTRASENA_MAESTRA, SECRETO, vf.TOKEN):
        assert valor not in str(error.value)
        assert valor not in caplog.text


def test_kdf_fuera_de_limites_se_rechaza():
    servidor = vf.VaultwardenFalso()
    servidor.kdf = (cifrado.KDF_PBKDF2, 5000, None, None)
    with pytest.raises(GestorMalConfigurado):
        _cliente(servidor).leer(REFERENCIA)


def test_llave_de_api_rechazada_es_no_configurado(servidor):
    with pytest.raises(GestorMalConfigurado):
        _cliente(servidor, VAULTWARDEN_CLIENT_SECRET='otro').leer(REFERENCIA)


@pytest.mark.parametrize('estado', [429, 500, 503])
def test_estados_transitorios_son_gestor_caido(servidor, estado):
    servidor.estado_forzado[RUTA_TOKEN] = estado
    with pytest.raises(GestorCaido):
        _cliente(servidor).leer(REFERENCIA)


def test_sin_respuesta_es_gestor_caido(servidor):
    servidor.excepcion = GestorCaido('simulado')
    with pytest.raises(GestorCaido):
        _cliente(servidor).leer(REFERENCIA)


def test_reutiliza_la_sesion_y_la_renueva_al_vencer(servidor):
    servidor.item(REFERENCIA, SECRETO)
    reloj = Reloj()
    cliente = _cliente(servidor, reloj)
    cliente.leer(REFERENCIA)
    cliente.leer(REFERENCIA)
    assert servidor.peticiones.count(('POST', RUTA_TOKEN)) == 1
    reloj.ahora += servidor.expira
    cliente.leer(REFERENCIA)
    assert servidor.peticiones.count(('POST', RUTA_TOKEN)) == 2


def test_un_401_renueva_la_sesion_una_sola_vez(servidor):
    servidor.item(REFERENCIA, SECRETO)
    cliente = _cliente(servidor)
    cliente.leer(REFERENCIA)
    servidor.token_vigente = 'token-nuevo-ficticio'
    assert cliente.leer(REFERENCIA).secreto == SECRETO
    servidor.estado_forzado[RUTA_SYNC] = 401
    with pytest.raises(GestorMalConfigurado):
        cliente.leer(REFERENCIA)


def test_la_rotacion_se_ve_en_la_siguiente_lectura(servidor):
    servidor.item(REFERENCIA, SECRETO)
    cliente = _cliente(servidor)
    cliente.leer(REFERENCIA)
    servidor.cambiar_contrasena(0, 'Valor-Rotado-Ficticio')
    assert cliente.leer(REFERENCIA).secreto == 'Valor-Rotado-Ficticio'


def test_representaciones_sin_secretos(servidor):
    servidor.item(REFERENCIA, SECRETO)
    cliente = _cliente(servidor)
    item = cliente.leer(REFERENCIA)
    textos = ' '.join([repr(item), str(item), repr(cliente), repr(cliente._cfg),
                       repr(cliente._sesion), repr(cliente._sesion.clave_usuario)])
    for valor in (SECRETO, vf.CLIENT_SECRET, vf.CONTRASENA_MAESTRA, vf.TOKEN,
                  vf.CORREO):
        assert valor not in textos


def test_no_registra_valores_en_logs(servidor, caplog):
    servidor.item(REFERENCIA, SECRETO)
    servidor.item('otro', SECRETO)['name'] = '2.AAAA|BBBB|CCCC'
    caplog.set_level(logging.DEBUG)
    _cliente(servidor).leer(REFERENCIA)
    for valor in (SECRETO, vf.CLIENT_SECRET, vf.CONTRASENA_MAESTRA, vf.TOKEN):
        assert valor not in caplog.text


# ------------------------------------------------------------ transporte


def test_contexto_tls_valida_certificado_y_nombre():
    contexto = vaultwarden.contexto_tls()
    assert contexto.verify_mode == ssl.CERT_REQUIRED
    assert contexto.check_hostname is True
    assert contexto.minimum_version >= ssl.TLSVersion.TLSv1_2


def test_transporte_sin_proxies_ni_redirecciones(monkeypatch):
    monkeypatch.setenv('https_proxy', 'http://proxy.pruebas.invalid:3128')
    transporte = TransporteHttps(cargar_configuracion(vf.ENTORNO))
    proxies = [h for h in transporte._abridor.handlers
               if isinstance(h, urllib.request.ProxyHandler)]
    # `ProxyHandler({})` reemplaza al de `urllib`, que leería `https_proxy`.
    assert all(not h.proxies for h in proxies)
    redirecciones = [h for h in transporte._abridor.handlers
                     if isinstance(h, urllib.request.HTTPRedirectHandler)]
    assert redirecciones and all(
        h.redirect_request(None, None, 302, '', {}, 'https://otro.invalid')
        is None for h in redirecciones)


class _Abridor:
    def __init__(self, efecto):
        self.efecto = efecto
        self.tiempo = None

    def open(self, peticion, timeout=None):
        self.tiempo = timeout
        raise self.efecto


def _transporte_con(efecto):
    transporte = TransporteHttps(cargar_configuracion(
        {**vf.ENTORNO, 'VAULTWARDEN_TIMEOUT_SECONDS': '7'}))
    transporte._abridor = _Abridor(efecto)
    return transporte


def test_transporte_usa_el_tiempo_de_espera_y_mapea_http_error():
    error = urllib.error.HTTPError(vf.URL, 503, 'x', {}, None)
    transporte = _transporte_con(error)
    assert transporte('GET', vf.URL, {}).estado == 503
    assert transporte._abridor.tiempo == 7


def test_transporte_certificado_invalido_es_no_configurado():
    causa = ssl.SSLCertVerificationError('certificado')
    with pytest.raises(GestorMalConfigurado):
        _transporte_con(urllib.error.URLError(causa))('GET', vf.URL, {})


def test_transporte_sin_red_es_gestor_caido():
    with pytest.raises(GestorCaido):
        _transporte_con(urllib.error.URLError('sin red'))('GET', vf.URL, {})
    with pytest.raises(GestorCaido):
        _transporte_con(TimeoutError())('GET', vf.URL, {})


def test_respuesta_demasiado_grande_se_rechaza(monkeypatch):
    monkeypatch.setattr(vaultwarden, 'TAMANO_MAXIMO_RESPUESTA', 4)

    class Grande:
        def read(self, n):
            return b'x' * n

    with pytest.raises(GestorMalConfigurado):
        vaultwarden._leer_acotado(Grande())


def test_cliente_del_entorno_sin_configuracion_falla_cerrado():
    vaultwarden.reiniciar_cliente()
    with pytest.raises(GestorMalConfigurado):
        vaultwarden.cliente_del_entorno({})
