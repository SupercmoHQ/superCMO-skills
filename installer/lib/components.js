'use strict';
// Places the plugin's non-MCP components (skills / agent / command) into a host's native location.
// Skills that a host can't represent are skipped and reported by the caller (never silently dropped).
const fs = require('fs');
const path = require('path');
const { PLUGIN_ROOT } = require('./config');

const SKILLS_SRC = path.join(PLUGIN_ROOT, 'skills');
const COMMANDS_SRC = path.join(PLUGIN_ROOT, 'commands');

function listSkills() {
  if (!fs.existsSync(SKILLS_SRC)) return [];
  return fs.readdirSync(SKILLS_SRC).filter((d) => fs.existsSync(path.join(SKILLS_SRC, d, 'SKILL.md')));
}

function copyTree(src, dst) {
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.cpSync(src, dst, { recursive: true, filter: (s) => !s.includes('__pycache__') && !s.endsWith('.pyc') });
}

// Copy skill dirs into a skills root (Claude Code, Codex). Clean-replaces each of OUR skill dirs so a
// re-run (upgrade) drops files removed within a skill; the user's other skills in the dir are untouched.
// Returns count placed.
function placeSkills(destRoot) {
  const names = listSkills();
  for (const n of names) {
    const dst = path.join(destRoot, n);
    fs.rmSync(dst, { recursive: true, force: true });
    copyTree(path.join(SKILLS_SRC, n), dst);
  }
  return names.length;
}

// Render each SKILL.md as a Cursor .mdc rule (Cursor has no skills concept). Prunes previously-installed
// supercmo rules first (we own the `supercmo-` prefix) so a re-run drops rules for removed skills.
// Returns count.
function placeCursorRules(rulesDir) {
  const names = listSkills();
  fs.mkdirSync(rulesDir, { recursive: true });
  for (const f of fs.readdirSync(rulesDir)) {
    if (f.startsWith('supercmo-') && f.endsWith('.mdc')) fs.rmSync(path.join(rulesDir, f), { force: true });
  }
  for (const n of names) {
    const body = fs.readFileSync(path.join(SKILLS_SRC, n, 'SKILL.md'), 'utf8');
    const stripped = body.replace(/^---\n[\s\S]*?\n---\n/, ''); // drop SKILL.md frontmatter
    const rule = `---\ndescription: SuperCMO ${n} skill — use when the request matches this workflow\nalwaysApply: false\n---\n\n${stripped.trim()}\n`;
    fs.writeFileSync(path.join(rulesDir, `supercmo-${n}.mdc`), rule);
  }
  return names.length;
}

// Copy a flat dir of .md files (agents, commands) into dest. Returns count.
function placeMdDir(srcDir, destDir) {
  if (!fs.existsSync(srcDir)) return 0;
  const files = fs.readdirSync(srcDir).filter((f) => f.endsWith('.md'));
  fs.mkdirSync(destDir, { recursive: true });
  for (const f of files) fs.copyFileSync(path.join(srcDir, f), path.join(destDir, f));
  return files.length;
}

// --- uninstall: remove only what we placed (by our known skill names / supercmo- prefix) ---

function removeSkills(destRoot) {
  let n = 0;
  for (const name of listSkills()) {
    const d = path.join(destRoot, name);
    if (fs.existsSync(d)) { fs.rmSync(d, { recursive: true, force: true }); n++; }
  }
  return n;
}

function removeCursorRules(rulesDir) {
  if (!fs.existsSync(rulesDir)) return 0;
  let n = 0;
  for (const f of fs.readdirSync(rulesDir)) {
    if (f.startsWith('supercmo-') && f.endsWith('.mdc')) { fs.rmSync(path.join(rulesDir, f), { force: true }); n++; }
  }
  return n;
}

function removeMdFiles(srcDir, destDir) {
  if (!fs.existsSync(srcDir) || !fs.existsSync(destDir)) return 0;
  let n = 0;
  for (const f of fs.readdirSync(srcDir)) {
    if (f.endsWith('.md') && fs.existsSync(path.join(destDir, f))) { fs.rmSync(path.join(destDir, f), { force: true }); n++; }
  }
  return n;
}

module.exports = {
  listSkills, placeSkills, placeCursorRules, placeMdDir,
  removeSkills, removeCursorRules, removeMdFiles,
  SKILLS_SRC, COMMANDS_SRC,
};
