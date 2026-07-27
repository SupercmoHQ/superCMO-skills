# Mode — on-model-shot

Fashion-grade imagery where a product is worn or held by an AI-rendered model — clothing, jewelry,
watches, eyewear, bags. The product is the hero; the model is the canvas.

- **Model:** `nano-banana-pro` (people / skin).
- **Pass the product photo** in `reference_images` to anchor fidelity. One image per variant. The model
  is **described from scratch in each prompt** — no stored identity, no face training.

## Preset → lighting

Match the light to the setting. Examples:

- **studio-clean** (catalog) → softbox key camera-left + fill bounce right + subtle hair backlight,
  5500K, clean even shadows.
- **street-style** (urban DTC) → available daylight + reflector fill, 5000K, candid.
- **outdoor-natural** → soft golden-hour backlight + reflector fill, 4500K.
- **closeup-detail** (jewelry / watches) → macro on the worn product, soft directional key.


## Prompt template

- `[PRODUCT]` — the wearable + exactly where worn on the body.
- `[MODEL]` — age range, gender presentation, hair texture, skin tone, realistic body proportions.
- `[POSE]` — posture, hand positions, eye direction, expression (specified to avoid AI errors).
- `[FRAMING]` — half-body / three-quarter / full-body.
- `[ENVIRONMENT]` — location matching the preset.
- `[WARDROBE / STYLING]` — supporting outfit in neutral tones that complements, not competes.
- `[LIGHTING]` — selected setup, Kelvin, highlight behavior on skin.
- `[LENS & CAMERA]` — `85mm portrait` or `50mm`, `f/2.8–f/5.6`; product tack-sharp.
- `[SKIN & DETAIL]` — natural skin texture (pores), no AI airbrushing.
- `[PRODUCT FIDELITY DIRECTIVE]` — product color, materials, design, dimensions faithful to the reference.
- `[STYLE REFERENCE]` — fashion / campaign anchors from `style-descriptors.md`.
- `[AVOID]` — Universal + Anti-uncanny + Anti-text-warp (if branding shows).

## Composition rules (anatomy)

- Specify hand placement ("relaxed fingers loosely curled at side"), eye direction, and realistic
  weight distribution with logical ground shadows.
- The product stays clearly visible and unaltered; the model never overshadows it.

## Aim for

1. Product matches the reference exactly (color, texture, design detail).
2. Hands and facial structure anatomically correct.
3. Skin texture realistic (natural pores, not plastic airbrush).
4. Pose natural; ground shadow logical.
5. Wardrobe complements without competing for focus.
