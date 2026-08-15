# Ad craft

Read on every ad. The workflow says what to decide; this says how a decision becomes a picture that reads as designed rather than assembled. An ad is art direction, not decoration — every element earns its place or comes out.

## The single-minded proposition

Work in the discipline of the single-minded proposition: every ad resolves one tension between a consumer truth and a product truth. Look for a human truth about how a person uses or feels about this kind of product — something true enough that it feels slightly uncomfortable to say out loud. Let that truth create tension. Resolve the tension into one idea — one sentence describing what the ad is about. If you cannot say it in one sentence, you have two ads, not one. Only then decide how the idea becomes a frame. Treatment follows idea; never the other way round. Write the copy last — say only what the picture leaves unsaid.

An ad carries **one product, one value proposition, one call to action**. Everything below serves the one message — cut what doesn't. The idea reads from the picture alone; the copy confirms it, never rescues it.

## The focal point

- **One dominant element**, two at most and only if held apart so they don't compete. The product is usually it — made dominant by size, by isolation in open space, by the brightest value falling on it, and by sitting on a rule-of-thirds intersection rather than dead centre. Centred reads static; off-centre carries tension.
- **Lead with the strongest element and demote the rest** — visibly smaller, lighter, lower in contrast. An ad that gives the logo, the product and the copy equal weight reads as amateur. Decide what wins.
- **Cap the focal points at three**: headline, product, call to action. Past three, nothing is emphasised.

## Figure and ground

The eye separates a subject from its background only when there is enough contrast between them; a product that shares its background's value or colour disappears in a feed.

- Push the product forward: a background of contrasting value or hue, a rim of clear space around it, or depth from a cast shadow or a thrown-back backdrop.
- Ask for the **contact shadow by name** — the dark seam where the product meets the surface. Without it the product reads as pasted on.

## Where the copy sits

Copy lives in the **negative space the product leaves** — never across its focal area. Decide the product's placement first, then place the type in the open region. The reading path is a route you build:

- **Visual-led ad** — the eye tracks top-left to top-right, down the diagonal, to the bottom-right. Put the logo top-left, the product on the diagonal, the call to action at the bottom-right where the eye ends.
- **Copy-led ad** — the eye scans the top line, a second line, then down the left edge. Front-load the message in the first line and the left of each block.

## Visual hierarchy

The component stack, in priority: **headline · product hero · offer / call to action · subhead or up to three benefit callouts · social proof · logo**. Rank them by size and contrast so the eye reads them in that order. Each benefit is one idea, scannable, subordinate to the headline. The logo establishes the brand but is rarely the loudest thing — in a feed the account name already sits beside the ad.

**The call to action is a button** — a filled shape (a pill or rounded rectangle) with the action text inside, set in the accent colour, placed where the reading path ends. Never a line of floating text. Describe the button's shape and colour treatment, chosen for this ad's mood.

## Type

- **Two typefaces at most** — one for the headline, one for the body — set far enough apart in weight or style that they read as a deliberate pair, not an accidental clash. More than two, or two that are similar-but-not-equal, reads amateur.
- **Distinct tiers**: a headline that dwarfs the body, a clear step down to subhead and callouts, the legal line smallest. The wider the size jump, the more theatrical the hierarchy.
- The headline is **short, high in the frame, the highest-contrast type** in the ad.
- Describe letterforms by character — weight, width, a serif or a clean sans — rather than naming a font. Quote every drawn string exactly. Give each line its size against the others and where it sits.

## Colour

- **Let one colour dominate the frame, a second hold the secondary areas, and the brand colour appear only as a small accent** — on the call-to-action and one or two touches. Held to a tenth of the frame, the accent pulls the eye to the action; flooded across the frame it stops pulling. Three to five colours in all.
- **A colour reads by what surrounds it**, not by how saturated it is. Make the accent pop by setting it against a quiet or complementary field, not by cranking it up.
- **The value test**: in greyscale the hierarchy must still hold — the headline still darkest-on-lightest, the product still separated. If it collapses when the colour is removed, the contrast is carried by hue alone and will read weakly. Fix the values.
- Drawn copy clears a legibility threshold against whatever sits behind it. A brand colour chosen for identity is often illegible as text — keep it as the accent and set the words in near-black or near-white.

## Grid and negative space

- **Align to a grid.** Shared edges and baselines are what separate designed from assembled; elements floating at arbitrary positions read as cheap.
- **Margins are structural, not leftover.** Generous space around the content signals confidence and premium; content crowded to the edges reads busy and cheap. Whitespace is an active element — a product isolated in open space commands more attention than one surrounded by clutter.
- Restraint is the tell of good art direction: maximum impact, fewest elements. Remove anything that carries no meaning.

## One ad or a set

- **A single ad** is one frame — one message, one hero, one call to action.
- **A set** is several separate ads — the same concept rendered across the ratio family, or distinct variants for testing. Hold the palette, the type and the product identical across every frame; vary only the one thing each variant is testing. A set of near-duplicates tests nothing — give each variant its own argument, and let that pick the staging.

## The ratio family and safe zones

Every placement ratio is **generated natively**, not cropped from a master — a naive crop cuts heads off and pushes the product out of frame.

