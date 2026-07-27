# Mode: testimonial (no product)

**Use when:** UGC / creator intent naming a service, app, or brand, with no physical product (an app
URL or a service name is not a product to feature).

## Models

- **Slots:** three per board, side by side in one wide (`landscape`) sheet — three talking-head
  moments of one clip.
- **Board:** `image_generate(requests=[{"model": "gpt-image-2", "aspect_ratio": "16:9", "reference_images": [<creator>]}])`
  — the creator reference only (add the previous board for K > 1), by supply order (`image_0.png`, …).
- **Clip:** `video_generate(model="veo3.1-fast", start_image=<board>, reference_images=[<creator>], aspect_ratio="portrait", generate_audio=true)`
  — one per board, run in parallel, then stitched in board order with hard cuts.

## Build the board

1. **Set the scene** — only the creator is on camera, speaking, in an everyday setting that fits what
   they're talking about (a home desk for a SaaS tool, a kitchen for a meal service, a car for a
   rideshare app). Nothing is held. Only if it's a named app or software may it appear on a device
   screen the creator glances at or turns toward — incidental, never a walk-through.
2. **Skip the product rules** — no angle-lock, real-world scale, interaction sequences, safe-verb
   table, weight/grip, or placement. This is `board-craft.md`'s no-product board.
3. **Map the arc across the three slots** (from `pipeline.md`), the service or app taking the
   product's place:

   | Arc role       | Slot 1        | Slot 2                          | Slot 3                    |
   | -------------- | ------------- | ------------------------------- | ------------------------- |
   | full arc (N=1) | hook — the stake / problem | the turn — the service/app comes in | closer — the result / verdict |

   It "comes in" as a spoken beat (naming it, what changed) — or, for a named app, a glance to the
   on-screen device — never a held reveal.
4. **Vary the shots** — three different actions at three different camera distances (`board-craft.md`):
   a lean-in to lens, a gesture mid-point, a settled close. POV is selfie-led (arm's-length front
   camera), optionally cutting to a tripod medium for a steadier "sit-down and explain" beat.

## Build the clip

1. **Audio** — the monologue is lip-synced across the clip (see `clip-craft.md`); follow `pipeline.md`
   (story shape, hook menu, first-word rule, anti-slop): lead with the human stake (the problem the
   service or app solved), let it come in at 40–60% as the turn, land the result in the closer. The
   claim captured in Step 3 is the one concrete the closer rests on — keep it honest; don't invent
   numbers.
2. **Close** — no on-image captions; the end call-to-action is off by default (ends on the final
   spoken line), added only if the brief asks ("try it free", "link's right there") — spoken, never a
   caption.
