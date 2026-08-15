"""Burn styled social captions into a video — local `ffmpeg` + libass, no vendor API, no key.

Renders a word-timed transcript (the shape `transcribe` returns) into an ASS subtitle file — pure
Python styling, positioning, brand colour, optional karaoke word-highlight — and burns it with the
`subtitles` filter using a font SHIPPED in the package (`fontsdir`), so there is zero system-font
dependency. Returns {ok, path, duration, resolution, size_bytes, lines} | {ok: False, error, ...}.
"""
import os
import shutil
import tempfile

from . import _ass, _ffmpeg, _fonts


def _word(item):
    """Normalize a transcript item to (text, start, end) or None if it lacks numeric timing."""
    if not isinstance(item, dict):
        return None
    text = _ass.clean(item.get("word") or item.get("text") or "")
    start, end = item.get("start"), item.get("end")
    if not text or start is None or end is None:
        return None
    try:
        return text, float(start), float(end)
    except (TypeError, ValueError):
        return None


def _lines(words, per_line):
    """Group normalized words into caption lines of `per_line` words each."""
    return [words[i:i + per_line] for i in range(0, len(words), per_line)]


def _build_ass(words, size, style):
    """Return the full ASS document string for the given normalized words + style."""
    w, h = size
    base = _ass.colour(style["primary_color"], "#FFFFFF")
    accent = _ass.colour(style["highlight_color"], "#FFE600")
    outline_c = _ass.colour(style["outline_color"], "#000000")
    karaoke = bool(style["karaoke"])
    # Karaoke sweeps SecondaryColour -> PrimaryColour per \k word. So the swept-to (active) colour
    # is Primary; the resting colour is Secondary. Non-karaoke: everything rests at `base`.
    primary, secondary = (accent, base) if karaoke else (base, base)
    align = _ass.ALIGN.get(style["position"], 2)
    bold = -1 if style["bold"] else 0
    fsize = style["font_size"]
    outline_w = style["outline"]
    margin_v = style["margin_v"]
    # A comma or newline in the font name would break the comma-delimited ASS Style line.
    font = str(style["font"]).replace(",", " ").replace("\n", " ").replace("\r", " ").strip() or "Inter"

    head = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {w}\nPlayResY: {h}\n"
        "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Cap,{font},{fsize},{primary},{secondary},{outline_c},&H64000000,"
        f"{bold},0,0,0,100,100,0,0,1,{outline_w},1,{align},40,40,{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    events = []
    for line in _lines(words, style["words_per_line"]):
        l_start, l_end = line[0][1], line[-1][2]
        if l_end <= l_start:
            l_end = l_start + 0.4
        if karaoke:
            parts = []
            for idx, (text, start, _end) in enumerate(line):
                nxt = line[idx + 1][1] if idx + 1 < len(line) else l_end
                cs = max(1, int(round((nxt - start) * 100)))
                parts.append(f"{{\\k{cs}}}{text}")
            body = " ".join(parts)
        else:
            body = " ".join(text for text, _s, _e in line)
        events.append(f"Dialogue: 0,{_ass.ts(l_start)},{_ass.ts(l_end)},Cap,,0,0,0,,{body}")
    return head + "\n".join(events) + "\n"


def _style(video_h, overrides):
    o = overrides or {}
    fsize = o.get("font_size") or max(16, round(video_h * 0.06))
    return {
        "font": o.get("font") or _fonts.DEFAULT_FONT_FAMILY,
        "font_size": int(fsize),
        "primary_color": o.get("primary_color", "#FFFFFF"),
        "highlight_color": o.get("highlight_color", "#FFE600"),
        "outline_color": o.get("outline_color", "#000000"),
        "position": o.get("position", "bottom"),
        "words_per_line": max(1, int(o.get("words_per_line", 5))),
        "karaoke": o.get("karaoke", True),
        "bold": o.get("bold", True),
        "outline": int(o.get("outline") or max(2, round(int(fsize) * 0.08))),
        "margin_v": int(o.get("margin_v") or round(video_h * 0.10)),
    }


