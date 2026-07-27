---
name: tts-generation
description: Generates spoken-audio narration or voiceover from text (read a script aloud, voice a video, narrate a post). Use when the user asks for text-to-speech, a voiceover, or to read text aloud. Analyzes intent, routes to the best model and voice, and structures the request to match.
license: Apache-2.0
metadata:
  version: "0.1.0"
  category: creative
---

# Text to Speech

Turn text into spoken audio via the `text_to_speech` tool. Two decisions drive quality: **which
model** (always) and **which voice** (from the model's catalog).

## Quick start

1. Read the brief and decide what kind of voiceover it is (Step 1).
2. Pick the model for that kind (Step 2).
3. Gather the inputs — the text, and a voice (Step 3).
4. Prepare the text the way the model reads best (Step 4).
5. Call `text_to_speech` with the args (Step 5).
6. Share the result (Step 6).

## Workflow

### Step 1: Decide what kind of voiceover it is

Read the brief and pick the one that fits best — this choice decides the model in Step 2:

- **Expressive, multilingual, or a distinctive voice** — character work, a non-English script, an
  emotive read → expressive multilingual.
- **Clean, natural narration, fast** — a product walkthrough, an explainer, a straight read →
  natural narration.
- **A controllable, styled delivery** — the user wants to direct the tone, pacing, or style of the
  read → controllable style.

### Step 2: Pick the model

Match the kind of voiceover to a model:

| Kind of voiceover                          | Model            |
| ------------------------------------------ | ---------------- |
| Expressive, multilingual, distinctive      | `elevenlabs-v3`  |
| Natural, low-latency narration             | `openai-tts`     |
| Expressive, controllable style             | `gemini-tts`     |

`elevenlabs-v3` is the default — top multilingual, expressive voices. Use `openai-tts` for natural
low-latency narration, or `gemini-tts` when the user wants to control the delivery style. If nothing
clearly fits, leave `model` unset (the tool's default) or call `list_voice_models` and pick by
`strengths`.

### Step 3: Get the inputs

Don't generate with a load-bearing detail missing — but ask only for what the brief actually needs:

- **No text supplied** → "What exact text should I read aloud?"
- **No voice named** → call `list_voice_models` and pick a fitting `voice` from the rows (each lists
  the available voices), or ask if the user has a preference. Omit `voice` to use the model's default.
- **Tone matters** → confirm the intended delivery (calm, upbeat, authoritative) so you can pick the
  voice and, on `gemini-tts`, style the read.

Otherwise, proceed.

### Step 4: Prepare the text

Pass clean, readable text. Spell out anything that should be read a particular way (numbers,
acronyms, dates). Use punctuation to shape pacing — commas and periods become natural pauses. Keep
sentences at a speakable length.

### Step 5: Generate

Call `text_to_speech`:

- `text` (required) — the script to read aloud.
- `model` from Step 2 (or omit for the default).
- `voice` — a voice name from `list_voice_models` (or omit for the model's default).
- `speed` — playback rate; leave unset for normal pace.

### Step 6: Return

Share the resulting audio with the user — the result is an audio URL or base64.

## Edge cases

- **Fits no kind** → leave `model` unset (tool default) or call `list_voice_models`.
- **Safety rejection** → remove the sensitive wording and retry once.
- **Generic failure** → retry once as-is, then report the error.
- **`error: "no_provider_configured"`** → relay the tool's `hint` (the user must set their key).

## Reference

- `references/voices.md` — picking a voice per model; use `list_voice_models` for the live catalog.
