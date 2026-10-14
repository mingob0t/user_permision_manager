#!/usr/bin/env python3
"""Las mismas reglas que el hook de Claude, para personas: se ejecuta como hook de git
pre-commit y revisa solo las líneas AGREGADAS en lo preparado (staged).

Uso en un proyecto (lo instala el agente `devops`, copiando esta carpeta a `scripts/lineamientos/`):
    .git/hooks/pre-commit  ->  python3 scripts/lineamientos/precommit.py
o como hook local en .pre-commit-config.yaml (language: system, pass_filenames: false).
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import excluido, git, raiz_proyecto, rama_actual, rama_protegida  # noqa: E402
from reglas import es_archivo_secreto, revisar_texto  # noqa: E402


def lineas_agregadas_por_archivo(raiz):
    _, diff = git(raiz, "diff", "--cached", "--unified=0", "--no-color", "--diff-filter=ACMR")
    por_archivo, actual = {}, None
    for linea in diff.splitlines():
        if linea.startswith("+++ "):
            actual = linea[6:] if linea.startswith("+++ b/") else None
            if actual:
                por_archivo.setdefault(actual, [])
        elif actual and linea.startswith("+") and not linea.startswith("+++"):
            por_archivo[actual].append(linea[1:])
    return {a: "\n".join(l) for a, l in por_archivo.items()}


def main():
    _, salida = git(os.getcwd(), "rev-parse", "--show-toplevel")
    raiz = raiz_proyecto(salida.strip() or os.getcwd())
    if not raiz:
        return 0
    errores = []
    if rama_actual(raiz) is None:
        errores.append("(git) commit en HEAD desacoplado: crea o cambia a la rama de la tarea")
    if rama_protegida(raiz):
        errores.append(f"(git) commit directo en la rama protegida `{rama_protegida(raiz)}`: usa una rama de tarea y un merge aprobado")
    _, preparados = git(raiz, "diff", "--cached", "--name-only", "--diff-filter=A")
    errores += [f"{a}: archivo con secretos o datos; debe estar en .gitignore" for a in preparados.splitlines()
                if es_archivo_secreto(a)]
    for archivo, texto in lineas_agregadas_por_archivo(raiz).items():
        ruta = os.path.join(raiz, archivo)
        if excluido(ruta, raiz):
            continue
        errores += [f"{archivo}: {e}" for e in revisar_texto(ruta, texto)]
    if not errores:
        return 0
    print("Commit rechazado por los lineamientos del proyecto:", file=sys.stderr)
    for e in errores:
        print(f"- {e}", file=sys.stderr)
    print("Corrige o, si es un archivo generado o de terceros, agrégalo a .claude/lineamientos-ignorar.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
