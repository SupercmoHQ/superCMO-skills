"""Mix a voiceover with a music bed and sound effects into one track — and, when a `video` is given,
lay that mixed track straight onto the video. Local `ffmpeg`, no vendor.

The voiceover (or the video's own speech) is the anchor; music is laid under it and, by default,
**ducked** beneath the speech via `sidechaincompress` so the words stay clear; sound effects drop in
at their offsets. With `video`, the result is the video with its finished soundtrack (one reliable
mux — no separate step); without it, a standalone audio file. Returns {ok, path, duration, ...} |
{ok: False, error, ...}.
"""
import os
import shutil
import tempfile

from . import _ffmpeg

# format -> encoder + default output extension (audio-only outputs)
_CODEC = {"mp3": "libmp3lame", "wav": "pcm_s16le", "aac": "aac", "m4a": "aac",
          "opus": "libopus", "ogg": "libvorbis", "flac": "flac"}
_DEFAULT_FORMAT = "mp3"
_DUCK = "sidechaincompress=threshold=0.03:ratio=8:attack=5:release=250"


def _fmt(output, fmt):
    if fmt and fmt.lower() in _CODEC:
        return fmt.lower()
    if output:
        ext = os.path.splitext(output)[1].lstrip(".").lower()
        if ext in _CODEC:
            return ext
    return _DEFAULT_FORMAT


def _norm_sfx(sfx):
    """Normalize sfx into [{file, at, gain}]. Accepts bare strings or dicts."""
    out = []
    for s in sfx or []:
        if isinstance(s, str):
            out.append({"file": s, "at": 0.0, "gain": 1.0})
        elif isinstance(s, dict) and (s.get("file") or s.get("path")):
            out.append({"file": s.get("file") or s.get("path"),
                        "at": float(s.get("at", 0) or 0), "gain": float(s.get("gain", 1) or 1)})
    return out


def _audio_only_filter(has_music, duck, sfx_meta, music_gain):
    """filter_complex for the audio-only mix (voice = input 0). Returns (graph, n_mix_inputs)."""
    parts, mix = [], []
    if has_music and duck:
        parts.append("[0:a]asplit=2[vmix][vkey]")
        voice_mix, voice_key = "[vmix]", "[vkey]"
    else:
        voice_mix, voice_key = "[0:a]", None
    mix.append(voice_mix)
    idx = 1
    if has_music:
        parts.append(f"[{idx}:a]volume={music_gain}[mg]")
        if duck:
            parts.append(f"[mg]{voice_key}{_DUCK}[mduck]")
            mix.append("[mduck]")
        else:
            mix.append("[mg]")
        idx += 1
    for j, s in enumerate(sfx_meta):
        parts.append(f"[{idx}:a]adelay={max(0, int(round(s['at'] * 1000)))}:all=1,volume={s['gain']}[s{j}]")
        mix.append(f"[s{j}]")
        idx += 1
    graph = (";".join(parts) + ";" + "".join(mix)
             + f"amix=inputs={len(mix)}:duration=first:dropout_transition=0:normalize=0"
               ",alimiter=limit=0.95[a]")
    return graph, len(mix)


def _mux_video_cmd(ffmpeg, video_path, voice_path, music_path, sfx_meta, music_gain, duck, out):
    """ffmpeg command that lays voice + ducked music + sfx (plus the video's own audio, if any) onto
    the video. Output length is the video's (``-shortest``). Returns the command list."""
    has_va = _ffmpeg.has_audio(video_path)
    cmd = [ffmpeg, "-y", "-i", video_path]
    idx = 1
    voice_i = music_i = None
    if voice_path:
        cmd += ["-i", voice_path]
        voice_i = idx
        idx += 1
    if music_path:
        cmd += ["-i", music_path]
        music_i = idx
        idx += 1
    sfx_i = []
    for s in sfx_meta:
        cmd += ["-i", s["_path"]]
        sfx_i.append(idx)
        idx += 1

    parts = []
    speech = (["[0:a]"] if has_va else []) + ([f"[{voice_i}:a]"] if voice_i is not None else [])
    sp = None
    if len(speech) == 1:
        sp = speech[0]
    elif len(speech) > 1:
        parts.append(f"{''.join(speech)}amix=inputs={len(speech)}:duration=longest:normalize=0[sp]")
        sp = "[sp]"

    mix = []
    if music_i is not None:
        parts.append(f"[{music_i}:a]volume={music_gain}[mg]")
        if sp and duck:
            parts.append(f"{sp}asplit=2[spmix][spkey]")
            # Pad the sidechain to +inf so sidechaincompress runs the MUSIC's full length (it ends
            # at the shorter input otherwise — truncating the bed to the VO). Music ducks only while
            # the VO plays, then rides at full level.
            parts.append("[spkey]apad[spkeyp]")
            parts.append(f"[mg][spkeyp]{_DUCK}[mduck]")
            mix += ["[spmix]", "[mduck]"]
        else:
            mix += ([sp] if sp else []) + ["[mg]"]
    elif sp:
        mix.append(sp)
    for j, i in enumerate(sfx_i):
        parts.append(f"[{i}:a]adelay={max(0, int(round(sfx_meta[j]['at'] * 1000)))}:all=1,"
                     f"volume={sfx_meta[j]['gain']}[s{j}]")
        mix.append(f"[s{j}]")

    # `apad` the final mix to +inf so `-shortest` bounds the output to the VIDEO, never to a shorter
    # audio track (a VO/bed shorter than the clip must NOT truncate the video — the video is the canvas).
    graph = ((";".join(parts) + (";" if parts else ""))
             + "".join(mix)
             + f"amix=inputs={len(mix)}:duration=longest:dropout_transition=0:normalize=0"
               ",apad,alimiter=limit=0.95[aout]")
    cmd += ["-filter_complex", graph, "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", out]
    return cmd


