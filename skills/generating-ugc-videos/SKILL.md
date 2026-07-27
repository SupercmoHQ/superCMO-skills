---
name: generating-ugc-videos
description: Generates a short vertical UGC-style video of an AI creator talking to camera about a product — a talking-head review, try-on/OOTD, step-by-step tutorial, or unboxing — or, when there's no product, a testimonial about a service, app, or brand. Use when the user asks for a UGC video, creator or influencer ad, tiktok-style review, unboxing, try-on, or testimonial video.
license: Apache-2.0
metadata:
  version: "0.1.0"
  category: creative
---

# UGC Video

Turn a product — or, with no product, a service or app — into a short vertical UGC video: an AI
creator on camera talking about it. This runs as a pipeline — analyze the subject, generate the
creator, write the monologue, lay out storyboards, animate each board into a clip with spoken audio,
and stitch — with one routing choice up front: the **format**, which sets how the shots are laid out.

## Workflow

### Step 1: Pick the format

Is there a physical product? If so, choose by what the creator does with it; if not, it's a testimonial.

| Subject | What the creator does | Format | Guide |
| ------- | --------------------- | ------ | ----- |
| Physical product | Holds it and talks about it ("review", "creator ad") | **review** | `references/mode-product-review.md` |
| Physical product | Wears it — clothing, accessories ("try-on", "haul", "OOTD") | **try-on** | `references/mode-product-tryon.md` |
| Physical product | Shows how to use it ("tutorial", "how-to") | **tutorial** | `references/mode-product-tutorial.md` |
| Physical product | Opens its package ("unboxing", "reveal") | **unboxing** | `references/mode-product-unboxing.md` |
| Service / app / brand | Talks about it — nothing to hold | **testimonial** | `references/mode-no-product-testimonial.md` |

If two product formats both fit, ask once — *"review, try-on, tutorial, or unboxing?"* Otherwise
default to review (with a product) or testimonial (without one).

Once you've picked, **read that format's guide** — the rest of the workflow depends on it.

### Step 2: Get any missing inputs

Don't start with a load-bearing detail missing — but ask only for what the brief actually needs,
bundled into one message; don't pile on a long list. The usual gaps:

- **No product supplied** → "Share the product — a URL or a photo — so I can feature it exactly."
- **The service/app/brand wasn't named** → "What's the service or app, and what the creator
  should say about it?"
- **No length given** → "How long — 10, 15, 30, or 45 seconds?"
- **If the format is unboxing** → also ask whether to use a real delivery-box photo or a generic box.

Use judgment beyond this list: if something else is genuinely load-bearing and unclear, ask it too —
e.g. a product was shared but you can't tell what it is, or there isn't enough context to feature it
well. Keep it to the few things that actually matter.

Don't ask about settings you can decide yourself — aspect ratio, model, resolution, audio, number of
boards, and stitching are all fixed. If the brief already covers what you need, don't ask at all.

### Step 3: Analyze the subject

- **A physical product** → normalize it with the `analyzing-products` skill (or a quick pass yourself if
  it isn't available). Write **one** product description and reuse it verbatim in every board and clip
  so the product looks identical throughout — its category and tier, how it's operated, its look,
  scale, and label. The detail lives in `references/board-craft.md`.
- **A service, app, or brand** → nothing to normalize. Note its name, what it does, and the one honest
  thing the creator will say. Nothing is held on camera. See `references/mode-no-product-testimonial.md`.

### Step 4: Plan the shoot

1. **Judge how much the brief specifies** — a few words → you make the creative calls; a sentence or
   two → follow their tone; a detailed shot list → follow it beat by beat. Carry this into Steps 6–8.
2. **Read `references/pipeline.md`** — the number of boards for the length, each clip's duration, and
   how the story spreads across the boards.
3. **Apply the format's guide** (read in Step 1) — map its slots and beats onto the boards from the
   duration split.

### Step 5: Make the creator

Read `references/creator-portrait.md`.

- **A photo of a person is attached** → use it as the creator; don't generate one, and don't ask to
  confirm.
- **Otherwise** → write the portrait prompt and generate it with `image_generate` (model
  `nano-banana-pro`, `9:16` aspect).

Keep the result — it's the reference that anchors the creator's face across every board.

### Step 6: Write the monologue

Write what the creator says, following `references/pipeline.md` (words per clip, how to open, the story
shape, phrases to avoid). Split it into one segment per board.

### Step 7: Lay out the boards

Read `references/board-craft.md` and the format's guide. Build boards **one at a time, in order** —
give each new board the previous one as a reference so the creator, setting, and product stay
consistent. Each board is one wide storyboard sheet (`16:9`) whose vertical slots are the shots;
generate it with `image_generate` (model `gpt-image-2`).

### Step 8: Animate each board into a clip

Read `references/clip-craft.md` and the format's guide. For each board, write the video prompt and give
it that board's monologue segment as the spoken line. Generate the clips **in parallel** with
`video_generate` (model `veo3.1-fast`, portrait aspect, native audio on) — the model speaks the line in
the same pass that renders the motion.

### Step 9: Check each clip

Watch each finished clip frame by frame against the QA checklist in `references/clip-craft.md` — one
product only, no more than two hands, absent features still absent, a cap on or off but not both, a
readable label, the creator's face unchanged, no text burned into the picture. If a clip is wrong, fix
its prompt and regenerate that one clip.

### Step 10: Stitch and return

- **One clip** → it is the final video.
- **Two or more** → join them in board order with hard cuts (no fades) via the `montage` tool.

Present only the final video — its path or URL and total length. Don't show the boards, the separate
clips, or ids unless asked.

## Edge cases

- **Can't tell the format** → ask the Step 1 question; if still unclear, use review (with a product) or
  testimonial (without one).
- **A product URL won't load** → ask for a photo instead.
- **A generation is refused as unsafe** → it's usually the creator image; regenerate the creator in
  more covering clothing (see `creator-portrait.md`), then redo the boards that used it. Try a few
  times, then stop and tell the user rather than deliver a broken video.
- **`error: "no_provider_configured"`** → relay the tool's `hint` (the user must set their key).
- **A dependency isn't available** (`analyzing-products`, `montage`) → do the rest of the job and tell the
  user which step couldn't run.

## Reference

**Shared — used by every format:**

- `references/pipeline.md` — boards and clips for a given length, how the story spreads, the monologue
  rules (Steps 4, 6).
- `references/creator-portrait.md` — the prompt that generates the creator (Step 5).
- `references/board-craft.md` — the shared rules for laying out a board (Step 7).
- `references/clip-craft.md` — the shared video-prompt rules and the frame-by-frame check (Steps 8–9).

**Format guides — read the one picked in Step 1:**

- `references/mode-product-review.md` — holds and reviews the product (3 slots).
- `references/mode-product-tryon.md` — wears the product (4 slots; a twirl and a fabric close-up).
- `references/mode-product-tutorial.md` — shows how to use it step by step (4 slots; a numbered step
  drawn into each slot).
- `references/mode-product-unboxing.md` — opens the product's package (4 slots; sealed box, then the reveal).
- `references/mode-no-product-testimonial.md` — no product; talks about a service, app, or brand (3 slots).
