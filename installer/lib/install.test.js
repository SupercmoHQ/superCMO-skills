'use strict';
// Regression tests for the multi-host installer. Run: `npm test` (node --test).
// Each test runs against a throwaway HOME + temp dirs; no real host config is touched.
// CLI-delegation hosts (codex/claude/vscode) are tested at the argv-construction level, so the
// suite needs none of those binaries; the real `<host> mcp add` round-trip is verified manually.
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const config = require('./config');
const json = require('./jsonhosts');
const cli = require('./clihosts');
const components = require('./components');
const install = require('../install');

// Fresh temp HOME with a known key set: FAL_KEY present, the others absent.
function setup() {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'supercmo-home-'));
  process.env.HOME = home;
  process.env.FAL_KEY = 'test-fal';
  for (const k of ['OPENAI_API_KEY', 'GEMINI_API_KEY', 'ELEVENLABS_API_KEY', 'FIRECRAWL_API_KEY']) delete process.env[k];
  return { home };
}
const tmpProj = () => fs.mkdtempSync(path.join(os.tmpdir(), 'supercmo-proj-'));
// Every host runs `uvx supercmo-skills@<version>` (from PyPI) — no --from, no env block.
const SPEC = config.SERVER_SPEC;
const optsFile = (o, extra = {}) => ({ serverPy: SPEC, command: 'uvx', argsPrefix: [], ...extra });
const read = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));
const addArgs = (o) => ({ name: 'supercmo', command: 'uvx', args: [SPEC] });

test('SERVER_SPEC pins supercmo-skills to the installer version (dist == console-script name)', () => {
  assert.match(SPEC, /^supercmo-skills@\d+\.\d+\.\d+$/, 'pinned PyPI spec');
});

test('ensureKeyFile creates ~/.supercmo/.env once with placeholders, never clobbers keys', () => {
  const o = setup();
  const r1 = config.ensureKeyFile();
  assert.equal(r1.created, true, 'created on first run');
  assert.equal(r1.file, path.join(o.home, '.supercmo', '.env'));
  const body = fs.readFileSync(r1.file, 'utf8');
  assert.ok(body.includes('FAL_KEY=') && body.includes('ELEVENLABS_API_KEY='), 'labeled placeholders');
  assert.ok(!body.includes('SUPERCMO_API_KEY'), 'no managed key in the placeholder');
  // user adds a key → re-run must NOT overwrite it
  fs.writeFileSync(r1.file, 'FAL_KEY=mykey\n');
  const r2 = config.ensureKeyFile();
  assert.equal(r2.created, false, 'not re-created');
  assert.equal(fs.readFileSync(r2.file, 'utf8').trim(), 'FAL_KEY=mykey', 'user key preserved');
});

// --- CLI-delegation hosts: assert the `<host> mcp add` argv we build (no binary needed) ---

test('codex: builds `codex mcp add <name> -- <cmd>` with NO env block (keys load from ~/.supercmo/.env)', () => {
  const o = setup();
  const { args, missing } = cli.HOSTS.codex.add(addArgs(o));
  assert.deepEqual(args, ['mcp', 'add', 'supercmo', '--', 'uvx', SPEC]);
  assert.ok(!args.includes('--env'), 'no --env: Codex forwards refs literally, so we never write them');
  assert.ok(!JSON.stringify(args).includes('test-fal'), 'no literal secret written');
  assert.deepEqual(missing, []);
  assert.deepEqual(cli.HOSTS.codex.remove('supercmo'), ['mcp', 'remove', 'supercmo']);
});

test('claude: builds `claude mcp add -s user <name> -- <cmd>` (user scope, NO env block)', () => {
  const o = setup();
  const { args } = cli.HOSTS.claude.add(addArgs(o));
  assert.deepEqual(args, ['mcp', 'add', '-s', 'user', 'supercmo', '--', 'uvx', SPEC]);
  assert.ok(!args.includes('--env'), 'no --env — keys load from ~/.supercmo/.env');
  assert.deepEqual(cli.HOSTS.claude.remove('supercmo'), ['mcp', 'remove', '-s', 'user', 'supercmo']);
});

