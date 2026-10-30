#!/usr/bin/env python3
# This file is part of Edita.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# core.py <carpeta try/> <core.json>: de cada compilación de prueba, qué archivos
# fallaron y si alguno es del «núcleo» (no es de interfaz). Un archivo es de interfaz
# si su nombre lo dice (diálogos, paneles, ventanas, la plantilla de N++…) o si todos
# sus errores son de la API de ventanas, GDI o diálogos de Win32.
import json
import os
import re
import sys

UI_NAME = re.compile(r'(dlg|dialog|about|dock|window|wnd|panel|toolbar|static|resource|^ui|view|tree|'
                     r'list|tab|menu|colou?r|font|splitter|config|option|setting|pref|form|ctrl|control|'
                     r'button|edit|combo|tooltip|theme|dpi|icon|image|bitmap|gui|hwnd|subclass|hook)', re.I)
UI_API = re.compile(r'^(Set|Get|Show|Move|Update|Invalidate|Enable|Destroy|Create|Def|Is|Load|Draw|Fill|'
                    r'Select|Delete|Release|Begin|End|Screen|Client|Track|Register|Unregister|Send|Post|'
                    r'Check|Map|Adjust|Redraw|Bring|Open|Close|Empty|Track)?'
                    r'.*(Window|Wnd|Dlg|Dialog|Focus|Cursor|DC|Text|Color|Brush|Pen|Font|Bitmap|Icon|Menu|'
                    r'Rect|Item|Clipboard|Caret|Object|Proc|Timer|Theme|Dpi|Paint|Capture|Message|Pos|Box)'
                    r'|^(WM|BM|BST|SW|WS|GWL|GWLP|DS|SS|LB|LBN|CB|CBN|EM|EN|BN|TCN|TCM|TVM|TVN|TVI|TVS|LVM|LVN|LVS|LVCF|LVIF|'
                    r'NM|TBN|TB|TTM|TTS|TTF|IDC|IDI|IMAGE|LR|COLOR|SM|SWP|HWND|MF|TPM|DT|PS|SRCCOPY|DLGC|VK|MK)_'
                    r'|^(LPNMHDR|NMHDR|HBRUSH|HFONT|HBITMAP|HICON|HCURSOR|HMENU|HGDIOBJ|PAINTSTRUCT|LOGFONT|'
                    r'RECT|POINT|SIZE|DLGTEMPLATE|LPDLGTEMPLATE|pMyDlgTemplate|pDlgTemplate|hDialogRC|'
                    r'TCITEM|TVITEM|LVITEM|LVCOLUMN|TOOLINFO|INITCOMMONCONTROLSEX|InitCommonControlsEx|'
                    r'WNDCLASS|WNDCLASSEX|MSG|CREATESTRUCT|DRAWITEMSTRUCT|LPDRAWITEMSTRUCT|MINMAXINFO|'
                    r'RGB|GetRValue|GetGValue|GetBValue|MAKEINTRESOURCE|LOWORD|HIWORD|WS_EX_LAYOUTRTL)$')
FAILED = re.compile(r'^FAILED: .*?/code/(\S+?)\.o\b', re.M)
ERROR = re.compile(r"/code/([^:]+):\d+:\d+: error: (?:'(?:::)?([A-Za-z_][A-Za-z_0-9]*)'.*)?")

out = {}
root = sys.argv[1]
for d in sorted(os.listdir(root)):
    log_path = os.path.join(root, d, 'build.log')
    if not os.path.exists(log_path):
        continue
    log = open(log_path, errors='replace').read()
    failed = sorted(set(FAILED.findall(log)))
    # errores por archivo (el que aparece en la línea, sea .cpp o .h)
    by_file = {}
    for m in ERROR.finditer(log):
        by_file.setdefault(m.group(1), []).append(m.group(2))
    core = []
    for f in failed:
        name = os.path.basename(f)
        if UI_NAME.search(name):
            continue
        ids = [i for i in by_file.get(f, []) if i]
        others = [i for i in by_file.get(f, []) if not i]
        if ids and not others and all(UI_API.search(i) for i in ids):
            continue
        core.append(f)
    out[d] = {'failed': len(failed), 'core_failed': core}
json.dump(out, open(sys.argv[2], 'w'), indent=0)
n = sum(1 for v in out.values() if v['failed'] and not v['core_failed'])
print(f'{n} compilaciones fallidas con el núcleo intacto')
