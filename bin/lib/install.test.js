'use strict';
// Regression tests for the multi-host installer. Run: `npm test` (node --test).
// Each test runs against a throwaway HOME + temp dirs; no real host config is touched.
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const config = require('./config');
const json = require('./jsonhosts');
const codex = require('./codex');
const components = require('./components');

// Fresh temp HOME with a known key set: FAL_KEY present, the others absent.
function setup() {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'supercmo-home-'));
  process.env.HOME = home;
  process.env.FAL_KEY = 'test-fal';
  for (const k of ['OPENAI_API_KEY', 'GEMINI_API_KEY', 'ELEVENLABS_API_KEY', 'XAI_API_KEY', 'FIRECRAWL_API_KEY']) delete process.env[k];
  const serverPy = config.installRuntime();
  return { home, serverPy };
}
const tmpProj = () => fs.mkdtempSync(path.join(os.tmpdir(), 'supercmo-proj-'));
const opts = (o, extra = {}) => ({ serverPy: o.serverPy, command: 'python3', argsPrefix: [], ...extra });
const read = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));

test('runtime is copied to a stable dir with server + scripts', () => {
  const o = setup();
  assert.ok(fs.existsSync(o.serverPy), 'server.py exists');
  assert.ok(fs.existsSync(path.join(o.home, '.supercmo', 'runtime', 'scripts', 'supercmo_skills')), 'scripts bundled');
  assert.ok(o.serverPy.startsWith(path.join(o.home, '.supercmo', 'runtime')), 'points at stable dir');
});

test('cursor: mcpServers literal env writes only present keys, reports missing', () => {
  const o = setup();
  const r = json.installCursor(opts(o));
  const s = read(r.file).mcpServers.supercmo;
  assert.equal(s.command, 'python3');
  assert.deepEqual(s.env, { FAL_KEY: 'test-fal' });
  assert.deepEqual(r.missing.sort(), ['ELEVENLABS_API_KEY', 'FIRECRAWL_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY', 'XAI_API_KEY']);
});

test('idempotent re-run leaves a single entry', () => {
  const o = setup();
  json.installCursor(opts(o));
  const r = json.installCursor(opts(o));
  assert.equal(Object.keys(read(r.file).mcpServers).length, 1);
});

test('--force guard: a differing existing entry throws without force, succeeds with it', () => {
  const o = setup();
  const r = json.installCursor(opts(o));
  const cfg = read(r.file);
  cfg.mcpServers.supercmo.args = ['/tampered'];
  fs.writeFileSync(r.file, JSON.stringify(cfg));
  assert.throws(() => json.installCursor(opts(o)), /already exists/);
  assert.doesNotThrow(() => json.installCursor(opts(o, { force: true })));
});

test('JSONC (comments + trailing comma) is tolerated and other servers preserved', () => {
  const o = setup();
  const file = path.join(o.home, '.cursor', 'mcp.json');
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, '{\n  // my server\n  "mcpServers": { "other": {"command":"x","args":[]}, }\n}');
  json.installCursor(opts(o));
  const cfg = read(file);
  assert.ok(cfg.mcpServers.other, 'user server kept');
  assert.ok(cfg.mcpServers.supercmo, 'our server added');
});

test('vscode: servers + inputs, no literal secret', () => {
  const o = setup();
  const r = json.installVscode(opts(o, { projectDir: tmpProj() }));
  const cfg = read(r.file);
  assert.equal(cfg.servers.supercmo.env.FAL_KEY, '${input:fal-key}');
  assert.ok(cfg.inputs.some((i) => i.id === 'fal-key' && i.password === true));
});

test('codex: toml block + literal env, preserves other tables', () => {
  const o = setup();
  const file = path.join(o.home, '.codex', 'config.toml');
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, 'model = "x"\n\n[other]\nk = "v"\n');
  codex.installCodex(opts(o));
  const t = fs.readFileSync(file, 'utf8');
  assert.match(t, /\[mcp_servers\.supercmo\]/);
  assert.match(t, /\[mcp_servers\.supercmo\.env\]/);
  assert.match(t, /FAL_KEY = "test-fal"/);
  assert.match(t, /\[other\]/);
});

test('gemini uses $VAR, claude uses ${VAR:-} expansion', () => {
  const o = setup();
  const g = read(json.installGemini(opts(o)).file).mcpServers.supercmo;
  assert.equal(g.env.FAL_KEY, '$FAL_KEY');
  const c = read(json.installClaude(opts(o, { projectDir: tmpProj() })).file).mcpServers.supercmo;
  assert.equal(c.env.FAL_KEY, '${FAL_KEY:-}');
});

test('claude without --project-dir throws plugin guidance', () => {
  const o = setup();
  assert.throws(() => json.installClaude(opts(o)), /plugin/);
});

test('opencode: mcp key, command array, {env:} expansion', () => {
  const o = setup();
  const s = read(json.installOpenCode(opts(o)).file).mcp.supercmo;
  assert.equal(s.type, 'local');
  assert.deepEqual(s.command, ['python3', o.serverPy]);
  assert.equal(s.environment.FAL_KEY, '{env:FAL_KEY}');
});

test('components: cursor rules pruned on re-place, user rule kept', () => {
  setup();
  const rules = fs.mkdtempSync(path.join(os.tmpdir(), 'rules-'));
  fs.writeFileSync(path.join(rules, 'supercmo-old.mdc'), '');
  fs.writeFileSync(path.join(rules, 'mine.mdc'), '');
  const n = components.placeCursorRules(rules);
  assert.ok(n >= 6, 'rules written');
  assert.ok(!fs.existsSync(path.join(rules, 'supercmo-old.mdc')), 'stale supercmo rule pruned');
  assert.ok(fs.existsSync(path.join(rules, 'mine.mdc')), 'user rule kept');
});

test('uninstall removes our entry, preserves the user server', () => {
  const o = setup();
  const r = json.installCursor(opts(o));
  const cfg = read(r.file);
  cfg.mcpServers.user = { command: 'x', args: [] };
  fs.writeFileSync(r.file, JSON.stringify(cfg));
  const u = json.uninstallCursor({});
  assert.equal(u.removed, true);
  const after = read(r.file);
  assert.ok(!after.mcpServers.supercmo, 'ours removed');
  assert.ok(after.mcpServers.user, 'user server kept');
});

test('uninstall claude removes skills but keeps the user skill', () => {
  const o = setup();
  const proj = tmpProj();
  json.installClaude(opts(o, { projectDir: proj }));
  components.placeSkills(path.join(proj, '.claude', 'skills'));
  fs.mkdirSync(path.join(proj, '.claude', 'skills', 'user-skill'), { recursive: true });
  fs.writeFileSync(path.join(proj, '.claude', 'skills', 'user-skill', 'keep.md'), '');
  json.uninstallClaude({ projectDir: proj });
  assert.ok(!fs.existsSync(path.join(proj, '.claude', 'skills', 'image-generation')), 'our skill removed');
  assert.ok(fs.existsSync(path.join(proj, '.claude', 'skills', 'user-skill', 'keep.md')), 'user skill kept');
});
