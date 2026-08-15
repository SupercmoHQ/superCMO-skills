# Caption fonts

`caption_video` burns captions with libass and points `fontsdir` here, so the font ships **in the
package** — no system-font dependency (the hosted sandbox has no fonts of its own).

## Drop-in required

Add 1–2 **OFL-licensed** `.ttf` files here (e.g. Inter, Montserrat). Requirements:

- The font's **internal family name must match** `_fonts.DEFAULT_FONT_FAMILY` (currently `Inter`),
  or update that constant to whatever you ship.
- Record the font + its OFL license in the repo root `NOTICE`.

Until a `.ttf` is present, `caption_video` still runs but falls back to the host's default font and
returns a `warning` — fine on a dev box, not acceptable for the hosted surface.

These files are bundled via `[tool.hatch.build.targets.wheel]` (they live under the package, so
`packages` includes them) and resolved at runtime with `importlib.resources`, so they load whether
installed as a wheel or an editable tree.
