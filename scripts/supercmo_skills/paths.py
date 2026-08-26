"""Canonical filesystem locations for generated media — resolved in one place.

The env-var name and its default live only here; every Python consumer (image/video/audio
persistence) resolves through `output_dir()`. The runtime may set the env var to redirect
(e.g. a session dir); unset falls back to the cwd-relative default.

(Scratch/working files are a shell-side concern — the analyzing-products download reads
`$SUPERCMO_SCRATCH_DIR` directly in bash, which can't import this module.)
"""
import datetime
import os

OUTPUT_DIR_ENV = "SUPERCMO_OUTPUT_DIR"     # durable generated media (images / video / audio)
_OUTPUT_DEFAULT = "./supercmo-media"       # cwd-relative: the host's working dir


def output_dir(explicit=None):
    """Where durable generated media lands: explicit arg > $SUPERCMO_OUTPUT_DIR > ./supercmo-media."""
    d = explicit or os.environ.get(OUTPUT_DIR_ENV) or _OUTPUT_DEFAULT
    return os.path.abspath(os.path.expanduser(d))


def research_dir(explicit=None, stamp=None):
    """Where a research run's documents land — `<output dir>/competitor-research/<YYYY-MM-DD-HHMM>`,
    a folder per run. Resolves through the same env var as generated media."""
    if explicit:
        return os.path.abspath(os.path.expanduser(explicit))
    stamp = stamp or datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    base = os.path.join(output_dir(), "competitor-research", stamp)
    candidate, n = base, 2
    # Claimed by creating it: two runs starting in the same minute would otherwise resolve to the
    # same name, and the second would write over the first.
    while True:
        try:
            os.makedirs(candidate)
            return candidate
        except FileExistsError:
            candidate, n = f"{base}-{n}", n + 1
