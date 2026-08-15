<div align="center">

<img src="assets/logo.png" alt="SuperCMO" width="120" />

# SuperCMO Skills

</div>

### Enable AI agents to create marketing videos and images

<!-- mcp-name: io.github.SupercmoHQ/supercmo -->
Open-source skills that empower any AI agent (Claude, Cursor, Codex, Hermes, etc.) to generate end-to-end marketing campaigns - UGC videos, ad videos, product photography and more.

Just provide a product photo and a brief. The agent extracts the product details, selects the optimal AI image and video models, casts AI actors, and edits the generated content into finished, campaign-ready assets. It can produce videos of any length while maintaining perfect actor and product consistency.

*The open-source alternative to closed AI marketing agents.*

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/SupercmoHQ/superCMO-skills/validate.yml?branch=main&label=CI)](https://github.com/SupercmoHQ/superCMO-skills/actions)

<details open>
<summary><strong>UGC video</strong></summary>

> `create an ugc video for this tshirt. it should be a get ready with me reel. snappy. very genz. [product-photo]`

<div align="center">
  <video src="https://github.com/user-attachments/assets/d9daa15f-c534-497e-8e35-6e497b7eaa05" width="300" controls></video>
</div>

</details>

<details open>
<summary><strong>Cartoon video ad</strong></summary>

> `create a cartoon video ad in stylized 3D style, promoting my tumbler. make it fun and entertaining. [product-photo]`

<div align="center">
  <video src="https://github.com/user-attachments/assets/45bff56d-ce38-43de-b555-63bb939ebfbb" width="300" controls></video>
</div>

</details>

<details open>
<summary><strong>Product ad video</strong></summary>

> `make me an ad video for this energy drink [product-photo]`

<div align="center">
  <video src="https://github.com/user-attachments/assets/ab64d169-743f-444a-a7a4-ccae571b0ea4" width="300" controls></video>
</div>

</details>

---

## Contents

- [See how it works](#see-how-it-works)
- [Quick start](#quick-start)
- [Start from a product photo](#start-from-a-product-photo)
- [Why SuperCMO Skills?](#why-supercmo-skills)
- [How the skills work together](#how-the-skills-work-together)
- [The Marketing Production Pipeline](#the-marketing-production-pipeline)
- [Install](#install)
- [Set up a key](#set-up-a-key)
- [Security & trust](#security--trust)
- [Telemetry](#telemetry)
- [Community](#community)
- [Contributing](#contributing)
- [License](#license)

---

## See how it works

A full production studio inside Claude. You provide a product photo and a high level (or detailed) brief.

The AI agent then plans the video → writes the script → generates the AI actor → creates storyboards → generates the video clips → stitches them together, and delivers the final video.

The best part? You stay in charge all along.

<div align="center">
  <video src="https://github.com/user-attachments/assets/08a2f818-b56d-488a-8029-57ad6ad3cd0a" width="680" controls></video>
</div>

---

## Quick start

**Paste this to your coding agent** (Claude Code, Cursor, Codex, …):

```
Run `npx --yes github:SupercmoHQ/superCMO-skills --all`. Tell me whether it succeeded, then follow the next steps it prints to set up a key.
```

Prefer to run it yourself:

```bash
npx --yes github:SupercmoHQ/superCMO-skills --all   # every detected host
```

Prefer a preview before spending? Every generation supports `dry_run` — the exact request and cost, no API call.

---

## Start from a product photo

Starting from your product is faster than describing a video from a blank prompt.

Hand SuperCMO a **single product photo** and it builds a UGC ad around it - a creator on camera reviewing, unboxing, trying on, or demoing your product:

1. Upload a product photo and give a short brief
2. It analyzes the product, picks the format, casts the creator, and writes the script. Then shows you the concept and waits for your approval before spending a cent
3. Once approved, it generates the storyboards, renders each clip, stitches them together, and hands back the finished video

```text
"Make a 30-second unboxing UGC ad for this product." [attach product photo]
```

What you get back is not a random clip. You get:

- **You stay in charge** - approve the creator, the concept, and the script before anything renders, and change any part along the way.
- **Consistency built in** - maintains the same actor and product across every clip, through the storyboard and anchor references
- **A finished, scroll-stopping video** - delivered at the length you asked for, ready to post

Works inside **Claude Code, Cursor, Codex, Hermes** - any agent that supports the Agent Skills spec.

---

### Why SuperCMO Skills?

| | |
| --- | --- |
| **You direct, it produces** | SuperCMO doesn't decide what your campaign should say — you do. It handles the production work underneath: scripting to your brief, casting, shooting, editing. It checks in at every step, so you can redirect it mid-run instead of accepting whatever comes out the end. |
| **No tool hopping** | Making one video ad today means jumping between tools: script in one, images in another, voice in a third, video in a fourth, then stitching it in an editor. SuperCMO does it all from a single brief, in one place. |
| **The right model, picked for you** | Every AI image/video model works differently and needs different prompting. Knowing that Veo wants one kind of prompt and Kling another — and which to reach for in the first place — is most of the work. SuperCMO's skills already know. You write the brief; it handles the rest. |
| **Consistency across every shot** | One good clip is easy. Ten clips where the product and the face stay identical is the part that breaks. SuperCMO storyboards before it renders and locks a reference into every generation, so continuity holds across the whole cut. |
| **Editing included** | It doesn't just hand back a raw 10-second clip. It generates the media, splits long clips, trims footage, adds voiceover, and stitches everything into a finished asset. |
| **Pay per use, no subscription** | Most marketing tools charge monthly whether you use them or not. SuperCMO doesn't — bring your own vendor keys (free), or generate on SuperCMO's keys and pay per use. No lock-in. |
| **Runs where you already work** | Inside Claude Code, Cursor, OpenAI Codex, Hermes, Openclaw, or any agent that supports the Agent Skills spec. Your keys and files stay on your machine. |

---

## How the skills work together

You act as the creative director, and your agent uses SuperCMO skills to orchestrate the entire production pipeline.

Here is an example of how the skills chain together behind the scenes to execute a complex brief like: *"Make a 1-minute video ad for this product [URL] with a voiceover."*

```text
[Brief] "Make a 1-minute video ad for this product [URL] with a voiceover."
   │
   ├── 1. Analyze ──> Scrapes the URL to understand the product and fetch product images.
   │
   ├── 2. Plan    ──> Breaks the 60s brief into four 15-second shots.
   │                  Writes the script and shot list.
   │
   ├── 3. Image  ──> Generates master reference images of the product 
   │                 using the best image models.
   │
   ├── 4. Video  ──> Generates the 4 video clips. Locks the anchor reference 
   │                  into every shot so the product doesn't shape-shift.
   │
   ├── 5. Audio   ──> Adds a voiceover, budgeting the script to match the 
   │                  exact length of the video.
   │
   └── 6. Stitch  ──> Stitches the finished clips together to create one 
                      continuous 1-minute video file.

```

## The Marketing Production Pipeline

SuperCMO installs a full creative agency into your text-based agent. It doesn't just generate media; it orchestrates the specific steps required to make high-converting ads:

* **Product Analysis** - Scrapes your URLs to extract brand guidelines, materials, and features so the AI models don't hallucinate your product.
* **Ad Copy & Scripting** - Breaks the brief into a shot-by-shot ad script tailored for platforms like Meta, TikTok, or YouTube.
* **Visual Generation** - Produces master reference images and locks them as anchors so your product looks consistent in every video frame.
* **Audio & Voiceover** - Generates natural, high-energy voiceovers paced perfectly to your video duration.
* **Post-Production** - Trims footage, syncs audio, and stitches the final MP4.

These are the discrete skills installed into your agent to run that pipeline:

<!-- SKILLS:START — auto-generated by scripts/sync_skills.py; do not edit by hand -->
| Skill | Description |
|-------|-------------|
| [analyzing-products](skills/analyzing-products/) | Analyzes an e-commerce link or photo to map out your product's exact physical mechanics and extract clean reference images, building a highly accurate creative brief without any manual research or extraction. |
| [generating-ad-videos](skills/generating-ad-videos/) | Produces a polished, cinematic product commercial in your brand's voice — a no-actor product showcase or an actor-led story ad, at any length. It storyboards every clip to hold your real product identical across cuts, writes the voiceover and casts the actor when the ad calls for one, then stitches it into one ready-to-run spot you approve step by step before anything expensive renders. |
| [generating-ai-actors](skills/generating-ai-actors/) | Casts a distinct, demographic-specific AI actor as a reusable identity reference, allowing you to reliably feature the exact same brand face across an entire multi-asset image and video campaign. |
| [generating-audio](skills/generating-audio/) | Converts scripts into audio. Lets you preview voice candidates from top models before generating. It then formats your script's numbers, dates, and URLs so the chosen AI model pronounces them accurately. |
| [generating-cartoon-videos](skills/generating-cartoon-videos/) | Produces a drawn, animated video for your product — cartoon, anime, illustrated or painted, at any length. Your product either stays exactly as photographed or is drawn into the style, and a cast of characters carries the story around it. It settles one art style, writes the story, draws your cast once so every cut is the same cast, then films it clip by clip and lays a voiceover over the top — with your approval before anything expensive renders. |
| [generating-image-ads](skills/generating-image-ads/) | Produces a scroll-stopping image ads for your product — one image, or a set in every placement ratio your feed needs. It keeps your real product and your brand identity perfectly consistent across every frame, and shapes the offer and claims you give it into a well designed ad, following industry best practices. |
| [generating-images](skills/generating-images/) | Routes your brief to the best of 10+ SOTA image models (like Nano Banana, GPT Image), writes detailed prompts as per model specifications and generates multiple variations instantly. |
| [generating-product-photos](skills/generating-product-photos/) | Directs a commercial photoshoot around your product, automatically applying the correct lighting, framing, camera angles and props to deliver studio-quality product shots across 10+ formats. |
| [generating-storyboards](skills/generating-storyboards/) | Draws out your entire video concept clip-by-clip as static images, enforcing strict character and product continuity so you can approve camera angles and visual flow before committing to expensive video renders. |
| [generating-ugc-videos](skills/generating-ugc-videos/) | Produces UGC videos of any length - like review, unboxing, try-on, tutorial and more. It casts the actor, writes the script, and storyboards multiple clips to lock in actor and product consistency. It lets you direct every step to get a cohesive, ready-to-run ad in minutes. |
| [generating-videos](skills/generating-videos/) | Routes your brief to the best of 10+ SOTA video models (like Veo, Seedance), writes detailed prompts as per model specifications and generates multi-clip stories that hold continuity across cuts, stitched into one file. |
| [writing-ad-copy](skills/writing-ad-copy/) | Writes the text that runs alongside your ad — headline, primary text, description and call to action — tuned to the fields and best practices of each platform it runs on: Facebook and Instagram, Google Search, LinkedIn, TikTok, X and Reddit. It works one angle several ways and sizes each field so nothing gets cut off in the feed. |
| [writing-video-prompts](skills/writing-video-prompts/) | Translates your scenes into the highly specific, detailed instructions that different video models require. It times the camera motion and steers around known AI rendering limits to match your exact visual brief. |
| [writing-video-scripts](skills/writing-video-scripts/) | Drafts spoken scripts built around proven opening hooks designed specifically to stop the scroll. It sizes the text to fit your exact runtime and paces words across natural breath points for human delivery. |
<!-- SKILLS:END -->

## Install

Every host loads the **same skills** + the **same local MCP server** - only the wiring differs.
**Prerequisite:** [`uv`](https://docs.astral.sh/uv/getting-started/installation/) on PATH — the MCP
server runs via `uvx`, which provisions Python and the server for you (nothing to `pip install`). The
root `pyproject.toml` / `package.json` are packaging scaffolding — you don't build anything by hand to
run or contribute to the skills.

**npx installer** - registers the MCP server via each host's own mechanism (`codex`/`claude mcp add` where a CLI exists; a `.cursor/mcp.json` for Cursor) and places the skills. One command does every detected host:

```bash
npx --yes github:SupercmoHQ/superCMO-skills --claude               # Claude Code
npx --yes github:SupercmoHQ/superCMO-skills --cursor --project-dir .  # Cursor (per project)
npx --yes github:SupercmoHQ/superCMO-skills --codex                # Codex
npx --yes github:SupercmoHQ/superCMO-skills --all                  # every detected host
```

If the SuperCMO tools don't show up in your agent afterward, restart it once.

**Claude Code plugin** - an alternative to `npx … --claude` (use one, not both): the whole repo installs as one plugin, managed by Claude Code:

```
/plugin marketplace add SupercmoHQ/superCMO-skills
/plugin install supercmo@superCMO-skills
```

**Codex plugin** - an alternative to `npx … --codex` (use one, not both): installs the skills + MCP server as one plugin, managed by Codex:

```bash
codex plugin marketplace add SupercmoHQ/superCMO-skills
codex plugin add supercmo@superCMO-skills
```

**Claude Cowork / Claude desktop** - download `supercmo-plugin.zip` from the
[latest release](https://github.com/SupercmoHQ/superCMO-skills/releases), then
**Settings → Plugins → Upload local plugin**.

**Found us on [skills.sh](https://skills.sh)?** `npx skills add SupercmoHQ/superCMO-skills` copies the
skills but **not the MCP server** they call — so `image_generate`/`video_generate` won't exist yet.
Install the server, then reload your agent:

```bash
npx --yes github:SupercmoHQ/superCMO-skills --all   # or --cursor --project-dir . · --codex · --all
```

## Set up a key

Generation needs a key. **Two ways — pick one:**

### Option A · Managed — one command

Generate on **SuperCMO's keys, pay per use** — no vendor signups, nothing to paste.

```bash
npx --yes github:SupercmoHQ/superCMO-skills login
```

Opens SuperCMO in your browser to **sign in and authorize this device**; the key is written to
`~/.supercmo/.env` automatically. Buy credits in the web app when you're ready.

### Option B · Bring your own keys — free

Bring your own vendor keys — requests go **directly to the model vendor; nothing routes through SuperCMO**.

**One file, every host.** The installer creates `~/.supercmo/.env`; the MCP server loads your keys from
there on any host (Claude Code, Cursor, Codex, …). Open it and add a key:

```bash
# ~/.supercmo/.env
WAVESPEED_API_KEY=your-key # image + video (start here) — https://wavespeed.ai
FAL_KEY=                   # image + video (alternative) — https://fal.ai
ELEVENLABS_API_KEY=        # voiceover (optional)        — https://elevenlabs.io
GEMINI_API_KEY=            # image/video analysis (opt.) — https://aistudio.google.com
FIRECRAWL_API_KEY=         # url extraction (optional)   — https://firecrawl.dev
```

* **One key to start:** `WAVESPEED_API_KEY` covers image + video and is what we recommend — users
  report better reliability there. `FAL_KEY` is fully supported too and serves the same models, so
  use it if that's the account you already have. With both set, WaveSpeed is used;
  `SUPERCMO_MEDIA_PROVIDER=fal` picks the other. The rest are optional — add one when you want that
  capability (voiceover, analysis, extraction).
* **Prefer environment variables?** Exporting the key (or putting it in your host's MCP config `env`
  block) also works and **takes precedence** — `~/.supercmo/.env` is just the reliable default that also
  works for GUI-launched hosts that don't inherit your shell.
* **Check what's set:** ask your agent to run the `setup_status` tool (host-agnostic, no path needed).

## Security & trust

These skills run inside your agent. Exactly what happens:

* **Open source & inspectable.** Every skill, script, and the MCP server lives in this repo under
  Apache-2.0 — read, diff, or pin before you run it.
* **Your keys stay local (BYOK).** With your own vendor keys, they live in `~/.supercmo/.env` (or your
  host's MCP config `env` / your shell); the server reads them from its process environment and requests
  go **directly to the vendor — nothing routes through SuperCMO**. With the **managed** key, requests go
  to SuperCMO's proxy (billed to your credits) — you never hand us a vendor key.
* **The MCP server is local + minimal.** A stdlib-only Python package (`supercmo-skills` on PyPI, source
  in `scripts/supercmo_skills/mcp/`), fetched and run on demand via `uvx supercmo-skills@<version>` — it
  runs on your machine, launched by your host, and starts only when your host enables the plugin.
* **Dry-run everything.** Generation tools support `dry_run` - a free preview of the exact request
  (keys masked), no API call.

Found something off? [Open an issue](https://github.com/SupercmoHQ/superCMO-skills/issues).

## Telemetry

SuperCMO sends **anonymous, opt-out** usage counts from the MCP server so we can see which tools get
used and prioritize. Full details in [`TELEMETRY.md`](TELEMETRY.md).

* **What we send:** the tool name, whether it succeeded, how long it took, versions (OS / Python /
  SuperCMO), and a random install id. Nothing else.
* **What we NEVER send:** your prompts, tool arguments, generated media, file paths, keys, hostname,
  username, or IP address.
* **Turn it off** (any one): `SUPERCMO_TELEMETRY=false`, `DO_NOT_TRACK=1`, or `DISABLE_TELEMETRY=1`.
  It also honors Claude Code's `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`.
* **See what would be sent:** run with `SUPERCMO_TELEMETRY=log` - prints each payload instead of
  sending.
* Events go to our own endpoint (`api.getsupercmo.ai`), never a third-party analytics host. The
  random install id is **never** linked to any account.

## Community

Questions, ideas, or something you built? [Open an issue or discussion](https://github.com/SupercmoHQ/superCMO-skills/issues).

## Contributing

New skills and improvements welcome - see [`CONTRIBUTING.md`](CONTRIBUTING.md). In short:

1. Create `skills/<your-skill>/` (folder name = the `name` in frontmatter), using
   `skills/generating-images/` as the reference layout.
2. Keep `SKILL.md` short; push detail into `references/`, deterministic work into `scripts/`
   (stdlib-only where possible, BYO-keys from env, `--dry-run` on anything that mutates).
3. Validate - CI runs the same on every PR:

```bash
python3 scripts/quick_validate.py       # structural + strict-YAML frontmatter (blocking)
python3 scripts/listing_gate.py         # scripts compile + --dry-run gates (blocking)
python3 scripts/check_shared_client.py  # no raw vendor HTTP - the brokering seam (blocking)
python3 scripts/check_catalog_sync.py   # provider-key catalog single-sourced (blocking)
```

## License

Apache-2.0 - see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

The skill files, scripts, and MCP server in this repository are Apache-2.0. The hosted SuperCMO
product (`getsupercmo.ai`) is a separate service governed by its own terms.

<div align="center">

If SuperCMO saved you time, a ⭐ helps others find it.

Built by [SuperCMO](https://getsupercmo.ai) · [Report an issue](https://github.com/SupercmoHQ/superCMO-skills/issues)

</div>
