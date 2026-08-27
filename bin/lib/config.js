'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

// Package root = two levels up from bin/lib/.
const PLUGIN_ROOT = path.resolve(__dirname, '..', '..');
const SERVER_NAME = 'supercmo';
// The MCP server runs from PyPI via `uvx supercmo-skills@<version>` — pinned to this installer's
// version (single source) so the skills placed here and the server tools stay in lockstep. dist name
// == console-script name, so `uvx <spec>` resolves with no --from.
const SERVER_SPEC = `supercmo-skills@${require(path.join(PLUGIN_ROOT, 'package.json')).version}`;

function home() {
  return os.homedir();
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
  const dir = path.dirname(file);
  fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
  fs.chmodSync(dir, 0o700);   // mkdir mode is umask-masked; force 0700 (the dir holds the .env keyfile)
  const body = [
    '# SuperCMO keys — add at least one below.',
    '# Docs: https://github.com/SupercmoHQ/superCMO-skills#bring-your-own-keys',
    '',
    '# image + video (start here) — WaveSpeed is recommended (better reliability);',
    '# fal is fully supported too and serves the same models.',
    '# https://wavespeed.ai/dashboard',
    'WAVESPEED_API_KEY=',
    '# https://fal.ai/dashboard/keys',
    'FAL_KEY=',
    '# With both set, WaveSpeed is used; SUPERCMO_MEDIA_PROVIDER=fal picks the other.',
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
    '# social research (optional) — https://scrapecreators.com',
    'SCRAPECREATORS_API_KEY=',
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

module.exports = { PLUGIN_ROOT, SERVER_NAME, SERVER_SPEC, home, ensureKeyFile, setKey };
