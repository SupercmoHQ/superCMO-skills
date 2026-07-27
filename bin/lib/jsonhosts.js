'use strict';
// MCP registration for the JSON-config hosts: the `mcpServers` de-facto cluster
// (Cursor, Windsurf, Cline) and VS Code (`servers` + `inputs`).
const fs = require('fs');
const path = require('path');
const { SERVER_NAME, MEDIA_KEYS, keysFromEnv, home } = require('./config');

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

// Literal-env server entry (Cursor/Windsurf/Cline). Writes only keys present in the shell env.
function literalServerEntry(serverPy, command, argsPrefix) {
  const { present, missing } = keysFromEnv();
  return { entry: { command, args: [...argsPrefix, serverPy], env: present }, missing };
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
  const { entry, missing } = literalServerEntry(serverPy, command, argsPrefix);
  mergeServer(file, 'mcpServers', entry, force);
  return { file, missing, notes: [] };
}

function installWindsurf({ force, serverPy, command, argsPrefix }) {
  const file = path.join(home(), '.codeium', 'windsurf', 'mcp_config.json');
  const { entry, missing } = literalServerEntry(serverPy, command, argsPrefix);
  mergeServer(file, 'mcpServers', entry, force);
  return { file, missing, notes: [] };
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
  const { entry, missing } = literalServerEntry(serverPy, command, argsPrefix);
  entry.disabled = false;
  entry.autoApprove = [];
  mergeServer(file, 'mcpServers', entry, force);
  return { file, missing, notes: [] };
}

// VS Code: `servers` (type stdio) + top-level `inputs[]` secure prompts; no literal secrets written.
function installVscode({ projectDir, force, serverPy, command, argsPrefix }) {
  if (!projectDir) throw new Error('VS Code needs --project-dir <workspace> (writes .vscode/mcp.json).');
  const file = path.join(projectDir, '.vscode', 'mcp.json');
  const env = {};
  const inputs = MEDIA_KEYS.map((k) => {
    const id = k.toLowerCase().replace(/_/g, '-');
    env[k] = `\${input:${id}}`;
    return { type: 'promptString', id, description: `${k} for SuperCMO (leave blank if unused)`, password: true };
  });
  const cfg = readJson(file);
  cfg.servers = cfg.servers || {};
  const entry = { type: 'stdio', command, args: [...argsPrefix, serverPy], env };
  const existing = cfg.servers[SERVER_NAME];
  if (existing && !force && JSON.stringify(existing) !== JSON.stringify(entry)) {
    throw new Error(`${file}: a different "${SERVER_NAME}" already exists. Re-run with --force.`);
  }
  cfg.servers[SERVER_NAME] = entry;
  cfg.inputs = cfg.inputs || [];
  const haveIds = new Set(cfg.inputs.map((i) => i.id));
  for (const inp of inputs) if (!haveIds.has(inp.id)) cfg.inputs.push(inp);
  writeJson(file, cfg);
  return { file, missing: [], notes: ['VS Code prompts for each key on first use (blank = unused).'] };
}

// OpenCode: opencode.json (project) or ~/.config/opencode/opencode.json (global). MCP servers under
// the `mcp` key: type "local", `command` is an ARRAY, env key is `environment`. OpenCode supports
// `{env:VAR}` substitution, so keys are referenced from its environment (single-source, not literal).
function installOpenCode({ projectDir, force, serverPy, command, argsPrefix }) {
  const file = projectDir
    ? path.join(projectDir, 'opencode.json')
    : path.join(home(), '.config', 'opencode', 'opencode.json');
  const environment = {};
  for (const k of MEDIA_KEYS) environment[k] = `{env:${k}}`;
  const entry = { type: 'local', command: [command, ...argsPrefix, serverPy], enabled: true, environment };
  const cfg = readJson(file);
  cfg.mcp = cfg.mcp || {};
  const existing = cfg.mcp[SERVER_NAME];
  if (existing && !force && JSON.stringify(existing) !== JSON.stringify(entry)) {
    throw new Error(`${file}: a different "${SERVER_NAME}" already exists. Re-run with --force.`);
  }
  cfg.mcp[SERVER_NAME] = entry;
  writeJson(file, cfg);
  return { file, missing: [], notes: ['OpenCode resolves {env:VAR}; launch it from a shell that has your keys.'] };
}

// Expansion-env entry: keys reference the shell env in the host's own syntax (no literal secrets).
function expansionEnv(fmt) {
  const e = {};
  for (const k of MEDIA_KEYS) e[k] = fmt(k);
  return e;
}

