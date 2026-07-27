#!/usr/bin/env node
'use strict';
// SuperCMO multi-host installer. Projects the plugin (MCP server + skills + agent + command)
// onto each AI-agent host using that host's native config. See docs/multi-host-install.md.
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { home, installRuntime } = require('./lib/config');
const json = require('./lib/jsonhosts');
const codex = require('./lib/codex');
const components = require('./lib/components');

// No skills concept — the MCP tools are the capability; skills/agent/command are skipped.
const noSkillsNote = () => ['skipped: skills, agent, command (host has no skills concept; MCP tools provide the capability)'];

// Find a working Python 3 interpreter and how to invoke it (command + any prefix args).
function detectPython() {
  const candidates =
    process.platform === 'win32'
      ? [['py', ['-3']], ['python', []], ['python3', []]]
      : [['python3', []], ['python', []]];
  for (const [command, argsPrefix] of candidates) {
    try {
      const r = spawnSync(command, [...argsPrefix, '--version'], { stdio: 'ignore' });
      if (r.status === 0) return { command, argsPrefix };
    } catch (_) { /* not found, try next */ }
  }
  throw new Error(`no Python 3 found (tried ${candidates.map((c) => c[0]).join(', ')}). Install Python 3 and re-run.`);
}

// Increment 1: JSON-config MCP hosts. Others land in later increments.
const HOSTS = {
  cursor: {
    label: 'Cursor', run: json.installCursor, uninstall: json.uninstallCursor, detect: () => fs.existsSync(path.join(home(), '.cursor')),
    place: ({ projectDir }) => projectDir
      ? [`skills → .cursor/rules (${components.placeCursorRules(path.join(projectDir, '.cursor', 'rules'))} rules)`, 'skipped: agent, command (no Cursor equivalent)']
      : ['skipped: skills/agent/command — pass --project-dir to place Cursor rules'],
  },
  windsurf: { label: 'Windsurf', run: json.installWindsurf, uninstall: json.uninstallWindsurf, detect: () => fs.existsSync(path.join(home(), '.codeium', 'windsurf')), place: noSkillsNote },
  cline: { label: 'Cline', run: json.installCline, uninstall: json.uninstallCline, detect: () => fs.existsSync(path.dirname(path.dirname(json.clineSettingsFile()))), place: noSkillsNote },
  vscode: { label: 'VS Code', run: json.installVscode, uninstall: json.uninstallVscode, detect: () => false, place: noSkillsNote }, // workspace-scoped: only via explicit --vscode --project-dir
  codex: {
    label: 'Codex', run: codex.installCodex, uninstall: codex.uninstallCodex, detect: () => fs.existsSync(path.join(home(), '.codex')),
    place: ({ projectDir }) => {
      const root = projectDir ? path.join(projectDir, '.agents', 'skills') : path.join(home(), '.agents', 'skills');
      return [`skills → ${root} (${components.placeSkills(root)})`, 'skipped: agent, command (Codex has no separate agent/command concept)'];
    },
  },
  opencode: { label: 'OpenCode', run: json.installOpenCode, uninstall: json.uninstallOpenCode, detect: () => fs.existsSync(path.join(home(), '.config', 'opencode')), place: () => ['skipped: skills, agent, command (add guidance via AGENTS.md; MCP tools provide the capability)'] },
  gemini: { label: 'Gemini CLI', run: json.installGemini, uninstall: json.uninstallGemini, detect: () => fs.existsSync(path.join(home(), '.gemini')), place: () => ['skipped: skills, agent, command here — use the Gemini extension for the full bundle'] },
  claude: {
    label: 'Claude Code', run: json.installClaude, uninstall: json.uninstallClaude, detect: () => false, // plugin is the default path; standalone only via explicit --claude --project-dir
    place: ({ projectDir }) => projectDir
      ? [
          `skills → .claude/skills (${components.placeSkills(path.join(projectDir, '.claude', 'skills'))})`,
          `agent → .claude/agents (${components.placeMdDir(components.AGENTS_SRC, path.join(projectDir, '.claude', 'agents'))})`,
          `command → .claude/commands (${components.placeMdDir(components.COMMANDS_SRC, path.join(projectDir, '.claude', 'commands'))})`,
        ]
      : [],
  },
};
const PENDING = [];

