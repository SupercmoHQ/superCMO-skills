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

const installer = path.resolve(__dirname, '..', 'install.js');

function runInstaller(...args) {
  return require('child_process').spawnSync(process.execPath, [installer, ...args], {
    encoding: 'utf8',
  });
}

// Fresh temp HOME with a known key set: FAL_KEY present, the others absent.
function setup() {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'supercmo-home-'));
  process.env.HOME = home;
  process.env.FAL_KEY = 'test-fal';
  for (const k of ['OPENAI_API_KEY', 'GEMINI_API_KEY', 'ELEVENLABS_API_KEY', 'FIRECRAWL_API_KEY']) delete process.env[k];
  const serverPy = config.installRuntime();
  return { home, serverPy };
}
const tmpProj = () => fs.mkdtempSync(path.join(os.tmpdir(), 'supercmo-proj-'));
const optsFile = (o, extra = {}) => ({ serverPy: o.serverPy, command: 'python3', argsPrefix: [], ...extra });
const read = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));
const addArgs = (o) => ({ name: 'supercmo', command: 'python3', args: [o.serverPy] });

test('installer help flags print usage and exit successfully', () => {
  for (const flag of ['--help', '-h']) {
    const result = runInstaller(flag);
    assert.equal(result.status, 0, `${flag} exits successfully`);
    assert.match(result.stdout, /SuperCMO installer/, `${flag} prints usage`);
    assert.equal(result.stderr, '', `${flag} does not report an error`);
  }
});

test('runtime is copied to a stable dir with server + scripts', () => {
  const o = setup();
  assert.ok(fs.existsSync(o.serverPy), 'server.py exists');
  assert.ok(fs.existsSync(path.join(o.home, '.supercmo', 'runtime', 'scripts', 'supercmo_skills')), 'scripts bundled');
  assert.ok(o.serverPy.startsWith(path.join(o.home, '.supercmo', 'runtime')), 'points at stable dir');
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
  assert.deepEqual(args, ['mcp', 'add', 'supercmo', '--', 'python3', o.serverPy]);
  assert.ok(!args.includes('--env'), 'no --env: Codex forwards refs literally, so we never write them');
  assert.ok(!JSON.stringify(args).includes('test-fal'), 'no literal secret written');
  assert.deepEqual(missing, []);
  assert.deepEqual(cli.HOSTS.codex.remove('supercmo'), ['mcp', 'remove', 'supercmo']);
});

test('claude: builds `claude mcp add -s user <name> -- <cmd>` (user scope, NO env block)', () => {
  const o = setup();
  const { args } = cli.HOSTS.claude.add(addArgs(o));
  assert.deepEqual(args, ['mcp', 'add', '-s', 'user', 'supercmo', '--', 'python3', o.serverPy]);
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
  assert.equal(s.command, 'python3');
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
  assert.deepEqual(s.command, ['python3', o.serverPy]);
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
