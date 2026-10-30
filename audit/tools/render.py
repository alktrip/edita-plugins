#!/usr/bin/env python3
# This file is part of Edita.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# render.py <catalog.json> <lista-n++.json>: escribe en stdout las tablas de la
# auditoría en Markdown (se pegan en audit/README.md entre las marcas).
import collections
import json
import sys

CLASSES = [
    ('A', 'Compila sin cambios'),
    ('B1', 'Compila; hay que portar su interfaz'),
    ('B2', 'No compila: necesita un port'),
    ('C', 'Tecnología exclusiva de Windows: reescribir'),
    ('D', 'Sin código fuente'),
    ('R', 'Fuera de GitHub: revisar a mano'),
    ('E', 'Ya cubierto por Edita'),
]

catalog = json.load(open(sys.argv[1], encoding='utf-8'))
source = json.load(open(sys.argv[2], encoding='utf-8-sig'))


def cell(text):
    return str(text if text is not None else '—').replace('|', '\\|')


def link(e):
    url = f"https://github.com/{e['repo']}" if e['repo'] else e['homepage']
    return f"[{cell(e['name'])}]({url})" if url else cell(e['name'])


by_class = collections.defaultdict(list)
for e in catalog:
    by_class[e['class']].append(e)

print(f"Lista analizada: `pl.x64.json` versión {source['version']}, {len(catalog)} plugins.\n")
print('| Clase | Qué significa | Plugins | Con licencia que permite redistribuir |')
print('|---|---|---:|---:|')
for key, title in CLASSES:
    items = by_class.get(key, [])
    redist = sum(1 for e in items if e['redist'].startswith('sí'))
    print(f'| {key} | {title} | {len(items)} | {redist} |')
print(f'| | **Total** | **{len(catalog)}** | '
      f"**{sum(1 for e in catalog if e['redist'].startswith('sí'))}** |")

for key, title in CLASSES:
    items = sorted(by_class.get(key, []), key=lambda e: e['name'].lower())
    if not items:
        continue
    print(f'\n### {key}. {title} ({len(items)})\n')
    if key in ('A', 'B1', 'B2'):
        print('| Plugin | Versión | Licencia | Lenguaje | Líneas | Diálogos | Detalle |')
        print('|---|---|---|---|---:|---:|---|')
        for e in items:
            extra = []
            if e['mfc']:
                extra.append('MFC')
            if e['com']:
                extra.append('COM')
            if e['subclass']:
                extra.append('ventanas Win32')
            if e['archived']:
                extra.append('archivado')
            detail = e['reason'] + (f" ({', '.join(extra)})" if extra else '')
            print(f"| {link(e)} | {cell(e['version'])} | {cell(e['redist'])} | {cell(e['lang'])} | "
                  f"{e['loc'] or 0} | {e['dialogs'] or 0} | {cell(detail)} |")
    else:
        print('| Plugin | Versión | Licencia | Motivo |')
        print('|---|---|---|---|')
        for e in items:
            print(f"| {link(e)} | {cell(e['version'])} | {cell(e['redist'])} | {cell(e['reason'])} |")

# Backlog del SDK: qué falta en la capa de compatibilidad, por número de plugins
native = [e for e in catalog if e['class'] in ('A', 'B1', 'B2')]
stubs = collections.Counter(h.lower() for e in native for h in set(e['stubs']))
blocked = collections.Counter(s for e in native if e['class'] == 'B2' for s in e['symbols'])
print('\n### Backlog del SDK\n')
print('Cabeceras de Windows que no existen en `plugin-sdk/compat/` (la compilación de prueba las creó vacías), '
      'por número de plugins que las incluyen:\n')
print(', '.join(f'`{h}` ({n})' for h, n in stubs.most_common(30)) or '—')
print('\nIdentificadores y funciones que más frenan a los plugins de la clase B2 (los seis más repetidos de cada uno):\n')
print(', '.join(f'`{s}` ({n})' for s, n in blocked.most_common(40)) or '—')
