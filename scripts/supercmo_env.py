#!/usr/bin/env python3
"""SuperCMO environment + routing helpers (standard library only).

Every network script imports this first.

Credentials resolve from the process environment. A host can populate it via its MCP config
`env` block — Claude `.mcp.json`, Cursor `.cursor/mcp.json`, Codex `~/.codex/config.toml`
`[mcp_servers.*.env]` — or the user can export the vars. On import we ALSO load a fixed key
file, `~/.supercmo/.env` (the same idiom Hermes uses for `~/.hermes/.env`), so keys work on any
host without shell/GUI-env gymnastics. Precedence: a real env value always wins; the file only
fills vars that are empty or unset (a host's `${VAR:-}` ref injects an empty string — treated as
unset). No-op when the file is absent.

Route resolution — vendor calls pick their path in priority order:
  BYOK (direct vendor key in env) -> SUPERCMO_API_KEY (the metered proxy at
  SUPERCMO_API_URL) -> actionable error.
CLI:
  supercmo_env.py --status    # which keys are present in the environment
  supercmo_env.py --dry-run   # no network calls — prints a notice
"""
import http.client
import io
import ipaddress
import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_API_URL = "https://api.getsupercmo.ai"
PROXY_BASE = "/api/v1/supercmo/proxy"
ME_PATH = "/api/v1/supercmo/me"
RETRIES = 3
BACKOFF = [1, 2, 4]

KEY_FILE = os.path.join(os.path.expanduser("~"), ".supercmo", ".env")


def _load_key_file(path=KEY_FILE):
    """Load `~/.supercmo/.env` (KEY=VALUE, `#` comments, stdlib-only) into os.environ. A real env
    value wins; the file fills only empty/unset vars. Silent no-op if the file is missing/unreadable."""
    try:
        # errors="replace": a stray non-UTF-8 byte (e.g. an accented char in a comment, a smart quote
        # saved as Latin-1) must never crash startup or block the ASCII key lines — decode leniently
        # rather than raise UnicodeDecodeError (which is not an OSError, so it would escape otherwise).
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if v[:1] not in ("'", '"') and " #" in v:   # strip an inline comment on an unquoted value
            v = v.split(" #", 1)[0].strip()
        v = v.strip("'").strip('"')
        if k and v and not os.environ.get(k):        # real env wins; "" (unset ${VAR:-}) gets filled
            os.environ[k] = v


_load_key_file()  # populate the env from ~/.supercmo/.env before any key is read


def reload_keys():
    """Re-read ~/.supercmo/.env into os.environ. Idempotent — fills only empty/unset vars and a real
    env value (e.g. a shell export) still wins — so it's called at every key lookup: a key added to
    the file AFTER the server started is picked up on the next tool call, no host restart needed.
    (Standard late-binding of file credentials, like boto3/gcloud/kubectl re-resolving their cred
    files; the file read is ~1ms, dwarfed by the vendor call it precedes.)"""
    _load_key_file()


def dbg(msg):
    """Low-volume diagnostic line to stderr (→ the host's mcp-stderr.log). stdout is the
    JSON-RPC channel, so diagnostics MUST go to stderr. Gated by SUPERCMO_DEBUG (default on)
    so it can be silenced with SUPERCMO_DEBUG=0."""
    if os.environ.get("SUPERCMO_DEBUG", "1") not in ("0", "false", "no", ""):
        try:
            sys.stderr.write(f"[supercmo {time.strftime('%H:%M:%S')}] {msg}\n")
            sys.stderr.flush()
        except Exception:
            pass
# Some CDNs/edges reject urllib's default "Python-urllib/x.y" User-Agent with a 403; a
# browser-like UA avoids those false rejections. Callers may override via a User-Agent in `headers`.
_USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

def api_url():
    return (os.environ.get("SUPERCMO_API_URL") or DEFAULT_API_URL).rstrip("/")


def supercmo_key():
    reload_keys()
    return os.environ.get("SUPERCMO_API_KEY")


def resolve_vendor_route(*byok_vars):
    """('direct', None) when any BYOK var is set; ('proxy', key) when the
    SuperCMO key is available; ('none', hint) otherwise. Re-reads ~/.supercmo/.env first, so a key
    added after the server started resolves live on this call — no host restart."""
    reload_keys()
    for var in byok_vars:
        if os.environ.get(var):
            return "direct", None
    key = supercmo_key()
    if key:
        return "proxy", key
    hint = ("No key set. Two options: (A) Managed — run "
            "`npx --yes github:SupercmoHQ/superCMO-skills login` to sign in and pay per use; or "
            f"(B) bring your own {' or '.join(byok_vars)} — add it to ~/.supercmo/.env. "
            "Ask the user which option they want; don't run login unless they choose managed. Then try again.")
    return "none", hint


