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


def _dur(path):
    """Duration in seconds, or None."""
    return _probe(path)[0]


def _build_narration(ffmpeg, takes, clip_durations, workdir):
    """One continuous narration track aligned to the clips: take N starts where clip N starts, and is
    padded with silence to that clip's length. Returns (path, None) | (None, error). A take longer than
    its clip is an error, not a truncation — the fix is a shorter line, never a faster read."""
    padded = []
    for i, (take, clip_len) in enumerate(zip(takes, clip_durations)):
        take_len = _dur(take)
        if clip_len and take_len and take_len > clip_len + 0.05:
            return None, (f"narration take {i + 1} runs {take_len:.1f}s but clip {i + 1} is only "
                          f"{clip_len:.1f}s — shorten the line and re-voice that take")
        out = os.path.join(workdir, f"vo_{i}.wav")
        # pad to the clip's length so the next take starts exactly on the next clip
        rc, err = _run([ffmpeg, "-y", "-i", take, "-af",
                        f"apad=whole_dur={clip_len}" if clip_len else "anull",
                        "-ar", "48000", "-ac", "2", out])
        if rc != 0 or not _ok(out):
            return None, f"could not prepare narration take {i + 1}: {err[-300:]}"
        padded.append(out)
    listing = os.path.join(workdir, "vo.txt")
    with open(listing, "w") as fh:
        for p in padded:
            fh.write(f"file '{p}'\n")
    joined = os.path.join(workdir, "narration.wav")
    rc, err = _run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", listing, "-c", "copy", joined])
    if rc != 0 or not _ok(joined):
        return None, f"could not join the narration takes: {err[-300:]}"
    return joined, None


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


def _clip_src(clip):
    """A clip is a path/URL string, or an object {clip|url|path, in, out} to trim before joining.
    Returns (src, in_seconds, out_seconds)."""
    if isinstance(clip, dict):
        return (clip.get("clip") or clip.get("url") or clip.get("path"),
                clip.get("in"), clip.get("out"))
    return clip, None, None


def _trim(ffmpeg, path, t_in, t_out, workdir, i):
    """Cut [t_in, t_out] seconds out of `path` (re-encode for an accurate cut). (trimmed, None) |
    (None, error). Never raises: non-numeric or out-of-range in/out return a structured error."""
    out = os.path.join(workdir, f"trim_{i}.mp4")
    try:
        start = float(t_in) if t_in is not None else 0.0
        stop = float(t_out) if t_out is not None else None
    except (TypeError, ValueError):
        return None, f"in/out must be numbers of seconds; got in={t_in!r}, out={t_out!r}"
    if start < 0 or (stop is not None and stop <= start):
        return None, f"trim needs 0 <= in < out (seconds); got in={start}, out={stop}"
    cmd = [ffmpeg, "-y"]
    if start:
        cmd += ["-ss", str(start)]
    cmd += ["-i", path]
    if stop is not None:
        cmd += ["-t", str(stop - start)]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", out]
    rc, err = _run(cmd)
    if rc != 0 or not _ok(out):                                  # includes in >= clip duration (empty cut)
        return None, f"could not trim (in={t_in}, out={t_out}): {err[-200:]}"
    return out, None


def video_stitch(clips, music=None, subtitles=None, narration=None, output=None, output_dir=None,
                 dry_run=False):
    """Concatenate `clips` in order into one video with hard cuts, audio kept. Each clip is a path
    or URL, or an object {clip, in, out} to trim to [in, out] seconds before joining. Optional
    `narration` (one take per clip, laid over with the clips' own audio ducked under), background
    `music` (mixed under) and burned-in `subtitles` (SRT). Returns
    {ok, path, clips, duration, resolution, size_bytes} | {ok: False, error, hint?/detail?}."""
    if not isinstance(clips, list) or len(clips) < 2:
        return {"ok": False, "error": "clips must be a list of at least two video files, in play order.",
                "hint": "a single clip needs no stitching — pass two or more"}
    if narration is not None:
        if not isinstance(narration, list) or len(narration) != len(clips):
            return {"ok": False,
                    "error": "narration must be a list with one audio take per clip, in the same order.",
                    "hint": f"{len(clips)} clips were passed, so pass {len(clips)} takes"}
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
                "narration": [{"clip": i + 1, "take": t} for i, t in enumerate(narration or [])],
                "plan": "concat in order (hard cuts); scale mismatched clips; burn subtitles; "
                        "lay narration over with clip audio ducked under; overlay music"}

    workdir = tempfile.mkdtemp(prefix="supercmo_stitch_")
    try:
        resolved = []
        for i, c in enumerate(clips):
            src, t_in, t_out = _clip_src(c)
            if not src:
                return {"ok": False, "error": f"clip {i}: missing a file path or URL."}
            path, err = _resolve(src, workdir, f"clip_{i}.mp4")
            if err:
                return {"ok": False, "error": err}
            if t_in is not None or t_out is not None:
                path, err = _trim(ffmpeg, path, t_in, t_out, workdir, i)
                if err:
                    return {"ok": False, "error": f"clip {i}: {err}"}
            resolved.append(path)
        music_path = None
        if music:
            music_path, err = _resolve(music, workdir, "music.mp3")
            if err:
                return {"ok": False, "error": f"music: {err}"}
        takes = []
        for i, n in enumerate(narration or []):
            path, err = _resolve(n, workdir, f"vo_src_{i}.wav")
            if err:
                return {"ok": False, "error": f"narration take {i + 1}: {err}"}
            takes.append(path)
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

        # 1b) Lay the narration over, one take per clip, with the clips' own audio ducked beneath it.
        if takes:
            vo, err = _build_narration(ffmpeg, takes, [_dur(p) for p in resolved], workdir)
            if err:
                return {"ok": False, "error": err,
                        "hint": "one take per clip, each no longer than the clip it belongs to"}
            voiced = os.path.join(workdir, "voiced.mp4")
            rc, err = _run([ffmpeg, "-y", "-i", stage, "-i", vo, "-filter_complex",
                            "[0:a]volume=0.25[amb];[1:a]volume=1.0[vo];"
                            "[amb][vo]amix=inputs=2:duration=first:dropout_transition=0[a]",
                            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", voiced])
            if rc != 0 or not _ok(voiced):
                return {"ok": False, "error": "ffmpeg could not lay the narration over the clips.",
                        "hint": "check the takes are valid audio files", "detail": err[-500:]}
            stage = voiced

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
