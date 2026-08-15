"""Overlay a logo and text on a video and stamp a branded end card — local `ffmpeg` + libass, no
vendor. Logo via the `overlay` filter, text via libass (no drawtext / fontconfig dependency), and
an optional end-card image appended as a short still. Returns {ok, path, duration, resolution,
size_bytes} | {ok: False, error, ...}.
"""
import os
import shutil
import tempfile

from . import _ass, _ffmpeg, _fonts

# named position -> overlay x:y expression (W,H = main video; w,h = logo; {m} = margin px)
_OVERLAY_XY = {
    "top-left": "{m}:{m}",
    "top-right": "W-w-{m}:{m}",
    "bottom-left": "{m}:H-h-{m}",
    "bottom-right": "W-w-{m}:H-h-{m}",
    "center": "(W-w)/2:(H-h)/2",
}


def _texts_ass(texts, size):
    """Build an ASS document for timed text overlays, or None if none are usable."""
    w, h = size
    events, n = [], 0
    for t in texts or []:
        if not isinstance(t, dict):
            continue
        body = _ass.clean(t.get("text") or "")
        start, end = t.get("start"), t.get("end")
        if not body or start is None or end is None:
            continue
        try:
            s, e = float(start), float(end)
        except (TypeError, ValueError):
            continue
        align = _ass.ALIGN.get(t.get("position", "center"), 5)
        fs = int(t.get("font_size") or max(20, round(h * 0.05)))
        inline_c = "&H" + _ass.colour(t.get("color") or t.get("colour"), "#FFFFFF")[4:] + "&"
        events.append(f"Dialogue: 0,{_ass.ts(s)},{_ass.ts(e)},Ovl,,0,0,0,,"
                      f"{{\\an{align}\\fs{fs}\\c{inline_c}}}{body}")
        n += 1
    if not n:
        return None
    head = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {w}\nPlayResY: {h}\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Ovl,{_fonts.DEFAULT_FONT_FAMILY},{max(20, round(h * 0.05))},&H00FFFFFF,"
        "&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3,1,5,60,60,60,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    return head + "\n".join(events) + "\n"


def _decorate(ffmpeg, src, workdir, logo_path, logo_position, logo_scale, texts_ass, iw, match, out):
    """Apply logo + text overlays to `src` -> `out` as a sequential filter chain. `match` =
    (fps, w, h) normalises frame params for a later concat, or None to leave them. Returns
    (rc, stderr)."""
    cmd = [ffmpeg, "-y", "-i", src]
    steps, cur = [], "[0:v]"
    if logo_path:
        cmd += ["-i", logo_path]
        lw = max(2, round(iw * logo_scale))
        margin = max(4, round(iw * 0.03))
        xy = _OVERLAY_XY.get(logo_position, _OVERLAY_XY["bottom-right"]).format(m=margin)
        steps.append(f"[1:v]scale={lw}:-1[lg]")
        steps.append(f"{cur}[lg]overlay={xy}[v_ov]")
        cur = "[v_ov]"
    if texts_ass:
        fonts = _fonts.stage_fonts(workdir)
        sub = "subtitles=texts.ass" + (f":fontsdir={os.path.basename(fonts)}" if fonts else "")
        steps.append(f"{cur}{sub}[v_txt]")
        cur = "[v_txt]"
    if match:
        f, _w, _h = match
        steps.append(f"{cur}fps={f},setsar=1,format=yuv420p[v_norm]")
        cur = "[v_norm]"
    if steps:
        cmd += ["-filter_complex", ";".join(steps), "-map", cur]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-map", "0:a?", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", out]
    return _ffmpeg.run(cmd, cwd=workdir)


