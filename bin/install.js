#!/usr/bin/env node
"use strict";
// SuperCMO multi-host installer. Registers the media MCP server and places the skills onto each host.
// MCP registration is DELEGATED to each host's first-party mechanism — we never hand-edit a host config:
//   - CLI hosts (Codex, Claude Code, VS Code): shell out to `<host> mcp add` (lib/clihosts.js).
//   - File hosts with no CLI (Cursor, Windsurf, Cline, OpenCode): safe JSON parse→merge→write (lib/jsonhosts.js).
// This is the ecosystem standard (Smithery CLI, vendor docs, Microsoft Playwright MCP) and makes config
// corruption structurally impossible. Skills are placed by copying files into each host's skills location.
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const {
  home,
  installRuntime,
  ensureKeyFile,
  SERVER_NAME,
} = require("./lib/config");
const cli = require("./lib/clihosts");
const json = require("./lib/jsonhosts");
const components = require("./lib/components");

// Find a working Python 3 interpreter and how to invoke it (command + any prefix args).
function detectPython() {
  const candidates =
    process.platform === "win32"
      ? [
          ["py", ["-3"]],
          ["python", []],
          ["python3", []],
        ]
      : [
          ["python3", []],
          ["python", []],
        ];
  for (const [command, argsPrefix] of candidates) {
    try {
      const r = spawnSync(command, [...argsPrefix, "--version"], {
        stdio: "ignore",
      });
      if (r.status === 0) return { command, argsPrefix };
    } catch (_) {
      /* not found, try next */
    }
  }
  throw new Error(
    `no Python 3 found (tried ${candidates.map((c) => c[0]).join(", ")}). Install Python 3 and re-run.`,
  );
}

// Skill placement (file copy into each host's skills location; MCP tools come from the server).
const codexPlace = ({ projectDir }) => {
  const root = projectDir
    ? path.join(projectDir, ".agents", "skills")
    : path.join(home(), ".agents", "skills");
  return [`skills → ${root} (${components.placeSkills(root)})`];
};
const cursorPlace = ({ projectDir }) =>
  projectDir
    ? [
        `skills → .cursor/rules (${components.placeCursorRules(path.join(projectDir, ".cursor", "rules"))} rules)`,
      ]
    : ["skills: pass --project-dir to render Cursor rules"];
// Claude Code: project .claude with --project-dir, else user-global ~/.claude — so `--all` sets up
// Claude Code fully (skills + MCP) without the plugin. The plugin is an alternative; use one or the other.
const claudeSkillsDir = (projectDir) =>
  projectDir
    ? path.join(projectDir, ".claude", "skills")
    : path.join(home(), ".claude", "skills");
const claudeCmdDir = (projectDir) =>
  projectDir
    ? path.join(projectDir, ".claude", "commands")
    : path.join(home(), ".claude", "commands");
const claudePlace = ({ projectDir }) => {
  const label = projectDir ? ".claude" : "~/.claude";
  return [
    `skills → ${label}/skills (${components.placeSkills(claudeSkillsDir(projectDir))})`,
    `command → ${label}/commands (${components.placeMdDir(components.COMMANDS_SRC, claudeCmdDir(projectDir))})`,
  ];
};
// Remove the skills we placed (the CLI's own `mcp remove` only handles the server registration).
const codexUnplace = ({ projectDir }) => {
  const root = projectDir
    ? path.join(projectDir, ".agents", "skills")
    : path.join(home(), ".agents", "skills");
  const n = components.removeSkills(root);
  return n ? [`removed ${n} skills`] : [];
};
const claudeUnplace = ({ projectDir }) => {
  const s = components.removeSkills(claudeSkillsDir(projectDir));
  const c = components.removeMdFiles(
    components.COMMANDS_SRC,
    claudeCmdDir(projectDir),
  );
  return s || c ? [`removed skills:${s} command:${c}`] : [];
};

