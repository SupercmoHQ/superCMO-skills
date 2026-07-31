'use strict';
// MCP registration for the JSON-config hosts that have NO first-party `mcp add` CLI: Cursor, Windsurf,
// Cline, OpenCode. (Codex/Claude/VS Code are handled by lib/clihosts.js via their own CLI.)
// We do a full structured read → merge → write (JSON.parse/stringify), never string/regex editing —
// the same safe approach Smithery uses for CLI-less clients. Our `supercmo` key is the only thing added
// or removed; every other server and top-level key is preserved.
//
// No env block is ever written: keys are delivered host-independently by the server, which loads
// ~/.supercmo/.env on startup (scripts/supercmo_env.py). We do NOT write `${env:VAR}` / `{env:VAR}`
// refs — host expansion of such refs is inconsistent across hosts and non-portable.
const fs = require('fs');
const path = require('path');
const { SERVER_NAME, home } = require('./config');

// Tolerant JSON read: strips // and /* */ comments and trailing commas so existing JSONC configs
// (common in VS Code / Cursor) don't abort the install. Clobber-safe: on unparseable input it throws.
function readJson(file) {
  if (!fs.existsSync(file)) return {};
  let raw = fs.readFileSync(file, 'utf8').trim();
  if (!raw) return {};
  const stripped = raw
    .replace(/\\"|"(?:\\.|[^"\\])*"|\/\/.*$|\/\*[\s\S]*?\*\//gm, (m) => (m[0] === '/' ? '' : m))
    .replace(/,(\s*[}\]])/g, '$1');
  return JSON.parse(stripped);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2) + '\n', 'utf8');
}

// Merge one server under `wrapperKey`, idempotent (replaces our entry, leaves others).
function mergeServer(file, wrapperKey, entry, force) {
  const cfg = readJson(file);
  cfg[wrapperKey] = cfg[wrapperKey] || {};
  const existing = cfg[wrapperKey][SERVER_NAME];
  if (existing && !force && JSON.stringify(existing) !== JSON.stringify(entry)) {
    throw new Error(`${file}: a different "${SERVER_NAME}" already exists. Re-run with --force to overwrite.`);
  }
  cfg[wrapperKey][SERVER_NAME] = entry;
  writeJson(file, cfg);
  return file;
}

// Cursor: project .cursor/mcp.json when projectDir given, else global ~/.cursor/mcp.json.
function installCursor({ projectDir, force, serverPy, command, argsPrefix }) {
  const file = projectDir
    ? path.join(projectDir, '.cursor', 'mcp.json')
    : path.join(home(), '.cursor', 'mcp.json');
  const entry = { command, args: [...argsPrefix, serverPy] };
  mergeServer(file, 'mcpServers', entry, force);
  return { file, missing: [], notes: ['Keys load from ~/.supercmo/.env; nothing secret is written here.'] };
}

function installWindsurf({ force, serverPy, command, argsPrefix }) {
  const file = path.join(home(), '.codeium', 'windsurf', 'mcp_config.json');
  const entry = { command, args: [...argsPrefix, serverPy] };
  mergeServer(file, 'mcpServers', entry, force);
  return { file, missing: [], notes: [] };
}

// Cline: the dominant install is the VS Code extension, which reads MCP config from VS Code
// globalStorage. Resolve that per-platform.
function clineSettingsFile() {
  const h = home();
  const base =
    process.platform === 'win32'
      ? path.join(process.env.APPDATA || path.join(h, 'AppData', 'Roaming'), 'Code', 'User')
      : process.platform === 'darwin'
        ? path.join(h, 'Library', 'Application Support', 'Code', 'User')
        : path.join(process.env.XDG_CONFIG_HOME || path.join(h, '.config'), 'Code', 'User');
  return path.join(base, 'globalStorage', 'saoudrizwan.claude-dev', 'settings', 'cline_mcp_settings.json');
}

function installCline({ force, serverPy, command, argsPrefix }) {
  const file = clineSettingsFile();
  const entry = { command, args: [...argsPrefix, serverPy], disabled: false, autoApprove: [] };
  mergeServer(file, 'mcpServers', entry, force);
  return { file, missing: [], notes: [] };
}

// OpenCode: opencode.json (project) or ~/.config/opencode/opencode.json (global). MCP servers under
// the `mcp` key: type "local", `command` is an ARRAY. No `environment` block — keys load from
// ~/.supercmo/.env (OpenCode's dollar-less `{env:VAR}` is a different syntax we don't rely on).
function installOpenCode({ projectDir, force, serverPy, command, argsPrefix }) {
  const file = projectDir
    ? path.join(projectDir, 'opencode.json')
    : path.join(home(), '.config', 'opencode', 'opencode.json');
  const entry = { type: 'local', command: [command, ...argsPrefix, serverPy], enabled: true };
  const cfg = readJson(file);
  cfg.mcp = cfg.mcp || {};
  const existing = cfg.mcp[SERVER_NAME];
  if (existing && !force && JSON.stringify(existing) !== JSON.stringify(entry)) {
    throw new Error(`${file}: a different "${SERVER_NAME}" already exists. Re-run with --force.`);
  }
  cfg.mcp[SERVER_NAME] = entry;
  writeJson(file, cfg);
  return { file, missing: [], notes: ['Keys load from ~/.supercmo/.env.'] };
}

// --- uninstall ---

function removeServerEntry(file, wrapperKey) {
  if (!fs.existsSync(file)) return { file, removed: false };
  const cfg = readJson(file);
  let removed = false;
  if (cfg[wrapperKey] && Object.prototype.hasOwnProperty.call(cfg[wrapperKey], SERVER_NAME)) {
    delete cfg[wrapperKey][SERVER_NAME];
    removed = true;
    writeJson(file, cfg);
  }
  return { file, removed };
}
const comp = () => require('./components');

function uninstallCursor({ projectDir }) {
  const file = projectDir ? path.join(projectDir, '.cursor', 'mcp.json') : path.join(home(), '.cursor', 'mcp.json');
  const { removed } = removeServerEntry(file, 'mcpServers');
  const rules = projectDir ? comp().removeCursorRules(path.join(projectDir, '.cursor', 'rules')) : 0;
  return { file, removed, notes: rules ? [`removed ${rules} rules`] : [] };
}
function uninstallWindsurf() {
  const file = path.join(home(), '.codeium', 'windsurf', 'mcp_config.json');
  return { ...removeServerEntry(file, 'mcpServers'), notes: [] };
}
function uninstallCline() {
  const file = clineSettingsFile();
  return { ...removeServerEntry(file, 'mcpServers'), notes: [] };
}
function uninstallOpenCode({ projectDir }) {
  const file = projectDir ? path.join(projectDir, 'opencode.json') : path.join(home(), '.config', 'opencode', 'opencode.json');
  return { ...removeServerEntry(file, 'mcp'), notes: [] };
}

module.exports = {
  installCursor, installWindsurf, installCline, installOpenCode, clineSettingsFile,
  uninstallCursor, uninstallWindsurf, uninstallCline, uninstallOpenCode, readJson,
};