def audio_mix(voice=None, music=None, sfx=None, video=None, music_gain=None, duck=True, format=None,
              output=None, output_dir=None, dry_run=False):
    """Assemble the audio for an ad. Without `video`: mix `voice` (required, the VO — anchors the
    length) with an optional `music` bed (ducked when `duck`) and `sfx` -> an audio file. With
    `video`: lay `voice` + ducked `music` + `sfx` (plus the video's OWN speech, if any) onto the
    video and return the video with its finished soundtrack. `sfx` = list of {file, at, gain} or bare
    paths; `music_gain` (default 0.25) sets the music level before ducking."""
    sfx_meta = _norm_sfx(sfx)
    music_gain = 0.25 if music_gain is None else float(music_gain)
    to_video = bool(video and str(video).strip())

    if to_video:
        if not (voice or music or sfx_meta):
            return {"ok": False, "error": "give at least one of voice, music, or sfx to lay onto the video."}
    elif not isinstance(voice, str) or not voice.strip():
        return {"ok": False, "error": "voice is required (the voiceover — a file path or http(s) URL); "
                "or pass a `video` to lay a mix onto."}

    if to_video:
        out = _ffmpeg.out_path(output, output_dir, "mixed.mp4")
    else:
        fmt = _fmt(output, format)
        out = _ffmpeg.out_path(output, output_dir, f"mixed.{fmt}")

    if dry_run:
        return {"ok": True, "_dry_run": True, "output": out, "onto_video": to_video,
                "has_music": bool(music), "sfx": len(sfx_meta), "duck": bool(music) and duck,
                "plan": "duck music under the speech (sidechaincompress), drop SFX at offsets, "
                        + ("mux onto the video" if to_video else "amix to one track")}

    ffmpeg, err = _ffmpeg.require("ffmpeg")
    if err:
        return err

    workdir = tempfile.mkdtemp(prefix="supercmo_mix_")
    try:
        vid_path = None
        if to_video:
            vid_path, err = _ffmpeg.resolve(video, workdir, "in.mp4")
            if err:
                return {"ok": False, "error": f"video: {err}"}
        voice_path = None
        if voice:
            voice_path, err = _ffmpeg.resolve(voice, workdir, "voice.wav")
            if err:
                return {"ok": False, "error": f"voice: {err}"}
        music_path = None
        if music:
            music_path, err = _ffmpeg.resolve(music, workdir, "music.mp3")
            if err:
                return {"ok": False, "error": f"music: {err}"}
        for i, s in enumerate(sfx_meta):
            p, err = _ffmpeg.resolve(s["file"], workdir, f"sfx_{i}.wav")
            if err:
                return {"ok": False, "error": f"sfx[{i}]: {err}"}
            s["_path"] = p

        if to_video:
            rc, err = _ffmpeg.run(_mux_video_cmd(ffmpeg, vid_path, voice_path, music_path, sfx_meta,
                                                 music_gain, duck, out))
        elif not music_path and not sfx_meta:
            rc, err = _ffmpeg.run([ffmpeg, "-y", "-i", voice_path, "-map", "0:a", "-c:a", _CODEC[fmt], out])
        else:
            graph, _n = _audio_only_filter(bool(music_path), duck, sfx_meta, music_gain)
            cmd = [ffmpeg, "-y", "-i", voice_path]
            if music_path:
                cmd += ["-i", music_path]
            for s in sfx_meta:
                cmd += ["-i", s["_path"]]
            cmd += ["-filter_complex", graph, "-map", "[a]", "-c:a", _CODEC[fmt], out]
            rc, err = _ffmpeg.run(cmd)

        if rc != 0 or not _ffmpeg.ok(out):
            return {"ok": False, "error": "ffmpeg could not assemble the audio.",
                    "hint": "confirm the video/voice/music/sfx are valid media files", "detail": err[-500:]}
        dur, res, sz = _ffmpeg.probe(out)
        result = {"ok": True, "path": out, "duration": dur, "size_bytes": sz}
        if to_video:
            result["resolution"] = res
        else:
            result["format"] = fmt
        return result
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":                                       # no-network / no-ffmpeg self-check
    g, n = _audio_only_filter(True, True, [{"at": 1.0, "gain": 0.8}], 0.25)
    assert n == 3 and "sidechaincompress" in g and "asplit" in g and "adelay=1000" in g, g
    # video mux command: video + voice + ducked music -> mux with -shortest
    cmd = _mux_video_cmd("ff", "v.mp4", "vo.wav", "m.mp3", [], 0.25, True, "out.mp4")
    joined = " ".join(cmd)
    assert "-shortest" in cmd and "[aout]" in joined and "sidechaincompress" in joined, joined
    assert cmd.count("-i") == 3
    assert _fmt("x.wav", None) == "wav" and _fmt(None, None) == "mp3"
    assert _norm_sfx(["a.wav", {"file": "b.wav", "at": 2}])[1]["at"] == 2.0
    dv = audio_mix(video="v.mp4", music="m.mp3", dry_run=True)
    assert dv["ok"] and dv["onto_video"] and dv["output"].endswith(".mp4"), dv
    da = audio_mix("vo.wav", music="m.mp3", dry_run=True)
    assert da["ok"] and not da["onto_video"], da
    assert not audio_mix()["ok"] and not audio_mix(video="v.mp4")["ok"]  # need a source
    print("audio_mix self-check OK")
