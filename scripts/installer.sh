#!/usr/bin/env bash
# Optional installer for the hosted distribution path. The PRIMARY install is native:
#   /plugin marketplace add SupercmoHQ/superCMO-skills
# This downloads the prebuilt one-plugin bundle (supercmo-plugin.zip) and extracts it
# (used by the hosted curl|bash flow and for offline testing).
set -euo pipefail

PLUGIN_ID="${1:-supercmo}"
ARCHIVE="${PLUGIN_ID}-plugin.zip"
# Phase-1 primary install is native (/plugin marketplace add). Remote download is opt-in via
# SUPERCMO_ASSET_BASE (set only when the asset host is live); default is local-dist.
ASSET_BASE="${SUPERCMO_ASSET_BASE:-https://assets.getsupercmo.ai/plugins}"
ARCHIVE_URL="${ASSET_BASE}/${ARCHIVE}"

echo "==> Installing SuperCMO plugin: ${PLUGIN_ID}"

CLAUDE_DIR="${HOME}/.claude"
OPENCODE_DIR="${HOME}/.opencode"

if [ -d "${CLAUDE_DIR}" ]; then
  PLATFORM="Claude Code"; TARGET_PATH="${CLAUDE_DIR}/plugins"
elif [ -d "${OPENCODE_DIR}" ]; then
  PLATFORM="OpenCode"; TARGET_PATH="${OPENCODE_DIR}/plugins"
else
  PLATFORM="Local Workspace"; TARGET_PATH="./.supercmo/plugins"
fi

echo "    Target: ${PLATFORM}"
mkdir -p "${TARGET_PATH}/${PLUGIN_ID}"

TEMP_ARCHIVE="$(mktemp "${TMPDIR:-/tmp}/${PLUGIN_ID}-plugin.XXXXXX")"   # unpredictable temp (no /tmp TOCTOU)
if [ -f "./dist/${ARCHIVE}" ]; then
  echo "    Using local build archive..."
  cp "./dist/${ARCHIVE}" "${TEMP_ARCHIVE}"
elif [ -n "${SUPERCMO_ASSET_BASE:-}" ]; then
  echo "    Downloading ${ARCHIVE_URL}..."
  curl -fsSL "${ARCHIVE_URL}" -o "${TEMP_ARCHIVE}"   # -f: fail on HTTP error instead of saving the error body
else
  echo "    No local build at ./dist/${ARCHIVE} and SUPERCMO_ASSET_BASE is not set."
  echo "    Phase-1 install is native — run:  /plugin marketplace add SupercmoHQ/superCMO-skills"
  echo "    (Or build locally first:  python3 scripts/package_plugins.py)"
  exit 1
fi

command -v python3 >/dev/null 2>&1 || { echo "❌ python3 is required to install and run the plugin."; exit 1; }

echo "    Extracting to ${TARGET_PATH}/${PLUGIN_ID}..."
python3 -m zipfile -e "${TEMP_ARCHIVE}" "${TARGET_PATH}/${PLUGIN_ID}/"
rm -f "${TEMP_ARCHIVE}"

echo "✓ Installed ${PLUGIN_ID} (${PLATFORM})."
