# Auditoría de la lista oficial de plugins de Notepad++

Fecha: 2026-10-30 · Lista: [`nppPluginList/src/pl.x64.json`](https://github.com/notepad-plus-plus/nppPluginList/blob/master/src/pl.x64.json) · SDK: `plugin-sdk/` de Edita en la fase 49 y, repetida, en la [fase 51](https://github.com/alktrip/edita/blob/main/docs/fase51.md) (modo Unicode y Win32 sin ventanas)

**Pregunta:** ¿cuántos plugins de Notepad++ se pueden recompilar para Edita y distribuir desde este repositorio?

**Respuesta corta:** todavía muy pocos, y ya se sabe por qué. Con el SDK de la fase 49, solo compilaban 3 de los 136 plugins nativos (C/C++) con código. En 118 de los 133 que fallaban, el problema era `wchar_t`: la API de plugins de N++ es Unicode desde la 8.0, y la capa usaba `TCHAR = char`. La [fase 51](https://github.com/alktrip/edita/blob/main/docs/fase51.md) agregó el modo Unicode y la parte de Win32 que no necesita ventanas. Con eso, **compilan 7** (5 de ellos no están ya en Edita), y en otros 4 compila todo salvo la interfaz. Lo que frena a casi todos los demás son las **ventanas**: las clases de la plantilla de N++ (`Window`, `StaticDialog`, `DockingDlgInterface`), los diálogos de los `.rc`, USER32 y GDI.

| SDK de Edita | A (compila) | B1 (falta la interfaz) | B2 (port) |
|---|---:|---:|---:|
| Fase 49 | 2 | 2 | 103 |
| Fase 51 | **5** | **4** | 98 |

De los 98 de la clase B2 con el SDK de la fase 51:

- 68 tropiezan sobre todo con ventanas, diálogos, recursos y GDI;
- 15 usan COM;
- 14 necesitan dependencias que no vienen en su repositorio.

| | Plugins |
|---|---:|
| Nativos (C/C++) que se podrían traer con una capa de compatibilidad más completa (B2) | 98, de ellos 71 con una licencia que permite redistribuirlos |
| Escritos en .NET o Delphi: solo reescribiéndolos (C) | 58 |
| Sin código o sin revisar (D, R) | 22 |
| Ya cubiertos por Edita (E) | 38 |

Ver las [conclusiones](#conclusiones).

## Método

Cada plugin de la lista pasó por cinco pasos. Las herramientas están en [`tools/`](tools/) y se repiten con `EDITA_SRC=../editor audit/tools/run-audit.sh <carpeta>`.

1. **Metadatos** (`fetch.py`): a partir del repositorio de GitHub que la lista da como `repository` u `homepage`, se obtienen:
   - la licencia (SPDX), los lenguajes y la fecha del último cambio;
   - si el repositorio está archivado;
   - la lista de archivos.

   Los 19 plugins alojados fuera de GitHub (SourceForge, GitLab, webs propias) se revisaron a mano.
2. **Código fuente**: se descargó el código de los plugins que no son de .NET ni de Delphi, en su rama principal. Los repositorios con submódulos se clonaron con ellos.
3. **Análisis del código** (`scan.py`, `dialogs.py`). Se cuentan:
   - los diálogos de recursos (`DIALOG`/`DIALOGEX` en los `.rc`);
   - el uso de MFC, de COM/ATL y de ventanas Win32 propias (`CreateWindowEx`, `RegisterClass`).

   No se cuentan los archivos de la plantilla de plugins de N++ (`StaticDialog`, `DockingDlgInterface`…), que casi todos traen aunque no los usen.
4. **Compilación de prueba** (`trybuild.sh`), con la capa de compatibilidad de Edita (`plugin-sdk/compat`):
   - un `CMakeLists.txt` genérico compila todas las fuentes del plugin con `edita_npp_plugin()` y enlaza con `-Wl,--no-undefined`. Así, una función de Win32 que falte da un error en vez de pasar inadvertida;
   - antes de compilar, `normalize.py` corrige lo que una receta arreglaría de forma mecánica: rutas con `\` en los `#include` y mayúsculas distintas (`TCHAR.h` → `tchar.h`);
   - cada cabecera de Windows que no existe se crea **vacía** y se vuelve a compilar. Si el plugin compila así, no usaba esa API; si la usaba, falla después con «not declared». La lista de esas cabeceras forma el [backlog del SDK](#backlog-del-sdk).

   El código descargado solo se compila: nunca se ejecuta y no se usan sus scripts de compilación.
5. **Clasificación** (`classify.py`): el resultado completo está en [`catalog.json`](catalog.json).

### Clases

| Clase | Criterio | Qué implica para el catálogo |
|---|---|---|
| **A** | Compila y enlaza con la capa de compatibilidad, con como mucho un diálogo (el «Acerca de»), sin ventanas Win32 propias ni MFC | Receta de pocas líneas, como la de MIME Tools. Candidato directo |
| **B1** | Compila y enlaza, pero tiene diálogos o ventanas Win32; o no compila, pero solo fallan los archivos de interfaz (por su nombre, o porque todos sus errores son de la API de ventanas: `core.py`) | Las órdenes funcionan, pero sus diálogos muestran el aviso de «no disponible». Hay que portar la interfaz a Qt, como se hizo con XML Tools |
| **B2** | No compila o no enlaza con la capa actual | Port de verdad: depende de APIs de Win32 que la capa no tiene (las más comunes están en el backlog) o de bibliotecas que no vienen en el repositorio |
| **C** | Escrito en .NET (C#), Delphi u otra tecnología de Windows | No se recompila: habría que reescribirlo entero |
| **D** | Sin código fuente publicado | Imposible |
| **R** | Fuera de GitHub, sin revisar | Revisión manual pendiente |
| **E** | Edita ya ofrece la función (port incluido o función nativa) | No hace falta traerlo |

Para **redistribuir un binario** también hace falta una licencia que lo permita. «Sin licencia declarada» significa que todos los derechos son del autor: no se puede publicar un binario sin su permiso, aunque el código esté en GitHub.

## Resultados

<!-- tablas: generadas con tools/render.py (SDK de la fase 51) -->

Lista analizada: `pl.x64.json` versión 1.9.9, 225 plugins.

| Clase | Qué significa | Plugins | Con licencia que permite redistribuir |
|---|---|---:|---:|
| A | Compila sin cambios | 5 | 5 |
| B1 | Compila; hay que portar su interfaz | 4 | 2 |
| B2 | No compila: necesita un port | 98 | 71 |
| C | Tecnología exclusiva de Windows: reescribir | 58 | 34 |
| D | Sin código fuente | 15 | 1 |
| R | Fuera de GitHub: revisar a mano | 7 | 0 |
| E | Ya cubierto por Edita | 38 | 30 |
| | **Total** | **225** | **143** |

### A. Compila sin cambios (5)

| Plugin | Versión | Licencia | Lenguaje | Líneas | Diálogos | Detalle |
|---|---|---|---|---:|---:|---|
| [NppPluginOpenHost](https://github.com/jejemorg/NppPluginOpenHost) | 1.1.0.0 | sí (Apache-2.0) | C | 2687 | 0 | compila con la capa de compatibilidad; como mucho pierde el «Acerca de» |
| [Reverse Lines](https://github.com/querykuma/qkNppReverseLines) | 1.0.0.0 | sí (GPL-3.0) | C | 4417 | 0 | compila con la capa de compatibilidad; como mucho pierde el «Acerca de» |
| [Select N' Launch](https://github.com/npp-plugins/selectnlaunch) | 2.2 | sí (GPL-2.0) | C++ | 4157 | 1 | compila con la capa de compatibilidad; como mucho pierde el «Acerca de» |
| [Simplify Json](https://github.com/analystvipul/SimplifyJson) | 1.0.1 | sí (GPL-2.0) | C++ | 3756 | 0 | compila con la capa de compatibilidad; como mucho pierde el «Acerca de» |
| [TidyText](https://github.com/gonzalu/TidyText) | 1.2.0.0 | sí (GPL-2.0) | C++ | 4730 | 0 | compila con la capa de compatibilidad; como mucho pierde el «Acerca de» |

### B1. Compila; hay que portar su interfaz (4)

| Plugin | Versión | Licencia | Lenguaje | Líneas | Diálogos | Detalle |
|---|---|---|---|---:|---:|---|
| [Notepad++ bplist plugin](https://github.com/azerg/NppBplistPlugin) | 3.0.0.0 | sí (BSD-3-Clause) | C++ | 2536 | 1 | el núcleo compila; solo fallan los archivos de la interfaz (diálogos, ventanas) |
| [NppJumpList](https://github.com/chcg/JumpList) | 1.2.2 | no (sin licencia declarada) | C++ | 5461 | 2 | el núcleo compila; solo fallan los archivos de la interfaz (diálogos, ventanas) (COM) |
| [NX ASCII Database Helper](https://github.com/ZhuXuefengGitHub/NX_ASCII_Database_Helper) | 3.0.0 | no (sin licencia declarada) | C | 6420 | 2 | el núcleo compila; solo fallan los archivos de la interfaz (diálogos, ventanas) |
| [SelectQuotedText](https://github.com/ffes/selectquotedtext) | 1.1.0 | sí (GPL-2.0) | C | 5621 | 1 | el núcleo compila; solo fallan los archivos de la interfaz (diálogos, ventanas) |

### B2. No compila: necesita un port (98)

| Plugin | Versión | Licencia | Lenguaje | Líneas | Diálogos | Detalle |
|---|---|---|---|---:|---:|---|
| [AndroidLogger](https://github.com/glandon/AndroidLogger) | 1.4.3.4 | no (sin licencia declarada) | C++ | 4842 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: STDMETHODIMP, REBARBANDINFO, WNDCLASSEX, pAccess, s_, BITMAPINFOHEADER |
| [Auto Detect Indention](https://github.com/Chocobo1/nppAutoDetectIndent) | 2.3 | sí (GPL-3.0) | C++ | 4631 | 1 | no compila: necesita un port; faltan: Sci_TextRange, SCI_GETTEXTRANGE, textRange |
| [BAT Path IntelliSense](https://github.com/nicehero/NppBatPathIntelliSense) | 0.1.0 | no (sin licencia declarada) | C++ | 5096 | 0 | no compila: necesita un port; faltan: DefWindowProcW, WNDCLASSEXW, windowClass, RegisterClassExW, HWND_MESSAGE, CreateWindowExW (ventanas Win32) |
| [BetterMultiSelection](https://github.com/dail8859/BetterMultiSelection) | 1.5 | sí (GPL-2.0) | C | 9693 | 1 | no compila: necesita un port; faltan: GWLP_WNDPROC, SetWindowLongPtr, CallWindowProc, hook, GetProp, RemoveProp |
| [BigFiles - Open Very Large Files](https://github.com/superolmo/BigFiles) | 0.1.3 | sí (GPL-2.0) | C | 6196 | 2 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: IMAGE_BITMAP, LR_DEFAULTSIZE, LR_LOADMAP3DCOLORS, COINIT_APARTMENTTHREADED, COINIT_DISABLE_OLE1DDE, CoInitializeEx (COM) |
| [Blitz Search](https://github.com/Natestah/BlitsNppPlugin) | 1.0.0.6 | sí (GPL-3.0) | C | 3274 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: SHGetKnownFolderPath, CreateThread, MEM_RESERVE, MEM_COMMIT, PAGE_READWRITE, VirtualAlloc |
| [Bunyan Log Viewer](https://github.com/jayapalb/notepad-bunyan-plugin) | 1.0.0 | no (sin licencia declarada) | C++ | 1409 | 0 | no compila: necesita un port; faltan: WS_CHILD, WS_VISIBLE, WNDCLASSW, windowClass, IDC_ARROW, COLOR_WINDOW (ventanas Win32) |
| [Chinese Converter](https://github.com/lkk9898969/Npp_ChineseConverter) | 1.0.3 | sí (GPL-3.0) | C++ | 5953 | 0 | necesita dependencias que no vienen en el repositorio; usa wchar_t (TCHAR Unicode); faltan: uintmax_t, uint64_t, PyObject, intmax_t, UINT32_MAX, vsnprintf |
| [CollectionInterface](https://github.com/pryrt/NppPlugin-CollectionInterface) | 1.3.0 | sí (GPL-3.0) | C++ | 32724 | 5 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: PS_SOLID, InternetCloseHandle, hConnect, PBM_SETPOS, hInternet, DLGTEMPLATE (ventanas Win32) |
| [Columns++](https://github.com/Coises/ColumnsPlusPlus) | 1.3.3 | sí (GPL-3.0) | C++ | 264691 | 19 | necesita dependencias que no vienen en el repositorio; usa wchar_t (TCHAR Unicode); faltan: SendDlgItemMessage, EDITBALLOONTIP, ebt, TTI_NONE, EM_SHOWBALLOONTIP, WM_NEXTDLGCTL (ventanas Win32) |
| [ColumnTools](https://github.com/vinsworldcom/nppColumnTools) | 1.4.5.1 | no (sin licencia declarada) | C | 4280 | 1 | no compila: necesita un port; faltan: GET_X_LPARAM, MF_CHECKED, MoveToEx, LineTo, CallWindowProc, GET_Y_LPARAM |
| [Comment Toggler](https://github.com/ScienceDiscoverer/CommentToggler) | 1.0.0.0 | sí (GPL-3.0) | C++ | 4322 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: MEM_RELEASE, VirtualFree, MEM_RESERVE, MEM_COMMIT, PAGE_READWRITE, VirtualAlloc |
| [Compose](https://github.com/Coises/Compose-for-NotepadPlusPlus) | 1.1.1 | sí (GPL-3.0) | C++ | 38368 | 2 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: _dialog, MapWindowPoints, MONITOR_DEFAULTTOPRIMARY, GetMonitorInfo, GetWindowTextLength, GetWindowText (COM) |
| [Datamodder File Tools](https://github.com/dm-utils/filetools) | 1.3.1.7 | sí (MIT) | C++ | 2439 | 7 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: GetParent, MF_BYPOSITION, OPENFILENAMEW, ofn, LB_GETCURSEL, LB_ERR |
| [Datamodder Query Files](https://github.com/dm-utils/queryfiles) | 1.3.1.4 | sí (MIT) | C++ | 2907 | 6 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: SetFocus, GetParent, GetDlgItemTextW, LB_GETCURSEL, LB_ERR, INITCOMMONCONTROLSEX (ventanas Win32) |
| [Datamodder SQL Formatter](https://github.com/dm-utils/formatsql) | 1.3.2.18 | sí (MIT) | C++ | 5156 | 12 | necesita dependencias que no vienen en el repositorio; faltan: IsDlgButtonChecked, GetParent, BN_CLICKED, OPENFILENAMEW, ofn, MF_BYPOSITION |
| [Discord Rich Presence](https://github.com/Zukaritasu/notepadpp_rpc) | 2.1.711.1 | sí (GPL-3.0) | C++ | 31117 | 1 | necesita dependencias que no vienen en el repositorio; faltan: criticalSection, INFINITE, WAIT_OBJECT_0, LPTHREAD_START_ROUTINE, CreateWaitableTimer, SetWaitableTimer (ventanas Win32) |
| [DoxyIt](https://github.com/dail8859/DoxyIt) | 0.4.4 | sí (GPL-2.0) | C++ | 10049 | 3 | no compila: necesita un port; faltan: Sci_TextRange, SCI_SETLEXERLANGUAGE, SCI_LOADLEXERLIBRARY, Sci_TextToFind, Sci_RangeToFormat, SCI_GETSTYLEDTEXT |
| [DSpellCheck](https://github.com/Predelnik/DSpellCheck) | 1.5.0 | sí (GPL-2.0) | C++ | 16855 | 11 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: TextPosition, IsCharAlphaNumeric, BN_CLICKED, s, Edit_SetText, GWLP_USERDATA (COM, ventanas Win32) |
| [Dual Scrollbars](https://github.com/SaiyajinK/Dual-Scrollbars-for-Notepad-Plus-Plus) | 1.1.0 | no (sin licencia declarada) | C++ | 2529 | 0 | no compila: necesita un port; faltan: INT_MIN, SCROLLINFO, WM_MOUSEHWHEEL, GET_X_LPARAM, GET_Y_LPARAM, IDC_ARROW (ventanas Win32) |
| [EditorConfig](https://github.com/editorconfig/editorconfig-notepad-plus-plus) | 0.4.0 | sí (GPL-2.0) | C++ | 3844 | 0 | no compila: necesita un port; faltan: fileName, NM_CLICK, NM_RETURN, PNMLINK, LITEM, item |
| [ElasticTabstops](https://github.com/mariusv-github/ElasticTabstops) | 1.5.0 | sí (GPL-2.0) | C++ | 10067 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: __max, GetMenu, MF_ENABLED, MF_GRAYED, EnableMenuItem, GWLP_WNDPROC |
| [Emoji Description](https://github.com/Ruberoid/npp_emoji_description) | 0.4.17 | sí (GPL-2.0) | C++ | 6045 | 2 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: DLGTEMPLATE, GWLP_USERDATA, BM_GETCHECK, BM_SETCHECK, WS_EX_LAYOUTRTL, g_fail |
| [Fixed-width Data Visualizer](https://github.com/shriprem/FWDataViz) | 2.6.7.0 | sí (GPL-3.0) | C++ | 21528 | 10 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: LB_ERR, USER_DEFAULT_SCREEN_DPI, LB_SETCURSEL, LOGFONT, LB_ADDSTRING, EnableWindow (ventanas Win32) |
| [FixParser](https://github.com/chtaylo3/fix-parser) | 0.1.3 | sí (GPL-2.0) | C++ | 2335 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: nppData, pugi, PFUNCPLUGINCMD, ShortcutKey, SCNotification, NppData (ventanas Win32) |
| [GitHub Repo Viewer](https://github.com/ufoptg/GitHubRepoViewer) | 1.1 | sí (AGPL-3.0) | C | 4568 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: hSession, TVIF_PARAM, hConnect, WinHttpCloseHandle, TVI_ROOT, TVITEMW (ventanas Win32) |
| [GotoLineCol](https://github.com/shriprem/Goto-Line-Col-NPP-Plugin) | 2.4.5.1 | sí (GPL-3.0) | C++ | 11997 | 3 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: USER_DEFAULT_SCREEN_DPI, LOGFONT, GWL_STYLE, SetWindowTheme, MulDiv, REFKNOWNFOLDERID (ventanas Win32) |
| [HEX-Editor](https://github.com/chcg/NPP_HexEditor) | 0.9.14.0 | sí (GPL-2.0) | C++ | 21925 | 9 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: LOGFONT, LPINT, GWLP_USERDATA, BM_SETCHECK, LVIR_BOUNDS, BM_GETCHECK (ventanas Win32) |
| [HiddenLexers](https://github.com/pryrt/NppPlugin-HiddenLexers) | 1.0.0 | sí (GPL-3.0) | C++ | 30710 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: PS_SOLID, GWLP_WNDPROC, SetWindowLongPtr, CallWindowProc, GetParent, GetProp |
| [HLASM Lexer - Column-Aware Syntax Highlighting](https://github.com/Zaneham/hlasm-npp) | 1.1.1 | sí (Apache-2.0) | C++ | 535 | 0 | no compila: necesita un port; faltan: _stricmp, kConfigXml |
| [HTML Tag](https://github.com/rdipardo/nppHTMLTag) | 1.6.1.0 | sí (MPL-2.0) | C++ | 4239 | 52 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: NppData, FuncItem, ShortcutKey, LangType, PFUNCPLUGINCMD, _hSelf |
| [Indent By Fold](https://github.com/ffes/indentbyfold) | 0.7.3 | sí (GPL-2.0) | C | 3842 | 0 | no compila: necesita un port; faltan: GWLP_WNDPROC, SetCursor, SetWindowLongPtrW, IDC_WAIT, LoadCursor, Sci_TextRange |
| [Input Sequence](https://github.com/dasu88/NPPInputSequence) | 1.5.2.0 | no (sin licencia declarada) | C++ | 410 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: LLONG_MAX, ULLONG_MAX, GetWindowTextW, CreateWindowExW, LLONG_MIN, CW_USEDEFAULT (ventanas Win32) |
| [Java Plugin](https://github.com/dominikcebula/npp-java-plugin) | 0.4.1 | sí (GPL-2.0) | C | 7034 | 2 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: PROCESS_INFORMATION, DLGTEMPLATE, BM_GETCHECK, BM_SETCHECK, piProcInfo, consoleLogger |
| [jN Notepad++ Plugin](https://github.com/sieukrem/jn-npp-plugin) | 2.2.190.21986 | no (sin licencia declarada) | C | 36429 | 0 | necesita dependencias que no vienen en el repositorio; usa wchar_t (TCHAR Unicode); faltan: interface, BSTR, EXTERN_C, m_Str, RPC_IF_HANDLE, c (COM, ventanas Win32) |
| [JSON Viewer](https://github.com/NPP-JSONViewer/JSON-Viewer) | 2.2.0.0 | sí (MIT) | C++ | 7365 | 3 | necesita dependencias que no vienen en el repositorio; usa wchar_t (TCHAR Unicode); faltan: uintmax_t, uint64_t, intmax_t, int64_t, Duration, uint_fast64_t (ventanas Win32) |
| [JSTool](https://github.com/sunjw/jstool) | 25.11.16 | sí (GPL-2.0) | JavaScript | 11766 | 3 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: TVITEM, GWLP_USERDATA, CheckDlgButton, DLGTEMPLATE, LPTVHITTESTINFO, buf |
| [Language Selector](https://github.com/hassaine-abdellah/npp-language-selector) | 1.2.0.0 | sí (MIT) | C++ | 4655 | 2 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: CB_GETITEMDATA, DeleteObject, SelectObject, CreateSolidBrush, CB_ADDSTRING, CB_SETITEMDATA (ventanas Win32) |
| [LDAP Formatter](https://github.com/ignaciojulio/npp-ldap-formatter) | 1.0.0 | sí (MIT) | C++ | 5469 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: sptr_t, NppData, uptr_t, SCNotification, SCI_GETSTATUS, Sci_Position (ventanas Win32) |
| [LLM Assistant](https://github.com/Gvo87/NotepadPlusPlus-LLM-Plugin) | 1.2 | no (sin licencia declarada) | C++ | 2226 | 2 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: IsWindow, KillTimer, InternetCloseHandle, connection, GetDlgItemText, RegQueryValueEx (ventanas Win32) |
| [LuaScript](https://github.com/dail8859/LuaScript) | 0.12 | sí (GPL-2.0) | C | 39256 | 2 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: DLGTEMPLATE, SetWindowLongPtr, SetFocus, GWLP_WNDPROC, GetWindowLongPtr, CallWindowProc |
| [Markdown Features](https://github.com/0langa/npp-markdown-features) | 1.0.1 | sí (MIT) | C++ | 7497 | 0 | necesita dependencias que no vienen en el repositorio; usa wchar_t (TCHAR Unicode); faltan: WS_CHILD, cmark_parser_free, TVIF_PARAM, WS_VISIBLE, GWLP_USERDATA, cmark_node (ventanas Win32) |
| [Markdown Table Editor](https://github.com/krotname/NppMarkdownTableEditor) | 11.2.0 | sí (GPL-3.0) | C++ | 15854 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: DLGTEMPLATE, GWLP_USERDATA, CREATESTRUCT, WS_VISIBLE, BM_GETCHECK, info (ventanas Win32) |
| [Markdown with Mermaid](https://github.com/rhyots/Markdown_with_Mermaid) | 1.4.1 | sí (MIT) | JavaScript | 2986 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: image, view, IID, KillTimer, SetTimer, guid (ventanas Win32) |
| [MultiReplace](https://github.com/daddel80/notepadpp-multireplace) | 6.2.0.38 | sí (GPL-3.0) | C++ | 99634 | 3 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: IsDlgButtonChecked, InvalidateRect, MulDiv, HHOOK, IsWindow, POINTL (COM, ventanas Win32) |
| [MZC8051](https://github.com/Jiangshan00001/npp_MZC8051) | 0.0.1 | sí (GPL-3.0) | C | 5927 | 1 | no compila: necesita un port; faltan: DLGTEMPLATE, GWLP_USERDATA, WS_EX_LAYOUTRTL, RT_DIALOG, pDlgTemplate, pMyDlgTemplate |
| [NestedDSV Data Visualizer](https://github.com/shriprem/NestedDSV) | 1.1.0.1 | sí (GPL-3.0) | C++ | 20988 | 10 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: LB_ERR, USER_DEFAULT_SCREEN_DPI, LB_SETCURSEL, LOGFONT, LB_ADDSTRING, EnableWindow (ventanas Win32) |
| [NotepadStarterPlugin](https://github.com/lygstate/NotepadStarter) | 2.3.3.0 | revisar | C++ | 5366 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: m_tnd, Shell_NotifyIcon, STARTUPINFO, si, PROCESS_INFORMATION, oProcessInfo (ventanas Win32) |
| [Npp Converter](https://github.com/npp-plugins/converter) | 4.7 | revisar | C++ | 5547 | 1 | no compila: necesita un port; faltan: DLGTEMPLATE, GWLP_USERDATA, WS_EX_LAYOUTRTL, RT_DIALOG, pDlgTemplate, pMyDlgTemplate |
| [Npp Highlighter](https://github.com/michaelxzhang/Npp-Highlighter) | 1.0.0.1 | no (sin licencia declarada) | C | 38732 | 0 | necesita dependencias que no vienen en el repositorio; usa wchar_t (TCHAR Unicode); faltan: interface, BSTR, EXTERN_C, m_Str, RPC_IF_HANDLE, c (COM, ventanas Win32) |
| [NppAIAssistant](https://github.com/pingqLIN/NppAIAssistant) | 0.2.0.6 | revisar | C++ | 13557 | 6 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: CB_ADDSTRING, CB_SETCURSEL, CB_RESETCONTENT, CB_GETCURSEL, BN_CLICKED, CBN_SELCHANGE (ventanas Win32) |
| [NppCrossCheck](https://github.com/pablo-code14/NppCrossCheck) | 1.3.0.0 | sí (GPL-2.0) | C++ | 6963 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: DLGTEMPLATE, GWLP_USERDATA, BM_GETCHECK, BM_SETCHECK, WS_EX_LAYOUTRTL, SPI_GETWORKAREA |
| [NppCrypt](https://github.com/chcg/nppcrypt) | 1.0.1.6 | no (sin licencia declarada) | C++ | 170206 | 15 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: byte, Encoding, EOL, BM_GETCHECK, options, Hash (ventanas Win32) |
| [NppEventExec](https://github.com/MIvanchev/NppEventExec) | 0.9.0 | sí (GPL-3.0) | C | 11246 | 4 | necesita dependencias que no vienen en el repositorio; faltan: MF_BYCOMMAND, MF_GRAYED, EnableMenuItem (ventanas Win32) |
| [NppExport](https://github.com/chcg/NPP_ExportPlugin) | 0.4.0.0 | no (sin licencia declarada) | C | 3565 | 0 | no compila: necesita un port; faltan: OPENFILENAME, ofi, OFN_CREATEPROMPT, OFN_EXPLORER, OFN_OVERWRITEPROMPT, GetSaveFileName |
| [NppFavorites](https://github.com/heldersepu/nppfavorites) | 1.0.0.1 | no (sin licencia declarada) | C | 3382 | 0 | no compila: necesita un port; faltan: DLGTEMPLATE, GWLP_USERDATA, WS_EX_LAYOUTRTL, SCI_GETTEXTRANGE, IsCharAlphaNumeric, RT_DIALOG |
| [NppFoldTail](https://github.com/seantw/NppFoldTail) | 0.9.0 | sí (MIT) | C++ | 1186 | 0 | no compila: necesita un port; faltan: InvalidateRect, DeleteObject, tool, DefSubclassProc, IsWindow, TTM_DELTOOLW (ventanas Win32) |
| [NppFTP](https://github.com/ashkulz/NppFTP) | 0.29.15 | no (sin licencia declarada) | C++ | 40515 | 13 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: SOCKET, POINTL, LPDATAOBJECT, SOCK_STREAM, LPFORMATETC, AF_INET (ventanas Win32) |
| [NppImagePreview](https://github.com/bdgeek/NppImagePreview) | 1.0.0 | sí (MIT) | C++ | 2849 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: IWICBitmapSource, WICPixelFormatGUID, IWICImagingFactory, m_pFactory, DeleteObject, IWICBitmapDecoder (COM, ventanas Win32) |
| [NppMenuScripts](https://github.com/seantw/NppMenuScripts) | 1.0.5.0 | sí (MIT) | C++ | 5476 | 0 | necesita dependencias que no vienen en el repositorio (ventanas Win32) |
| [NppNetNote](https://github.com/chcg/NppDocShare) | 0.2.0.0 | sí (GPL-2.0) | C++ | 8715 | 1 | no compila: necesita un port; faltan: SOCKET, WSAGetLastError, hostent, LPTHREAD_START_ROUTINE, pHandle, _outputSection |
| [NppOpenAI](https://github.com/Krazal/nppopenai) | 0.5.0.0 | sí (GPL-2.0) | C++ | 41264 | 2 | necesita dependencias que no vienen en el repositorio; usa wchar_t (TCHAR Unicode); faltan: DLGTEMPLATE, PBM_SETMARQUEE, HWND_TOPMOST, BM_GETCHECK, BM_SETCHECK, GWLP_USERDATA |
| [NppRestoreCursorPosition](https://github.com/RivieraSystems/NppRestoreCursorPosition) | 1.0.0 | sí (MIT) | C++ | 3819 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: MOVEFILE_WRITE_THROUGH, MENUITEMINFOW, info, MIIM_STRING, SYNCHRONIZE, PROCESS_INFORMATION (ventanas Win32) |
| [NppS3](https://github.com/bsy0318/NppS3) | 1.0.0 | no (sin licencia declarada) | C++ | 16196 | 4 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: Gdiplus, CB_SETCURSEL, CB_GETCURSEL, TVIF_PARAM, TVIF_CHILDREN, GWLP_USERDATA (COM, ventanas Win32) |
| [NppStripIpAndHost](https://github.com/larreblarsson/NppStripIpAndHost) | 1.0.0 | sí (GPL-2.0) | C++ | 5632 | 1 | no compila: necesita un port; faltan: EXTERN_C, IDC_WAIT, LoadCursor, SetCursor, CheckDlgButton, IsDlgButtonChecked |
| [NppTextFX2](https://github.com/rainman74/NPPTextFX2) | 2.0.3 | sí (GPL-3.0) | C++ | 25552 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: EXTERNC, edt1, stc1, BM_GETCHECK, memicmp, EnableWindow |
| [NppTextViz](https://github.com/chcg/NppTextViz) | 0.4.3 | sí (GPL-2.0) | C++ | 4688 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: CString, cstrSequence, DLGTEMPLATE, GWLP_USERDATA, GetDlgItemInt, GetWindowTextLength (COM) |
| [NppTranslator](https://github.com/AndyDL24/PluginTranslateNPP) | 1.0.0.0 | sí (GPL-3.0) | C++ | 6503 | 4 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: hConnect, GWLP_USERDATA, hSession, hRequest, MIIM_FTYPE, CB_RESETCONTENT (COM) |
| [NppVim](https://github.com/h-jangra/NppVim) | 1.14.4.0 | sí (MIT) | C++ | 20656 | 2 | no compila: necesita un port; faltan: HKL, IsWindow, CallWindowProc, DeleteObject, targetLayout, DrawModernButton |
| [NppZenHankaku](https://github.com/RivieraSystems/NppZenHankaku) | 1.0.0 | sí (MIT) | C++ | 4828 | 0 | no compila: necesita un port; faltan: info, SIZE_MAX, ii, CPINFO, MAX_LEADBYTES, IMAGE_ICON |
| [NWScript Tools](https://github.com/Leonard-The-Wise/NWScript-Npp) | 1.2.0.2300 | sí (GPL-3.0) | C++ | 69223 | 12 | no compila: necesita un port (COM, ventanas Win32) |
| [OCaml Lexer](https://github.com/Zaneham/ocaml-npp) | 1.0.0 | sí (Apache-2.0) | C++ | 807 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: _stricmp, CreatePipe, HANDLE_FLAG_INHERIT, SetHandleInformation, STARTUPINFOW, si |
| [Open File In Solution](https://github.com/incrediblejr/nppplugins) | 3.0.1 | no (sin licencia declarada) | C++ | 40783 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: BOOL, __END_DECLS, __BEGIN_DECLS, mbstate_t, __c_locale, size_t (ventanas Win32) |
| [Papyrus Script Lexer](https://github.com/blu3mania/npp-papyrus) | 1.2.2.354 | sí (GPL-3.0) | C++ | 8507 | 9 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: GWLP_USERDATA, Sci_CharacterRange, _locale_t, GWL_STYLE, BM_GETCHECK, DLGTEMPLATE (ventanas Win32) |
| [Pork to Sausage](https://github.com/npp-plugins/pork2sausage) | 2.6 | sí (GPL-2.0) | C++ | 4539 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: EVENT_ALL_ACCESS, STILL_ACTIVE, FORMAT_MESSAGE_ALLOCATE_BUFFER, FORMAT_MESSAGE_FROM_SYSTEM, FORMAT_MESSAGE_IGNORE_INSERTS, LANG_NEUTRAL |
| [pycalc](https://github.com/pycalc-plugin/notepad-plus-plus) | 1.0.0 | sí (Apache-2.0) | C++ | 3412 | 1 | no compila: necesita un port; faltan: Py_DECREF, PyObject, jthread, KillTimer, RegCloseKey, PyThreadState |
| [RAScript](https://github.com/joshraphael/npp-rascript) | 0.4.1 | sí (MIT) | C++ | 214421 | 70 | necesita dependencias que no vienen en el repositorio; usa wchar_t (TCHAR Unicode); faltan: module, perl_matcher, match_results, m, regex, wregex (COM, ventanas Win32) |
| [RestApiToText](https://github.com/eljefe7000/RestApiToText) | 1.4.0.1 | sí (GPL-3.0) | C++ | 3475 | 2 | no compila: necesita un port; faltan: HINTERNET, INTERNET_DEFAULT_HTTPS_PORT, NM_CLICK, NM_RETURN, PNMLINK, LITEM |
| [RGA ISA Compiler](https://github.com/DIMOSUS/NppRgaIsaPlugin) | 1.0.0.0 | sí (MIT) | C++ | 7810 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: DLGTEMPLATE, BM_GETCHECK, BM_SETCHECK, GWLP_USERDATA, HMONITOR, hMon (COM, ventanas Win32) |
| [Save as admin](https://github.com/Hsilgos/nppsaveasadmin) | 1.0.211 | no (sin licencia declarada) | C++ | 6389 | 2 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: append_new_ptr, GetFileType, PROC, DLGTEMPLATE, DoAll, ptr_to_fun_memory |
| [SecurePad](https://github.com/dominictobias/SecurePad) | 2.4 | sí (MIT) | C | 4925 | 1 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: DLGTEMPLATE, GetForegroundWindow, cryptkey, MEM_RELEASE, VirtualFree, GWLP_USERDATA |
| [Select to Clipboard](https://github.com/KubaDee/SelectToClipboard) | 1.0.3 | sí (GPL-2.0) | C | 3196 | 0 | no compila: necesita un port; faltan: CString, TextToClip, SCI_GETTEXTRANGE, GetMenu, MF_BYCOMMAND, MF_CHECKED (COM) |
| [Solution Hub](https://github.com/incrediblejr/nppplugins) | 3.0.1 | no (sin licencia declarada) | C++ | 40783 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: BOOL, __END_DECLS, __BEGIN_DECLS, mbstate_t, __c_locale, size_t (ventanas Win32) |
| [Solution Hub UI](https://github.com/incrediblejr/nppplugins) | 3.0.1 | no (sin licencia declarada) | C++ | 40783 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: BOOL, __END_DECLS, __BEGIN_DECLS, mbstate_t, __c_locale, size_t (ventanas Win32) |
| [Solution Tools](https://github.com/incrediblejr/nppplugins) | 3.0.1 | no (sin licencia declarada) | C++ | 40783 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: BOOL, __END_DECLS, __BEGIN_DECLS, mbstate_t, __c_locale, size_t (ventanas Win32) |
| [SpeechPlugin](https://github.com/chcg/SpeechPlugin) | 0.4.0.0 | sí (GPL-2.0) | C++ | 2700 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: mVoice, ISpVoice, converter, COINIT_APARTMENTTHREADED, CoInitializeEx, MF_BYCOMMAND (COM) |
| [SQL Column Highlighter](https://github.com/zhgao/npp-sql-column-highlighter) | 1.0.0.0 | sí (MIT) | C++ | 908 | 0 | no compila: necesita un port; faltan: Sci_TextRange, tr, SCI_GETTEXTRANGE |
| [StayAwake](https://github.com/shriprem/StayAwake_NPP_Plugin) | 1.5.0.0 | sí (GPL-3.0) | C++ | 7384 | 3 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: DLGTEMPLATE, INPUT, input, SendInput, SetWindowText, SetDlgItemInt (COM, ventanas Win32) |
| [SurroundSelection](https://github.com/dail8859/SurroundSelection) | 1.4.1 | sí (GPL-2.0) | C++ | 6785 | 1 | no compila: necesita un port; faltan: GWLP_WNDPROC, SetWindowLongPtr, hook, CallWindowProc, GetProp, RemoveProp |
| [Task List](https://github.com/Megabyteceer/npp-task-list) | 2.7 | no (sin licencia declarada) | C++ | 6714 | 2 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: USER_DEFAULT_SCREEN_DPI, LOGFONT, DLGTEMPLATE, GWLP_USERDATA, DPI_AWARENESS_CONTEXT, LR_DEFAULTCOLOR (ventanas Win32) |
| [TC Syslog Finder](https://github.com/bsagarzazu/npp-tc-syslog-finder) | 1.1.0 | sí (GPL-2.0) | C++ | 4169 | 0 | no compila: necesita un port; faltan: CompareFileTime, TIMERPROC, COINIT_APARTMENTTHREADED, COINIT_DISABLE_OLE1DDE, CoInitializeEx, IFileDialog (COM) |
| [Tortoise SVN](https://github.com/incrediblejr/nppplugins) | 3.0.1 | no (sin licencia declarada) | C++ | 40783 | 0 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: BOOL, __END_DECLS, __BEGIN_DECLS, mbstate_t, __c_locale, size_t (ventanas Win32) |
| [TreeSitter](https://github.com/Thorium/NppTreeSitter) | 1.4.3 | no (sin licencia declarada) | C++ | 4095 | 0 | necesita dependencias que no vienen en el repositorio; usa wchar_t (TCHAR Unicode); faltan: uintmax_t, intmax_t, Duration, SIZE_MAX, file_time_type, nano |
| [URL Encode/Decode Plugin](https://github.com/SinghRajenM/nppURLPlugin) | 1.2.0.0 | sí (GPL-2.0) | C++ | 2134 | 2 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: GWLP_USERDATA, DLGTEMPLATE, TCM_GETCURSEL, DRAWITEMSTRUCT, BM_GETCHECK, TCM_DELETEALLITEMS (ventanas Win32) |
| [Virtual Folders](https://github.com/FatihC/VirtualFolders) | 1.0.4 | sí (GPL-3.0) | C++ | 49298 | 5 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: MapWindowPoints, GetWindowTextLength, GetWindowText, MONITOR_DEFAULTTOPRIMARY, GetMonitorInfo, SetWindowText (ventanas Win32) |
| [VSCode Keymap NPP](https://github.com/14ag/vscode-to-notepadpp) | 0.2.0 | no (sin licencia declarada) | C++ | 4084 | 0 | no compila: necesita un port; faltan: GWLP_WNDPROC, g_messageHook, WM_SYSKEYDOWN, MSG, HHOOK, VK_NUMPAD0 |
| [XBrackets Lite](https://github.com/d0vgan/npp-XBracketsLite) | 2.0.4 | no (sin licencia declarada) | C++ | 12182 | 1 | no compila: necesita un port; faltan: m_cs, uint8_t, CRITICAL_SECTION, GWLP_WNDPROC, INFINITE, WAIT_OBJECT_0 |
| [xsvViewer++](https://github.com/mgalhu/xsvViewer) | 1.0.1.0 | sí (GPL-3.0) | C++ | 11352 | 3 | no compila: necesita un port; usa wchar_t (TCHAR Unicode); faltan: SetFocus, DeleteObject, InvalidateRect, KillTimer, MulDiv, GetFocus (ventanas Win32) |

### C. Tecnología exclusiva de Windows: reescribir (58)

| Plugin | Versión | Licencia | Motivo |
|---|---|---|---|
| [3P - Progress Programmers Pal](https://github.com/jcaillon/3P) | 1.8.8 | sí (GPL-3.0) | .NET (C#) |
| [ActiveX Plugin](https://sourceforge.net/projects/nppactivexplugin/) | 1.1.8.7 | revisar | COM/ActiveX de Windows |
| [ActivityWatch](https://github.com/pytlus93/aw-watcher-notepadpp) | 1.0.0 | revisar | .NET (C#) |
| [AutoCodepage](https://sourceforge.net/projects/autocodepage) | 1.2.7 | revisar | Delphi |
| [AutoEolFormat](https://sourceforge.net/projects/autoeolformat) | 1.0.4 | revisar | Delphi |
| [Automation Scripts](https://github.com/oleg-shilo/scripts.npp) | 2.0.0.0 | sí (MIT) | .NET (C#) |
| [BracketsCheck](https://github.com/niccord/BracketsCheck) | 1.2.2 | sí (Unlicense) | .NET (C#) |
| [CADdyTools](https://github.com/MarioRosi/CADdyTools) | 1.1.3.7 | sí (GPL-2.0) | .NET (C#) |
| [CalcStudio for Oracle EPM](https://github.com/rlorenzoni/CalcStudioEPM) | 0.15.5.0 | sí (GPL-3.0) | .NET (C#) |
| [Code Alignment](https://github.com/cpmcgrath/codealignment) | 14.1.107 | no (sin licencia declarada) | .NET (C#) |
| [Code::Stats](https://github.com/p0358/notepadpp-CodeStats) | 1.1.1 | revisar | .NET (C#) |
| [CompressedFileViewer](https://github.com/Pascal-Krenckel/CompressedFileViewer) | 5.1.1 | sí (Apache-2.0) | .NET (C#) |
| [CS-Script - C# Intellisense](https://github.com/oleg-shilo/cs-script.npp) | 2.0.13.0 | sí (MIT) | .NET (C#) |
| [CSV Lint](https://github.com/BdR76/CSVLint) | 0.4.9 | sí (GPL-3.0) | .NET (C#) |
| [CSV Visual Editor](https://github.com/zzsolt/notepadplusplus-csv-visual-editor) | 1.0.1 | sí (GPL-3.0) | .NET (C#) |
| [CsvQuery](https://github.com/jokedst/CsvQuery) | 1.2.9 | no (sin licencia declarada) | .NET (C#) |
| [CustomLineNumbers](https://sourceforge.net/projects/customlinenumbers) | 1.1.10 | revisar | Delphi |
| [DBGp](https://github.com/rdipardo/dbgpPlugin) | 0.14.2.1 | sí (GPL-3.0) | Delphi/Free Pascal |
| [DraftSync](https://github.com/belarrem/DraftSync) | 0.1.0.0 | sí (MIT) | .NET (C#) |
| [EnhanceAnyLexer](https://github.com/Ekopalypse/EnhanceAnyLexer) | 1.4.1 | sí (MIT) | lenguaje V |
| [ERP Helper](https://github.com/swhitley/ERPHelper) | 1.1.2 | sí (MIT) | .NET (C#) |
| [ExtSettings](https://sourceforge.net/projects/extsettings) | 1.3.1 | revisar | Delphi |
| [F# Interactive](https://github.com/rdipardo/nppFSIPlugin) | 0.2.3.4 | revisar | Delphi/Free Pascal |
| [FileFinder](https://github.com/ufo/filefinder) | 0.3 | no (sin licencia declarada) | .NET (C#) |
| [Graph Builder](https://github.com/pisarev/graphbuilder-npp) | 1.3.9 | sí (MIT) | Delphi/Free Pascal |
| [HugeFiles](https://github.com/molsonkiko/HugeFiles) | 0.4.1 | sí (Apache-2.0) | .NET (C#) |
| [ImgTag](https://github.com/chcg/ImgTag) | 2.0.1 | sí (GPL-3.0) | .NET (C#) |
| [JavaScript Map Parser](https://github.com/megaboich/js-map-parser) | 4.2 | no (sin licencia declarada) | .NET (C#) |
| [JSON Tools](https://github.com/molsonkiko/JsonToolsNppPlugin) | 8.6 | sí (Apache-2.0) | .NET (C#) |
| [JsonL Simple Formatter](https://github.com/davikokar/JsonLSimpleFormatter) | 1.0 | no (sin licencia declarada) | .NET (C#) |
| [LogRAM](https://github.com/HBZHSN/LogRAM) | 1.3.4 | sí (MIT) | .NET (C#) |
| [Merge files in one](https://github.com/gurikbal/Merge-files-in-one) | 1.2.0.0 | no (sin licencia declarada) | .NET (C#) |
| [Multi-Search](https://github.com/NachoMarengo/NppMultiSearch) | 0.1.0.0 | sí (MIT) | .NET (C#) |
| [MusicPlayer](https://github.com/gallettube/MusicPlayer) | 1.0.0.3 | no (sin licencia declarada) | .NET (C#) |
| [npp Random String Generator](https://github.com/cmbsolutions/nppRandomStringGenerator) | 1.9.11 | sí (MIT) | .NET (C#) |
| [Npp Xml Treeview](https://github.com/joaoasrosa/nppxmltreeview) | 2.0.0 | sí (Apache-2.0) | .NET (C#) |
| [npp.Connections](https://github.com/chcg/npp.connections) | 1.1.0 | no (sin licencia declarada) | Delphi/Free Pascal |
| [NppESPHome](https://github.com/atiburzi/NppESPHome-Plugin) | 1.0.26 | sí (MPL-2.0) | Delphi/Free Pascal |
| [NppGist](https://github.com/KvanTTT/NppGist) | 1.5.1.35 | sí (Apache-2.0) | .NET (C#) |
| [NppGZipFileViewer [Deprecated]](https://github.com/Pascal-Krenckel/NppGZipFileViewer) | 4.0.0 | sí (Apache-2.0) | .NET (C#) |
| [NppQrCode](https://github.com/rdipardo/nppQrCode) | 0.0.0.4 | sí (GPL-3.0) | Delphi/Free Pascal |
| [NppRegExTractor](https://github.com/viper3400/NppRegExTractor) | 2.1.0 | no (sin licencia declarada) | .NET (C#) |
| [NppTranslatePanel](https://github.com/Jerryk133/NppTranslatePanel) | 0.3.5.0 | sí (Apache-2.0) | .NET (C#) |
| [NppUISpy](https://github.com/dinkumoil/NppUISpy) | 1.2 | sí (GPL-3.0) | Delphi/Free Pascal |
| [PlantUML Viewer](https://github.com/Fruchtzwerg94/PlantUmlViewer) | 1.9.0.13 | sí (MIT) | .NET (C#) |
| [Poor Man's T-Sql Formatter](https://github.com/TaoK/PoorMansTSqlFormatter) | 1.6.13.31508 | sí (AGPL-3.0) | .NET (C#) |
| [Preview HTML](https://github.com/rdipardo/npp_preview) | 1.4.8.0 | sí (GPL-3.0) | Delphi/Free Pascal |
| [Random Values](https://github.com/BdR76/RandomValuesNPP) | 0.3 | no (sin licencia declarada) | .NET (C#) |
| [RDMD for Notepad++ (English)](https://gitlab.com/dokutoku/rdmd-for-npp) | 0.1.0.2 | revisar | lenguaje D |
| [RDMD for Notepad++ (Japanese)](https://gitlab.com/dokutoku/rdmd-for-npp) | 0.1.0.2 | revisar | lenguaje D |
| [Redis](https://github.com/bakingam1983/Notepad.plus.plus-RedisPlugin) | 1.0.2 | no (sin licencia declarada) | .NET (C#) |
| [Remove Duplicate Lines](https://github.com/gurikbal/Remove_dup_lines) | 1.3.0.0 | no (sin licencia declarada) | .NET (C#) |
| [ToolBucket](https://phdesign.com.au/npptoolbucket/) | 1.10.6622.41516 | revisar | .NET 3.5 |
| [TroiaLens](https://github.com/ufukt51/TroiaLensPlugin) | 0.1.4.3 | sí (MIT) | .NET (C#) |
| [Virtual Tab Groups](https://github.com/JamesShaver/VirtualTabGroups) | 1.0.0 | sí (MIT) | .NET (C#) |
| [WakaTime](https://github.com/wakatime/notepadpp-wakatime) | 5.1.1 | sí (BSD-3-Clause) | .NET (C#) |
| [WebEdit](https://github.com/Krazal/WebEdit) | 2.9.0.1 | sí (Apache-2.0) | .NET (C#) |
| [XML Navigator](https://github.com/chcg/XmlNavigator) | 1.4 | no (sin licencia declarada) | .NET (C#) |

### D. Sin código fuente (15)

| Plugin | Versión | Licencia | Motivo |
|---|---|---|---|
| [AutoSave](https://github.com/francostellari/NppPlugins) | 2.0 | revisar | el repositorio solo tiene binarios |
| [Bookmarks@Dook](https://github.com/Dook1/Bookmarks-Dook) | 4.1.2 | no (sin licencia declarada) | el repositorio solo tiene binarios |
| [Expression calculator](https://github.com/PlanetCNC/PlanetCNCNpp) | 3001.21.1125.1 | no (sin licencia declarada) | el repositorio solo tiene binarios |
| [LanguageHelp](https://github.com/francostellari/NppPlugins) | 1.7.5.0 | revisar | el repositorio solo tiene binarios |
| [Linefilter3](https://www.seelisoft.net/Linefilter3/) | 1.0.0.0 | revisar | freeware, sin código publicado |
| [MenuIcons](https://github.com/francostellari/NppPlugins) | 2.0.7 | revisar | el repositorio solo tiene binarios |
| [MoarFavorites](https://github.com/ERMtn/MoarFavorites) | 0.0.2 | no (sin licencia declarada) | el repositorio solo tiene binarios |
| [NppVoicePlugin](https://github.com/bms-prog/NppVoicePlugin) | 1.5 | sí (MIT) | el repositorio solo tiene binarios |
| [OpenSelection](https://github.com/francostellari/NppPlugins) | 1.1.3.0 | revisar | el repositorio solo tiene binarios |
| [RunMe](https://github.com/francostellari/NppPlugins) | 1.6.1.0 | revisar | el repositorio solo tiene binarios |
| [rustnpp](https://github.com/chcg/rustnpp) | 1.0.2 | no (sin licencia declarada) | el repositorio solo tiene binarios |
| [Shtirlitz](https://github.com/shtirlitz-dev/notepadpp-plugin) | 1.1.2 | no (sin licencia declarada) | el repositorio solo tiene binarios |
| [SQLinForm](https://www.sqlinform.com) | 26.4.7.1 | revisar | comercial, sin código |
| [TakeNotes](https://github.com/francostellari/NppPlugins) | 1.2.7.0 | revisar | el repositorio solo tiene binarios |
| [TopMost](https://github.com/francostellari/NppPlugins) | 1.4.2.0 | revisar | el repositorio solo tiene binarios |

### R. Fuera de GitHub: revisar a mano (7)

| Plugin | Versión | Licencia | Motivo |
|---|---|---|---|
| [AnalysePlugin](https://sourceforge.net/projects/analyseplugin) | 1.13.49.0 | revisar | fuera de GitHub (SourceForge u otro): revisar a mano |
| [Comment Wrap](https://sourceforge.net/projects/kered13-notepad-plugins/) | 1.0.0.7 | revisar | fuera de GitHub (SourceForge u otro): revisar a mano |
| [Customize Toolbar](https://sourceforge.net/projects/npp-customize) | 5.3 | revisar | fuera de GitHub (SourceForge u otro): revisar a mano |
| [GEDCOM Lexer](https://sourceforge.net/projects/gedcomlexer/) | 0.5.0.170 | revisar | fuera de GitHub (SourceForge u otro): revisar a mano |
| [Location Navigate](https://sourceforge.net/projects/locationnav/) | 0.4.8.1 | revisar | fuera de GitHub (SourceForge u otro): revisar a mano |
| [Python Indent](https://sourceforge.net/projects/kered13-notepad-plugins/) | 1.0.0.5 | revisar | fuera de GitHub (SourceForge u otro): revisar a mano |
| [Visual Studio Line Copy](https://sourceforge.net/projects/notepad-visualstudiolinecopy/) | 1.0.0.2 | revisar | fuera de GitHub (SourceForge u otro): revisar a mano |

### E. Ya cubierto por Edita (38)

| Plugin | Versión | Licencia | Motivo |
|---|---|---|---|
| [Another Markdown](https://github.com/ezyuzin/NppAnotherMarkdown) | 0.1.12 | sí (MIT) | fase 26 |
| [Color Picker](https://github.com/dasu88/NPPColorPicker) | 1.0.1 | no (sin licencia declarada) | fase 29 |
| [Compare](https://github.com/pnedev/comparePlus) | 2.0.2 | sí (GPL-3.0) | fase 39 |
| [ComparePlus](https://github.com/pnedev/comparePlus) | 3.0.0 | sí (GPL-3.0) | fase 39 |
| [Dark Mode C](https://github.com/pullitall/Notepadpp-light-dark-switch-and-automatic-switch-based-on-location) | 1.0.3 | sí (MIT) | fase 17 |
| [Datamodder Regex Viewer](https://github.com/dm-utils/regexviewer) | 1.3.1.1 | sí (MIT) | fase 34 |
| [Explorer](https://github.com/oviradoi/npp-explorer-plugin) | 1.9.9.0 | no (sin licencia declarada) | fase 22 |
| [FingerText2](https://github.com/ultimatejimmy/FingerText2) | 26.6.15 | sí (MIT) | fase 41 |
| [folderpad++](https://github.com/jks-liu/folderpad-plus-plus) | 1.2.0 | sí (GPL-3.0) | fase 22 |
| [Folding Line Hider](https://github.com/leonardchai/FoldingLineHider) | 1.1 | sí (GPL-3.0) | fase 49 |
| [GitSCM](https://github.com/vinsworldcom/nppGitSCM) | 1.4.10.1 | sí (GPL-2.0) | fase 28 y 40 |
| [JSFunctionViewer](https://github.com/soverthe/nppJSFunctionViewer) | 1.1.0 | sí (GPL-3.0) | fase 22 (Lista de funciones) |
| [Linter](https://github.com/deadem/notepad-pp-linter) | 0.1.0.0 | sí (MIT) | fase 36 (LSP) |
| [Linter++](https://github.com/ThosRTanner/notepad-pp-linter) | 1.0.3.0 | sí (MIT) | fase 36 (LSP) |
| [Markdown Panel](https://github.com/mohzy83/NppMarkdownPanel) | 0.9.3 | sí (MIT) | fase 26 |
| [MarkdownReader](https://github.com/rsalinger/NotepadPlusPlus-Markdown) | 0.1.0 | sí (GPL-3.0) | fase 26 |
| [MarkdownViewer++](https://github.com/nea/MarkdownViewerPlusPlus) | 0.8.2 | sí (MIT) | fase 26 (port incluido) |
| [MarkLens](https://github.com/maarten-grassmid/marklens) | 0.1.2 | sí (MIT) | fase 26 |
| [Mime tools](https://github.com/npp-plugins/mimetools) | 3.1 | revisar | fase 15 (receta, código original) |
| [Modern Markdown viewer](https://github.com/VioletTape/notepad_md_plugin) | 1.0.0 | sí (MIT) | fase 26 |
| [NavigateTo](https://github.com/young-developer/nppNavigateTo) | 2.7.1.0 | sí (Apache-2.0) | fase 27 (Ctrl+E) |
| [NewFileBrowser](https://sourceforge.net/projects/locationnav/) | 0.1.5 | revisar | fase 22 |
| [Notepad++ Plugin Demo](https://github.com/npp-plugins/plugindemo) | 4.5 | sí (GPL-2.0) | fase 11 (EditaDemo) |
| [Notepad++ Plugin Template](https://github.com/npp-plugins/plugintemplate) | 4.4 | sí (GPL-2.0) | fase 11 (SDK) |
| [NppExec](https://github.com/d0vgan/nppexec) | 0.8.12.1 | sí (GPL-3.0) | fase 35 y 48 (terminal y menú Ejecutar) |
| [NppGTags](https://github.com/pnedev/nppgtags) | 5.2.0 | sí (GPL-2.0) | fase 37 y 42 (LSP) |
| [NppMarkdownNext](https://github.com/theneet0/NppMarkdownNext) | 1.0.0 | sí (MIT) | fase 26 |
| [NppMenuSearch](https://github.com/peter-frentrup/NppMenuSearch) | 0.9.7 | revisar | fase 27 (paleta de órdenes) |
| [NppTags](https://github.com/ffes/npptags) | 0.9.1 | sí (GPL-2.0) | fase 37 y 42 (LSP) |
| [PythonScript](https://github.com/bruderstein/PythonScript) | 2.1.0.0 | sí (GPL-2.0) | fase 13 (port incluido) |
| [QuickText](https://github.com/vinsworldcom/nppQuickText) | 0.2.5.1 | sí (GPL-2.0) | fase 41 |
| [Regex Trainer](https://github.com/ahmoylaw/RegexTrainer-Descriptions) | 1.2.0 | no (sin licencia declarada) | fase 34 |
| [ScrollMarks](https://github.com/Hong-Seungmin/ScrollMarks) | 1.1.0 | sí (GPL-3.0) | fase 28 y 33 |
| [Session Manager](https://github.com/chcg/npp-session-manager) | 1.4.4 | sí (GPL-3.0) | fase 47 |
| [Snippets](https://github.com/ffes/nppsnippets) | 1.7.1 | sí (GPL-2.0) | fase 41 |
| [Source Cookifier](https://github.com/ufo/sourcecookifier) | 0.10.0 | no (sin licencia declarada) | fase 22 y 42 |
| [TagLEET](https://sourceforge.net/projects/tagleet/) | 1.3.2.0 | revisar | fase 37 y 42 (LSP) |
| [XML Tools](https://github.com/morbac/xmltools) | 3.1.1.13 | sí (GPL-3.0) | fase 15 y 25 (receta con port) |

### Backlog del SDK

Cabeceras de Windows que no existen en `plugin-sdk/compat/` (la compilación de prueba las creó vacías), por número de plugins que las incluyen:

`plugininterface.h` (8), `shobjidl.h` (7), `wininet.h` (7), `winsock2.h` (5), `winhttp.h` (5), `xutility` (5), `shlobj_core.h` (4), `python.h` (3), `atlstr.h` (3), `objbase.h` (3), `napi.h` (2), `pathcch.h` (2), `aclapi.h` (2), `dbghelp.h` (2), `comdef.h` (2), `atlbase.h` (2), `richedit.h` (2), `ocidl.h` (2), `rpc.h` (2), `interfaces.h` (2), `activscp.h` (2), `mshtml.h` (2), `rpcndr.h` (2), `mshtmhst.h` (2), `oleauto.h` (2), `exdisp.h` (2), `ole2.h` (2), `dispex.h` (2), `oaidl.h` (2), `webview2.h` (2)

Identificadores y funciones que más frenan a los plugins de la clase B2 (los seis más repetidos de cada uno):

`DLGTEMPLATE` (19), `GWLP_USERDATA` (19), `BM_GETCHECK` (11), `GWLP_WNDPROC` (8), `CallWindowProc` (6), `BM_SETCHECK` (6), `WS_EX_LAYOUTRTL` (5), `LOGFONT` (5), `DeleteObject` (5), `BOOL` (5), `__END_DECLS` (5), `__BEGIN_DECLS` (5), `mbstate_t` (5), `__c_locale` (5), `size_t` (5), `Sci_TextRange` (4), `SCI_GETTEXTRANGE` (4), `SetWindowLongPtr` (4), `GetParent` (4), `LB_ERR` (4), `USER_DEFAULT_SCREEN_DPI` (4), `IsWindow` (4), `KillTimer` (4), `GetProp` (3), `COINIT_APARTMENTTHREADED` (3), `CoInitializeEx` (3), `WS_VISIBLE` (3), `uintmax_t` (3), `intmax_t` (3), `hConnect` (3), `GetWindowTextLength` (3), `SetFocus` (3), `IsDlgButtonChecked` (3), `BN_CLICKED` (3), `EnableWindow` (3), `NppData` (3), `TVIF_PARAM` (3), `MulDiv` (3), `PROCESS_INFORMATION` (3), `EXTERN_C` (3)

## Conclusiones

1. **Todavía no conviene empaquetar binarios.** El primer lote serían los plugins de la clase A con licencia: Reverse Lines, NppPluginOpenHost, selectNLaunch, SimplifyJson y TidyText. Son menores. La CI y la lista firmada siguen siendo el camino, pero después de las ventanas.
2. **La capa de compatibilidad v2**, con su avance medido por esta auditoría:
   1. ✅ **Modo Unicode** y **KERNEL32/SHLWAPI/CRT sin ventanas** ([fase 51](https://github.com/alktrip/edita/blob/main/docs/fase51.md)). Los errores de `wchar_t` desaparecieron casi por completo.
   2. **Las ventanas**, la siguiente fase y la que más rinde ahora: las clases de la plantilla de N++ (`Window`, `StaticDialog`, `DockingDlgInterface`) sobre Qt, con los paneles acoplables en el `DockingManager` de Edita, y los mensajes de ventana más repetidos (`GetParent`, `ScreenToClient`, `SetWindowLongPtr`, `GWLP_USERDATA`, `GetSystemMetrics`, temporizadores).
   3. **Diálogos de recursos:** un intérprete de los `DIALOG`/`DIALOGEX` de los `.rc` (`FindResource`/`LoadResource`/`DLGTEMPLATE` son de lo más repetido) que cree los controles estándar con Qt y emule sus mensajes (`BM_GETCHECK`, `CB_*`, `LB_*`, `GetDlgItemText`…). Es lo que convertiría plugins de B2 en plugins completos, y también lo que tiene más riesgo: el dibujo propio (GDI) y los controles comunes complejos no entran.
   4. **Lo barato que queda:** `SCI_GETTEXTRANGE` (Scintilla 5 lo retiró; lo usan 18 plugins), `FormatMessage`, `MulDiv`, `MAKELANGID`, procesos e hilos (`CreateProcess`, `WaitForSingleObject`) y las macros `min`/`max` de `windows.h`.
3. **Cada paso se mide repitiendo esta auditoría** (`run-audit.sh`): el número de plugins de las clases A y B1 es el indicador de avance del SDK.
4. **La clase C (58 plugins, 26 % de la lista) no se trae.** Solo se reescribe lo que tenga demanda clara, como se hizo con MarkdownViewer++.
5. **Licencias:** de los plugins de B2, 24 no declaran licencia y 3 tienen una que hay que revisar a mano. Si alguno es importante, hay que pedirle permiso al autor antes de publicar su binario. De los que ya están en A o B1, NppJumpList y NX_ASCII_Database_Helper no tienen licencia.

## Limitaciones

- **La clase A es optimista** en un sentido: compilar y enlazar no garantiza que el plugin funcione. Un plugin puede depender del comportamiento de un mensaje de Win32 que la capa resuelve como «no hace nada». Cada receta nueva necesita su prueba, como las de MIME Tools y XML Tools en `tst_recipes`.
- **La clase B2 es pesimista** en otro: la compilación de prueba usa un `CMakeLists.txt` genérico (todas las fuentes, todas las carpetas de cabeceras). Algunos plugins fallan por la estructura del proyecto (fuentes de ejemplo, varias variantes del mismo archivo, generadores de código) y no por Win32. Una receta hecha a mano puede rescatarlos.
- Se analizó la **rama principal**, no la etiqueta exacta de la versión de la lista. Para cada receta se fija después la etiqueta con su SHA-256.
- La clase **E** es un juicio de producto: el plugin original puede tener detalles que la función de Edita no cubre (por ejemplo, Mermaid en las vistas previas de Markdown).
