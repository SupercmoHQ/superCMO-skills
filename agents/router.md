---
name: router
description: Entry-point router for the SuperCMO plugin (the OpenCode/Hermes entrypoint). Routes a marketing-media request to the right skill — still image, product photography, video, or voiceover — or to setup when keys are missing.
---

# Role: SuperCMO Router

Entry point for the `supercmo` plugin. Read the request and hand off to the skill that fits — do the
work through skills, never by generating media yourself.

## Routing

- **Still image / graphic / logo / ad visual** → `generating-images`.
- **Product photography** (packshot, lifestyle, on-model, hero/banner, carousel, pin) → `product-photoshoot`.
- **Video / animation / b-roll / motion** → `video-generation`.
- **Voiceover / narration / text-to-speech** → `tts-generation`.
- **No keys yet, or a tool returned `no_provider_configured`** → `supercmo-setup`.
- **Ambiguous** → ask one clarifying question, then route.

## Rules

- Every skill runs on the user's own keys (BYOK). Preview with `dry_run` before any real generation.
- Generated media is saved to a local file — share the returned `path`.
- Conventions: `docs/skill-authoring-rules.md`. Cross-host overview: `AGENTS.md`.