def caption_video(video, transcript, style=None, output=None, output_dir=None, dry_run=False):
    """Burn `transcript` (a list of {text|word, start, end} — the `transcribe` shape) onto `video`
    as styled captions. `style` (all optional): font, font_size, primary_color, highlight_color,
    outline_color, position (bottom|center|top), words_per_line, karaoke, bold, outline, margin_v.
    Timestamps are relative to the video's own audio (t=0)."""
    if not isinstance(video, str) or not video.strip():
        return {"ok": False, "error": "video is required (a file path or http(s) URL)."}
    if not isinstance(transcript, list) or not transcript:
        return {"ok": False, "error": "transcript must be a non-empty list of {text, start, end} items.",
                "hint": "call transcribe on the video/VO first, then pass its `words`."}
    words = [w for w in (_word(i) for i in transcript) if w]
    if not words:
        return {"ok": False, "error": "no transcript item had usable text + numeric start/end.",
                "hint": "each item needs `text` (or `word`), `start`, and `end` in seconds."}

    ffmpeg, err = _ffmpeg.require("ffmpeg")
    if err:
        return err
    out = _ffmpeg.out_path(output, output_dir, "captioned.mp4")

    if dry_run:
        return {"ok": True, "_dry_run": True, "output": out, "words": len(words),
                "lines": (len(words) + _style(1080, style)["words_per_line"] - 1)
                // _style(1080, style)["words_per_line"],
                "plan": "render ASS (styled, positioned, optional karaoke) and burn via libass"}

    workdir = tempfile.mkdtemp(prefix="supercmo_caption_")
    try:
        src, err = _ffmpeg.resolve(video, workdir, "in.mp4")
        if err:
            return {"ok": False, "error": err}
        size = _ffmpeg.video_size(src) or (1080, 1920)
        st = _style(size[1], style)
        ass = _build_ass(words, size, st)
        with open(os.path.join(workdir, "caps.ass"), "w", encoding="utf-8") as f:
            f.write(ass)
        fonts = _fonts.stage_fonts(workdir)                     # None -> fontconfig default
        vf = "subtitles=caps.ass" + (f":fontsdir={os.path.basename(fonts)}" if fonts else "")
        rc, err = _ffmpeg.run(
            [ffmpeg, "-y", "-i", src, "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-c:a", "copy", out], cwd=workdir)
        if rc != 0 or not _ffmpeg.ok(out):
            return {"ok": False, "error": "ffmpeg could not burn the captions.",
                    "hint": "confirm the video is valid and the transcript timings are in seconds",
                    "detail": err[-500:]}
        dur, res, sz = _ffmpeg.probe(out)
        result = {"ok": True, "path": out, "duration": dur, "resolution": res, "size_bytes": sz,
                  "lines": (len(words) + st["words_per_line"] - 1) // st["words_per_line"]}
        if fonts is None:
            result["warning"] = ("no caption font is shipped in the package yet — used the host's "
                                 "default font. The hosted sandbox needs a bundled .ttf.")
        return result
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":                                       # no-network / no-ffmpeg self-check
    doc = _build_ass(
        [("Hello", 0.0, 0.5), ("world", 0.5, 1.0), ("now", 1.0, 1.4)],
        (1080, 1920), _style(1920, {"karaoke": True}))
    assert "[Events]" in doc and "\\k" in doc and "PlayResX: 1080" in doc, doc
    assert _ass.ts(1.23) == "0:00:01.23" and _ass.ts(65.0) == "0:01:05.00"
    plain = _build_ass([("Hi", 0.0, 0.4)], (720, 1280), _style(1280, {"karaoke": False}))
    assert "\\k" not in plain and "Dialogue:" in plain
    dry = caption_video("x.mp4", [{"text": "hi", "start": 0, "end": 1}], dry_run=True)
    assert dry["ok"] and dry["_dry_run"] and dry["words"] == 1, dry
    bad = caption_video("x.mp4", [{"text": "hi"}])               # no timing
    assert not bad["ok"], bad
    print("caption_video self-check OK")
