"""Anonymous, opt-out usage telemetry — stdlib only, never breaks a call.

WHAT: counts which tools/skills get used. Sends ONLY an allowlist of fields
(tool name, ok/fail, duration, versions, anonymous install id). NEVER prompts,
tool arguments, generated content, file paths, hostnames, IPs, or account ids.

HOW (reliability): every tool call appends one JSON line to a per-process spool
file, then a daemon thread uploads batches best-effort. The spool survives a
SIGKILL (the MCP host kills stdio servers abruptly); leftover spools are drained
by the next process. The whole path is wrapped so a telemetry failure can NEVER
surface as a tool error or block a call.

OPT-OUT (env wins over config): SUPERCMO_TELEMETRY=false|log, DO_NOT_TRACK,
DISABLE_TELEMETRY, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC. Default is ON for the
MCP server (no prompt surface); the CLI prompts in `supercmo init` and writes the
choice to <home>/telemetry.json, which this module then honours.

See docs: superCMO-skills/TELEMETRY.md.
"""
from __future__ import annotations

import json
import os
import platform
import sys
import threading
import time
import urllib.request
import uuid
from pathlib import Path

_EVENT = "oss_tool_used"
_DEFAULT_ENDPOINT = "https://api.getsupercmo.ai/api/v1/telemetry/events"
_SPOOL_MAX_LINES = 500          # per-process cap; drop past this
_BATCH_MAX = 100                # events per upload
_FLUSH_INTERVAL = 30.0          # min seconds between uploads
_HTTP_TIMEOUT = 2.0             # seconds per attempt
_UA = "supercmo-telemetry/1"

# ── allowlist: the ONLY keys that ever leave the machine ────────────────────
_ALLOWLIST = (
    "event", "install_id", "session_id", "event_id", "tool_name", "surface",
    "model_id", "provider", "ok", "duration_ms", "error_class", "error_code",
    "route", "supercmo_version", "os", "arch", "python_version", "is_ci",
    "agent", "sample_rate",
)

_CI_ENVS = ("CI", "GITHUB_ACTIONS", "BUILDKITE", "GITLAB_CI", "CIRCLECI",
            "TRAVIS", "APPVEYOR", "TEAMCITY_VERSION", "JENKINS_URL")
_AGENT_ENVS = {  # env var present -> label (value never read)
    "CLAUDECODE": "claude", "CURSOR_EDITOR": "cursor",
    "GEMINI_CLI": "gemini", "GITHUB_COPILOT_CLI_MODE": "copilot",
}
_FALSEY = {"", "0", "false", "no", "disabled", "off"}


# ── process-static context (computed once, cheaply) ─────────────────────────
def _is_ci() -> bool:
    return any(os.environ.get(v) for v in _CI_ENVS)


def _agent() -> str | None:
    labels = [lbl for env, lbl in _AGENT_ENVS.items() if os.environ.get(env)]
    return ",".join(labels) if labels else None


def _version() -> str:
    try:
        from importlib.metadata import version
        return version("supercmo-skills")
    except Exception:
        return "unknown"


_SESSION_ID = str(uuid.uuid4())
_COUNTER = 0
_COUNTER_LOCK = threading.Lock()
_CTX = {
    "os": platform.system().lower() or "unknown",
    "arch": platform.machine().lower() or "unknown",
    "python_version": ".".join(map(str, sys.version_info[:2])),
    "supercmo_version": _version(),
    "is_ci": _is_ci(),
    "agent": _agent(),
    "sample_rate": 100,
}

_flush_lock = threading.Lock()
_flushing = False
_last_flush = 0.0
_surface = None  # set by the entry point (mcp/cli); env SUPERCMO_SURFACE wins over it


def set_surface(name: str) -> None:
    """Entry points label their surface once (MCP server → 'mcp', CLI → 'cli')."""
    global _surface
    _surface = name


def _surface_ctx() -> str:
    # env wins so a CLI parent can label MCP subprocesses it spawns as 'cli'.
    return os.environ.get("SUPERCMO_SURFACE", "").strip() or _surface or "direct"


# ── paths ───────────────────────────────────────────────────────────────────
def _home() -> Path:
    env = os.environ.get("SUPERCMO_HOME", "").strip()
    return Path(env) if env else (Path.home() / ".supercmo")


def _state_dir() -> Path:
    # State (NOT config): a random install id lives here so it is never synced,
    # dotfile-committed, or Docker-copied — which would merge distinct installs.
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:
        base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "supercmo"


def _consent_path() -> Path:
    return _home() / "telemetry.json"


def _install_id_path() -> Path:
    return _state_dir() / "install-id"


def _spool_dir() -> Path:
    return _state_dir() / "telemetry-spool"


def _endpoint() -> str:
    return os.environ.get("SUPERCMO_TELEMETRY_ENDPOINT", _DEFAULT_ENDPOINT)


