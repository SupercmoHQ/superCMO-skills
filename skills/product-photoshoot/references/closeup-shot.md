# Mode — closeup-shot

A tight crop of the product as hero alongside human elements (hands, lips, a cheek) — beauty, skincare,
fragrance, wellness application shots.

- **Model:** `nano-banana-pro` (skin realism).
- **Always pass the product photo** in `reference_images` to lock its identity. One image per call.

## Interaction → lighting

Match the light to the action. Examples:

- **serum-application** → soft beauty-dish key from the front, slight under-fill, 5000K; gentle
  catchlight on glass and skin.
- **pour-into-palm** → top-down softbox key, 5000K; highlights liquid viscosity, hand partly in shadow.
- **dropper-mid-air** → hard directional key with a grid, 5000K; freezes a single droplet against deep
  shadow.

## Prompt template

- `[FRAMING]` — tight closeup, product is hero; the exact crop (e.g. hands cradling the item).
- `[PRODUCT]` — precise packaging, materials, visible branding.
- `[PERSON CONTEXT]` — visible human parts as background context (fingers, lips), natural skin.
- `[INTERACTION]` — the action: applying, holding, pouring, touching.
- `[LIGHTING]` — selected setup: direction, Kelvin, shadow; realistic highlights, no plastic sheen.
- `[LENS & CAMERA]` — `85mm portrait` or `100mm macro`, `f/2.8–f/4`; product tack-sharp, skin to bokeh.
- `[SKIN & DETAIL]` — natural skin: visible pores, fine hairs, micro-imperfections; no AI airbrush.
- `[COLOR PALETTE]` — 2–3 brand tones.
- `[STYLE REFERENCE]` — beauty / closeup anchors from `style-descriptors.md`.
- `[AVOID]` — Universal + Anti-uncanny + Anti-text-warp (if a label shows).

## Composition rules

- Product occupies ~40–60% of the frame.
- Never a full face — tight crops only (nose-to-chin, eye area, lips, a cheek).
- Hands relaxed and natural (cradling, not stiff or posed).

## Aim for

1. Product covers ~40–60% of the frame and matches the reference.
2. Skin texture natural (pores, not plastic airbrush).
3. Hands / visible features anatomically correct.
4. Lighting has clear direction; realistic catchlights, no sheen.
5. Label / text sharp and unwarped.
