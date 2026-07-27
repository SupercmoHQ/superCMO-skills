#!/usr/bin/env python3
"""TEMPLATE script — demonstrates the skill script contract. Delete with the
example skill once real skills exist.

Contract (see docs/skill-authoring-rules.md):
  - Standalone: depends only on the Python stdlib + the user's own env vars.
    No imports from the repo root; bundle/declare anything shared.
  - BYO-keys: read credentials from env (SERVICE_API_KEY convention), never a file.
  - --dry-run: print the request that WOULD be sent (secrets masked); make no call.
  - Output JSON to stdout, diagnostics to stderr; meaningful exit codes.
  - Non-interactive (no prompts — an agent can't answer them).
"""
import argparse
import json
import os
import sys


def build_request(arg):
    return {
        "method": "POST",
        "url": "https://api.example.com/v1/do-thing",
        "headers": {"Authorization": "Bearer <token>"},
        "body": {"arg": arg},
    }


def main():
    p = argparse.ArgumentParser(description="Example skill script (template).")
    p.add_argument("--arg", default="demo")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the request without sending it (secrets masked).")
    args = p.parse_args()

    req = build_request(args.arg)

    if args.dry_run:
        masked = dict(req, headers={"Authorization": "***"})
        print(json.dumps({"_dry_run": True, **masked}, indent=2))
        return 0

    token = os.environ.get("EXAMPLE_API_KEY")
    if not token:
        print(json.dumps({"ok": False, "error": "EXAMPLE_API_KEY not set (bring your own key)."}),
              file=sys.stderr)
        return 1

    # Real call would go here. Template prints a placeholder result.
    print(json.dumps({"ok": True, "result": f"did thing with arg={args.arg}"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
