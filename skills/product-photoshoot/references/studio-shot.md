# Mode — studio-shot

Studio-quality product photography on neutral, seamless, or controlled backgrounds — the e-commerce
default for Shopify / Amazon listings, catalogs, and packshots.

- **Model:** `nano-banana-2`, or `gpt-image-2` when a label or printed text must stay perfectly legible.
- **One image per call** — make one call per variant.

## Style presets

Pick by product and brand; each binds a lighting + background + camera feel:

- **clean-studio** (default) — seamless light-grey gradient, soft frontal key light, very light
  shadows. Universal e-commerce.
- **dramatic-studio** — strong rim lighting, deep contrast shadows, moody backdrop. Premium
  electronics, fragrance, hero shots.
- **minimal-design** — pastel or single-color paper backdrop, geometric arrangement, ample empty
  space. Modern DTC.
- **etsy-handmade** — warm soft daylight, textured oak / linen / slate surfaces, organic shadows.
  Artisan and small-batch goods.
- **luxury-editorial** — rich jewel-tone background, marble or velvet, polished surface reflections.
  Jewelry, perfume, fashion.
- **vibrant-color** — bold color-blocking, saturated background, flat graphic staging. Food,
  cosmetics, bright consumer goods.
- **floating-product** — product suspended in mid-air, soft ground shadow, accents catching slight
  motion. Flagship hero shots.
- **ingredient-flatlay** — top-down view, product surrounded by arranged raw materials. Skincare,
  supplements, culinary.

## Prompt template

Fill each bracket in order:

- `[SUBJECT]` — "Hero shot of {{exact product, material/finish, label/branding if visible}}."
- `[COMPOSITION]` — camera angle, framing, rule-of-thirds placement, negative-space directive.
- `[LIGHTING]` — direction + quality + Kelvin + shadow behavior.
- `[LENS & CAMERA]` — "Shot on {{focal length}}, aperture {{f-stop}}, {{depth of field}}, sharp focus
  on {{area}}" (e.g. `100mm macro, f/8` for tight detail).
- `[MATERIALS & TEXTURE]` — surface treatments, reflections, micro-detail.
- `[COLOR PALETTE]` — 2–3 dominant tones; brand hex codes if given.
- `[STYLE REFERENCE]` — anchors for the preset from `style-descriptors.md` (a look, never a name).
- `[BRAND INTEGRATION]` — brand colors + mood (clean / warm / edgy / refined) if the brief gives them.
- `[QUALITY MARKERS]` — "tack-sharp, hyper-detailed, photorealistic, commercial-grade."
- `[AVOID]` — merged negatives (Universal + Anti-text-warp if a label shows).

## Composition rules

- The product is the single hero; center or rule-of-thirds with intentional negative space.
- Background follows the chosen preset — never muddy, no unprompted detail.
- A realistic contact shadow anchors the product to the surface.

## Aim for

1. Product recognizable, matches the reference if one was supplied.
2. Lighting has clear direction and quality, not flat.
3. Shadows physically plausible (contact shadow at base, falling away from the key).
4. Label / text on the product sharp and unwarped.
5. No AI artifacts on edges or reflections.
6. Background intentional, not muddy.
7. Color palette aligns with the brand colors given.
