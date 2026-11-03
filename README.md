# Plugins de Edita

Catálogo de plugins de [Edita](https://github.com/alktrip/edita), el editor para Linux y macOS inspirado en Notepad++.

Este repositorio está separado de la aplicación por tres motivos:

- Los plugins tienen su propio ritmo: una versión nueva de un plugin no obliga a publicar una versión de Edita, y al revés.
- La compilación de los plugins para cada plataforma (Linux x86_64, Linux aarch64 y macOS) no pesa en la CI de la aplicación.
- Los binarios se publican en los *Releases* de este repositorio, no en git, así que el historial de la aplicación no crece con cada paquete.

## Cómo funciona

1. Cada plugin tiene una **receta** (`recipes/<carpeta>/recipe.json`). La receta indica:
   - la etiqueta original publicada por el autor, con su SHA-256;
   - los parches y los archivos propios (*overlay*) del port;
   - los requisitos de compilación.

   No hay forks ni binarios hechos a mano: la receta es la fuente de verdad. El formato está en [docs/plugins.md](https://github.com/alktrip/edita/blob/main/docs/plugins.md) de Edita.
2. La **CI** compila cada receta para cada plataforma y publica un `.zip` por plugin y plataforma. También genera la **lista de plugins**, firmada, con el formato de `nppPluginList.json` de Notepad++.
3. El **administrador de plugins** de Edita descarga la lista y comprueba la firma. Al instalar un plugin:
   - descarga el binario y comprueba su SHA-256;
   - si no hay binario para la plataforma del equipo, compila la receta en local, como hasta ahora.

Cada plugin conserva la licencia de su autor. Los parches y los *overlays* de una receta tienen la licencia del plugin que modifican, y el resto del repositorio (recetas, scripts, auditoría), la de Edita (GPL v3 o posterior). Cada paquete lleva la licencia del plugin junto al `.so` (`license-files` en la receta). Como el código original y el port son públicos, el binario cumple con la obligación de ofrecer el código correspondiente.

## Contenido

| Carpeta | Qué hay |
|---|---|
| [`audit/`](audit/) | **Auditoría de la lista oficial de N++** (225 plugins): qué se puede compilar para Edita, qué hay que portar, qué no se puede traer y por qué. Incluye las herramientas para repetirla |
| [`recipes/`](recipes/) | Las recetas, una carpeta por plugin |
| [`scripts/build-all.sh`](scripts/build-all.sh) | Compila y prueba las recetas con Edita: `scripts/build-all.sh ruta/a/edita salida/` |
| `.github/workflows/` | Compilación y publicación (pendiente) |

## Recetas

Todas compilan el código de la etiqueta que publicó el autor, sin cambios salvo los parches indicados, y pasan su prueba (`check` en la receta) con `edita --check-plugin`.

| Plugin | Versión | Licencia | Qué hace | Parches |
|---|---|---|---|---|
| [Reverse Lines](recipes/qkNppReverseLines/) | 1.0.0.0 | GPL-3.0-or-later | Invierte el orden de las líneas | 1 línea: el NUL de `SCI_GETSELTEXT` (Scintilla 5); el original escribe un byte fuera de su búfer |
| [NppPluginOpenHost](recipes/NppPluginOpenHost/) | 1.1 | Apache-2.0 | Abre el archivo hosts | 1 línea: `/etc/hosts` en vez del de Windows |
| [Select 'N' Launch](recipes/selectNLaunch/) | 2.2 | GPL-2.0-or-later | Abre la selección con la aplicación asociada a una extensión | — |
| [Simplify JSON](recipes/SimplifyJson/) | 1.0.1 | GPL-2.0-only | Escapa, desescapa, da formato y minifica JSON | 3 líneas: el NUL de `SCI_GETSELTEXT`; el original pierde el último carácter de la selección |
| [TidyText](recipes/TidyText/) | 1.2.0 | GPL-2.0-or-later | Resalta y repara caracteres invisibles y mojibake | 2 líneas: el NUL de `SCI_GETSELTEXT`, al enviar la selección a un asistente |
| [Auto Detect Indention](recipes/nppAutoDetectIndent/) | 2.3 | GPL-3.0-or-later | Ajusta la sangría a la de cada documento | — (su submódulo, la plantilla de N++, va como `extra-sources`) |
| [SQL Column Highlighter](recipes/SqlColumnHighlighter/) | 1.0.0 | MIT | Resalta las columnas y valores de un `INSERT` | — |

Los tres parches de `SCI_GETSELTEXT` corrigen fallos que también tienen en Notepad++: en la Scintilla actual (la serie 5, la de Notepad++ y la de Edita), el valor que devuelve no cuenta el NUL final, pero sí lo escribe. Los plugins se escribieron con la regla anterior.

## Estado

| Paso | Estado |
|---|---|
| Auditoría del catálogo de N++ | ✅ [audit/](audit/) |
| Capa de compatibilidad v2, parte 1: Unicode y Win32 sin ventanas | ✅ [fase 51 de Edita](https://github.com/alktrip/edita/blob/main/docs/fase51.md): de 3 a 7 plugins que compilan; ahora el bloqueo son las ventanas |
| Capa de compatibilidad v2, parte 2: ventanas, plantilla de N++ y paneles acoplables | ✅ [fase 52 de Edita](https://github.com/alktrip/edita/blob/main/docs/fase52.md): compilan 11 plugins (8 que Edita no tiene) y otros 6 salvo la interfaz |
| Capa de compatibilidad v2, parte 3: diálogos, menús y cadenas de los `.rc` | ✅ [fase 53 de Edita](https://github.com/alktrip/edita/blob/main/docs/fase53.md): compilan 12 plugins con su interfaz (9 que Edita no tiene) y otros 6 salvo la interfaz |
| Capa de compatibilidad v2, parte 4: controles comunes, bucles de mensajes y dibujo | Pendiente |
| Recetas del primer lote y su prueba (`--build-recipe`, `--check-plugin`) | ✅ [fase 54 de Edita](https://github.com/alktrip/edita/blob/main/docs/fase54.md): los 7 plugins de la clase A con una licencia que permite redistribuirlos |
| CI: compilar las recetas por plataforma y publicar la lista firmada | Pendiente |
| Edita: descargar la lista remota, verificar la firma e instalar los binarios | Pendiente |
| Mudar las recetas de MIME Tools y XML Tools desde el repositorio de Edita | Pendiente |
| Siguientes lotes: los plugins de la clase B1, según avance la capa | Pendiente |
