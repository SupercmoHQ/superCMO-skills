"""Stitch finished video clips into one file — local `ffmpeg`, no vendor API, no key.

Concatenates clips in order with a hard cut between each, keeping each clip's audio. Optionally lays
a background-music track under the whole video and burns in subtitles from an SRT file. Clips of
different sizes are scaled to a common frame. Stdlib + the system `ffmpeg` / `ffprobe` binaries only.
"""
import json
import os
import shutil
import subprocess
import tempfile

import supercmo_env

from . import paths


def _resolve(src, workdir, name):
    """(local_path, None) | (None, error). Downloads an http(s) URL into workdir as `name`."""
    src = src.strip() if isinstance(src, str) else src
    if not src:
        return None, "an input path is empty"
    if src.startswith(("http://", "https://")):
        dst = os.path.join(workdir, name)
        try:
            supercmo_env.safe_download(src, dst)                 # SSRF-guarded (blocks internal/metadata IPs)
        except Exception as e:                                   # blocked / network / 404 / etc.
            return None, f"could not download {src}: {e}"
        return dst, None
    path = os.path.abspath(os.path.expanduser(src))
    if not os.path.isfile(path):
        return None, f"file not found: {src}"
    return path, None


def _res(path):
    """(width, height) via ffprobe, or None."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", path],
            capture_output=True, text=True, timeout=30)
        st = (json.loads(out.stdout or "{}").get("streams") or [{}])[0]
        return (st["width"], st["height"]) if st.get("width") else None
    except Exception:
        return None


def _probe(path):
    """(duration_s, 'WxH', size_bytes) — best effort for the result report."""
    size = os.path.getsize(path) if os.path.isfile(path) else None
    r = _res(path)
    dur = None
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            out = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                capture_output=True, text=True, timeout=30)
            d = float(json.loads(out.stdout or "{}").get("format", {}).get("duration", 0))
            dur = round(d, 2) if d else None
        except Exception:
            pass
    return dur, (f"{r[0]}x{r[1]}" if r else None), size


def _run(cmd, cwd=None, timeout=1200):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stderr or ""
    except subprocess.TimeoutExpired:
        return 1, "ffmpeg timed out"


def _ok(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0


def _concat_copy(ffmpeg, clips, workdir, out):
    """Stream-copy concat — instant and lossless when clips share codec, size, and fps."""
    listfile = os.path.join(workdir, "clips.txt")
    with open(listfile, "w") as f:
        for p in clips:
            f.write("file '%s'\n" % p.replace("'", "'\\''"))   # concat-demuxer quoting
    return _run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", out])


def _concat_scaled(ffmpeg, clips, target, out):
    """Concat clips letterboxed to `target` (w, h) — re-encode; handles mismatched sizes."""
    w, h = target
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    parts, labels = [], []
    for i in range(len(clips)):
        parts.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
                     f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]")
        labels.append(f"[v{i}][{i}:a]")
    filt = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(clips)}:v=1:a=1[v][a]"
    return _run([ffmpeg, "-y", *inputs, "-filter_complex", filt, "-map", "[v]", "-map", "[a]",
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", out])


def video_stitch(clips, music=None, subtitles=None, output=None, output_dir=None, dry_run=False):
    """Concatenate `clips` (paths or URLs) in order into one video with hard cuts, audio kept.
    Optional background `music` (mixed under) and burned-in `subtitles` (SRT). Returns
    {ok, path, clips, duration, resolution, size_bytes} | {ok: False, error, hint?/detail?}."""
    if not isinstance(clips, list) or len(clips) < 2:
        return {"ok": False, "error": "clips must be a list of at least two video files, in play order.",
                "hint": "a single clip needs no stitching — pass two or more"}
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return {"ok": False, "error": "ffmpeg is not installed or not on PATH.",
                "hint": "install ffmpeg (e.g. `brew install ffmpeg` / `apt-get install ffmpeg`), then retry"}

    out_dir = paths.output_dir(output_dir)
    out_path = (os.path.abspath(os.path.expanduser(output)) if output
                else os.path.join(out_dir, f"stitched_{len(clips)}clips.mp4"))

    if dry_run:
        return {"ok": True, "_dry_run": True, "clips": clips, "output": out_path,
                "music": bool(music), "subtitles": bool(subtitles),
                "plan": "concat in order (hard cuts); scale mismatched clips; burn subtitles; overlay music"}

    workdir = tempfile.mkdtemp(prefix="supercmo_stitch_")
    try:
        resolved = []
        for i, c in enumerate(clips):
            path, err = _resolve(c, workdir, f"clip_{i}.mp4")
            if err:
                return {"ok": False, "error": err}
            resolved.append(path)
        music_path = None
        if music:
            music_path, err = _resolve(music, workdir, "music.mp3")
            if err:
                return {"ok": False, "error": f"music: {err}"}
        if subtitles:
            srt_resolved, err = _resolve(subtitles, workdir, "subs.srt")
            if err:
                return {"ok": False, "error": f"subtitles: {err}"}
            srt_local = os.path.join(workdir, "subs.srt")       # the burn pass reads it by this name
            if os.path.abspath(srt_resolved) != srt_local:
                shutil.copy(srt_resolved, srt_local)

        os.makedirs(out_dir, exist_ok=True)

        # 1) Concatenate. Stream-copy when sizes match; scale-and-re-encode when they differ.
        sizes = [_res(p) for p in resolved]
        known = [s for s in sizes if s]
        cat = os.path.join(workdir, "cat.mp4")
        if known and len(set(known)) > 1:
            rc, err = _concat_scaled(ffmpeg, resolved, known[0], cat)
        else:
            rc, err = _concat_copy(ffmpeg, resolved, workdir, cat)
            if (rc != 0 or not _ok(cat)) and known:              # fall back to re-encode on copy failure
                rc, err = _concat_scaled(ffmpeg, resolved, known[0], cat)
        if rc != 0 or not _ok(cat):
            return {"ok": False, "error": "ffmpeg could not concatenate the clips.",
                    "hint": "confirm the clips are valid video files", "detail": err[-500:]}
        stage = cat

        # 2) Burn in subtitles (re-encodes the video). Run in workdir so the filter reads `subs.srt`.
        if subtitles:
            subbed = os.path.join(workdir, "subbed.mp4")
            rc, err = _run([ffmpeg, "-y", "-i", stage, "-vf", "subtitles=subs.srt",
                            "-c:a", "copy", subbed], cwd=workdir)
            if rc != 0 or not _ok(subbed):
                return {"ok": False, "error": "ffmpeg could not burn in the subtitles.",
                        "hint": "check the file is valid SRT", "detail": err[-500:]}
            stage = subbed

        # 3) Lay background music under the clips' own audio (video copied, audio re-mixed).
        if music_path:
            rc, err = _run([ffmpeg, "-y", "-i", stage, "-i", music_path, "-filter_complex",
                            "[1:a]volume=0.35[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
                            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", out_path])
            if rc != 0 or not _ok(out_path):
                return {"ok": False, "error": "ffmpeg could not add the background music.",
                        "hint": "check the music file is valid audio", "detail": err[-500:]}
        else:
            shutil.move(stage, out_path)

        dur, res, size = _probe(out_path)
        return {"ok": True, "path": out_path, "clips": len(resolved),
                "duration": dur, "resolution": res, "size_bytes": size}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
