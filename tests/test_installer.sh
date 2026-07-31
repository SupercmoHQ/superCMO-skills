#!/usr/bin/env bash
# Offline end-to-end test of scripts/installer.sh against the repo-as-one-plugin build.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_ID="supercmo"

echo "=== Testing installer (offline) ==="
cd "${REPO_ROOT}"

echo "Building plugin artifact..."
python3 "${REPO_ROOT}/scripts/package_plugins.py" >/dev/null

MOCK_HOME="/tmp/mock_home"
rm -rf "${MOCK_HOME}"
mkdir -p "${MOCK_HOME}/.claude"

echo "Running installer (HOME=${MOCK_HOME})..."
HOME="${MOCK_HOME}" "${REPO_ROOT}/scripts/installer.sh" "${PLUGIN_ID}"

TARGET="${MOCK_HOME}/.claude/plugins/${PLUGIN_ID}"
echo "Verifying ${TARGET}..."
if [ -f "${TARGET}/.claude-plugin/plugin.json" ] && \
   [ -f "${TARGET}/skills/generating-images/SKILL.md" ] && \
   [ ! -d "${TARGET}/skills/generating-images/evals" ]; then
  echo "✓ Installer verification PASSED."
else
  echo "❌ Error: Extracted layout validation failed!"
  exit 1
fi

rm -rf "${REPO_ROOT}/dist"
echo "=== Done ==="
exit 0
