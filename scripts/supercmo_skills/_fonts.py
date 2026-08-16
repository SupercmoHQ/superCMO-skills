"""Caption fonts shipped in the package (`_assets/fonts/*.ttf`), resolved via
`importlib.resources` so they load whether installed as a wheel or an editable tree — never via
`__file__`. `stage_fonts` copies them into a working dir so libass `fontsdir=fonts` can reference
them by a clean relative path (no filtergraph escaping of absolute paths).

If no font ships (the .ttf is a licensed asset added out-of-band), the caption tool falls back to
the host's fontconfig default — fine on a dev box, but the hosted sandbox needs the shipped font.
"""
import importlib.resources as ir
import os

_PKG = "supercmo_skills"
# The default family name referenced in the ASS Style. Must match the shipped .ttf's internal
# family name. Kept here so the tool and the asset stay in one story.
DEFAULT_FONT_FAMILY = "Inter"


def _font_files():
    try:
        base = ir.files(_PKG) / "_assets" / "fonts"
    except (ModuleNotFoundError, FileNotFoundError):
        return []
    try:
        return [e for e in base.iterdir()
                if e.name.lower().endswith((".ttf", ".otf")) and e.is_file()]
    except (FileNotFoundError, NotADirectoryError):
        return []


def available():
    """Names of the shipped font files (empty if none are bundled yet)."""
    return [f.name for f in _font_files()]


def stage_fonts(dest_dir):
    """Copy shipped fonts into `dest_dir`/fonts; return that path, or None if none ship."""
    files = _font_files()
    if not files:
        return None
    fonts = os.path.join(dest_dir, "fonts")
    os.makedirs(fonts, exist_ok=True)
    for f in files:
        with open(os.path.join(fonts, f.name), "wb") as out:
            out.write(f.read_bytes())
    return fonts
