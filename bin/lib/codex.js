'use strict';
// MCP registration for Codex CLI — ~/.codex/config.toml (or project .codex/config.toml).
// Codex does NOT inherit the shell env by default, so keys are written literally into
// [mcp_servers.<name>.env] (the documented Codex form). TOML is edited as text (no TOML lib in
// stdlib): our own [mcp_servers.supercmo*] tables are removed and rewritten (idempotent);
// every other table in the file is preserved untouched.
const fs = require('fs');
const path = require('path');
const { SERVER_NAME, keysFromEnv, home } = require('./config');

const tomlEsc = (s) => String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"');

function installCodex({ projectDir, serverPy, command, argsPrefix }) {
  const file = projectDir
    ? path.join(projectDir, '.codex', 'config.toml')
    : path.join(home(), '.codex', 'config.toml');
  const { present, missing } = keysFromEnv();

  const args = [...argsPrefix, serverPy].map((a) => `"${tomlEsc(a)}"`).join(', ');
  let block = `[mcp_servers.${SERVER_NAME}]\ncommand = "${tomlEsc(command)}"\nargs = [${args}]\n`;
  const envLines = Object.entries(present).map(([k, v]) => `${k} = "${tomlEsc(v)}"`).join('\n');
  if (envLines) block += `\n[mcp_servers.${SERVER_NAME}.env]\n${envLines}\n`;

  let text = fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : '';
  // Drop any existing [mcp_servers.supercmo] / [mcp_servers.supercmo.<sub>] tables (header + body
  // up to the next table header or EOF). The `(\.[^\]]*)?` won't match a sibling like `supercmo-x`.
  text = text.replace(new RegExp(`(^|\\n)\\[mcp_servers\\.${SERVER_NAME}(\\.[^\\]]*)?\\][^\\[]*`, 'g'), '\n');
  text = text.replace(/\n{3,}/g, '\n\n').trimEnd();

  const out = (text ? text + '\n\n' : '') + block.trimEnd() + '\n';
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, out, 'utf8');
  return { file, missing, notes: [] };
}

function uninstallCodex({ projectDir }) {
  const file = projectDir
    ? path.join(projectDir, '.codex', 'config.toml')
    : path.join(home(), '.codex', 'config.toml');
  let removed = false;
  if (fs.existsSync(file)) {
    const before = fs.readFileSync(file, 'utf8');
    let text = before
      .replace(new RegExp(`(^|\\n)\\[mcp_servers\\.${SERVER_NAME}(\\.[^\\]]*)?\\][^\\[]*`, 'g'), '\n')
      .replace(/\n{3,}/g, '\n\n')
      .trimEnd();
    fs.writeFileSync(file, text ? text + '\n' : '', 'utf8');
    removed = before !== (text ? text + '\n' : '');
  }
  const root = projectDir ? path.join(projectDir, '.agents', 'skills') : path.join(home(), '.agents', 'skills');
  const skills = require('./components').removeSkills(root);
  return { file, removed, notes: skills ? [`removed ${skills} skills`] : [] };
}

module.exports = { installCodex, uninstallCodex };
