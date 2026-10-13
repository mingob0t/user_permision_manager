"""Utilidades compartidas por los hooks de lineamientos: raíz del proyecto, extensiones,
exclusiones y git. Sin reglas de negocio: solo infraestructura."""
import fnmatch
import os
import subprocess

# Archivos generados o de terceros que nunca se revisan.
EXCLUSIONES_POR_DEFECTO = [
    "*.g.dart", "*.freezed.dart", "*.gr.dart", "*.mocks.dart", "*.config.dart",
    "*.min.js", "*.min.css", "*.map", "*.lock", "package-lock.json", "pubspec.lock",
    "node_modules/*", "vendor/*", "dist/*", "build/*", ".next/*", "coverage/*",
    "Library/*", "Temp/*", "Obj/*", "Logs/*", "Packages/*", ".dart_tool/*",
    ".git/*", "*/node_modules/*", "*/build/*",
]
ARCHIVO_EXCLUSIONES = os.path.join(".claude", "lineamientos-ignorar")
ARCHIVO_FLUJO = os.path.join(".claude", "flujo.json")
FLUJO_POR_DEFECTO = {
    # main = producción, staging = pruebas/QA, develop = integración (entorno dev).
    "protegidas": ["main", "master", "staging", "develop"],
    "base_de_tareas": "develop",
}


import re as _re

_CAMBIO_DIR = _re.compile(r"(?:^|[;&|(\n]|&&|\|\|)\s*(?:cd|pushd)\s+(\"[^\"]*\"|'[^']*'|[^\s;&|)]+)")
_GIT_C = _re.compile(r"\bgit\s+-C\s+(\"[^\"]*\"|'[^']*'|\S+)")


def _resolver(destino, base):
    """Ruta absoluta de un destino de cd o git -C; None si depende de variables o subcomandos."""
    destino = destino.strip("\"'")
    if any(c in destino for c in "$`*?") or destino == "-":
        return None
    destino = os.path.expanduser(destino)
    return os.path.normpath(destino if os.path.isabs(destino) else os.path.join(base, destino))


def directorio_en(comando, posicion, cwd):
    """Carpeta donde se ejecuta la parte del comando que empieza en `posicion`, considerando los
    `cd`/`pushd` previos y un `git -C` en esa misma parte. Devuelve (ruta, determinable)."""
    actual, determinable = cwd, True
    for m in _CAMBIO_DIR.finditer(comando[:posicion]):
        destino = _resolver(m.group(1), actual)
        if destino is None:
            determinable = False
        else:
            actual = destino
    fin = comando.find("\n", posicion)
    tramo = comando[posicion: fin if fin != -1 else len(comando)]
    git_c = _GIT_C.search(tramo)
    if git_c:
        destino = _resolver(git_c.group(1), actual)
        if destino is None:
            return actual, False
        actual = destino
    return actual, determinable


def directorios_del_comando(comando, cwd):
    """Todas las carpetas a las que el comando cambia (para saber si sale del proyecto)."""
    carpetas, actual = [], cwd
    for m in list(_CAMBIO_DIR.finditer(comando)) + list(_GIT_C.finditer(comando)):
        destino = _resolver(m.group(1), actual if m.re is _GIT_C else actual)
        carpetas.append(destino)
        if destino and m.re is _CAMBIO_DIR:
            actual = destino
    return carpetas


def raiz_proyecto(ruta):
    """Sube desde ruta hasta encontrar docs/planeacion; devuelve la raíz o None."""
    actual = os.path.abspath(ruta)
    while not os.path.isdir(actual):
        padre = os.path.dirname(actual)
        if padre == actual:
            return None
        actual = padre
    while True:
        if os.path.isdir(os.path.join(actual, "docs", "planeacion")):
            return actual
        padre = os.path.dirname(actual)
        if padre == actual:
            return None
        actual = padre


def extension(ruta):
    nombre = os.path.basename(ruta).lower()
    for compuesta in (".min.js", ".min.css"):
        if nombre.endswith(compuesta):
            return compuesta
    return os.path.splitext(nombre)[1]


def patrones_exclusion(raiz):
    patrones = list(EXCLUSIONES_POR_DEFECTO)
    archivo = os.path.join(raiz, ARCHIVO_EXCLUSIONES)
    if os.path.isfile(archivo):
        with open(archivo, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith("#"):
                    patrones.append(linea.rstrip("/") + "/*" if linea.endswith("/") else linea)
    return patrones


def excluido(ruta, raiz):
    relativa = os.path.relpath(os.path.abspath(ruta), raiz).replace(os.sep, "/")
    nombre = os.path.basename(relativa)
    return any(fnmatch.fnmatch(relativa, p) or fnmatch.fnmatch(nombre, p) for p in patrones_exclusion(raiz))


def git(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    return r.returncode, r.stdout


def rama_actual(cwd):
    codigo, salida = git(cwd, "symbolic-ref", "-q", "--short", "HEAD")
    return salida.strip() if codigo == 0 else None


def flujo(raiz):
    import json
    conf = dict(FLUJO_POR_DEFECTO)
    archivo = os.path.join(raiz, ARCHIVO_FLUJO)
    if os.path.isfile(archivo):
        with open(archivo, encoding="utf-8") as f:
            conf.update(json.load(f))
    return conf


def rama_protegida(raiz):
    rama = rama_actual(raiz)
    return rama if rama and rama in flujo(raiz)["protegidas"] else None


def rama_base(cwd):
    preferida = flujo(cwd)["base_de_tareas"] if os.path.isdir(os.path.join(cwd, ".git")) else None
    for candidata in ([preferida] if preferida else []) + ["develop", "main", "master"]:
        if git(cwd, "rev-parse", "--verify", "-q", candidata)[0] == 0:
            return candidata
    return None
