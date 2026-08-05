'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

// Package root = two levels up from bin/lib/. When published, mcp-server/ + scripts/ ship here
// (this may be a transient npx cache dir — see installRuntime).
const PLUGIN_ROOT = path.resolve(__dirname, '..', '..');
const SERVER_NAME = 'supercmo';

function home() {
  return os.homedir();
}

// Copy the server runtime (mcp-server/ + scripts/) into a STABLE location so host configs never
// point at the ephemeral npx cache (~/.npm/_npx/<hash>/…) that npm garbage-collects. Idempotent:
// overwrites on each run so re-installing picks up a newer version. Returns the stable server.py path.
function installRuntime() {
  const dest = path.join(home(), '.supercmo', 'runtime');
  const skip = (src) => src.endsWith('__pycache__') || src.includes(`${path.sep}__pycache__${path.sep}`) || src.endsWith('.pyc');
  for (const sub of ['mcp-server', 'scripts']) {
    const from = path.join(PLUGIN_ROOT, sub);
    if (!fs.existsSync(from)) throw new Error(`packaged ${sub}/ missing at ${from}`);
    const to = path.join(dest, sub);
    fs.rmSync(to, { recursive: true, force: true });
    fs.cpSync(from, to, { recursive: true, filter: (s) => !skip(s) });
  }
  return path.join(dest, 'mcp-server', 'server.py');
}

// Create ~/.supercmo/.env with labeled placeholders the FIRST time only — NEVER clobber a user's keys
// on re-install. The MCP server loads this file (scripts/supercmo_env.py) so keys work on every host
// without touching per-host configs. chmod 600. Returns {file, created}.
function ensureKeyFile() {
  const file = path.join(home(), '.supercmo', '.env');
  if (fs.existsSync(file)) {
    fs.chmodSync(file, 0o600);
    return { file, created: false };
  }
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const body = [
    '# SuperCMO keys — add at least one below, then restart your host.',
    '# Docs: https://github.com/SupercmoHQ/superCMO-skills#bring-your-own-keys',
    '',
    '# image + video (start here) — get a key at https://fal.ai/dashboard/keys',
    'FAL_KEY=',
    '',
    '# voiceover (optional) — https://elevenlabs.io/app/settings/api-keys',
    'ELEVENLABS_API_KEY=',
    '',
    '# image / video analysis (optional) — https://aistudio.google.com/app/apikey',
    'GEMINI_API_KEY=',
    '',
    '# url extraction (optional) — https://www.firecrawl.dev/app/api-keys',
    'FIRECRAWL_API_KEY=',
    '',
  ].join('\n');
  fs.writeFileSync(file, body, { mode: 0o600 });
  return { file, created: true };
}

// Set a single KEY=value in ~/.supercmo/.env, preserving every OTHER line (the file is shared
// with the user's other keys). Ensures the file exists first, then: replaces the line for `name`
// in place (whether it was empty or already set), or appends it if absent. chmod 600. Used by
// `supercmo login` to write the managed SUPERCMO_API_KEY without a copy-paste. Returns the path.
function setKey(name, value) {
  if (!/^[A-Z][A-Z0-9_]*$/.test(name)) throw new Error('invalid environment key name.');
  if (typeof value !== 'string' || !value || /[\u0000-\u001f\u007f]/.test(value))
    throw new Error('invalid credential returned by the login service.');
  const { file } = ensureKeyFile();
  const line = `${name}=${value}`;
  const re = new RegExp(`^\\s*${name}\\s*=`);
  const lines = fs.readFileSync(file, 'utf8').split('\n');
  let replaced = false;
  for (let i = 0; i < lines.length; i++) {
    if (re.test(lines[i])) {
      lines[i] = line;
      replaced = true;
      break;
    }
  }
  if (!replaced) {
    // Append, keeping a single trailing newline (the placeholder body ends with '').
    if (lines.length && lines[lines.length - 1] === '') lines[lines.length - 1] = line;
    else lines.push(line);
    lines.push('');
  }
  fs.writeFileSync(file, lines.join('\n'), { mode: 0o600 });
  fs.chmodSync(file, 0o600);
  return file;
}

module.exports = { PLUGIN_ROOT, SERVER_NAME, home, installRuntime, ensureKeyFile, setKey };
