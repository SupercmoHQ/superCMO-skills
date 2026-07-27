#!/usr/bin/env bash
# Optional installer for the hosted distribution path. The PRIMARY install is native:
#   /plugin marketplace add SupercmoHQ/superCMO-skills
# This downloads the prebuilt one-plugin tarball and extracts it (used by the hosted
# curl|bash flow and for offline testing).
set -euo pipefail

PLUGIN_ID="${1:-supercmo}"
# Phase-1 primary install is native (/plugin marketplace add). Remote tarball download is
# opt-in via SUPERCMO_ASSET_BASE (set only when the asset host is live); default is local-dist.
ASSET_BASE="${SUPERCMO_ASSET_BASE:-https://assets.getsupercmo.ai/plugins}"
TARBALL_URL="${ASSET_BASE}/${PLUGIN_ID}.tar.gz"

echo "==> Installing SuperCMO plugin: ${PLUGIN_ID}"

CLAUDE_DIR="${HOME}/.claude"
HERMES_DIR="${HOME}/.hermes"
OPENCODE_DIR="${HOME}/.opencode"

if [ -d "${CLAUDE_DIR}" ]; then
  PLATFORM="Claude Code"; TARGET_PATH="${CLAUDE_DIR}/plugins"
elif [ -d "${HERMES_DIR}" ]; then
  PLATFORM="Hermes"; TARGET_PATH="${HERMES_DIR}/plugins"
elif [ -d "${OPENCODE_DIR}" ]; then
  PLATFORM="OpenCode"; TARGET_PATH="${OPENCODE_DIR}/plugins"
else
  PLATFORM="Local Workspace"; TARGET_PATH="./.supercmo/plugins"
fi

echo "    Target: ${PLATFORM}"
mkdir -p "${TARGET_PATH}/${PLUGIN_ID}"

TEMP_TAR="/tmp/${PLUGIN_ID}.tar.gz"
if [ -f "./dist/${PLUGIN_ID}.tar.gz" ]; then
  echo "    Using local build archive..."
  cp "./dist/${PLUGIN_ID}.tar.gz" "${TEMP_TAR}"
elif [ -n "${SUPERCMO_ASSET_BASE:-}" ]; then
  echo "    Downloading ${TARBALL_URL}..."
  curl -sSL "${TARBALL_URL}" -o "${TEMP_TAR}"
else
  echo "    No local build at ./dist/${PLUGIN_ID}.tar.gz and SUPERCMO_ASSET_BASE is not set."
  echo "    Phase-1 install is native — run:  /plugin marketplace add SupercmoHQ/superCMO-skills"
  echo "    (Or build locally first:  python3 scripts/package_plugins.py)"
  exit 1
fi

echo "    Extracting to ${TARGET_PATH}/${PLUGIN_ID}..."
tar -xzf "${TEMP_TAR}" -C "${TARGET_PATH}/${PLUGIN_ID}"
rm -f "${TEMP_TAR}"

command -v python3 >/dev/null 2>&1 || echo "⚠️  python3 not found — some skill scripts may not run."
echo "✓ Installed ${PLUGIN_ID} (${PLATFORM})."
