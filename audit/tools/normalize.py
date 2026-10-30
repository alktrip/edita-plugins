#!/usr/bin/env python3
# This file is part of Edita.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# normalize.py <carpeta-del-código> <carpeta-con-cabeceras>...
#
# Corrige en los #include lo que solo funciona en Windows y que cualquier receta
# arreglaría de forma mecánica:
#   - las barras invertidas (npp\PluginInterface.h → npp/PluginInterface.h);
#   - las mayúsculas (TCHAR.h → tchar.h, Windows.h → windows.h), porque en
#     Windows el sistema de archivos no las distingue.
# La cabecera se busca, sin distinguir mayúsculas, junto al archivo, en el árbol del
# plugin y en las carpetas indicadas (la capa de compatibilidad, Scintilla, Lexilla).
# Si existe con otro nombre o en otra carpeta, se reescribe el #include.
import os
import re
import sys

root = sys.argv[1]
extra = sys.argv[2:]
SOURCES = ('.c', '.cc', '.cpp', '.cxx', '.h', '.hh', '.hpp', '.hxx', '.inl', '.rc')
INCLUDE = re.compile(r'^(\s*#\s*include\s*)([<"])([^>"]+)([>"])', re.M)

# Índice: nombre en minúsculas → rutas reales
by_name = {}
tree = []
for dp, dn, fn in os.walk(root):
    for f in fn:
        full = os.path.join(dp, f)
        tree.append(full)
        by_name.setdefault(f.lower(), []).append(full)
sdk_names = {}
for d in extra:
    for f in os.listdir(d):
        sdk_names.setdefault(f.lower(), f)


def resolve(including_dir, path, quoted):
    path = path.replace('\\', '/')
    if not quoted:
        # <...>: solo las cabeceras del SDK (no confundir <string.h> con un String.h del plugin)
        return sdk_names.get(os.path.basename(path).lower(), path)
    # 1. Relativa al archivo, sin distinguir mayúsculas componente a componente
    cur = including_dir
    ok = True
    parts = []
    for comp in path.split('/'):
        if comp in ('.', '..'):
            cur = os.path.normpath(os.path.join(cur, comp))
            parts.append(comp)
            continue
        try:
            match = next((e for e in os.listdir(cur) if e.lower() == comp.lower()), None)
        except OSError:
            match = None
        if match is None:
            ok = False
            break
        cur = os.path.join(cur, match)
        parts.append(match)
    if ok:
        return '/'.join(parts)
    base = os.path.basename(path).lower()
    # 2. Una cabecera del SDK (está en las rutas de inclusión)
    if base in sdk_names:
        return sdk_names[base]
    # 3. En otro sitio del árbol del plugin: ruta relativa al archivo que la incluye
    candidates = by_name.get(base, [])
    if len(candidates) >= 1:
        # La que más se parezca a la ruta pedida
        want = path.lower()
        best = max(candidates, key=lambda c: len(os.path.commonprefix([c.lower()[::-1], want[::-1]])))
        return os.path.relpath(best, including_dir)
    return path


changed = 0
for full in tree:
    if not full.lower().endswith(SOURCES):
        continue
    try:
        raw = open(full, 'rb').read()
    except OSError:
        continue
    for enc in ('utf-8', 'latin-1'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    here = os.path.dirname(full)

    def fix(m):
        new = resolve(here, m.group(3), m.group(2) == '"')
        return f'{m.group(1)}"{new}"' if m.group(2) == '"' else f'{m.group(1)}<{new}>'

    out = INCLUDE.sub(fix, text)
    if out != text:
        open(full, 'w', encoding=enc, newline='').write(out)
        changed += 1
print(f'{changed} archivos con #include corregidos')
