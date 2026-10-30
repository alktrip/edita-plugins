#!/bin/bash
# This file is part of Edita.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Repite la auditoría de la lista oficial de plugins de Notepad++.
#
#   EDITA_SRC=../editor audit/tools/run-audit.sh <carpeta-de-trabajo>
#
# Necesita git, gh (con sesión iniciada: la API de GitHub sin sesión solo permite 60
# consultas por hora), curl, python3, cmake, ninja, un compilador de C++ y Qt 6.
# Descarga el código de unos 140 repositorios (~650 MB) y los compila: tarda
# alrededor de una hora. El código descargado solo se compila, nunca se ejecuta,
# y con un CMakeLists.txt propio (no se usan los scripts de compilación del original).
set -euo pipefail
WORK=$(realpath -m "${1:?Uso: run-audit.sh <carpeta-de-trabajo>}")
TOOLS=$(dirname "$(realpath "$0")")
AUDIT=$(dirname "$TOOLS")
export EDITA_SRC=$(realpath "${EDITA_SRC:?Falta EDITA_SRC (carpeta del código de Edita)}")
mkdir -p "$WORK/npl" "$WORK/src" "$WORK/try"

echo '1/5 Lista oficial de N++'
curl -sSL -o "$WORK/npl/pl.x64.json" \
    https://raw.githubusercontent.com/notepad-plus-plus/nppPluginList/master/src/pl.x64.json

echo '2/5 Metadatos de GitHub (licencia, lenguajes, archivos)'
python3 -I "$TOOLS/fetch.py" "$WORK"

echo '3/5 Código fuente de los plugins que no son de .NET ni Delphi'
python3 -I -c "
import json,sys
for r in json.load(open(sys.argv[1])):
    if r.get('repo') and r.get('main') not in ('C#','Pascal'): print(r['repo'])" "$WORK/rows.json" |
    sort -u | xargs -P 8 -I{} sh -c '
        d="$0/src/$(echo {} | tr / _)"; [ -d "$d" ] && exit 0; mkdir -p "$d"
        curl -sSL https://codeload.github.com/{}/tar.gz/HEAD | tar xz -C "$d" --strip-components=1
        # Los archivos de GitHub no traen los submódulos: clonar esos repositorios
        if [ -f "$d/.gitmodules" ]; then
            rm -rf "$d"; git clone -q --depth 1 --recurse-submodules --shallow-submodules https://github.com/{} "$d"
        fi' "$WORK"
python3 -I "$TOOLS/scan.py" "$WORK/src" "$WORK/scan.json"
python3 -I "$TOOLS/dialogs.py" "$WORK/src" "$WORK/dialogs.json"

echo '4/5 Compilación de prueba con la capa de compatibilidad de Edita'
ls -d "$WORK"/src/* | xargs -P 4 -I{} "$TOOLS/trybuild.sh" {} "$WORK/try" >/dev/null 2>&1

python3 -I "$TOOLS/core.py" "$WORK/try" "$WORK/core.json"
echo '5/5 Clasificación'
python3 -I "$TOOLS/classify.py" "$WORK" "$AUDIT/catalog.json"
python3 -I "$TOOLS/render.py" "$AUDIT/catalog.json" "$WORK/npl/pl.x64.json" > "$WORK/tables.md"
echo "Tablas en $WORK/tables.md (pegarlas en audit/README.md)"