def _endcard_clip(ffmpeg, img, dur, w, h, f, with_audio, out):
    """Render an end-card still image into a `dur`-second clip matching (w, h, fps f)."""
    cmd = [ffmpeg, "-y", "-loop", "1", "-t", f"{dur}", "-i", img]
    if with_audio:
        cmd += ["-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    vf = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
          f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={f},format=yuv420p")
    cmd += ["-vf", vf, "-map", "0:v"]
    if with_audio:
        cmd += ["-map", "1:a", "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", out]
    return _ffmpeg.run(cmd)


def video_overlay(video, logo=None, logo_position="bottom-right", logo_scale=0.15, texts=None,
                  end_card=None, end_card_duration=3.0, output=None, output_dir=None, dry_run=False):
    """Overlay a `logo` (PNG, at a named corner, sized `logo_scale` x video width) and timed
    `texts` (list of {text, start, end, position, color, font_size}) onto `video`, and optionally
    append an `end_card` image as a `end_card_duration`-second still. At least one of logo / texts /
    end_card is required. Requires ffmpeg."""
    if not isinstance(video, str) or not video.strip():
        return {"ok": False, "error": "video is required (a file path or http(s) URL)."}
    if not (logo or texts or end_card):
        return {"ok": False, "error": "nothing to do — pass at least one of logo, texts, or end_card."}

    ffmpeg, err = _ffmpeg.require("ffmpeg")
    if err:
        return err
    out = _ffmpeg.out_path(output, output_dir, "overlaid.mp4")

    if dry_run:
        return {"ok": True, "_dry_run": True, "output": out, "logo": bool(logo),
                "texts": len(texts or []), "end_card": bool(end_card),
                "plan": "overlay logo/text via libass; append end-card still"}

    workdir = tempfile.mkdtemp(prefix="supercmo_overlay_")
    try:
        src, err = _ffmpeg.resolve(video, workdir, "in.mp4")
        if err:
            return {"ok": False, "error": err}
        size = _ffmpeg.video_size(src) or (1080, 1920)
        iw, ih = size
        logo_path = None
        if logo:
            logo_path, err = _ffmpeg.resolve(logo, workdir, "logo.png")
            if err:
                return {"ok": False, "error": f"logo: {err}"}
        texts_ass = _texts_ass(texts, size) if texts else None
        if texts_ass:
            with open(os.path.join(workdir, "texts.ass"), "w", encoding="utf-8") as fh:
                fh.write(texts_ass)

        decorated = bool(logo or texts_ass)
        f = _ffmpeg.fps(src) or 30.0
        match = (f, iw, ih) if end_card else None                # normalise only when we will concat

        if decorated:
            stage1 = os.path.join(workdir, "stage1.mp4")
            rc, err = _decorate(ffmpeg, src, workdir, logo_path, logo_position, logo_scale,
                                texts_ass, iw, match, stage1)
            if rc != 0 or not _ffmpeg.ok(stage1):
                return {"ok": False, "error": "ffmpeg could not apply the overlays.",
                        "hint": "confirm the video and logo are valid files", "detail": err[-500:]}
        else:
            stage1 = src                                         # end_card only

        if not end_card:
            shutil.move(stage1, out) if decorated else _ffmpeg.run(
                [ffmpeg, "-y", "-i", src, "-c", "copy", out])
            dur, res, sz = _ffmpeg.probe(out)
            return {"ok": True, "path": out, "duration": dur, "resolution": res, "size_bytes": sz}

        ec_img, err = _ffmpeg.resolve(end_card, workdir, "endcard.png")
        if err:
            return {"ok": False, "error": f"end_card: {err}"}
        with_audio = _ffmpeg.has_audio(stage1)
        endcard = os.path.join(workdir, "endcard.mp4")
        rc, err = _endcard_clip(ffmpeg, ec_img, float(end_card_duration or 3.0), iw, ih, f,
                                with_audio, endcard)
        if rc != 0 or not _ffmpeg.ok(endcard):
            return {"ok": False, "error": "ffmpeg could not build the end card.",
                    "hint": "confirm the end_card is a valid image", "detail": err[-500:]}
        if with_audio:
            fc = "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]"
            maps = ["-map", "[v]", "-map", "[a]", "-c:a", "aac"]
        else:
            fc = "[0:v][1:v]concat=n=2:v=1:a=0[v]"
            maps = ["-map", "[v]"]
        rc, err = _ffmpeg.run([ffmpeg, "-y", "-i", stage1, "-i", endcard, "-filter_complex", fc,
                               *maps, "-c:v", "libx264", "-pix_fmt", "yuv420p", out])
        if rc != 0 or not _ffmpeg.ok(out):
            return {"ok": False, "error": "ffmpeg could not append the end card.",
                    "hint": "the main clip and end card could not be joined", "detail": err[-500:]}
        dur, res, sz = _ffmpeg.probe(out)
        return {"ok": True, "path": out, "duration": dur, "resolution": res, "size_bytes": sz,
                "end_card": True}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":                                       # no-network / no-ffmpeg self-check
    doc = _texts_ass([{"text": "50% OFF", "start": 0, "end": 2, "position": "top", "color": "#FF0000"}],
                     (1080, 1920))
    assert doc and "50% OFF" in doc and "\\an8" in doc and "[Events]" in doc, doc
    assert _texts_ass([{"text": "x"}], (100, 100)) is None       # no timing -> dropped
    assert _OVERLAY_XY["bottom-right"].format(m=20) == "W-w-20:H-h-20"
    dry = video_overlay("v.mp4", logo="l.png", end_card="e.png", dry_run=True)
    assert dry["ok"] and dry["logo"] and dry["end_card"], dry
    assert not video_overlay("v.mp4")["ok"]                      # nothing to do
    print("video_overlay self-check OK")
