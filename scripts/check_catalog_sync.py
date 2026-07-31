#!/usr/bin/env python3
"""Guard: the provider-key catalog has ONE source of truth — each provider module's BYOK_ENV
(scripts/supercmo_skills/providers/*.py, enumerated by client.provider_modules()). Keys are now
delivered ONLY via ~/.supercmo/.env (no host env block on any host — see supercmo_env.py), so the
single non-Python copy of the key list that must stay in lockstep is the .env template the installer
writes; a stale template means a new provider's key gets no placeholder and users don't know to add it:

  - bin/lib/config.js  ensureKeyFile() — the labeled `~/.supercmo/.env` placeholders a user fills in

SUPERCMO_API_KEY (managed lane) is not a BYOK provider and is intentionally absent from the template,
so it's excluded. Run in CI (validate.yml). Blocking.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from supercmo_skills import client  # noqa: E402


def registry_keys():
    return {mod.BYOK_ENV for mod in client.provider_modules().values()}


def env_template_keys():
    # ponytail: the ensureKeyFile() .env body writes one placeholder per provider as a quoted dotenv
    # line, e.g. 'FAL_KEY='. That `'KEY='` shape is unique to the template in config.js, so a
    # whole-file scan is unambiguous and dependency-free. If another `'KEY='` literal is ever added
    # elsewhere in config.js, scope this to the ensureKeyFile() body instead.
    src = open(os.path.join(ROOT, "bin", "lib", "config.js"), encoding="utf-8").read()
    keys = set(re.findall(r"""['"]([A-Z][A-Z0-9_]*)=['"]""", src))
    if not keys:
        print("✗ check_catalog_sync: no 'KEY=' placeholders found in bin/lib/config.js ensureKeyFile()")
        raise SystemExit(1)
    return keys


def main():
    reg = registry_keys()
    got = env_template_keys()
    if got != reg:
        print("✗ provider-key catalog drift — the ~/.supercmo/.env template is stale vs the provider registry:")
        print(f"  - bin/lib/config.js ensureKeyFile(): {sorted(got)} != registry {sorted(reg)} "
              f"(missing {sorted(reg - got)}, extra {sorted(got - reg)})")
        return 1
    print(f"✓ provider-key catalog in sync ({len(reg)} keys): registry == ~/.supercmo/.env template")
    return 0


if __name__ == "__main__":
    sys.exit(main())
