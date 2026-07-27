'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

// Package root = two levels up from bin/lib/. When published, mcp-server/ + scripts/ ship here
// (this may be a transient npx cache dir — see installRuntime).
const PLUGIN_ROOT = path.resolve(__dirname, '..', '..');
const SERVER_NAME = 'supercmo';

// The media keys the server reads. SUPERCMO_API_KEY (managed/hosted) is intentionally excluded.
const MEDIA_KEYS = ['FAL_KEY', 'OPENAI_API_KEY', 'GEMINI_API_KEY', 'ELEVENLABS_API_KEY', 'XAI_API_KEY', 'FIRECRAWL_API_KEY'];

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

// Read media keys present in the installing shell's environment (for hosts that need literal values).
function keysFromEnv() {
  const present = {};
  const missing = [];
  for (const k of MEDIA_KEYS) {
    if (process.env[k]) present[k] = process.env[k];
    else missing.push(k);
  }
  return { present, missing };
}

module.exports = { PLUGIN_ROOT, SERVER_NAME, MEDIA_KEYS, keysFromEnv, home, installRuntime };