test('vscode: builds `code --add-mcp` JSON with NO env block, no literal secret', () => {
  const o = setup();
  const { args } = cli.HOSTS.vscode.add(addArgs(o));
  assert.equal(args[0], '--add-mcp');
  const j = JSON.parse(args[1]);
  assert.equal(j.name, 'supercmo');
  assert.ok(!j.env, 'no env block — keys load from ~/.supercmo/.env');
  assert.ok(!JSON.stringify(j).includes('test-fal'), 'no literal key value');
});

test('runCli returns cliMissing for an absent binary', () => {
  const r = cli.runCli('supercmo-no-such-bin-xyz', ['mcp', 'list']);
  assert.equal(r.cliMissing, true);
});

// Both shipped plugin manifests must register command + args ONLY — never an env block. Writing
// `${VAR:-}` refs is non-portable and proven broken (Codex forwards them literally → 401); keys come
// from ~/.supercmo/.env, which the server loads on startup.
test('plugin manifests (.mcp.json, .codex-plugin/mcp.json) register no env block', () => {
  const root = path.resolve(__dirname, '..', '..');
  for (const rel of ['.mcp.json', '.codex-plugin/mcp.json']) {
    const s = JSON.parse(fs.readFileSync(path.join(root, rel), 'utf8')).mcpServers.supercmo;
    assert.ok(s.command && Array.isArray(s.args), `${rel}: registers command + args`);
    assert.ok(!s.env, `${rel}: no env block — keys load from ~/.supercmo/.env`);
  }
});

// --- File hosts (no first-party CLI): safe JSON merge ---

test('cursor: registers command + args, no env block, no literal secret', () => {
  const o = setup();
  const r = json.installCursor(optsFile(o));
  const s = read(r.file).mcpServers.supercmo;
  assert.equal(s.command, 'uvx');
  assert.deepEqual(s.args, [SPEC]);
  assert.ok(!s.env, 'no env block — keys load from ~/.supercmo/.env');
  assert.ok(!JSON.stringify(s).includes('test-fal'), 'no literal key value written');
});

test('cursor idempotent re-run leaves a single entry', () => {
  const o = setup();
  json.installCursor(optsFile(o));
  const r = json.installCursor(optsFile(o));
  assert.equal(Object.keys(read(r.file).mcpServers).length, 1);
});

test('cursor --force guard: differing entry throws without force, succeeds with it', () => {
  const o = setup();
  const r = json.installCursor(optsFile(o));
  const cfg = read(r.file);
  cfg.mcpServers.supercmo.args = ['/tampered'];
  fs.writeFileSync(r.file, JSON.stringify(cfg));
  assert.throws(() => json.installCursor(optsFile(o)), /already exists/);
  assert.doesNotThrow(() => json.installCursor(optsFile(o, { force: true })));
});

test('cursor JSONC (comments + trailing comma) tolerated, other servers preserved', () => {
  const o = setup();
  const file = path.join(o.home, '.cursor', 'mcp.json');
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, '{\n  // my server\n  "mcpServers": { "other": {"command":"x","args":[]}, }\n}');
  json.installCursor(optsFile(o));
  const cfg = read(file);
  assert.ok(cfg.mcpServers.other, 'user server kept');
  assert.ok(cfg.mcpServers.supercmo, 'our server added');
});

test('opencode: mcp key, command array, no environment block', () => {
  const o = setup();
  const s = read(json.installOpenCode(optsFile(o)).file).mcp.supercmo;
  assert.equal(s.type, 'local');
  assert.deepEqual(s.command, ['uvx', SPEC]);
  assert.ok(!s.environment, 'no environment block — keys load from ~/.supercmo/.env');
});

test('cursor uninstall removes our entry, preserves the user server', () => {
  const o = setup();
  const r = json.installCursor(optsFile(o));
  const cfg = read(r.file);
  cfg.mcpServers.user = { command: 'x', args: [] };
  fs.writeFileSync(r.file, JSON.stringify(cfg));
  const u = json.uninstallCursor({});
  assert.equal(u.removed, true);
  const after = read(r.file);
  assert.ok(!after.mcpServers.supercmo, 'ours removed');
  assert.ok(after.mcpServers.user, 'user server kept');
});

// --- skill placement (unchanged; used by codex/claude place + unplace) ---