def _request(method, url, body=None, headers=None, timeout=120, retries=None):
    """JSON request with retries. Returns (parsed, status, error). `retries` overrides the module
    default — pass 1 for a status poll so a single unanswered request can't stack up 3×timeout of
    dead wait inside one call (the caller paces its own retry loop)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    hdrs = {"Content-Type": "application/json", "User-Agent": _USER_AGENT, **(headers or {})}
    last_err, last_status = None, None
    attempts = RETRIES if retries is None else max(1, retries)
    for attempt in range(attempts):
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8")), resp.status, None
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            last_err, last_status = detail, e.code
            if e.code in (400, 401, 402, 403, 404, 409, 429):
                return None, e.code, detail  # no retry on client errors / rate limits
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = f"{type(e).__name__}: {e}"
        if attempt < attempts - 1:
            time.sleep(BACKOFF[min(attempt, len(BACKOFF) - 1)])
    return None, last_status, last_err


def _request_raw(method, url, body=None, headers=None, timeout=120, retries=None,
                 raw_body=None, content_type=None):
    """Like _request but returns the raw response bytes (for binary responses, e.g. audio).
    Returns (data_bytes, content_type, status, error). `retries` overrides the module default —
    pass a small value (e.g. 1) for media downloads so a slow CDN can't consume minutes of the
    caller's timeout budget on top of an already-long generation.

    Pass `raw_body` (bytes) + `content_type` to send a RAW BINARY body verbatim (e.g. a media
    upload PUT to vendor storage) instead of a JSON body — this keeps binary uploads on the seam."""
    if raw_body is not None:
        data = raw_body
        hdrs = {"User-Agent": _USER_AGENT, **(headers or {})}
        if content_type:
            hdrs["Content-Type"] = content_type
    else:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        hdrs = {"Content-Type": "application/json", "User-Agent": _USER_AGENT, **(headers or {})}
    last_err, last_status = None, None
    attempts = RETRIES if retries is None else max(1, retries)
    for attempt in range(attempts):
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), resp.headers.get("Content-Type", ""), resp.status, None
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            last_err, last_status = detail, e.code
            if e.code in (400, 401, 402, 403, 404, 429):
                return None, None, e.code, detail
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = f"{type(e).__name__}: {e}"
        if attempt < attempts - 1:
            time.sleep(BACKOFF[min(attempt, len(BACKOFF) - 1)])
    return None, None, last_status, last_err


# --- SSRF-safe fetch of an agent-supplied URL (OWASP SSRF Cheat Sheet / CWE-918) --------------
# Validate the RESOLVED IP (not the URL string) and connect to that pinned IP, so a hostname that
# resolves public-then-internal (DNS rebinding) can't reach loopback / RFC1918 / link-local /
# cloud-metadata addresses. Redirects are re-validated per hop; the download is size-capped.
_SSRF_MAX_BYTES = 512 * 1024 * 1024   # 512 MB cap on a downloaded asset


def _ip_is_public(ip_str):
    a = ipaddress.ip_address(ip_str)
    if a.version == 6 and a.ipv4_mapped is not None:   # ::ffff:169.254.169.254 etc.
        a = a.ipv4_mapped
    return not (a.is_private or a.is_loopback or a.is_link_local or a.is_reserved
                or a.is_multicast or a.is_unspecified) and a.is_global


def _resolve_public(host, port):
    """Resolve host → one validated (family, ip). Raises ValueError if ANY resolved address is
    non-public (block-list on the resolved IP, per OWASP — string checks are insufficient)."""
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise ValueError(f"could not resolve host: {host}") from e
    picked = None
    for fam, _st, _pr, _cn, sa in infos:
        if not _ip_is_public(sa[0]):
            raise ValueError(f"blocked non-public address for {host}: {sa[0]}")
        picked = picked or (fam, sa[0])
    if not picked:
        raise ValueError(f"could not resolve host: {host}")
    return picked


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host, ip, **kw):
        super().__init__(host, **kw)
        self._pin = ip

    def connect(self):
        self.sock = socket.create_connection((self._pin, self.port), self.timeout, self.source_address)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, ip, **kw):
        super().__init__(host, **kw)
        self._pin = ip

    def connect(self):
        sock = socket.create_connection((self._pin, self.port), self.timeout, self.source_address)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)   # cert/SNI = hostname


def safe_download(url, dest, timeout=60, max_bytes=_SSRF_MAX_BYTES, _redirects=3):
    """Fetch an agent-supplied http(s) URL to `dest` with SSRF protection. Connects to the validated,
    pinned IP; re-validates each redirect hop; caps the size. Returns dest, or raises ValueError on a
    blocked / oversized / failed fetch."""
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme: {p.scheme or '(none)'}")
    if not p.hostname:
        raise ValueError("URL has no host")
    port = p.port or (443 if p.scheme == "https" else 80)
    _fam, ip = _resolve_public(p.hostname, port)
    if p.scheme == "https":
        conn = _PinnedHTTPSConnection(p.hostname, ip, port=port, timeout=timeout,
                                      context=ssl.create_default_context())
    else:
        conn = _PinnedHTTPConnection(p.hostname, ip, port=port, timeout=timeout)
    try:
        path = (p.path or "/") + (f"?{p.query}" if p.query else "")
        conn.request("GET", path, headers={"User-Agent": _USER_AGENT, "Host": p.hostname})
        resp = conn.getresponse()
        if resp.status in (301, 302, 303, 307, 308):
            loc = resp.headers.get("Location")
            if not loc or _redirects <= 0:
                raise ValueError("too many redirects")
            return safe_download(urllib.parse.urljoin(url, loc), dest, timeout, max_bytes, _redirects - 1)
        if resp.status != 200:
            raise ValueError(f"download failed ({resp.status})")
        total = 0
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("download exceeds size cap")
                f.write(chunk)
        return dest
    finally:
        conn.close()


def safe_fetch_bytes(url, timeout=60, max_bytes=_SSRF_MAX_BYTES, _redirects=3):
    """SSRF-guarded fetch of an agent-supplied http(s) URL, returning (data_bytes, content_type).
    Same protection as safe_download (validated + pinned IP, per-hop redirect re-validation, size cap)
    but in-memory, for callers that need the bytes rather than a file — e.g. inlining an image/video for
    a vision model server-side. Raises ValueError on a blocked / oversized / failed fetch."""
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme: {p.scheme or '(none)'}")
    if not p.hostname:
        raise ValueError("URL has no host")
    port = p.port or (443 if p.scheme == "https" else 80)
    _fam, ip = _resolve_public(p.hostname, port)   # blocks loopback / RFC1918 / link-local / metadata
    if p.scheme == "https":
        conn = _PinnedHTTPSConnection(p.hostname, ip, port=port, timeout=timeout,
                                      context=ssl.create_default_context())
    else:
        conn = _PinnedHTTPConnection(p.hostname, ip, port=port, timeout=timeout)
    try:
        path = (p.path or "/") + (f"?{p.query}" if p.query else "")
        conn.request("GET", path, headers={"User-Agent": _USER_AGENT, "Host": p.hostname})
        resp = conn.getresponse()
        if resp.status in (301, 302, 303, 307, 308):
            loc = resp.headers.get("Location")
            if not loc or _redirects <= 0:
                raise ValueError("too many redirects")
            return safe_fetch_bytes(urllib.parse.urljoin(url, loc), timeout, max_bytes, _redirects - 1)
        if resp.status != 200:
            raise ValueError(f"fetch failed ({resp.status})")
        data = bytearray()
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            data += chunk
            if len(data) > max_bytes:
                raise ValueError("fetch exceeds size cap")
        return bytes(data), resp.headers.get("Content-Type", "")
    finally:
        conn.close()


def proxy_request(capability, body, method="POST", call_id=None, timeout=120):
    """Call the metered proxy. Returns the parsed response dict, or a
    structured {'ok': False, ...} error the caller can print and exit on.
    402 -> insufficient_credits (the agent should relay a top-up prompt).
    timeout bounds the call — managed video/tts block server-side on the vendor queue (~minutes)."""
    key = supercmo_key()
    if not key:
        return {"ok": False, "error": "SUPERCMO_API_KEY missing — cannot use the metered proxy."}
    headers = {"Authorization": f"Bearer {key}"}
    if method != "GET":
        body = dict(body or {})
        call_id = call_id or body.get("call_id")
        if not isinstance(call_id, str) or not call_id.strip() or len(call_id) > 120:
            return {
                "ok": False,
                "error": "managed_request_setup_error",
                "detail": "the managed client did not assign this request an operation ID",
                "fix": "upgrade or reinstall SuperCMO, then retry",
            }
        body["call_id"] = call_id
    url = f"{api_url()}{PROXY_BASE}/{capability.lstrip('/')}"
    parsed, status, err = _request(method, url, body=body if method != "GET" else None,
                                   headers=headers, timeout=timeout)
    if parsed is not None:
        return parsed
    if status == 402:
        return {"ok": False, "error": "insufficient_credits",
                "action": "top_up", "detail": err,
                "topup": "https://getsupercmo.ai/settings?tab=billing"}
    if status == 409:
        return {"ok": False, "error": "duplicate_call_id", "detail": err,
                "fix": "the prior managed request already used this call ID; do not retry it."}
    if status == 429:
        return {"ok": False, "error": "rate_limited", "detail": err,
                "fix": "the service is rate-limiting; wait for the cooldown before retrying."}
    if status in (401, 403):
        return {"ok": False, "error": "supercmo_key_rejected",
                "detail": err, "fix": "re-issue the key in Settings -> API Keys"}
    return {"ok": False, "error": f"proxy {capability} failed ({status}): {err}"}


def proxy_submit(capability, body, call_id=None, timeout=120):
    """Submit a generation to the metered proxy. The proxy may answer **synchronously** (a final
    {ok, ...media...}) or **asynchronously** ({ok, job_id}) for a long-running job — the client
    handles both (a job_id becomes a pending handle it later polls with proxy_job_status). Returns
    the parsed response dict, or a structured {ok: False, ...} error.

    The client assigns ``call_id`` once per operation and the transport automatically reuses it
    across network retries, so one intended operation is charged at most once."""
    return proxy_request(capability, body, call_id=call_id, timeout=timeout)


def proxy_job_status(job_id, timeout=60):
    """Poll an async proxy job at GET {PROXY_BASE}/jobs/<job_id>, normalizing the proxy's
    {status, result} envelope to the client's shape: pending → {ok: True, done: False, state};
    completed → {ok: True, done: True, <video|audio>, duration?}; else {ok: False, ...}. (The proxy
    async backend is not live yet — this is the client-side contract; see the async TODO.)"""
    if not job_id:
        return {"ok": False, "error": "proxy job_id missing on the handle."}
    key = supercmo_key()
    if not key:
        return {"ok": False, "error": "SUPERCMO_API_KEY missing — cannot poll the proxy job."}
    url = f"{api_url()}{PROXY_BASE}/jobs/{urllib.parse.quote(str(job_id))}"
    parsed, status, err = _request("GET", url, headers={"Authorization": f"Bearer {key}"}, timeout=timeout)
    if parsed is None:
        return {"ok": False, "error": f"proxy job status failed ({status})", "detail": err}
    state = parsed.get("status")
    if state in ("IN_QUEUE", "IN_PROGRESS", "PENDING", "pending", "queued", "running"):
        return {"ok": True, "done": False, "state": state}
    result = parsed.get("result") or parsed
    if not isinstance(result, dict):
        return {"ok": False, "error": f"proxy job state: {state}", "detail": json.dumps(parsed)[:500]}
    if result.get("video") or result.get("audio"):
        out = {"ok": True, "done": True}
        for k in ("video", "audio", "duration"):
            if result.get(k) is not None:
                out[k] = result[k]
        return out
    return {"ok": False, "error": f"proxy job state: {state}", "detail": json.dumps(parsed)[:500]}


def proxy_spec(capability, body):
    """Dry-run shape for proxy-routed calls."""
    return {
        "method": "POST",
        "url": f"{api_url()}{PROXY_BASE}/{capability.lstrip('/')}",
        "headers": {"Authorization": "Bearer SUPERCMO_API_KEY", "Content-Type": "application/json"},
        "body": body,
    }


def _selftest():
    """Assert key-file loading and the managed-proxy error/idempotency contract."""
    global _request
    import tempfile
    scratch_root = os.path.dirname(__file__)
    with tempfile.TemporaryDirectory(dir=scratch_root) as scratch:
        p = os.path.join(scratch, ".env")
        with open(p, "wb") as f:  # non-UTF-8 comment byte + a valid ASCII key line + parsing edges
            f.write(b"# cl\xe9 (non-utf8 comment)\nFAL_KEY=fromfile\nGEMINI_API_KEY=g  # inline\n"
                    b"ELEVENLABS_API_KEY=\"quoted\"\nEMPTY=\n")
        for k in ("FAL_KEY", "GEMINI_API_KEY", "ELEVENLABS_API_KEY", "EMPTY"):
            os.environ.pop(k, None)
        os.environ["FAL_KEY"] = "realenv"             # a real env value must win over the file
        _load_key_file(p)
        assert os.environ["FAL_KEY"] == "realenv", "real env value must win"
        assert os.environ["GEMINI_API_KEY"] == "g", "inline comment stripped on unquoted value"
        assert os.environ["ELEVENLABS_API_KEY"] == "quoted", "surrounding quotes stripped"
        assert "EMPTY" not in os.environ, "empty value must not be set"
        os.environ["FAL_KEY"] = ""                     # empty (unset ${VAR:-}) must be filled
        _load_key_file(p)
        assert os.environ["FAL_KEY"] == "fromfile", "empty/unset var filled from the file"
        _load_key_file(os.path.join(p, "does-not-exist"))  # missing file: no-op, must not raise

    real_request = _request
    os.environ["SUPERCMO_API_KEY"] = "managed"
    observed = {}

    def stub_request(method, url, body=None, headers=None, timeout=120, retries=None):
        observed.update(method=method, url=url, body=body, headers=headers, timeout=timeout)
        return {"ok": True}, 200, None

    try:
        _request = stub_request
        missing = proxy_request("image", {"prompt": "x"})
        assert missing["error"] == "managed_request_setup_error"
        assert proxy_request("image", {"prompt": "x"}, call_id="stable-operation") == {"ok": True}
        generated_call_id = observed["body"]["call_id"]
        assert generated_call_id == "stable-operation"
        _request = lambda *args, **kwargs: (None, 402, "balance low")
        payment = proxy_request("image", {}, call_id="payment-test")
        assert payment["action"] == "top_up" and payment["topup"].startswith("https://")
        _request = lambda *args, **kwargs: (None, 409, "already used")
        duplicate = proxy_request("image", {}, call_id="duplicate-test")
        assert duplicate["error"] == "duplicate_call_id" and "do not retry" in duplicate["fix"]
    finally:
        _request = real_request
        os.environ.pop("SUPERCMO_API_KEY", None)

    real_urlopen, real_sleep = urllib.request.urlopen, time.sleep
    bodies = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"ok": true}'

    try:
        def retry_once(req, timeout=None):
            bodies.append(req.data)
            if len(bodies) == 1:
                raise urllib.error.URLError("lost response")
            return Response()

        urllib.request.urlopen = retry_once
        time.sleep = lambda _seconds: None
        parsed, status, err = _request(
            "POST", "https://example.test/proxy", {"call_id": generated_call_id}, retries=2
        )
        assert parsed == {"ok": True} and status == 200 and err is None
        assert len(bodies) == 2 and bodies[0] == bodies[1]

        attempts = []

        def conflict(req, timeout=None):
            attempts.append(req.data)
            raise urllib.error.HTTPError(
                req.full_url, 409, "Conflict", {}, io.BytesIO(b'{"detail":"duplicate"}')
            )

        urllib.request.urlopen = conflict
        _parsed, status, _err = _request(
            "POST", "https://example.test/proxy", {"call_id": generated_call_id}, retries=3
        )
        assert status == 409 and len(attempts) == 1
    finally:
        urllib.request.urlopen, time.sleep = real_urlopen, real_sleep
    print("supercmo_env selftest: OK")


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    if "--dry-run" in args:
        print(json.dumps({"_dry_run": True, "method": None, "url": None, "headers": None, "body": None,
                          "note": "supercmo_env is a local env loader/router — no API calls on its own"}, indent=2))
        return
    interesting = ["SUPERCMO_API_KEY", "SUPERCMO_API_URL", "FAL_KEY", "ELEVENLABS_API_KEY",
                   "GEMINI_API_KEY", "FIRECRAWL_API_KEY"]
    print(json.dumps({
        "ok": True,
        "source": "process environment — loaded from ~/.supercmo/.env, or a host MCP config env block / shell export",
        "api_url": api_url(),
        "keys_present": {k: bool(os.environ.get(k)) for k in interesting},
    }, indent=2))


if __name__ == "__main__":
    main()
