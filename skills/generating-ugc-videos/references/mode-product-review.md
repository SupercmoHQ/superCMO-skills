# Mode: review (talking-head)

**Use when:** UGC talking-head — the creator holds and reviews a specific physical product (not
wearing, unboxing, or a step-by-step how-to).

## Models

- **Slots:** three per board, side by side in one wide (`landscape`) sheet — three sequential moments
  of one clip.
- **Board:** `image_generate(requests=[{"model": "gpt-image-2", "aspect_ratio": "16:9", "reference_images": […]}])`.
  References in supply order — product, creator, then previous board (K > 1) — named `image_0.png`,
  `image_1.png`, `image_2.png`; the previous board carries identity, location, lighting, wardrobe, and
  product forward.
- **Clip:** `video_generate(model="veo3.1-fast", start_image=<board>, aspect_ratio="portrait", generate_audio=true)`
  — one call per board, run in parallel, then stitched in board order with hard cuts.

## Build the board

1. **Map the arc across the three slots** (arc role from `pipeline.md`):

   | Arc role      | Slot 1              | Slot 2                     | Slot 3                    |
   | ------------- | ------------------- | -------------------------- | ------------------------- |
   | full arc (N=1)| hook — grab         | main — use / core moment   | closer — reaction/result  |
   | hook+setup    | hook                | setup / context            | first look at the product |
   | apply+closer  | apply / demo        | result                     | closer / sign-off         |
   | hook          | hook                | build                      | into the product          |
   | main          | use                 | detail / benefit           | continue                  |
   | reveal        | tease               | reveal                     | react                     |
   | closer        | last benefit        | result                     | wrap                      |

2. **Pick the opener** (first board only) — use the shared hook menu in `pipeline.md`; register by
   brief tone: hyped → Mid-collision or Dropped-in; warm → calmer talking-head beat;
   cool / luxury → deadpan. The energy behind it is the performance register in `board-craft.md`.

3. **Show the product** — the creator holds and demonstrates it using its real usage mechanic (from
   Step 3 — for example a spray, a pump, a swipe, a scoop, or twisting off a cap). Follow the
   interaction-sequence and safe-verb rules in
   `board-craft.md`; show the exact mechanic, never a vague "uses it".

4. **Vary the shots** — three different actions at three different camera distances (`board-craft.md`);
   expressions evolve slot to slot, never the same look three times; default to the high-energy
   register (`board-craft.md`) unless the brief's tone calls for warm, dry, or cool.

## Build the clip

1. **Audio** — the monologue is lip-synced across the clip (see `clip-craft.md`).
2. **Close** — no on-image captions, and no end call-to-action; the review ends on the final spoken line.