test('components: cursor rules pruned on re-place, user rule kept', () => {
  setup();
  const rules = fs.mkdtempSync(path.join(os.tmpdir(), 'rules-'));
  fs.writeFileSync(path.join(rules, 'supercmo-old.mdc'), '');
  fs.writeFileSync(path.join(rules, 'mine.mdc'), '');
  const n = components.placeCursorRules(rules);
  assert.equal(n, components.listSkills().length, 'a rule per skill written');
  assert.ok(!fs.existsSync(path.join(rules, 'supercmo-old.mdc')), 'stale supercmo rule pruned');
  assert.ok(fs.existsSync(path.join(rules, 'mine.mdc')), 'user rule kept');
});

test('components: removeSkills removes our skills, keeps the user skill', () => {
  setup();
  const dest = path.join(tmpProj(), 'skills');
  components.placeSkills(dest);
  const names = components.listSkills();
  assert.ok(names.length >= 1 && fs.existsSync(path.join(dest, names[0])), 'a real skill was placed');
  fs.mkdirSync(path.join(dest, 'user-skill'), { recursive: true });
  fs.writeFileSync(path.join(dest, 'user-skill', 'keep.md'), '');
  components.removeSkills(dest);
  assert.ok(!fs.existsSync(path.join(dest, names[0])), 'our skill removed');
  assert.ok(fs.existsSync(path.join(dest, 'user-skill', 'keep.md')), 'user skill kept');
});

// --- `supercmo login` (RFC 8628 device grant) — setKey writer + runLogin client ---

test('setKey appends SUPERCMO_API_KEY, preserves other keys, and is idempotent', () => {
  const o = setup();
  config.ensureKeyFile();
  const file = config.setKey('SUPERCMO_API_KEY', 'sk-scmo-abc');
  let body = fs.readFileSync(file, 'utf8');
  assert.ok(body.includes('SUPERCMO_API_KEY=sk-scmo-abc'), 'key written');
  assert.ok(body.includes('FAL_KEY='), 'placeholder preserved');
  config.setKey('SUPERCMO_API_KEY', 'sk-scmo-xyz');
  body = fs.readFileSync(file, 'utf8');
  assert.equal((body.match(/SUPERCMO_API_KEY=/g) || []).length, 1, 'exactly one line');
  assert.ok(body.includes('sk-scmo-xyz') && !body.includes('sk-scmo-abc'), 'overwritten in place');
});

test('setKey fills an existing empty SUPERCMO_API_KEY= and never clobbers a real user key', () => {
  const o = setup();
  const file = path.join(o.home, '.supercmo', '.env');
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, 'FAL_KEY=mykey\nSUPERCMO_API_KEY=\n');
  config.setKey('SUPERCMO_API_KEY', 'sk-scmo-new');
  assert.equal(
    fs.readFileSync(file, 'utf8').trim(),
    'FAL_KEY=mykey\nSUPERCMO_API_KEY=sk-scmo-new',
    'filled the empty line, user key intact',
  );
});

test('setKey rejects control characters and corrects existing key-file permissions', () => {
  const o = setup();
  const file = path.join(o.home, '.supercmo', '.env');
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, 'FAL_KEY=mykey\n', { mode: 0o644 });
  assert.throws(
    () => config.setKey('SUPERCMO_API_KEY', 'valid-token\nINJECTED=value'),
    /invalid credential/,
  );
  assert.equal(fs.readFileSync(file, 'utf8'), 'FAL_KEY=mykey\n', 'invalid token changed nothing');
  config.setKey('SUPERCMO_API_KEY', 'valid-token');
  if (process.platform !== 'win32') {
    assert.equal(fs.statSync(file).mode & 0o777, 0o600, 'existing file tightened to owner-only');
  }
});

