# Caption fonts

`caption_video` burns captions with libass and points `fontsdir` here, so the font ships **in the
package** — no system-font dependency (the hosted sandbox has no fonts of its own).

## Shipped fonts

`Inter-Regular.ttf` and `Inter-Bold.ttf` (SIL OFL) ship here; their internal family name matches
`_fonts.DEFAULT_FONT_FAMILY` (`Inter`), and the license is recorded in the repo root `NOTICE`.

To swap or add a font: keep it **OFL-licensed**, make sure the font's **internal family name
matches** `_fonts.DEFAULT_FONT_FAMILY` (or update that constant to whatever you ship), and record
it in `NOTICE`. If this directory is ever emptied, `caption_video` still runs but falls back to
the host's default font and returns a `warning` — fine on a dev box, not acceptable for the
hosted surface.

These files are bundled via `[tool.hatch.build.targets.wheel]` (they live under the package, so
`packages` includes them) and resolved at runtime with `importlib.resources`, so they load whether
installed as a wheel or an editable tree.