- **Keep content clear of the platform's own furniture.** On a full-screen vertical placement the top strip and the bottom third are covered by the interface and the real call-to-action button — keep the drawn copy and the offer out of them. The commonest amateur mistake is drawing a call to action exactly where the platform paints its button over it.
- Per ratio: a **square** balances product and copy across the frame with room to breathe; a **tall vertical** lands the hook in the upper-middle and the product mid-frame, clear of the covered strips; a **wide** frame runs the eye left to right — logo left, product and headline centre, call to action far right — and carries little copy, since there's no room to build an argument.

## Brand anchors

Where the user gave guidelines, hold them: the palette as the colours above, the logo placed visibly but never the loudest element and never redrawn (pass it as a labelled reference image, don't describe it into being), the typeface honoured in the letterform description, and anything they never put in frame kept out. Never invent a logo, badge, or asset that isn't attached. Consistency across a set is what makes the ads read as one brand rather than a pile of assets.

## Keep the product real

The one rule an ad cannot break: the product in the frame is the real one. A viewer who spots a made-up product — wrong shape, invented logo, a label that reads as gibberish — feels cheated, and the ad is worse than none.

- The real product photo rides in `reference_images` on every call, and the prompt states it outright: the product is the one in the reference and reaches the image unchanged.
- The background, the styling and the light are the model's to build; the product's geometry, colour, label and text are not.

## Anti-patterns

Three known failure modes. Do not produce them.

- Lighting that glows from multiple sources at once with no coherent key — a glow that seems to come from everywhere at once. Every frame must have ONE primary light, named with quality and direction.
- The uncanny-valley framing of a person grinning while holding the product at chest height. If a person appears, they are doing something real, not posing for a stock photo.
- More than two typefaces in one ad. Two is clean, three is risky, four or more is amateur.

## Realism — the reject filters

Below the design, the picture also has to not read as machine-made. These are table stakes, checked on every output, in priority of what a viewer notices first: **product accuracy, then legible text, then hands, then faces, then background.**

- **Waxy, over-smooth surfaces and skin** → ask for real texture by name — pores, grain, worn material, a matte finish. Quality words won't remove the sheen; naming the texture does.
- **The over-cinematic, HDR, stock-catalogue look** → natural colour balance, one coherent light source and direction, a specific real-world lighting rather than stacked lighting adjectives.
- **Garbled or warped text, fused fingers, extra limbs, melted or doubled geometry, ghost watermarks** → treat as a **reject**. Hand the frame back and say what's off. Never silently regenerate to fix it — a second generation bills again and the user may accept the first.
- Phrase exclusions as the thing you want instead; there is no negative-prompt parameter. State the product invariants ("the product's shape, colour and label unchanged") and the marks to keep out ("no watermark, no invented lettering, no logos that aren't the brand's").

Deterministic layout — pixel-exact type, a locked grid, the offer held precisely out of a safe zone — is not something the model hits reliably from a prompt. Steer it toward these principles, check the output against them, and hand back what misses rather than paying to chase perfection.

## How the prompt is assembled

Every prompt is built in this order:

1. **The preservation block** — fixed, included whenever the product photo is attached: the attached image is the exact product; its shape, colour, label, text and design stay as they are; build only the ad around it. All text, labels, logos, and printed copy on the product packaging must remain fully legible and unobstructed. Never overlay rendered ad text on top of the product's own label.
2. **The layout** — the format, the focal point and its placement, the reading path, and where each piece of copy sits, written as physical regions of the frame.
3. **The copy** — every drawn string in quotes, each with its size against the others and its position, per the type and hierarchy above.
4. **The look** — the palette as dominant / secondary / accent, the light and background that separate the product, the register the ad reads at.
5. **The exclusions** — the product invariants and the marks to keep out, phrased as wants.

Whatever the model's form, the prompt must carry all of this:

- The attached product and how it sits in the frame — placed, lit, composed, never redrawn.
- The composition: where the product sits, what the eye lands on first, where the negative space lives.
- ONE primary light source, named with quality and direction (e.g. "soft window light from camera-left", "single hard top-light", "tight cool key light at 45° from above").
- The surface, environment, and any props, named with specific materials rather than vague descriptors.
- Camera or lens vocabulary when it adds information (focal length, depth of field, angle), not as decoration.
- The treatment register in one phrase — a description of mood and behaviour, not naming a brand, designer, or movement to imitate.
- Every rendered text element, wrapped in single quotes with the exact literal characters, plus a typographic description (weight, family feel, scale, colour, position). For a CTA, describe the button shape and colour treatment chosen for this ad's mood.

Keep the entire prompt under 350 words. Write nothing the picture does not need. End with a short genre tag.

For `gpt-image-2`, write parts 2–4 as short labelled segments on separate lines. For `nano-banana-pro`, write them as a single coherent paragraph of natural prose, with the drawn strings still quoted. Where more than one reference image is passed, label them Image 1, Image 2, say what each is, and refer to them by number. Image 1 is always the product — the hero of the ad. Any images after it are alternate angles, props, or a brand logo for the same product, never separate products; let alternate angles inform the photography, and place a supplied logo visibly.

The finished ad must read as a real piece of paid social work, not a template fill: a photorealistic product that reads as the photographed item, a designed layout, and every rendered text element crisp and legible at mobile feed size.
