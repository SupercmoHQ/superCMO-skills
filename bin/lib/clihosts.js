'use strict';
// MCP registration for hosts that ship a first-party `mcp add` CLI — Codex, Claude Code, VS Code.
// We DELEGATE to that CLI (the host owns and writes its own config file) instead of editing
// ~/.codex/config.toml / settings.json / .mcp.json ourselves. This is the ecosystem standard
// (Smithery CLI, vendor docs, Microsoft's Playwright MCP all do exactly this) and it makes config
// corruption structurally impossible — we never parse or rewrite the host's config.
//
// Secrets: we register ONLY command + args, never an env block. Keys are delivered host-independently
// by the server itself, which loads ~/.supercmo/.env on startup (scripts/supercmo_env.py). We do NOT
// write `${VAR:-}` env references: host expansion of such refs is non-portable and proven broken —
// Codex forwards env values verbatim, so a `${FAL_KEY:-}` ref lands as that literal string and 401s.
const { execFileSync } = require('child_process');

// Run `<bin> <args...>`; classify the outcome. Never throws.
function runCli(bin, args) {
  try {
    execFileSync(bin, args, { stdio: 'pipe' });
    return { ok: true };
  } catch (e) {
    if (e && e.code === 'ENOENT') return { cliMissing: true };
    return { ok: false, error: (e.stderr || e.stdout || e.message || '').toString().trim().slice(0, 300) };
  }
}

const HOSTS = {
  // Codex — `codex mcp add <name> -- <command> [args]`, home scope. No env block: Codex does not expand
  // `${VAR:-}` refs (it forwards env values verbatim), so keys come from ~/.supercmo/.env instead.
  codex: {
    bin: 'codex',
    add: ({ name, command, args }) => ({ args: ['mcp', 'add', name, '--', command, ...args], missing: [] }),
    remove: (name) => ['mcp', 'remove', name],
    snippet: ({ name, command, args }) =>
      `Codex CLI not found. Add this to ~/.codex/config.toml:\n\n[mcp_servers.${name}]\ncommand = "${command}"\nargs = [${args.map((a) => `"${a}"`).join(', ')}]`,
  },
  // Claude Code — standalone/non-plugin path (the PLUGIN is the primary install). `-s user` writes to
  // ~/.claude.json (user scope), NOT the cwd's project .mcp.json. No env block — keys load from
  // ~/.supercmo/.env; `mcp add` defaults to stdio transport.
  claude: {
    bin: 'claude',
    add: ({ name, command, args }) => ({ args: ['mcp', 'add', '-s', 'user', name, '--', command, ...args], missing: [] }),
    remove: (name) => ['mcp', 'remove', '-s', 'user', name],
    snippet: ({ name }) =>
      `Claude CLI not found. Preferred install is the plugin:\n  /plugin marketplace add SupercmoHQ/superCMO-skills\n  /plugin install ${name}@superCMO-skills`,
  },
  // VS Code — `code --add-mcp '{…}'`. No env block; keys load from ~/.supercmo/.env.
  vscode: {
    bin: process.platform === 'win32' ? 'code.cmd' : 'code',
    add: ({ name, command, args }) => ({ args: ['--add-mcp', JSON.stringify({ name, command, args })], missing: [] }),
    remove: null, // VS Code has no `--remove-mcp`; uninstall is manual (MCP: Open User Configuration).
    snippet: ({ name, command, args }) =>
      `VS Code CLI not found. Run:\n  code --add-mcp '${JSON.stringify({ name, command, args })}'`,
  },
};

// Register the server with a CLI host. Idempotent: remove-then-add so a re-run never duplicates or
// errors on "already exists". Returns { ok | cliMissing | error, missing, snippet }.
function install(hostKey, { name, command, args }) {
  const h = HOSTS[hostKey];
  const built = h.add({ name, command, args });
  if (h.remove) runCli(h.bin, h.remove(name)); // best-effort; ignore "not found"
  const r = runCli(h.bin, built.args);
  return { ...r, missing: built.missing, snippet: () => h.snippet({ name, command, args }) };
}

function uninstall(hostKey, { name }) {
  const h = HOSTS[hostKey];
  if (!h.remove) return { unsupported: true };
  return runCli(h.bin, h.remove(name));
}

module.exports = { HOSTS, install, uninstall, runCli };
