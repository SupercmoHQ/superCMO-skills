---
name: generating-videos
description: ALWAYS read this skill before generating or animating any video, or calling video_generate — text-to-video, image-to-video, a start→end transition, or a reference / motion / audio-guided clip. Turns a brief into a video clip — sets the model, picks the mode, and structures the video prompt. Use whenever the user asks to generate, create, make, or animate a video, produce b-roll, or bring an image to life.
license: Apache-2.0
metadata:
  version: "0.1.0"
  category: creative
  summary: "Turns text briefs or still images into videos. Generates everything from cinematic b-roll to animated product shots, automatically structuring the complex prompts required by top video models."
---

# Video Generation

Turn a brief into a video clip via the `video_generate` tool. 
The decisions that drive quality are **which mode** you choose and **how you write the motion prompt**.

**Scope.** This skill is the open-ended video engine — turning a brief into a clip, on its own or
from supplied media. Purpose-built marketing formats — a creator talking to camera about a product
(UGC), a premium product commercial, animated motion-graphics or brand reels, cartoon or anime
animation — are their own skills and out of scope here.

## Workflow

### Step 1: Pick the model and load its parameters

**`seedance-2.0` is the default** — the general-purpose workhorse; a weak result is usually the
prompt's fault, not the model's. Reach for another only on a clear signal:

| Reach for another model when the brief… | Model | Guide |
| --- | --- | --- |
| Needs spoken dialogue with lip-sync, the tightest prompt-following, or top cinematic quality | `veo-3.1` | `references/prompt-veo.md` |
| Is editing an existing clip (restyle, add or replace an element, fix on-screen text), or hinges on legible on-screen text | `gemini-omni` | `references/prompt-gemini-omni.md` |
| Must hold one person or character consistent across references or several shots | `kling-3.0-pro` | `references/prompt-kling.md` |
| Has an edgy or sensitive subject Seedance would refuse, or wants the fastest, cheapest draft | `grok-imagine-video` | `references/prompt-grok.md` |
| Is a high-volume or cost-sensitive batch where top quality isn't essential | `wan-2.7` | `references/prompt-wan.md` |

When several fit, take them in order:

- The user **named** a model → use it.
- Seedance **refused** (`nsfw` / `ip`) or keeps failing → the fallback above (edgy or blocked →
  `grok-imagine-video`).
- A clear capability above → that model.
- Otherwise stay on `seedance-2.0`; when two tie, prefer the newer.

The `-fast` / `-lite` / `-turbo` / `-standard` / `-mini` variants share their family's guide, and
Seedance filters hard on real people, trademarked characters, and graphic content — flag a clearly
sensitive brief before you spend.

Then **call `list_video_models` for the chosen model** and read its accepted modes, aspect ratios,
durations, resolutions, and media — each validates its own subset, and you need these before picking
a mode or writing the prompt.

### Step 2: Pick the mode

From the modes that model accepts, pick what you feed the tool — each input below shapes the clip a
different way, and a model can take several of them together (a start frame alongside references, for
instance).

| The brief is… | Mode | What you pass |
| --- | --- | --- |
| A scene described in words, no image | **text-to-video** | `prompt` only |
| A still to bring to life ("animate this", "make this move") | **image-to-video** | `prompt` + `start_frame_image` |
| A move from one held frame to another | **start→end transition** | `prompt` + `start_frame_image` + `end_frame_image` |
| A subject, character, or style to carry (not tied to a specific frame) | **reference image** | `prompt` + `reference_images` |
| Motion or style taken from existing footage | **video-to-video** | `prompt` + `reference_videos` |
| Timed to an existing track (lip-sync, beat) | **audio-guided** | `prompt` + `reference_audios` |

A single supplied image can serve as a **start frame** (animate that exact frame in place) or a
**reference** (carry its subject or style into a new scene) — pick by what the user wants, from the
inputs and combinations Step 1 showed the model accepts.

### Step 3: Get any missing inputs

Ask only for what would change the result and can't be sensibly defaulted — for example a start
frame when the user says "animate this" but attaches nothing, the aspect ratio when the destination
decides the crop, or whether the clip should carry sound. Bundle everything you need into one ask
rather than a back-and-forth; if the user has signalled they don't want questions, choose sensible
defaults, state them in a line, and proceed.

### Step 4: Read the supplied media first

When a frame or reference is supplied, read it before writing anything — call `image_analysis` on an
image (a start or end frame, or a reference image) and `video_analysis` on a reference video — and
name what it already fixes so your prompt animates or matches it instead of contradicting it. Skip
this when you already know the media (you made it this turn, or it came with a description).

### Step 5: Write the motion prompt

Build the prompt as the chosen model's guide specifies (from **Step 1**). Each model wants a different shape, so read its guide first. With a start frame or reference, the image already fixes the look — the prompt carries the **motion**: what moves, the camera behaviour, the physics, and the audio. A dense, concrete, physical description beats a thin one-liner.

**Pace it to the length.** Fit the amount of action — and speech — to the clip's duration. Aim for roughly one distinct action or shot every couple of seconds, so a short clip carries only a few beats. Spoken dialogue runs at about two to three words a second, so each line has to fit its clip. When the brief needs more time, action, or dialogue than one clip allows — or the same subject has to hold across several shots — build it as several clips and stitch them (see **Longer or multi-clip videos** below).

