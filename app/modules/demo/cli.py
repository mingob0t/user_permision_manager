"""Comando `flask --app run:app demo cargar` (FNC-131).

- Solo con `APP_ENV=development`; si no, sale con código 1 sin escribir.
- Contraseñas: ninguna fija. En una terminal las pide con confirmación; con
  `--password-desde-stdin` lee una línea; sin terminal ni opción genera una
  aleatoria por cuenta nueva y la imprime una sola vez.
- Idempotente: lo que ya existe no se duplica ni cambia de contraseña.
"""
import os
import secrets
import sys

import click
from flask.cli import AppGroup

from app import db
from app.modules.auth.acceso_local import ENTORNO_DESARROLLO, VAR_ENTORNO
from app.modules.demo import carga, datos

demo_cli = AppGroup('demo', help='Datos demo para validar en local (FNC-131).')

MENSAJE_ENTORNO = ('Este comando solo corre con APP_ENV=development; no se '
                   'escribió nada.')
MENSAJE_CORTA = (f'La contraseña debe tener al menos '
                 f'{datos.LARGO_MINIMO_CONTRASENA} caracteres.')
MENSAJE_SIN_STDIN = 'No llegó ninguna contraseña por la entrada estándar.'


def hay_terminal():
    return sys.stdin.isatty()


def _es_desarrollo():
    # Misma regla que `auth/acceso_local` (su función es privada).
    return (os.getenv(VAR_ENTORNO) or '').strip().lower() == ENTORNO_DESARROLLO


def _validada(texto):
    if len(texto) < datos.LARGO_MINIMO_CONTRASENA:
        raise click.ClickException(MENSAJE_CORTA)
    return texto


def _contrasenas(nuevos, desde_stdin):
    """({correo: contraseña}, generadas) para las cuentas nuevas."""
    if not nuevos:
        return {}, False
    if desde_stdin:
        linea = sys.stdin.readline().rstrip('\r\n')
        if not linea:
            raise click.ClickException(MENSAJE_SIN_STDIN)
        unica = _validada(linea)
    elif hay_terminal():
        unica = _validada(click.prompt(
            'Contraseña para las cuentas demo nuevas', hide_input=True,
            confirmation_prompt=True))
    else:
        return {c: secrets.token_urlsafe(datos.BYTES_CONTRASENA_ALEATORIA)
                for c in nuevos}, True
    return {c: unica for c in nuevos}, False


def _imprimir(informe, contrasenas, generadas):
    click.echo('\nÁreas y plataformas:')
    for nombre, estado in informe['areas'] + informe['plataformas']:
        click.echo(f'  {nombre}: {estado}')
    click.echo(f'  Solicitud pendiente de demo: {informe["solicitud"]}')
    click.echo('\nCuentas locales (entrar con el correo):')
    click.echo(f'  {"Usuario":<28}{"Rol":<14}{"Área":<24}Estado')
    for cuenta, estado in informe['cuentas']:
        click.echo(f'  {cuenta.correo:<28}{cuenta.rol:<14}{cuenta.area:<24}'
                   f'{estado}')
    if generadas:
        click.echo('\nContraseñas generadas (se muestran solo ahora):')
        for correo, texto in contrasenas.items():
            click.echo(f'  {correo}  {texto}')
    elif contrasenas:
        click.echo('\nLas cuentas nuevas usan la contraseña que indicaste.')
    else:
        click.echo('\nNo hubo cuentas nuevas: las contraseñas no cambian.')
    click.echo('La cuenta semilla `admin` (superadmin) sigue como estaba.')


@demo_cli.command('cargar')
@click.option('--password-desde-stdin', 'desde_stdin', is_flag=True,
              help='Lee la contraseña de las cuentas nuevas de la entrada '
                   'estándar (una línea).')
def cargar(desde_stdin):
    """Crea áreas, plataformas, cuentas locales y una solicitud de demo."""
    if not _es_desarrollo():
        raise click.ClickException(MENSAJE_ENTORNO)
    contrasenas, generadas = _contrasenas(carga.correos_nuevos(), desde_stdin)
    try:
        informe = carga.cargar(contrasenas)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    _imprimir(informe, contrasenas, generadas)
