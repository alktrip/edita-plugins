#!/usr/bin/env python3
# This file is part of Edita.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# classify.py <carpeta-de-trabajo> <catalog.json>: une la lista de N++, los metadatos
# de GitHub, el análisis del código y la compilación de prueba, y clasifica cada plugin.
import collections
import json
import os
import re
import sys

base = sys.argv[1]
pl = json.load(open(f'{base}/npl/pl.x64.json', encoding='utf-8-sig'))['npp-plugins']
rows = {r['folder']: r for r in json.load(open(f'{base}/rows.json'))}
scan = json.load(open(f'{base}/scan.json'))
dialogs = json.load(open(f'{base}/dialogs.json'))
# Qué archivos fallaron y si alguno es del núcleo (core.py); opcional
core = json.load(open(f'{base}/core.json')) if os.path.exists(f'{base}/core.json') else {}

# Ya cubiertos por Edita: fase en la que se hizo
COVERED = {
    'PythonScript': '13 (port incluido)', 'MarkdownViewerPlusPlus': '26 (port incluido)',
    'XMLTools': '15 y 25 (receta con port)', 'mimeTools': '15 (receta, código original)',
    'ComparePlugin': '39', 'ComparePlus': '39', 'NppExec': '35 y 48 (terminal y menú Ejecutar)',
    'Explorer': '22', 'NewFileBrowser': '22', 'folderpad++': '22',
    'AnotherMarkdown': '26', 'NppMarkdownPanel': '26', 'MarkLens': '26', 'NMD': '26',
    'MarkdownReader': '26', 'NppMarkdownNext': '26',
    'NppSnippets': '41', 'FingerText2': '41', 'QuickText': '41', 'GitSCM': '28 y 40',
    'JSFunctionViewer': '22 (Lista de funciones)', 'NavigateTo': '27 (Ctrl+E)',
    'NppMenuSearch': '27 (paleta de órdenes)', 'SessionMgr': '47', 'FoldingLineHider': '49',
    'Linter': '36 (LSP)', 'Linter++': '36 (LSP)', 'RegexViewer': '34', 'RegexTrainer': '34',
    'NPPColorPicker': '29', 'ScrollMarks': '28 y 33', 'NppTags': '37 y 42 (LSP)',
    'NppGTags': '37 y 42 (LSP)', 'TagLEET': '37 y 42 (LSP)', 'SourceCookifier': '22 y 42',
    'dark_mode_C': '17', 'NppPluginDemo': '11 (EditaDemo)', 'NppPluginTemplate': '11 (SDK)',
}
# Fuera de GitHub, revisados a mano
OFF_GITHUB = {
    'ActiveX': ('C', 'COM/ActiveX de Windows'), 'AutoCodepage': ('C', 'Delphi'),
    'AutoEolFormat': ('C', 'Delphi'), 'CustomLineNumbers': ('C', 'Delphi'),
    'ExtSettings': ('C', 'Delphi'), 'NppToolBucket': ('C', '.NET 3.5'),
    'SQLinFormNpp64': ('D', 'comercial, sin código'),
    'Linefilter3': ('D', 'freeware, sin código publicado'),
    'rdmd-en-x64': ('C', 'lenguaje D'), 'rdmd-ja-x64': ('C', 'lenguaje D'),
}
DOTNET_WRAPPED = {'JsMapParser.NppPlugin', 'PoorMansTSqlFormatterNppPlugin'}
LANG = {'C#': '.NET (C#)', 'Pascal': 'Delphi/Free Pascal', 'V': 'lenguaje V'}

UNDECLARED = re.compile(r"error: '([A-Za-z_][A-Za-z_0-9]*)' (?:was not declared|has not been declared|does not name a type)")
UNDEFINED = re.compile(r"undefined reference to `([A-Za-z_][A-Za-z_0-9]*)")