const HOSTS = {
  // --- CLI-delegation hosts: `<host> mcp add` owns the config ---
  codex: {
    label: "Codex",
    kind: "cli",
    key: "codex",
    detect: () => fs.existsSync(path.join(home(), ".codex")),
    place: codexPlace,
    unplace: codexUnplace,
  },
  vscode: { label: "VS Code", kind: "cli", key: "vscode", detect: () => false }, // explicit --vscode only
  claude: {
    label: "Claude Code",
    kind: "cli",
    key: "claude",
    detect: () => fs.existsSync(path.join(home(), ".claude")),
    place: claudePlace,
    unplace: claudeUnplace,
  }, // or the plugin (alternative)

  // --- File hosts (no first-party CLI): safe JSON merge ---
  cursor: {
    label: "Cursor",
    kind: "file",
    run: json.installCursor,
    uninstall: json.uninstallCursor,
    detect: () => fs.existsSync(path.join(home(), ".cursor")),
    place: cursorPlace,
  },
  windsurf: {
    label: "Windsurf",
    kind: "file",
    run: json.installWindsurf,
    uninstall: json.uninstallWindsurf,
    detect: () => fs.existsSync(path.join(home(), ".codeium", "windsurf")),
  },
  cline: {
    label: "Cline",
    kind: "file",
    run: json.installCline,
    uninstall: json.uninstallCline,
    detect: () =>
      fs.existsSync(path.dirname(path.dirname(json.clineSettingsFile()))),
  },
  opencode: {
    label: "OpenCode",
    kind: "file",
    run: json.installOpenCode,
    uninstall: json.uninstallOpenCode,
    detect: () => fs.existsSync(path.join(home(), ".config", "opencode")),
  },
};

function parseArgs(argv) {
  const opts = {
    hosts: [],
    all: false,
    projectDir: null,
    force: false,
    uninstall: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--all") opts.all = true;
    else if (a === "--force") opts.force = true;
    else if (a === "--uninstall") opts.uninstall = true;
    else if (a === "--project-dir")
      opts.projectDir = path.resolve(argv[++i] || ".");
    else if (a.startsWith("--") && HOSTS[a.slice(2)])
      opts.hosts.push(a.slice(2));
    else throw new Error(`Unknown option: ${a}`);
  }
  return opts;
}

function usage() {
  console.log(`SuperCMO installer

  supercmo-install --codex                       # Codex (codex mcp add)
  supercmo-install --claude --project-dir <dir>  # Claude Code standalone; else use the plugin
  supercmo-install --vscode                      # VS Code (code --add-mcp)
  supercmo-install --cursor [--project-dir <dir>]  # Cursor (.cursor/mcp.json)
  supercmo-install --windsurf | --cline | --opencode
  supercmo-install --all                         # every detected host
  [--force] overwrite a differing existing server entry (file hosts)
  --uninstall --<host> [--project-dir <dir>]     # remove what we added (--all for every detected host)`);
}

function runUninstall(hosts, opts) {
  let failures = 0;
  for (const h of hosts) {
    const host = HOSTS[h];
    try {
      if (host.kind === "cli") {
        const r = cli.uninstall(host.key, { name: SERVER_NAME });
        if (r.unsupported)
          console.log(
            `· ${host.label}: uninstall is manual (host has no remove command)`,
          );
        else if (r.cliMissing)
          console.log(
            `· ${host.label}: ${host.key} CLI not found — nothing to remove`,
          );
        else if (r.ok)
          console.log(`✓ ${host.label}: removed via ${host.key} mcp remove`);
        else {
          failures++;
          console.error(`✗ ${host.label}: ${r.error}`);
        }
        for (const n of host.unplace
          ? host.unplace({ projectDir: opts.projectDir })
          : [])
          console.log(`  · ${n}`);
      } else {
        const r = host.uninstall({ projectDir: opts.projectDir });
        console.log(
          `${r.removed ? "✓" : "·"} ${host.label}: ${r.removed ? "removed from" : "nothing to remove in"} ${r.file}`,
        );
        for (const n of r.notes || []) console.log(`  · ${n}`);
      }
    } catch (e) {
      failures++;
      console.error(`✗ ${host.label}: ${e.message}`);
    }
  }
  if (opts.all) {
    const rt = path.join(home(), ".supercmo", "runtime");
    fs.rmSync(rt, { recursive: true, force: true });
    console.log(`· removed runtime ${rt}`);
  }
  return failures;
}

