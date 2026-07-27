# Mode — pin-graphic

A vertical Pinterest pin — moodboard layouts, organic warmth, muted pastel tones, layered storytelling.
Quieter and warmer than the saturated Instagram look.

- **Model:** `nano-banana-2`, or `gpt-image-2` when the pin carries a rendered headline.
- **One image per call.**

## Prompt template

- `[FORMAT]` — strict vertical portrait composition, framed for a 2:3 pin.
- `[SUBJECT]` — product or scene arrangement.
- `[COMPOSITION]` — strong visual entry point near the top to hook the eye; asymmetric, hand-crafted.
- `[AESTHETIC]` — target style (Cottagecore, Scandinavian, Clean-girl, Quiet-luxury).
- `[LIGHTING]` — warm 3200K–4500K, soft natural window light or golden-hour glow.
- `[SURFACE & TEXTURE]` — cozy tactile surfaces (raw wood, textured linen, glazed ceramic).
- `[COLOR PALETTE]` — the selected muted palette.
- `[STYLE REFERENCE]` — lifestyle / home anchors from `style-descriptors.md`.
- `[TYPOGRAPHY]` — apply the `typography.md` 3-case rule if the pin carries text.
- `[QUALITY MARKERS]` + `[AVOID]` — exclude neon tones, square crops, sterile stock; Universal
  (+ Anti-flat-band if text space is reserved).

## Composition rules

- Always vertical (portrait), composed for a 2:3 pin.
- Top-of-frame hook; asymmetric, layered, hand-made feel — not centered or sterile.
- Muted and pastel over saturated.

## Aim for

1. Output is vertical (portrait) orientation.
2. Palette leans muted / pastel, not saturated.
3. Backdrop feels cozy and textured, not sterile.
4. Any text integrated and legible (per the typography case).
