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

Las recetas, los parches y los *overlays* tienen la misma licencia que Edita (GPL v3 o posterior). Cada plugin conserva la licencia de su autor. Como el código original y el port son públicos, el binario cumple con la obligación de ofrecer el código correspondiente.

## Contenido

| Carpeta | Qué hay |
|---|---|
| [`audit/`](audit/) | **Auditoría de la lista oficial de N++** (225 plugins): qué se puede compilar para Edita, qué hay que portar, qué no se puede traer y por qué. Incluye las herramientas para repetirla |
| `recipes/` | Recetas (se mudan desde `editor/data/plugins/recipes/`) |
| `.github/workflows/` | Compilación y publicación (pendiente) |

## Estado

| Paso | Estado |
|---|---|
| Auditoría del catálogo de N++ | ✅ [audit/](audit/) |
| Capa de compatibilidad v2, parte 1: Unicode y Win32 sin ventanas | ✅ [fase 51 de Edita](https://github.com/alktrip/edita/blob/main/docs/fase51.md): de 3 a 7 plugins que compilan; ahora el bloqueo son las ventanas |
| Capa de compatibilidad v2, parte 2: ventanas, plantilla de N++ y paneles acoplables | ✅ [fase 52 de Edita](https://github.com/alktrip/edita/blob/main/docs/fase52.md): compilan 11 plugins (8 que Edita no tiene) y otros 6 salvo la interfaz |
| Capa de compatibilidad v2, parte 3: diálogos, menús y cadenas de los `.rc` | ✅ [fase 53 de Edita](https://github.com/alktrip/edita/blob/main/docs/fase53.md): compilan 12 plugins con su interfaz (9 que Edita no tiene) y otros 6 salvo la interfaz |
| Capa de compatibilidad v2, parte 4: controles comunes, bucles de mensajes y dibujo | Pendiente |
| Mudar las recetas desde el repositorio de Edita | Pendiente |
| CI: compilar las recetas por plataforma y publicar la lista firmada | Pendiente |
| Edita: descargar la lista remota, verificar la firma e instalar los binarios | Pendiente |
| Primer lote: los plugins de las clases A y B1 de la auditoría repetida, con una licencia que permite redistribuirlos | Pendiente |
