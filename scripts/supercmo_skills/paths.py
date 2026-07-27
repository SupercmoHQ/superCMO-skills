"""Canonical filesystem locations for generated media — resolved in one place.

The env-var name and its default live only here; every Python consumer (image/video/tts
persistence) resolves through `output_dir()`. The runtime may set the env var to redirect
(e.g. a session dir); unset falls back to the cwd-relative default.

(Scratch/working files are a shell-side concern — the analyzing-products download reads
`$SUPERCMO_SCRATCH_DIR` directly in bash, which can't import this module.)
"""
import os

OUTPUT_DIR_ENV = "SUPERCMO_OUTPUT_DIR"     # durable generated media (images / video / audio)
_OUTPUT_DEFAULT = "./supercmo-media"       # cwd-relative: the host's working dir


def output_dir(explicit=None):
    """Where durable generated media lands: explicit arg > $SUPERCMO_OUTPUT_DIR > ./supercmo-media."""
    d = explicit or os.environ.get(OUTPUT_DIR_ENV) or _OUTPUT_DEFAULT
    return os.path.abspath(os.path.expanduser(d))
