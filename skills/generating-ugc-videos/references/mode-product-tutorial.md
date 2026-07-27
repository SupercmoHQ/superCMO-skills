# Mode: tutorial (how-to demonstration)

**Use when:** UGC how-to / step-by-step demonstration of using a specific physical product.

Tutorial replaces the story frame with a step spine — **no story mode, no hook menu.** Its defining
feature: every slot carries a `Step N — Heading` caption rendered *into* the image by the board model
— not a video overlay, not a fifth panel, not something added later.

## Models

- **Slots:** four per board — four equal vertical panels side by side in one wide (`landscape`) sheet.
  One slot = one step.
- **Board:** `image_generate(requests=[{"model": "gpt-image-2", "aspect_ratio": "16:9", "reference_images": […]}])`.
  gpt-image-2 renders the on-image caption text — describe each caption as the exact words to draw
  inside its slot. References in supply order (product, creator, then the previous board for K > 1) as
  `image_0.png`, `image_1.png`, …; the previous board carries identity, location, lighting, wardrobe,
  and product forward.
- **Clip:** `video_generate(model="veo3.1-fast", start_image=<board>, aspect_ratio="portrait", generate_audio=true)`
  — one call per board, run in parallel, then stitched in board order with hard cuts.

## Step 1: Work out the usage steps (before any board)

Before drafting the monologue or building a board, work out the real steps of using this product.

1. **List the realistic actions** a person actually performs, in order, start to finish (pick up,
   uncap, dispense, apply, finish). Base them on the product's true usage mechanic — never invent
   physically impossible or fake steps.
2. **Fit the list to exactly four steps per board.** Total steps = 4 × N (N from `pipeline.md`).
   - **Too few** → expand: add a setup / preparation step at the front and/or a finishing / cleanup
     step at the end.
   - **Too many** → condense: merge adjacent micro-actions into one step.
   - **User gave an explicit ordered step list** → use it as-is, 1:1, in their order. Do not re-derive.
3. **Number steps globally across boards.** Board 1 = Steps 1–4, Board 2 = Steps 5–8, Board J =
   Steps 4(J−1)+1 … 4J. Numbering never restarts per board.
4. Write each as a short caption string: `Step N — Heading`, Title Case, en-dash (`—`) with single
   spaces around it, English only — for instance `Step 1 — Prime The Skin`, `Step 5 — Press And Hold`,
   `Step 8 — Set With Mist` (the 1 / 5 / 8 show global numbering carrying across boards).

The four captions for a board are that board's ordered slot headings.

## Build the board

1. **Set the shot** — slot 1 usually shows the product being **picked up** (except when Step 1 is a
   pre-product action, e.g. "wash hands"). The four slots span camera distances (`board-craft.md` — at
   least one tight, one mid, one wider; all four in one band = rewrite); a natural cadence is medium
   establishing → tighter on the action → macro on the mechanic → three-quarter close. Expressions
   evolve slot to slot: focused setup → instructive demonstration → concentrated application → settled
   satisfaction. Never the same look four times.

2. **Bake in the step captions** (the defining rule):

   > **Override:** `board-craft.md` forbids any text on the sheet. Tutorial is the one exception — the
   > `Step N — Heading` captions below are required. Nothing else on the sheet may carry text: no
   > watermark, badge, number, or subtitle beyond the four step captions.

   Each slot has **exactly one** caption, rendered as text inside the image by the board model. Spell
   it out per slot in the prompt as the literal words to render — say, `Step 1 — Prime The Skin`
   in slot 1, `Step 2 — Press The Pump` in slot 2. Do not write a generic "add the step caption"; name the
   exact glyphs for every slot.

   **Identical typography across all four slots** — same font style, size, color, position, casing.
   State this in the prompt and repeat the styling on each slot so the row reads as one consistent set.
   - **Position:** top-center by default, padded ~5–7% from the top edge, horizontally centered.
   - **Off the face:** the caption must never overlap the character's face. If the face crosses the
     top-center zone in any slot, move that caption to **bottom-center** — and apply that same
     bottom-center position to **all four** slots. Never mix positions within a board.
   - **Size:** readable at thumbnail scale, roughly 60–70% of slot width. Same on all four.
   - **Color:** high-contrast against the slot background (white with a soft drop-shadow, dark
     charcoal, or a product-toned tint). Same on all four.
   - **Casing:** Title Case headings (ALL-CAPS only if the category style is bold-condensed).
   - **Lines:** one line preferred, two maximum. If any slot needs two lines, wrap all four the same way.
   - **Legibility:** demand sharp, fully legible text — no AI-text glitching, no warped or doubled
     letters, no extra characters. State this both per-slot and once more in the closing render rules.
   - Beyond these four Step captions, **no other on-image text** anywhere.

   Pick the font vibe from the product category and reuse it identically on all four captions
   (natural-language style descriptions, not font-file names):

   | Product category                         | Font vibe                                             |
   | ---------------------------------------- | ----------------------------------------------------- |
   | Skincare / serums / creams / luxury beauty | High-contrast editorial serif, fine hairline strokes, magazine-cover feel |
   | Fragrance / perfume                      | Understated fine serif or a slim elegant sans, quiet luxury |
   | Color cosmetics / makeup                 | Contemporary sans or a styled slanted serif, on-trend |
   | Tech / electronics                       | Clean geometric sans, neutral and precise             |
   | Fitness / gym / sports                   | Heavy compressed sans set ALL-CAPS, high-energy       |
   | Food / beverage / snacks                 | Soft rounded sans or a casual handwritten script, approachable |
   | Coffee / artisan food                    | Characterful serif or hand-lettered display, crafted feel |
   | Fashion / accessories / jewelry          | Spare thin sans or a couture-style fine serif         |
   | Home / decor / candles                   | Delicate serif or a gentle refined sans, unhurried    |
   | Outdoor / lifestyle                      | Clean sans with a touch more weight, active           |
   | Default (uncertain)                      | Plain readable sans at regular weight                 |