function runInstall(hosts, opts) {
  const py = detectPython();
  const serverPy = installRuntime(); // stable copy at ~/.supercmo/runtime (npx-cache-proof)
  const kf = ensureKeyFile(); // ~/.supercmo/.env — the server loads keys from here on every host
  console.log(`· python: ${[py.command, ...py.argsPrefix].join(" ")}`);
  console.log(`· runtime: ${serverPy}`);
  console.log(
    `· keys:    ${kf.file} ${kf.created ? "(created)" : "(exists — kept your keys)"}`,
  );

  let failures = 0;
  for (const h of hosts) {
    const host = HOSTS[h];
    try {
      if (host.kind === "cli") {
        const r = cli.install(host.key, {
          name: SERVER_NAME,
          command: py.command,
          args: [...py.argsPrefix, serverPy],
        });
        if (r.cliMissing) {
          console.log(
            `· ${host.label}: ${host.key} CLI not found — add it manually:`,
          );
          for (const line of r.snippet().split("\n"))
            console.log(`    ${line}`);
        } else if (r.ok) {
          console.log(`✓ ${host.label}: registered via ${host.key} mcp add`);
        } else {
          failures++;
          console.error(`✗ ${host.label}: ${r.error}`);
        }
      } else {
        const r = host.run({
          projectDir: opts.projectDir,
          force: opts.force,
          serverPy,
          command: py.command,
          argsPrefix: py.argsPrefix,
        });
        console.log(`✓ ${host.label}: wrote ${r.file}`);
        for (const n of r.notes || []) console.log(`  · ${n}`);
      }
      for (const line of host.place
        ? host.place({ projectDir: opts.projectDir })
        : [])
        console.log(`  · ${line}`);
    } catch (e) {
      failures++;
      console.error(`✗ ${host.label}: ${e.message}`);
    }
  }
  console.log("");
  console.log(
    "Last step — add the key(s) for what you want to do, then RESTART your host:",
  );
  console.log("");
  // Each BYOK key → what it unlocks. FAL drives image_generate + video_generate; GEMINI drives
  // image_analysis + video_analysis (used across the product, image and video skills); ELEVENLABS
  // drives audio; FIRECRAWL drives url_extraction. Ordered by how much each one gives you.
  const KEY_GUIDE = [
    ["FAL_KEY", "generate images + video", "https://fal.ai/dashboard/keys"],
    [
      "GEMINI_API_KEY",
      "analyze a photo or video",
      "https://aistudio.google.com/app/apikey",
    ],
    [
      "ELEVENLABS_API_KEY",
      "generate voiceover + narration",
      "https://elevenlabs.io/app/settings/api-keys",
    ],
    [
      "FIRECRAWL_API_KEY",
      "extract data from URLs",
      "https://www.firecrawl.dev/app/api-keys",
    ],
  ];
  for (const [env, cap, url] of KEY_GUIDE)
    console.log(`  ${env.padEnd(19)}  ${cap.padEnd(37)}  ${url}`);
  console.log("");
  console.log(
    "  Start with FAL_KEY (covers image + video); add GEMINI_API_KEY to analyze a photo",
  );
  console.log(
    `  or video and generate from it. Put keys in ${kf.file} or export them`,
  );
  console.log(
    "  in your shell — they load only after a host restart, not in this session.",
  );
  return failures;
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  let hosts = opts.hosts;
  if (opts.all) hosts = Object.keys(HOSTS).filter((h) => HOSTS[h].detect());
  if (!hosts.length) {
    usage();
    process.exit(opts.all ? 0 : 1);
  }
  const failures = opts.uninstall
    ? runUninstall(hosts, opts)
    : runInstall(hosts, opts);
  process.exit(failures ? 1 : 0);
}

main();
