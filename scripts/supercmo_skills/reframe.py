"""Reframe a video to a new aspect ratio — local `ffmpeg`, no vendor. Convert between 9:16, 1:1,
16:9 (or any W:H) by cropping to fill (default, agent can steer the crop focus) or padding to fit
(letterbox). Returns {ok, path, aspect, resolution, duration, size_bytes} | {ok: False, error,...}.
"""
import shutil
import tempfile

from . import _ffmpeg


def _ratio(aspect):
    """'9:16' | '9x16' -> width/height float, or None."""
    if not isinstance(aspect, str):
        return None
    for sep in (":", "x", "/"):
        if sep in aspect:
            a, b = aspect.split(sep, 1)
            try:
                w, h = float(a), float(b)
                return w / h if w > 0 and h > 0 else None
            except ValueError:
                return None
    return None


def _target(iw, ih, r, mode):
    """Output (w, h) for target ratio `r`. crop = the largest r-ratio rect INSIDE the input (pure
    crop, no upscaling); pad = the smallest r-ratio canvas CONTAINING the input (letterbox)."""
    ow, oh = iw, round(iw / r)
    if mode == "crop":
        if oh > ih:
            oh, ow = ih, round(ih * r)
    else:                                                        # pad
        if oh < ih:
            oh, ow = ih, round(ih * r)
    ow -= ow % 2
    oh -= oh % 2
    return max(2, ow), max(2, oh)


def _vf(iw, ih, ow, oh, mode, focus):
    if mode == "crop":
        fx = min(1.0, max(0.0, float((focus or {}).get("x", 0.5))))
        fy = min(1.0, max(0.0, float((focus or {}).get("y", 0.5))))
        x = max(0, round((iw - ow) * fx))
        y = max(0, round((ih - oh) * fy))
        return f"crop={ow}:{oh}:{x}:{y}"
    return (f"scale={ow}:{oh}:force_original_aspect_ratio=decrease,"
            f"pad={ow}:{oh}:(ow-iw)/2:(oh-ih)/2,setsar=1")


def reframe(video, aspect, mode="crop", focus=None, output=None, output_dir=None, dry_run=False):
    """Reframe `video` to `aspect` (e.g. '9:16', '1:1', '16:9'). `mode`: 'crop' (fill, default) or
    'pad' (letterbox). `focus` = {x, y} in 0-1 steers the crop window (default centre). Keeps audio."""
    if not isinstance(video, str) or not video.strip():
        return {"ok": False, "error": "video is required (a file path or http(s) URL)."}
    r = _ratio(aspect)
    if r is None:
        return {"ok": False, "error": f"aspect must be a W:H ratio like '9:16'; got {aspect!r}."}
    if mode not in ("crop", "pad"):
        return {"ok": False, "error": "mode must be 'crop' or 'pad'."}

    out = _ffmpeg.out_path(output, output_dir, f"reframed_{aspect.replace(':', 'x')}.mp4")

    if dry_run:
        return {"ok": True, "_dry_run": True, "output": out, "aspect": aspect, "mode": mode,
                "plan": f"{mode} the video to {aspect}"}

    ffmpeg, err = _ffmpeg.require("ffmpeg")
    if err:
        return err

    workdir = tempfile.mkdtemp(prefix="supercmo_reframe_")
    try:
        src, err = _ffmpeg.resolve(video, workdir, "in.mp4")
        if err:
            return {"ok": False, "error": err}
        size = _ffmpeg.video_size(src)
        if not size:
            return {"ok": False, "error": "could not read the video's dimensions.",
                    "hint": "confirm the input is a valid video file"}
        iw, ih = size
        ow, oh = _target(iw, ih, r, mode)
        vf = _vf(iw, ih, ow, oh, mode, focus)
        rc, err = _ffmpeg.run(
            [ffmpeg, "-y", "-i", src, "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-c:a", "copy", out])
        if rc != 0 or not _ffmpeg.ok(out):
            return {"ok": False, "error": "ffmpeg could not reframe the video.",
                    "hint": "confirm the input is a valid video file", "detail": err[-500:]}
        dur, res, sz = _ffmpeg.probe(out)
        return {"ok": True, "path": out, "aspect": aspect, "mode": mode, "resolution": res,
                "duration": dur, "size_bytes": sz}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":                                       # no-network / no-ffmpeg self-check
    assert _ratio("9:16") and abs(_ratio("16:9") - 16 / 9) < 1e-6 and _ratio("bad") is None
    # 1920x1080 -> 9:16 crop = vertical strip inside the frame, no upscaling
    assert _target(1920, 1080, 9 / 16, "crop") == (608, 1080), _target(1920, 1080, 9 / 16, "crop")
    # 1920x1080 -> 9:16 pad = taller canvas containing the frame
    ow, oh = _target(1920, 1080, 9 / 16, "pad")
    assert oh == 1080 or ow == 1920  # one dimension is preserved
    assert _target(1080, 1080, 1.0, "crop") == (1080, 1080)
    assert "crop=608:1080" in _vf(1920, 1080, 608, 1080, "crop", {"x": 0.5, "y": 0.5})
    assert "pad=" in _vf(1080, 1080, 1080, 1920, "pad", None)
    dry = reframe("v.mp4", "9:16", dry_run=True)
    assert dry["ok"] and dry["aspect"] == "9:16", dry
    assert not reframe("v.mp4", "notaratio")["ok"]
    print("reframe self-check OK")