def build_info(key):
    d = f'{base}/try/{key}'
    if not key or not os.path.exists(f'{d}/result'):
        return None, [], [], False
    result = open(f'{d}/result').read().strip()
    stubs = open(f'{d}/stubs.txt').read().split() if os.path.exists(f'{d}/stubs.txt') else []
    log = open(f'{d}/build.log', errors='replace').read() if os.path.exists(f'{d}/build.log') else ''
    symbols = UNDEFINED.findall(log) if result == 'link' else UNDECLARED.findall(log)
    top = [s for s, _ in collections.Counter(symbols).most_common(6)]
    # La API de plugins de N++ es Unicode (wchar_t) desde la 8.0; la capa usa TCHAR = char
    wide = result in ('compile', 'link', 'deps') and bool(re.search(r'wchar_t|wstring', log))
    return result, stubs, top, wide


catalog = []
for p in pl:
    folder = p['folder-name']
    r = rows.get(folder, {})
    key = (r.get('repo') or '').replace('/', '_')
    s = scan.get(key, {})
    result, stubs, symbols, wide = build_info(key)
    e = {
        'folder': folder, 'name': p['display-name'], 'version': p['version'],
        'repo': r.get('repo'), 'homepage': p.get('homepage', ''),
        'license': r.get('license'), 'lang': r.get('main'), 'archived': r.get('archived'),
        'pushed': (r.get('pushed') or '')[:10], 'stars': r.get('stars'),
        'build': result, 'stubs': stubs, 'symbols': symbols, 'wide': wide,
        'dialogs': dialogs.get(key, {}).get('dlgres'), 'loc': s.get('loc'),
        'mfc': bool(s.get('mfc')), 'com': bool(s.get('com')), 'subclass': bool(s.get('window')),
    }
    if folder in COVERED:
        cls, why = 'E', 'fase ' + COVERED[folder]
    elif not e['repo']:
        cls, why = OFF_GITHUB.get(folder, ('R', 'fuera de GitHub (SourceForge u otro): revisar a mano'))
    elif e['lang'] in LANG or folder in DOTNET_WRAPPED:
        cls, why = 'C', LANG.get(e['lang'], '.NET (C#)')
    elif e['lang'] == '(sin código)' or result == 'nosrc':
        cls, why = 'D', 'el repositorio solo tiene binarios'
    elif result in ('ok', 'stubs'):
        # Desde la fase 53 de Edita, los diálogos de los .rc funcionan: si compila (sin
        # MFC), compila entero, con su interfaz
        simple = not e['mfc']
        cls = 'A' if simple else 'B1'
        why = ('compila entero con la capa de compatibilidad, interfaz incluida (ventanas y diálogos del .rc)' if simple
               else 'compila, pero usa MFC: su interfaz hay que portarla a Qt')
        if stubs:
            why += ' (con cabeceras vacías: ' + ', '.join(stubs) + ')'
    elif core.get(key, {}).get('failed') and not core[key]['core_failed']:
        cls = 'B1'
        why = 'el núcleo compila; solo fallan los archivos de la interfaz (diálogos, ventanas)'
    else:
        cls = 'B2'
        why = {
            'link': 'compila, pero usa funciones de Win32 que la capa no tiene',
            'deps': 'necesita dependencias que no vienen en el repositorio',
            'cfgfail': 'no compila: necesita un port',
        }.get(result, 'no compila: necesita un port')
        if wide:
            why += '; usa wchar_t (TCHAR Unicode)'
        if symbols:
            why += '; faltan: ' + ', '.join(symbols)
    e['class'], e['reason'] = cls, why
    lic = e['license']
    if not e['repo'] or lic == 'NOASSERTION':
        e['redist'] = 'revisar'
    elif lic is None:
        e['redist'] = 'no (sin licencia declarada)'
    else:
        e['redist'] = f'sí ({lic})'
    catalog.append(e)

json.dump(catalog, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(collections.Counter(e['class'] for e in catalog))