### Step 6: Generate

Call `video_generate` with a `requests` list (one object per clip):

- Per object: `prompt` (required); the mode inputs from Step 2; `duration`, `resolution`,
  `aspect_ratio`, and `generate_audio` as the task needs. Omit `model` to take the default; set it
  only when the user named one.
- **A batch of different clips** (an A/B set, several shots) → add one request object per clip to the
  same call. For variations of one idea, repeat the same object.

Video is long-running: the tool waits for each clip, but a clip that runs long comes back as
`{status: "pending", …}` (a job handle, not a failure). Pass that exact handle to `job_status` to
retrieve the finished clip — **never re-run a pending clip** with `video_generate`; that starts a new,
separately-billed job. If it's still pending, call `job_status` again with the same handle.

### Step 7: Return

Once every clip has finished (rejoin any `pending` ones via `job_status` first), share the resulting
video URL(s) and local file path(s) with the user.

## Longer or multi-clip videos

A single clip caps at the model's maximum length (`list_video_models` gives the exact range).
Anything longer is built as a set of clips generated separately, then joined into one file. 
Work through these steps in order:

1. **Plan the shots.** Break the brief into an ordered shot list — each shot one clip within the
   model's allowed durations, and together covering the whole story. Decide what happens in each shot
   and pick its length so the shots **add up to the target** (e.g. a longer target split into a few
   shots at the durations the model allows).
2. **Budget the script.** Spread any dialogue or voiceover across the shots so each line fits its
   clip's seconds (about two to three words a second). Set the ambient sound, music, or SFX for each
   shot.
3. **Anchor any recurring subject.** Clips are generated independently, so a back-reference ("the
   same woman", "that sneaker again") drifts into a different-looking thing each time. Whenever a
   person, product, or signature prop appears in more than one shot, before generating any clip:
   - Generate **one** clean still of that subject — a portrait for a person, a plain product shot for
     an object — by handing off to the `generating-images` skill (skip this if the user already
     supplied one).
   - Pass that **same** still as `reference_images` in **every** shot the subject appears in.
   - Describe the subject's look word-for-word the same in each prompt; vary only the shot, action,
     and framing. This anchoring works on **any** model.
4. **Keep the world continuous.** Repeat the palette, lighting, and setting in every shot's prompt,
   and open each shot on the state the previous one ended in, so a hard cut reads as continuous.
5. **Generate the clips.** Send all the shots in one `video_generate` call — one request object per
   shot, the same aspect ratio and resolution across the set.
6. **Stitch into one video.** Wait until every clip has finished — rejoin any that came back
   `pending` via `job_status` before stitching. Hand the finished clips, in order, to the
   `video_stitch` tool — it joins them with a hard cut between each and preserves each clip's audio.
   Don't assemble the clips by hand. Return the stitched video (and the individual clips if the user
   wants them).

## Edge cases

- **Safety / NSFW rejection** → name a workable stand-in for whatever tripped the filter (cover the
  wardrobe, change the setting) and resubmit. If the subject itself is the block, switch to
  `grok-imagine-video` (see **Step 1**) and read its guide. A second rejection: tell the user which
  element is blocked instead of retrying blind.
- **Still generating (`status: "pending"`) or the call times out** → the clip is still rendering on
  the server, **not** a failure — do **not** resubmit (that starts a second billed job). If you got a
  pending handle, call `job_status` with it to rejoin; if the call timed out with no handle, wait and
  tell the user it's still processing rather than firing a fresh generation.
- **Generic failure** (an explicit error result, not a timeout) → read the error. If it names a
  parameter or a limit, correct that and resubmit. Otherwise resubmit once; if it fails again, either
  switch to a fallback model (**Step 1**) and write to its guide, or give the user the error text
  rather than guessing.
- **Reference or frame rejected on count / mode** → the error states the model's limit or supported
  modes; adjust to it (or check `list_video_models`).
- **The user wants a standalone audio file, not clip audio** (a voiceover to drop on a timeline, or
  a music track or sound effect they need to place or mix themselves) → native clip audio can't give
  them that; it bakes into the picture. Hand speech to `generating-audio`, and say plainly that
  separate music and effects tracks aren't generated here.
- **Unsure which model fits a named request** → call `list_video_models` and pick by `strengths`.
- **`error: "no_provider_configured"`** → relay the tool's `hint` (the user must set their key).

## Reference

**Model prompt guides** — read the one for the chosen model (see **Step 1**):

- `references/prompt-seedance.md` — the default; native audio markers, one-move-per-shot, storyboards.
- `references/prompt-veo.md` — cinematography-first order, `SFX:` / `Ambient noise:` markers, timecodes.
- `references/prompt-gemini-omni.md` — conversational editing of an existing clip; edits, not extends.
- `references/prompt-kling.md` — director-script style, `@Element` references, per-speaker dialogue labels.
- `references/prompt-grok.md` — tight front-loaded briefs, positive-only exclusions, one action per clip.
- `references/prompt-wan.md` — front-loaded prose, multi-shot timestamps, driving-audio sync.