# ── install id: random UUID4, atomic create, never a machine fingerprint ────
def install_id() -> str:
    if _is_ci():
        return "CI"  # collapse all CI runs to one identity; never mint per-run
    try:
        p = _install_id_path()
        if p.exists():
            v = p.read_text(encoding="utf-8").strip()
            if v:
                return v
        p.parent.mkdir(parents=True, exist_ok=True)
        new = str(uuid.uuid4())
        tmp = p.parent / f".install-id.{os.getpid()}.tmp"
        tmp.write_text(new, encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        try:
            os.link(tmp, p)          # atomic: exactly one racing process wins
        except FileExistsError:
            pass                     # someone else won; fall through to re-read
        finally:
            try:
                tmp.unlink()
            except OSError:
                pass
        return p.read_text(encoding="utf-8").strip() or "<unknown>"
    except Exception:
        return "<unknown>"           # never raise from id creation


# ── enabled / mode resolution (env wins over config) ────────────────────────
def _mode() -> str:
    """'off' | 'log' | 'on'."""
    try:
        v = os.environ.get("SUPERCMO_TELEMETRY", "").strip().lower()
        if v == "log":
            return "log"
        if v in _FALSEY and v != "":
            return "off"
        if os.environ.get("DO_NOT_TRACK", "").strip().lower() in ("1", "true"):
            return "off"
        if os.environ.get("DISABLE_TELEMETRY", "").strip():
            return "off"
        if os.environ.get("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "").strip():
            return "off"
        # config file (written by `supercmo init` consent); absent -> opt-out default ON
        p = _consent_path()
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("enabled") is False:
                return "off"
        return "on"
    except Exception:
        return "on"


def is_enabled() -> bool:
    return _mode() != "off"


def set_consent(enabled: bool) -> None:
    """Persist the CLI consent choice to <home>/telemetry.json."""
    try:
        p = _consent_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"enabled": bool(enabled)}) + "\n", encoding="utf-8")
    except Exception:
        pass


def reset_install_id() -> None:
    try:
        _install_id_path().unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass


# ── record: build allowlisted event, spool it, trigger upload ───────────────
def record(tool_name: str, ok: bool, duration_ms: int, *, surface: str | None = None,
           model_id: str | None = None, provider: str | None = None,
           route: str | None = None, error_class: str | None = None,
           error_code: str | None = None) -> None:
    """Emit one usage event. NEVER raises, NEVER blocks on the network.

    Called from the shared client dispatch (all surfaces) and the MCP server. `surface`
    defaults to the process context (mcp/cli/direct)."""
    try:
        mode = _mode()
        if mode == "off":
            return
        global _COUNTER
        with _COUNTER_LOCK:
            _COUNTER += 1
            n = _COUNTER
        ev = {
            "event": _EVENT,
            "install_id": install_id(),
            "session_id": _SESSION_ID,
            "event_id": f"{_SESSION_ID}:{n}",
            "tool_name": tool_name,
            "surface": surface or _surface_ctx(),
            "model_id": model_id,
            "provider": provider,
            "ok": bool(ok),
            "duration_ms": int(duration_ms),
            "error_class": error_class,
            "error_code": error_code,
            "route": route,
            **_CTX,
        }
        ev = {k: ev.get(k) for k in _ALLOWLIST}   # hard allowlist — nothing else ships
        if mode == "log":
            sys.stderr.write("[supercmo telemetry] " + json.dumps(ev) + "\n")
            return
        _spool(ev)
        _maybe_flush()
    except Exception:
        pass  # telemetry must never break the caller


def _spool(ev: dict) -> None:
    d = _spool_dir()
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"spool-{os.getpid()}.jsonl"
    try:
        if f.exists() and sum(1 for _ in f.open(encoding="utf-8")) >= _SPOOL_MAX_LINES:
            return  # bounded: drop rather than grow unbounded
    except Exception:
        pass
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ev) + "\n")


# ── upload: daemon thread, best-effort, drains ALL spools incl. orphans ─────
def _maybe_flush(force: bool = False) -> None:
    global _flushing, _last_flush
    with _flush_lock:
        if _flushing:
            return
        now = time.time()
        if not force and (now - _last_flush) < _FLUSH_INTERVAL:
            return
        _flushing = True
    t = threading.Thread(target=_flush_all, daemon=True)
    t.start()


def _flush_all() -> None:
    global _flushing, _last_flush
    try:
        d = _spool_dir()
        if not d.exists():
            return
        for f in sorted(d.glob("spool-*.jsonl")):
            _flush_file(f)
    except Exception:
        pass
    finally:
        with _flush_lock:
            _flushing = False
            _last_flush = time.time()


def _flush_file(f: Path) -> None:
    try:
        lines = [ln for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except Exception:
        return
    if not lines:
        try:
            f.unlink()
        except Exception:
            pass
        return
    remaining = list(lines)
    while remaining:
        batch, remaining = remaining[:_BATCH_MAX], remaining[_BATCH_MAX:]
        events = []
        for ln in batch:
            try:
                events.append(json.loads(ln))
            except Exception:
                pass
        if events and not _post(events):
            return  # network failure: leave the whole file for next time
    try:
        f.unlink()  # everything sent
    except Exception:
        pass


def _post(events: list) -> bool:
    body = json.dumps({"events": events}).encode("utf-8")
    for attempt in range(2):  # one retry, no backoff ladder
        try:
            req = urllib.request.Request(
                _endpoint(), data=body, method="POST",
                headers={"Content-Type": "application/json", "User-Agent": _UA},
            )
            with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
                return 200 <= resp.status < 300
        except Exception:
            if attempt == 1:
                return False
    return False


# ── status (for `supercmo telemetry status`) ────────────────────────────────
def status() -> dict:
    return {
        "mode": _mode(),
        "enabled": is_enabled(),
        "install_id": install_id(),
        "endpoint": _endpoint(),
        "consent_file": str(_consent_path()),
        "install_id_file": str(_install_id_path()),
        "example_payload": {k: _CTX.get(k) for k in _ALLOWLIST if k in _CTX},
    }