// Gemini CLI: ~/.gemini/settings.json (global) or project .gemini/settings.json. `mcpServers` with
// `$VAR` expansion from the shell env (Gemini supports $VAR / ${VAR}).
function installGemini({ projectDir, force, serverPy, command, argsPrefix }) {
  const file = projectDir
    ? path.join(projectDir, '.gemini', 'settings.json')
    : path.join(home(), '.gemini', 'settings.json');
  const entry = { command, args: [...argsPrefix, serverPy], env: expansionEnv((k) => `$${k}`) };
  mergeServer(file, 'mcpServers', entry, force);
  return { file, missing: [], notes: ['Keys resolve from the shell that launches Gemini ($VAR).'] };
}

// Claude Code: the plugin already bundles this MCP server. For a non-plugin (standalone) setup,
// write a project-scoped .mcp.json with `${VAR:-}` expansion. User/global scope lives in the
// Claude-managed ~/.claude.json, which we don't edit directly — use the plugin or --project-dir.
function installClaude({ projectDir, force, serverPy, command, argsPrefix }) {
  if (!projectDir) {
    throw new Error(
      'Claude Code gets SuperCMO via the plugin: `/plugin marketplace add SupercmoHQ/superCMO-skills` then `/plugin install supercmo@superCMO-skills`. For a standalone project registration instead, pass --project-dir <dir> to write a project .mcp.json.'
    );
  }
  const file = path.join(projectDir, '.mcp.json');
  const entry = { command, args: [...argsPrefix, serverPy], env: expansionEnv((k) => `\${${k}:-}`) };
  mergeServer(file, 'mcpServers', entry, force);
  return { file, missing: [], notes: ['Standalone project registration; keys resolve via ${VAR:-} from your shell.'] };
}

// --- uninstall ---

function removeServerEntry(file, wrapperKey, tweak) {
  if (!fs.existsSync(file)) return { file, removed: false };
  const cfg = readJson(file);
  let removed = false;
  if (cfg[wrapperKey] && Object.prototype.hasOwnProperty.call(cfg[wrapperKey], SERVER_NAME)) {
    delete cfg[wrapperKey][SERVER_NAME];
    removed = true;
  }
  if (tweak) tweak(cfg);
  writeJson(file, cfg);
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
function uninstallVscode({ projectDir }) {
  if (!projectDir) throw new Error('VS Code uninstall needs --project-dir <workspace>.');
  const file = path.join(projectDir, '.vscode', 'mcp.json');
  const ids = new Set(MEDIA_KEYS.map((k) => k.toLowerCase().replace(/_/g, '-')));
  const { removed } = removeServerEntry(file, 'servers', (cfg) => {
    if (Array.isArray(cfg.inputs)) cfg.inputs = cfg.inputs.filter((i) => !ids.has(i.id));
  });
  return { file, removed, notes: [] };
}
function uninstallOpenCode({ projectDir }) {
  const file = projectDir ? path.join(projectDir, 'opencode.json') : path.join(home(), '.config', 'opencode', 'opencode.json');
  return { ...removeServerEntry(file, 'mcp'), notes: [] };
}
function uninstallGemini({ projectDir }) {
  const file = projectDir ? path.join(projectDir, '.gemini', 'settings.json') : path.join(home(), '.gemini', 'settings.json');
  return { ...removeServerEntry(file, 'mcpServers'), notes: [] };
}
function uninstallClaude({ projectDir }) {
  if (!projectDir) throw new Error('Claude Code: uninstall the plugin via /plugin, or pass --project-dir to remove a standalone project registration.');
  const file = path.join(projectDir, '.mcp.json');
  const { removed } = removeServerEntry(file, 'mcpServers');
  const c = comp();
  const s = c.removeSkills(path.join(projectDir, '.claude', 'skills'));
  const a = c.removeMdFiles(c.AGENTS_SRC, path.join(projectDir, '.claude', 'agents'));
  const cm = c.removeMdFiles(c.COMMANDS_SRC, path.join(projectDir, '.claude', 'commands'));
  return { file, removed, notes: [`removed skills:${s} agent:${a} command:${cm}`] };
}

module.exports = {
  installCursor, installWindsurf, installCline, installVscode, installOpenCode,
  installGemini, installClaude, readJson, clineSettingsFile,
  uninstallCursor, uninstallWindsurf, uninstallCline, uninstallVscode,
  uninstallOpenCode, uninstallGemini, uninstallClaude,
};
