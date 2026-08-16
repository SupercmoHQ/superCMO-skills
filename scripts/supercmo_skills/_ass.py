"""Minimal ASS (Advanced SubStation Alpha) primitives shared by caption_video and video_overlay —
colour conversion, timestamps, and text sanitising. Pure Python; no ffmpeg, no vendor."""

ALIGN = {"bottom": 2, "center": 5, "top": 8,
         "bottom-left": 1, "bottom-right": 3, "top-left": 7, "top-right": 9}


def colour(hex_colour, fallback="#FFFFFF"):
    """#RRGGBB -> ASS &HAABBGGRR (opaque). Falls back on a malformed value."""
    h = str(hex_colour or "").lstrip("#")
    if len(h) != 6:
        h = fallback.lstrip("#")
    try:
        int(h, 16)
    except ValueError:
        h = fallback.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def ts(seconds):
    """Seconds -> ASS timestamp H:MM:SS.cs."""
    cs = int(round(max(0.0, float(seconds)) * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def clean(text):
    """Make text safe inside an ASS Dialogue Text field (strip override-tag characters)."""
    return (str(text).replace("\\", "/").replace("{", "(").replace("}", ")")
            .replace("\n", " ").replace("\r", " ").replace("\t", " ").strip())