function parseArgs(argv) {
  const opts = { hosts: [], all: false, projectDir: null, force: false, uninstall: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--all') opts.all = true;
    else if (a === '--force') opts.force = true;
    else if (a === '--uninstall') opts.uninstall = true;
    else if (a === '--project-dir') opts.projectDir = path.resolve(argv[++i] || '.');
    else if (a.startsWith('--') && HOSTS[a.slice(2)]) opts.hosts.push(a.slice(2));
    else if (a.startsWith('--') && PENDING.includes(a.slice(2))) {
      throw new Error(`--${a.slice(2)} is not implemented yet (later increment).`);
    } else throw new Error(`Unknown option: ${a}`);
  }
  return opts;
}

function usage() {
  console.log(`SuperCMO installer

  supercmo-install --cursor [--project-dir <dir>]
  supercmo-install --windsurf
  supercmo-install --cline
  supercmo-install --vscode --project-dir <workspace>
  supercmo-install --codex [--project-dir <dir>]
  supercmo-install --opencode [--project-dir <dir>]
  supercmo-install --gemini [--project-dir <dir>]
  supercmo-install --claude --project-dir <dir>   # standalone; else use the plugin
  supercmo-install --all            # every detected host above
  [--force] overwrite a differing existing server entry
  --uninstall --<host> [--project-dir <dir>]   # remove what we wrote (add --all for every detected host)`);
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  let hosts = opts.hosts;
  if (opts.all) hosts = Object.keys(HOSTS).filter((h) => HOSTS[h].detect());
  if (!hosts.length) { usage(); process.exit(opts.all ? 0 : 1); }

  if (opts.uninstall) {
    let failures = 0;
    for (const h of hosts) {
      const host = HOSTS[h];
      try {
        const r = host.uninstall({ projectDir: opts.projectDir });
        console.log(`${r.removed ? '✓' : '·'} ${host.label}: ${r.removed ? 'removed from' : 'nothing to remove in'} ${r.file}`);
        for (const n of r.notes || []) console.log(`  · ${n}`);
      } catch (e) {
        failures++;
        console.error(`✗ ${host.label}: ${e.message}`);
      }
    }
    if (opts.all) {
      const rt = path.join(home(), '.supercmo', 'runtime');
      fs.rmSync(rt, { recursive: true, force: true });
      console.log(`· removed runtime ${rt}`);
    }
    process.exit(failures ? 1 : 0);
  }

  const py = detectPython();
  const serverPy = installRuntime(); // copy runtime to ~/.supercmo/runtime (stable, npx-cache-proof)
  console.log(`· python: ${[py.command, ...py.argsPrefix].join(' ')}`);
  console.log(`· runtime: ${serverPy}`);

  let failures = 0;
  for (const h of hosts) {
    const host = HOSTS[h];
    try {
      const r = host.run({ projectDir: opts.projectDir, force: opts.force, serverPy, command: py.command, argsPrefix: py.argsPrefix });
      console.log(`✓ ${host.label}: wrote ${r.file}`);
      if (r.missing && r.missing.length) {
        console.log(`  ⚠ keys not in your env (server will lack those providers): ${r.missing.join(', ')}`);
      }
      for (const n of r.notes || []) console.log(`  · ${n}`);
      for (const line of (host.place ? host.place({ projectDir: opts.projectDir }) : [])) console.log(`  · ${line}`);
    } catch (e) {
      failures++;
      console.error(`✗ ${host.label}: ${e.message}`);
    }
  }
  process.exit(failures ? 1 : 0);
}

main();