3. **Show the product's full action** — the real usage mechanic, **including the application / finish**,
   not just dispensing (a serum is `dispense → apply / pat in`, a cream is `scoop → smooth on`). Follow
   the interaction-sequence, safe-verb, weight/grip, and body-part-lock rules in `board-craft.md`.

4. **Arc** — one constant arc for every board: the four numbered steps in order, with no
   hook/continuation distinction. There is no per-board arc mapping to look up.

## Build the clip

1. **Even time-slicing** — tutorial steps carry equal weight, so split the clip duration evenly across
   the four cuts (for 15s, weight the two middle cuts slightly):

   | Clip length | Cut 1 | Cut 2 | Cut 3 | Cut 4 |
   | ----------- | ----- | ----- | ----- | ----- |
   | 4s          | 1s    | 1s    | 1s    | 1s    |
   | 6s          | 1.5s  | 1.5s  | 1.5s  | 1.5s  |
   | 8s          | 2s    | 2s    | 2s    | 2s    |
   | 10s         | 2.5s  | 2.5s  | 2.5s  | 2.5s  |
   | 12s         | 3s    | 3s    | 3s    | 3s    |
   | 15s         | 3.5s  | 4s    | 4s    | 3.5s  |

2. **Caption persistence** — each cut must state that its baked `Step N — Heading` caption stays
   visible the whole cut, sharp and legible, in the same baked position. Quote the caption text
   verbatim per cut. Never describe it animating in or out, redrawing, shifting, glitching, or being
   replaced — the captions are already in the source frames; the video just holds them steady.

3. **POV cadence** — tutorials lean tripod-heavy (most steps are two-handed demonstrations needing a
   locked-off frame). Default cadence: **tripod → tripod → tripod → selfie**. Use MIXED phrasing that
   matches each cut's POV.

4. **Audio** — board 1 opens with a greeting + product introduction (`pipeline.md` rule); later boards
   open mid-thought with no re-greeting. Keep the tone calm and instructional — each cut's line says
   what the character is doing in that step (say, "Two pumps, right here" or "Then I work it in gently").
   Avoid the hype tells in `clip-craft.md`.

## End call-to-action (last cut of the last board only)

On the final cut of the final board — and nowhere else — add a brief CTA tail in the last ~0.5–1s:

- **Spoken** — a short English phrase appended after the last step's line, e.g. `Tap the link.` /
  `Come follow me.` (~1s), or a single word like `Subscribe!` (≤0.5s if time is tight).
- **Gesture** — a quick downward hand gesture toward the bottom edge of the frame, plus a selfie
  pull-in close to lens with a confident half-smile.
- It is **audio + gesture only**. Never a caption on the frame, never a fifth slot, never new on-screen
  text. The Step 4 caption stays as-is throughout.
- It is **built into Cut 4's existing time** — it never extends the clip duration. If the monologue is
  running long, trim the spoken line earlier rather than lengthening the clip.

Intermediate boards get **no** CTA — their final cut ends naturally on the step's action.

## Language

English only, everywhere — every step caption, the monologue, and the CTA. No exceptions.
