"""Reglas mecánicas de los lineamientos sobre texto nuevo y comandos de commit.
Cada función devuelve una lista de errores en español; lista vacía = cumple."""
import os
import re

from comun import directorio_en, extension, raiz_proyecto, rama_actual, rama_protegida

MARCADO = {".html", ".htm", ".jinja", ".j2", ".jsx", ".tsx", ".vue", ".svelte", ".php", ".uxml"}
SCRIPTS = {".js", ".mjs", ".cjs", ".ts"}
ESTILOS = {".css", ".scss", ".sass", ".less", ".uss"}
SIN_REVISION_IP = {".svg", ".lock", ".map", ".min.js", ".min.css"}
DOCUMENTACION = {".md"}

IP = re.compile(r"(?<![\d.])((?:\d{1,3}\.){3}\d{1,3})(?![\d.])")
IP_PERMITIDAS = {"0.0.0.0", "127.0.0.1"}
LINEA_SVG = re.compile(r"\sd=\"|<path|points=|viewBox|<polygon|<polyline")
SECRETOS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "llave privada"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "llave de acceso AWS"),
]
HEX_EN_CSS = re.compile(r":[^;{}]*?(#[0-9a-fA-F]{3,8})\b")
HEX_EN_CODIGO = re.compile(r"[\"'(:\s](#[0-9a-fA-F]{3,8})\b(?![\w-])")
RGB_LITERAL = re.compile(r"\b(?:rgba?|hsla?)\(\s*\d")
STYLE_ATTR = re.compile(r"\bstyle\s*=\s*([\"'])(.*?)\1", re.S)
STYLE_JSX = re.compile(r"\bstyle\s*=\s*\{\{(.*?)\}\}", re.S)
DART_COLOR = re.compile(r"\bColor\(\s*0x[0-9A-Fa-f]{6,8}\s*\)|\bColor\.fromA?RGBO?\(\s*\d|\bColors\.(?!transparent\b)\w+")
SOLO_VARIABLES = re.compile(r"^\s*(--[\w-]+\s*:[^;]*;?\s*)*$")
ARCHIVO_TEMA_DART = ("theme", "token", "color", "palette", "tema")
COMMIT_REAL = re.compile(r"(?m)(?:^|[;&|(])\s*git(?:\s+-C\s+\S+)?(?:\s+-c\s+\S+)*\s+commit\b")
ID_TAREA = re.compile(r"\[(FNC|DIS)-\d{3}\]")
GIT_ADD = re.compile(r"(?m)(?:^|[;&|(])\s*git(?:\s+-C\s+\S+)?\s+add\b([^;&|\n]*)")
ARCHIVO_SECRETO = re.compile(
    r"(^|/)(\.env(\.[\w-]+)?|id_rsa\w*|id_ed25519\w*|key\.properties|secret\.key|credentials[\w.-]*|"
    r"service-account[\w.-]*\.json|google-services\.json|GoogleService-Info\.plist)$"
    r"|\.(pem|key|p12|pfx|jks|keystore|sqlite3?|db|dump)$", re.I)


def es_archivo_secreto(ruta):
    nombre = ruta.strip().strip("'\"")
    return bool(ARCHIVO_SECRETO.search(nombre)) and not re.search(r"\.(example|sample|template)$", nombre)


def _estilos_inline(texto):
    errores = []
    for _, contenido in STYLE_ATTR.findall(texto):
        if not SOLO_VARIABLES.match(contenido):
            errores.append(f'estilo inline `style="{contenido.strip()[:40]}"`')
    for contenido in STYLE_JSX.findall(texto):
        claves = re.findall(r"([\"']?[\w-]+[\"']?)\s*:", contenido)
        if any(not c.strip("\"'").startswith("--") for c in claves):
            errores.append("estilo inline `style={{...}}` con propiedades que no son variables `--*`")
    if re.search(r"<style[\s>]", texto, re.I):
        errores.append("bloque `<style>` dentro de una plantilla o página")
    for m in re.finditer(r"\.style\.(\w+)", texto):
        if not re.match(r"\.style\.setProperty\(\s*[\"']--", texto[m.start():]):
            errores.append(f"asignación de estilo desde JS `.style.{m.group(1)}`")
            break
    return errores


def _colores_literales(ext, nombre, texto):
    errores = []
    if ext == ".dart" and not any(k in nombre for k in ARCHIVO_TEMA_DART):
        encontrados = DART_COLOR.findall(texto)
        if encontrados:
            errores.append(f"color literal en widget Flutter ({', '.join(sorted(set(encontrados))[:3])}); "
                           "usar Theme.of(context)/ColorScheme/ThemeExtension")
    if "token" in nombre:
        return errores
    hex_encontrados = []
    if ext in ESTILOS:
        hex_encontrados = HEX_EN_CSS.findall(texto)
    elif ext in MARCADO | SCRIPTS:
        hex_encontrados = HEX_EN_CODIGO.findall(texto)
    if hex_encontrados:
        errores.append(f"color literal {', '.join(sorted(set(hex_encontrados))[:3])} fuera del archivo de tokens")
    if ext in ESTILOS | MARCADO | SCRIPTS and RGB_LITERAL.search(texto):
        errores.append("color literal `rgb()/hsl()` con números fuera del archivo de tokens")
    return errores


def _ips(texto):
    errores = []
    for linea in texto.splitlines():
        if LINEA_SVG.search(linea):
            continue
        for ip in IP.findall(linea):
            if ip not in IP_PERMITIDAS and all(int(o) <= 255 for o in ip.split(".")):
                errores.append(f"dirección IP `{ip}` (usar un nombre de host desde una variable de entorno)")
    return errores


