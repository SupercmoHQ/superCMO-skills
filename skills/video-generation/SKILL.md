---
name: video-generation
description: Generates a video clip from a text prompt or an image start-frame (animate a product photo, bring a scene to life). Use when the user asks to generate, create, make a video, or animate an image. Analyzes intent, routes to the best model for the job, and structures the prompt to match.
license: Apache-2.0
metadata:
  version: "0.1.0"
  category: creative
---

# Video Generation

Turn a brief — text, optionally with a start-frame image — into a video clip via the
`video_generate` tool. Two decisions drive quality: **which model** (always) and **what to feed it**
(a start frame turns a still into motion; text-only generates from scratch).

## Quick start

1. Read the brief and decide what kind of video it is (Step 1).
2. Pick the model for that kind and read its prompt guide (Step 2).
3. Gather the inputs the model needs — a start frame is recommended (Step 3).
4. Write the prompt the model's way (Step 4).
5. Call `video_generate` with the args (Step 5).
6. Share the result (Step 6).

## Workflow

### Step 1: Decide what kind of video it is

Read the brief and pick the one that fits best — this choice decides the model in Step 2:

- **A supplied image to animate** — "animate this", "make this product photo move", "bring this
  scene to life", or any brief with a photo to start from → image-to-video.
- **A short clip from a description, no image** — "a drone shot over a coastline", "a coffee cup
  steaming on a desk" → text-to-video.
- **A quick rough draft** — the user wants to sketch an idea fast and iterate, polish later → draft.

### Step 2: Pick the model and read its prompt guide

Match the kind of video to a model, then **read its prompt guide before writing the prompt** — each
model expects a different prompt shape.

| Kind of video                                        | Model          | Prompt guide                       |
| ---------------------------------------------------- | -------------- | ---------------------------------- |
| Image-to-video with native audio (product, scene)    | `veo3.1-fast`  | `references/prompt-veo3.1-fast.md` |
| Text-to-video, default fallback                      | `veo3.1-fast`  | `references/prompt-veo3.1-fast.md` |
| Quick text/image-to-video draft                      | `grok-video`   | `references/prompt-grok-video.md`  |

`veo3.1-fast` is image-to-video with native audio and the default — best for turning a product or
scene image into a short clip. Reach for `grok-video` (xAI) when the user wants a fast draft or names
it. If nothing clearly fits, leave `model` unset (the tool's default) or call `list_video_models` and
pick by `strengths`.

### Step 3: Gather inputs

Don't generate with a load-bearing detail missing — but ask only for what the brief actually needs:

- **Animating a product or scene, but no image supplied** → "Share the start frame — a file or a
  direct image link — so the clip animates your exact product/scene." `veo3.1-fast` is image-to-video,
  so a start frame is recommended.
- **The destination (and so the crop) is unclear** → "Where will this run — square for a feed post,
  portrait for a story/Reel, or landscape for YouTube?"
- **Audio matters** → confirm whether the clip should have sound (`generate_audio`).

Otherwise, proceed.

### Step 4: Write the prompt

Build the prompt as the chosen model's prompt guide specifies. With a start frame, describe the
motion and what changes over the clip (camera move, action, how the subject animates) — the frame
already fixes the look, so the prompt carries the movement.

### Step 5: Generate

Call `video_generate`:

- `prompt` (required); `model` from Step 2 (or omit for the default).
- `image_url` **or** `reference_images` — a single start frame for image-to-video. `veo3.1-fast` is
  image-to-video, so a start frame is recommended.
- `duration` — clip length in seconds (default `8`).
- `resolution` — default `720p`.
- `aspect_ratio` — `square`, `landscape`, or `portrait`.
- `generate_audio` — `true` or `false` (native audio on `veo3.1-fast`).
- `seed` — set to reproduce a previous result.

The job blocks until the clip is ready — this can take a while for longer or higher-resolution
clips. Wait for it.

### Step 6: Return

Share the resulting video URL with the user.

## Edge cases

- **Fits no kind** → leave `model` unset (tool default) or call `list_video_models`.
- **Safety/NSFW rejection** → remove the sensitive wording and retry once.
- **Generic failure** → retry once as-is, then report the error.
- **`error: "no_provider_configured"`** → relay the tool's `hint` (the user must set their key).
- **Long jobs** → generation blocks until the clip is ready; don't abandon the call early.

## Reference

**Prompt guides** — read the one for the chosen model:

- `references/prompt-veo3.1-fast.md` — image-to-video with native audio; describe the motion, camera,
  and action over the clip.
- `references/prompt-grok-video.md` — natural-language director style for quick drafts.
