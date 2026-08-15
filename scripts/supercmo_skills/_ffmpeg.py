"""Shared ffmpeg/ffprobe helpers for the local post-production tools (caption_video, audio_mix,
reframe, video_overlay) — stdlib + the system ffmpeg/ffprobe binaries only, no vendor, no key.

Mirrors the resolve/run/probe helpers proven in `stitch.py`; kept in one place so the four new
local tools share them instead of each re-cloning. `stitch.py` predates this module and keeps its
own copies (surgical — a shipped tool is not refactored here).
"""
import json
import os
import shutil
import subprocess

import supercmo_env

from . import paths


def resolve(src, workdir, name):
    """(local_path, None) | (None, error). Downloads an http(s) URL into `workdir` as `name`,
    SSRF-guarded (blocks internal/metadata IPs); otherwise resolves a local file path."""
    src = src.strip() if isinstance(src, str) else src
    if not src:
        return None, "an input path is empty"
    if isinstance(src, str) and src.startswith(("http://", "https://")):
        dst = os.path.join(workdir, name)
        try:
            supercmo_env.safe_download(src, dst)
        except Exception as e:                                   # blocked / network / 404 / etc.
            return None, f"could not download {src}: {e}"
        return dst, None
    path = os.path.abspath(os.path.expanduser(src))
    if not os.path.isfile(path):
        return None, f"file not found: {src}"
    return path, None


def run(cmd, cwd=None, timeout=1200):
    """Run a command; return (returncode, stderr)."""
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stderr or ""
    except subprocess.TimeoutExpired:
        return 1, "ffmpeg timed out"


def ok(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0


def require(binary="ffmpeg"):
    """(path, None) | (None, error_dict). Locate ffmpeg/ffprobe with a structured install hint."""
    p = shutil.which(binary)
    if p:
        return p, None
    return None, {"ok": False, "error": f"{binary} is not installed or not on PATH.",
                  "hint": "install ffmpeg (e.g. `brew install ffmpeg` / `apt-get install ffmpeg`), then retry"}


def _ffprobe_json(args):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    try:
        out = subprocess.run([ffprobe, "-v", "error", *args, "-of", "json"],
                             capture_output=True, text=True, timeout=30)
        return json.loads(out.stdout or "{}")
    except Exception:
        return None


def video_size(path):
    """(width, height) via ffprobe, or None."""
    data = _ffprobe_json(["-select_streams", "v:0", "-show_entries", "stream=width,height", path])
    st = ((data or {}).get("streams") or [{}])[0]
    return (st["width"], st["height"]) if st.get("width") else None


def duration(path):
    """Media duration in seconds (float, 3 dp), or None. Works for audio and video."""
    data = _ffprobe_json(["-show_entries", "format=duration", path])
    try:
        d = float((data or {}).get("format", {}).get("duration", 0))
    except (TypeError, ValueError):
        return None
    return round(d, 3) if d else None


def has_audio(path):
    """True if the file has ≥1 audio stream. Best-effort → True when ffprobe is unavailable."""
    data = _ffprobe_json(["-select_streams", "a", "-show_entries", "stream=index", path])
    if data is None:
        return True
    return bool(data.get("streams"))


def fps(path):
    """Video frame rate as a float (from r_frame_rate), or None."""
    data = _ffprobe_json(["-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", path])
    rate = ((data or {}).get("streams") or [{}])[0].get("r_frame_rate")
    try:
        num, den = str(rate).split("/")
        return round(float(num) / float(den), 3) if float(den) else None
    except (ValueError, AttributeError, ZeroDivisionError):
        return None


def probe(path):
    """(duration_s, 'WxH'|None, size_bytes) — best-effort result report."""
    size = os.path.getsize(path) if os.path.isfile(path) else None
    r = video_size(path)
    return duration(path), (f"{r[0]}x{r[1]}" if r else None), size


def out_path(output, output_dir, default_name):
    """Resolve the output path: explicit `output` > `output_dir`/default > $SUPERCMO_OUTPUT_DIR."""
    p = (os.path.abspath(os.path.expanduser(output)) if output
         else os.path.join(paths.output_dir(output_dir), default_name))
    parent = os.path.dirname(p)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return p
