# Mode — web-banner

Wide-format images for website headers, landing pages, email campaigns, and section dividers.
Cinematic, crop-safe, conveys brand mood in under a second with a strong focal anchor.

- **Model:** `nano-banana-2`, or `gpt-image-2` when headline copy is rendered into the banner.
- **One image per call.**

## Banner presets

Examples:

- **cinematic-product-hero** — premium launch, wide atmospheric staging.
- **studio-product-wide** — category header, centered product grouping on a clean backdrop.
- **abstract-brand-mood** — no physical product; gradients, shadows, textures.

## Prompt template

- `[FORMAT]` — wide landscape cinematic layout.
- `[FOCAL SUBJECT]` — product anchored off-center (left or right third).
- `[COMPOSITION]` — horizontal flow lines; foreground / midground / background depth; subject inside a
  central crop-safe zone for mobile.
- `[ATMOSPHERE]` — refined / dramatic / calm mood with environmental depth.
- `[LIGHTING]` — quality, direction, Kelvin matched to the brand tier (hard and dramatic for luxury;
  soft and diffused for calm / wellness).
- `[LENS & CAMERA]` — wide `24mm`/`35mm`, anamorphic cinematic feel, retained DoF.
- `[COLOR PALETTE]` — brand-aligned tones; hex if given.
- `[STYLE REFERENCE]` — cinematic / landscape anchors from `style-descriptors.md`.
- `[TYPOGRAPHY]` — apply the `typography.md` rule; reserved copy space must be a natural blurred area,
  not a flat band.
- `[QUALITY MARKERS]` + `[AVOID]` — ban flat lighting, symmetrical splits (unless requested), generic
  stock; Universal + Anti-stock-feel (+ Anti-flat-band if copy space reserved).

## Composition rules

- Off-center focal placement; leave opposite space for website copy and buttons.
- A foreground element for depth (out-of-focus leaf, surface edge).
- Core subject survives responsive mobile crops.

## Aim for

1. Output is landscape orientation, composed crop-safe for a wide header.
2. Main subject off-center within the crop-safe zone.
3. Backdrop integrated, not a flat color band.
4. Lighting directional and matched to the brand tier.
5. Color palette aligns with the brand colors given.
