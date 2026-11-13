# Borradores de recetas

Recetas empezadas que todavía no compilan: la CI del catálogo no las ve (solo compila `recipes/`).

| Borrador | Qué falta |
|---|---|
| [HexEditor](HexEditor/) | HEX-Editor 0.9.14 necesita una parte nueva de la capa de compatibilidad de Edita: los controles que dibuja el plugin (`WM_DRAWITEM`), `EnumFontFamiliesEx`, el registro, `EnumDisplayMonitors`, `GetVersionEx`, los tooltips que siguen al ratón, `ModifyMenu`, `IsTextUnicode` y `DPI_AWARENESS_CONTEXT` (ver `docs/fase87.md` de Edita) |
