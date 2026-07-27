# supercmo_skills — the media gateway

One **stdlib-only** client shared by three consumers: the MCP server (Claude/GPT/any MCP client),
the OSS Hermes plugin (`hermes-plugins/supercmo_media`), and the hosted proxy. The agent passes a
**provider-blind model alias**; the gateway resolves it to a backend. This is the LiteLLM-Router
pattern: each capability has its own catalog, an alias maps to an ordered list of provider **routes**,
and the resolver picks one.

Three capabilities, three sibling functions (one vocabulary, matching the tool names):
`image_generate` · `video_generate` · `text_to_speech`.

```
agent → video_generate(prompt, model, …)            # `model` is a catalog ALIAS, never a provider
  client.video_generate:
     kind, provider, route = _select_route("video", model):
        for route in catalog.routes_of("video", model):   # ordered = priority
            if provider.is_available(): → ("direct", provider, route)   # BYO vendor key set
        elif SUPERCMO_API_KEY:          → ("proxy", …)                  # managed (we fan out server-side)
        else:                           → ("none", …)
     direct → provider.video_generate(route, payload, key)
     proxy  → supercmo_env.proxy_request("video", body)
     none   → {ok: False, error: "no_provider_configured", hint}
```

Priority is **BYO vendor-direct > BYO fal > managed**. The agent is **model-aware, provider-blind** —
never add a `provider` arg to a tool schema. Routing/vendor logic lives here, so the bindings and
skills stay identical across runtimes.

**Status (2026-06-26):** image, video, and tts are live via **BYO-direct** (vendor key) and **BYO fal**
through the MCP server and the OSS Hermes plugin. The **managed lane** resolves to `proxy` correctly but
needs the SuperCMO managed proxy to expose `/proxy/{image,video,tts}` (the next step) before it works
end-to-end. Scoped direct adapters: `openai` (image+tts), `xai` (image+video), `elevenlabs` (tts),
`gemini` (tts), plus `fal` (image sync + video/tts via its async queue).

## Catalog layout

`catalog.py` has one table per capability — `IMAGE_MODELS`, `VIDEO_MODELS`, `TTS_MODELS` — and the
lookups take the capability first: `get(capability, model)`, `routes_of(capability, model)`,
`list_models(capability, query=None)`, `default_model(capability)`. Each alias' `routes` is an ordered
list `[BYO vendor route(s) …, BYO fal route]`; the managed proxy is the implicit tail (no route entry).

## Add a model (existing provider)

Add one entry to the right table. fal image models use the `_fal(...)` helper; fal video/tts and direct
vendor routes use `_route(provider, vendor_model_id, **fields)`:

```python
# image (fal), in IMAGE_MODELS
"my-image": {"display": "My Image", "strengths": "…", "price": "$X/image",
    "routes": [_fal("fal-ai/my-image", "fal-ai/my-image/edit", 4, "aspect_ratio", _RATIO,
        {"num_images": 1}, {"prompt", "image_urls", "aspect_ratio", "num_images", "seed"})]},

# video (fal queue), in VIDEO_MODELS — note queued=True + sizes/defaults/supports
"my-video": {"display": "My Video", "strengths": "…", "price": "$X/s",
    "routes": [_route("fal", "fal-ai/my-video/image-to-video", queued=True, sizes=_VRATIO,
        defaults={"duration": "8"}, supports={"prompt", "image_url", "duration", "aspect_ratio"})]},
```

A model gains a **direct** route by prepending one ahead of fal (see below). It appears in both
bindings and `list_<cap>_models` automatically. Nothing else changes.

## Add a provider (direct vendor adapter)

1. **Create `providers/<name>.py`** with the uniform contract. Implement only the capabilities the
   vendor serves; each capability gets a `<cap>_generate` + a `<cap>_request_spec`:

   ```python
   BYOK_ENV = "OPENAI_API_KEY"                          # presence of this key → route here directly
   def is_available(): return bool(os.environ.get(BYOK_ENV))

   def image_generate(route, payload, key) -> dict:     # {ok, model, images:[{url|b64}], seed} | {ok: False, …}
   def image_request_spec(route, payload) -> dict:      # dry-run shape — MASK the key
   # …and/or video_generate/video_request_spec, tts_generate/tts_request_spec
   ```

   - `route` = the catalog route dict (your vendor's ids/params). `payload` = the semantic input
     (`{model, prompt, …}`; image refs are already resolved to URLs/data-URIs, `num_images` clamped 1–4).
   - Long-running vendors (video, some tts) submit + poll **inside** the adapter and return the final
     URL — the caller sees one blocking call (mirror `fal._queue_run`, or xAI's submit→poll loop).
   - Binary audio (openai/elevenlabs tts) returns bytes → base64 in `{audio: {b64, content_type}}`;
     fal tts returns `{audio: {url}}`. One envelope, two shapes — skills relay whichever is present.
   - **Never raise** out of an adapter and **never leak the key**. `_request` / `_request_raw` in
     `supercmo_env` are the only HTTP primitives (stdlib).

2. **Register it** in `client._PROVIDERS`:

   ```python
   _PROVIDERS = {"fal": _fal, "openai": _openai, "xai": _xai, "elevenlabs": _elevenlabs, "gemini": _gemini}
   ```

3. **Add routes** to the catalog models it serves (prepend ahead of fal; **list order = priority**):

   ```python
   IMAGE_MODELS["gpt-image-2"]["routes"].insert(0, _route("openai", "gpt-image-1",
       sizes={"square": "1024x1024", …}, supports={"prompt", "size", "n"}))
   ```

Now a user with `OPENAI_API_KEY` gets openai-direct for `gpt-image-2`; a fal user gets fal; a managed
user gets the proxy. The agent, tool schemas, bindings, and skills **do not change** — multi-provider
is entirely a `supercmo_skills` concern. (MCP BYOK also needs the key passed in `.mcp.json`'s `env`.)

## Add a capability

Add a `<NEW>_MODELS` table + `_TABLES`/`DEFAULTS` entry in `catalog.py`, a `<cap>_generate` sibling in
`client.py` (validate → prep input → `_select_route(cap, model)` → dispatch), the matching
`<cap>_generate`/`<cap>_request_spec` on each provider, the tool in the MCP server + the OSS plugin,
and a `skills/<cap>-generation/SKILL.md`. The selector + routing are reused as-is.

## Notes

- **Stdlib-only** — no third-party imports (this vendors into the Claude plugin with no install step).
- **No runtime fallback** — `_select_route` picks the first *available* route; it does not retry a
  second provider on a generation error (deliberate; revisit if you want a fallback chain).
- The catalog is bundled today; when the proxy exposes `GET /proxy/catalog`, `list_models()` can fetch
  + cache it with this list as the fallback.