test('runLogin: start -> poll pending -> poll approved -> writes the key to ~/.supercmo/.env', async () => {
  const o = setup();
  const responses = [
    { ok: true, json: async () => ({ device_code: 'dc', user_code: 'ABCD-2345', verification_uri_complete: 'https://x/activate?code=ABCD-2345', interval: 5, expires_in: 600 }) },
    { ok: false, status: 400, json: async () => ({ error: 'authorization_pending' }) },
    { ok: true, json: async () => ({ access_token: 'sk-scmo-frombackend', token_type: 'Bearer' }) },
  ];
  let call = 0;
  const opened = [];
  const code = await install.runLogin([], {
    fetch: async () => responses[call++],
    openBrowser: (u) => opened.push(u),
    sleep: async () => {},
    log: () => {},
  });
  assert.equal(code, 0, 'returns success');
  assert.equal(opened.length, 1, 'browser opened once');
  assert.equal(opened[0], 'https://x/activate?code=ABCD-2345', 'opened the verification URL');
  const body = fs.readFileSync(path.join(o.home, '.supercmo', '.env'), 'utf8');
  assert.ok(body.includes('SUPERCMO_API_KEY=sk-scmo-frombackend'), 'key delivered to the CLI written to .env');
});

test('runLogin: a terminal error (access_denied) throws and writes no key', async () => {
  const o = setup();
  const responses = [
    { ok: true, json: async () => ({ device_code: 'dc', user_code: 'AB', verification_uri_complete: 'https://x/activate', interval: 5, expires_in: 600 }) },
    { ok: false, status: 400, json: async () => ({ error: 'access_denied' }) },
  ];
  let call = 0;
  await assert.rejects(
    install.runLogin([], { fetch: async () => responses[call++], openBrowser: () => {}, sleep: async () => {}, log: () => {} }),
    /denied/i,
  );
  const file = path.join(o.home, '.supercmo', '.env');
  if (fs.existsSync(file)) assert.ok(!fs.readFileSync(file, 'utf8').includes('SUPERCMO_API_KEY='), 'no key on failure');
});

test('runLogin rejects an unsafe verification URL before opening a browser', async () => {
  let opened = false;
  await assert.rejects(
    install.runLogin([], {
      fetch: async () => ({
        ok: true,
        json: async () => ({
          device_code: 'dc',
          verification_uri_complete: 'file:///C:/Windows/System32/calc.exe',
          expires_in: 600,
        }),
      }),
      openBrowser: () => { opened = true; },
      sleep: async () => {},
      log: () => {},
    }),
    /unsafe verification URL/,
  );
  assert.equal(opened, false);
});

test('runLogin rejects a multiline managed token without modifying the key file', async () => {
  const o = setup();
  const responses = [
    { ok: true, json: async () => ({ device_code: 'dc', verification_uri_complete: 'https://x/activate', interval: 1, expires_in: 600 }) },
    { ok: true, json: async () => ({ access_token: 'valid-token\nFAL_KEY=injected' }) },
  ];
  let call = 0;
  await assert.rejects(
    install.runLogin([], {
      fetch: async () => responses[call++],
      openBrowser: () => {},
      sleep: async () => {},
      log: () => {},
    }),
    /invalid credential/,
  );
  const file = path.join(o.home, '.supercmo', '.env');
  if (fs.existsSync(file)) assert.ok(!fs.readFileSync(file, 'utf8').includes('injected'));
});

function stalledFetch(_url, options) {
  return new Promise((_resolve, reject) => {
    options.signal.addEventListener('abort', () => {
      const error = new Error('aborted');
      error.name = 'AbortError';
      reject(error);
    }, { once: true });
  });
}

test('runLogin: a stalled start request aborts at the per-request deadline', async () => {
  await assert.rejects(
    install.runLogin([], {
      fetch: stalledFetch,
      openBrowser: () => {},
      sleep: async () => {},
      log: () => {},
      requestTimeoutMs: 5,
    }),
    /could not start login \(request timed out\)/,
  );
});

test('runLogin: stalled token polls cannot outlive the device-code expiry', async () => {
  let calls = 0;
  const fetch = async (url, options) => {
    calls += 1;
    if (calls === 1) {
      return {
        ok: true,
        json: async () => ({
          device_code: 'dc',
          verification_uri_complete: 'https://x/activate',
          interval: 1,
          expires_in: 0.02,
        }),
      };
    }
    return stalledFetch(url, options);
  };
  await assert.rejects(
    install.runLogin([], {
      fetch,
      openBrowser: () => {},
      sleep: async () => {},
      log: () => {},
      requestTimeoutMs: 5,
    }),
    /login timed out/,
  );
  assert.ok(calls >= 2, 'at least one token poll was attempted');
});
