#!/usr/bin/env bash
# Build + validate the repo-as-one-plugin, then hand the artifact to the hosted
# deploy pipeline. The primary install path is native (`/plugin marketplace add`);
# this builds the additive tarball the hosted product serves.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Build & validate ==="

echo "Step 1: Structural + frontmatter validation..."
python3 "${REPO_ROOT}/scripts/quick_validate.py"

echo "Step 2: Agent Skills spec validation (skills-ref, best-effort)..."
if command -v skills-ref >/dev/null 2>&1; then
  for skill_dir in "${REPO_ROOT}/skills"/*/; do
    [ -f "${skill_dir}SKILL.md" ] && skills-ref validate "${skill_dir}" || true
  done
else
  echo "    skills-ref not installed locally — skipping (CI runs it)."
fi

echo "Step 3: Advisory trigger evals..."
python3 "${REPO_ROOT}/tests/evals/run_eval.py" || true

echo "Step 4: Package the plugin..."
python3 "${REPO_ROOT}/scripts/package_plugins.py"

echo "Step 5: Artifact built:"
for file in "${REPO_ROOT}"/dist/*.tar.gz; do echo "    ${file}"; done
echo "    The hosted deploy pipeline uploads + registers this artifact."

echo "=== Done ==="
exit 0