def _secretos(texto):
    return [f"posible secreto en el código ({d})" for patron, d in SECRETOS if patron.search(texto)]


def revisar_rama_al_editar(ruta, raiz):
    """En una rama protegida solo se permite escribir documentación (planeación, bitácora)."""
    protegida = rama_protegida(raiz)
    relativa = os.path.relpath(os.path.abspath(ruta), raiz).replace(os.sep, "/")
    if protegida and not relativa.startswith(("docs/", ".claude/")) and relativa != "CHANGELOG.md":
        return [f"estás en la rama protegida `{protegida}`: el código no se edita aquí. Crea la rama de la tarea "
                f"(`git switch -c fnc/FNC-###-titulo`) desde la rama base y trabaja ahí"]
    return []


def revisar_texto(ruta, texto):
    """Revisa el texto NUEVO que se escribirá en `ruta`."""
    ext = extension(ruta)
    nombre = os.path.basename(ruta).lower()
    if ext in DOCUMENTACION:
        # La documentación puede citar las reglas; solo se revisan IPs y secretos.
        return list(dict.fromkeys(_ips(texto) + _secretos(texto)))
    errores = []
    if ext in MARCADO | SCRIPTS:
        errores += _estilos_inline(texto)
    errores += _colores_literales(ext, nombre, texto)
    if ext not in SIN_REVISION_IP:
        errores += _ips(texto)
    errores += _secretos(texto)
    return list(dict.fromkeys(errores))


MOSTRAR_ARCHIVO = re.compile(r"(?:^|[;&|(\s])(?:cat|less|more|head|tail|bat|batcat|strings|xxd|od|nl|tac|grep|rg|awk|sed|cut|sort|diff|cp|scp|base64|openssl)\s+([^;&|\n]*)")
BITWARDEN = re.compile(r"(?:^|[;&|(\s])bw\s+(get|list|export|unlock|login|serve|send|receive|encode)\b")
AYUDA_SECRETOS = ("los secretos no se leen ni se muestran: en desarrollo usa `.env.example` para conocer los nombres; "
                  "en staging/producción vienen de Vaultwarden y los carga el script de despliegue, no el agente")


def revisar_lectura_secreta(herramienta, entrada):
    """Aplica en TODOS los proyectos: el agente no lee archivos de secretos ni consulta el gestor."""
    if herramienta == "Read":
        ruta = entrada.get("file_path", "")
        if es_archivo_secreto(ruta) and not ruta.lower().endswith((".db", ".sqlite", ".sqlite3", ".dump")):
            return [f"lectura de `{os.path.basename(ruta)}`: {AYUDA_SECRETOS}"]
        return []
    if herramienta != "Bash":
        return []
    comando = entrada.get("command", "")
    errores = []
    if BITWARDEN.search(comando):
        errores.append(f"comando de Bitwarden/Vaultwarden que expone secretos (`bw {BITWARDEN.search(comando).group(1)}`): {AYUDA_SECRETOS}")
    for m in MOSTRAR_ARCHIVO.finditer(comando):
        archivos = [a for a in m.group(1).split() if not a.startswith("-") and es_archivo_secreto(a)
                    and not a.lower().endswith((".db", ".sqlite", ".sqlite3", ".dump"))]
        if archivos:
            errores.append(f"comando que muestra o copia `{archivos[0]}`: {AYUDA_SECRETOS}")
            break
    return errores


def revisar_git_add(comando):
    errores = []
    for m in GIT_ADD.finditer(comando):
        argumentos = m.group(1).split()
        if any(a in ("-f", "--force") for a in argumentos):
            errores.append("`git add -f` fuerza archivos ignorados por .gitignore; si de verdad debe versionarse, ajusta el .gitignore con una tarea")
        secretos = [a for a in argumentos if not a.startswith("-") and es_archivo_secreto(a)]
        if secretos:
            errores.append(f"`git add` de archivos con secretos o datos ({', '.join(secretos[:3])}); deben estar en .gitignore")
    return errores


def revisar_commit(comando, cwd):
    """Cada `git commit` se evalúa en la carpeta donde realmente se ejecuta (cd previos, git -C)."""
    errores = []
    for m in COMMIT_REAL.finditer(comando):
        carpeta, determinable = directorio_en(comando, m.start(), cwd)
        if not determinable:
            errores.append("no se puede determinar en qué carpeta se ejecuta el `git commit` (usa una variable o un "
                           "subcomando en `cd`); usa una ruta literal o `git -C <ruta> commit` para que se validen sus reglas")
            continue
        if not raiz_proyecto(carpeta):
            continue
        nombre = f" (en `{carpeta}`)" if os.path.abspath(carpeta) != os.path.abspath(cwd) else ""
        if rama_actual(carpeta) is None:
            errores.append(f"commit en `HEAD` desacoplado{nombre}: crea o cambia a la rama de la tarea antes de hacer commit")
        protegida = rama_protegida(carpeta)
        if protegida:
            errores.append(f"commit directo en la rama protegida `{protegida}`{nombre}: los cambios entran por una rama "
                           "de tarea (`fnc/`, `dis/`) y luego por merge aprobado (tarea → develop → staging → main)")
        tramo = comando[m.start():]
        if "--amend" not in tramo.split("\n")[0] and not ID_TAREA.search(tramo):
            errores.append(f"el mensaje de commit no empieza con el ID de la tarea (`[FNC-###]` o `[DIS-###]`){nombre}")
    return list(dict.fromkeys(errores))
