# Board craft — writing one storyboard prompt

Build a single **storyboard sheet**: one wide image whose vertical slots each hold one photoreal,
iPhone-style moment. Slots read left to right as a story — first slot opens, last slot closes. These
rules are format-agnostic; the mode pack sets the slot count and arc.

**Model:** `gpt-image-2`. **Aspect:** `16:9` (gives the wide sheet).

```
image_generate(requests=[{
  "prompt": "<the sheet + per-slot description you write>",
  "model": "gpt-image-2",
  "aspect_ratio": "16:9",
  "reference_images": [<in supply order — see below>],
}])
```

## Reference images (by supply order)

Address references by the order passed to `reference_images`, named in the prompt as `image_0.png`,
`image_1.png`, `image_2.png`. **Never use any other naming.** Supply order is fixed: **product →
creator portrait → previous board** (previous board only from the second board on). Drop any that
don't apply and indices shift up:

| What you have | image_0 | image_1 | image_2 |
| ------------- | ------- | ------- | ------- |
| product + creator + previous board | product | creator | previous board |
| product + creator (first board) | product | creator | — |
| creator + previous board (no product) | creator | previous board | — |
| creator only | creator | — | — |

When a previous board is supplied, the prompt must explicitly carry its identity, location, lighting,
wardrobe, and product forward from that image.

## Build the prompt (in this order)

The mode pack fixes the slot count and each slot's beat. Assemble the prompt string in this order,
drawing on the rules in the next section:

1. **References first.** Name `image_0.png` (product + angle-lock note, if present), then the creator
   reference, then the previous-board reference (if any) with the "preserve identity / location /
   lighting / wardrobe / product" instruction.
2. **Identity line** — the same person appears in every slot, identical features, no drift.
3. **Sheet line** — the wide landscape sheet of equal vertical slots, thin white gutters, white
   background, all slots active, telling one continuous [DURATION]-second story, no placeholders.
4. **Global setting / lighting / outfit** — inherited defaults, identical outfit within a location.
5. **Global product line** (if a product is present) — real-world scale and the three-state
   clean-placement rule.
6. **Global hand / POV line** — the two-hand rule, selfie vs tripod, POV changes as hard cuts.
7. **Per slot**, in order: framing/distance, selfie or tripod POV, character action, product
   placement, explicit hand allocation, micro-behaviour, and a light/setting note. Keep each slot's
   action, distance, and (where useful) POV distinct from the others.
8. **Rendering-rules block** — the hard restrictions below, phrased as constraints.

## Rules for each part

### Product understanding — four modes

Read the product before writing slots. Mode depends on what was provided:

- **Image + description** — use both: description names it, image locks how it looks.
- **Image, no description** — read the image: category, container material, applicator type, how it's
  used, visible detail, real-world size, and any actions unsafe for it.
- **Description only, no image** — work from text; no angle to lock, so keep interaction to
  hold-and-present.
- **No product at all** — lifestyle / talking-head board (testimonial mode); skip all product rules.

### The character is fixed — never re-describe

The creator arrives as a reference image and is **never** described in words — no age, ethnicity,
looks, makeup, or facial features. State that **the same person from the reference appears in every
slot**: identical face, hair, body, proportions, identity, with no drift. Outfit defaults to what the
reference (and previous board, if any) shows, and stays identical across slots within one location.

### Setting & lighting

- **Default: inherit.** Every slot uses the same environment, time of day, and light direction shown
  in the creator reference (and previous board, if supplied).
- **Fallback by category** when the reference is unusable or absent:

  | Product category | Default location |
  | ---------------- | ---------------- |
  | Cosmetics / makeup / fragrance | a bathroom or a bedroom |
  | Skincare / haircare / body care | a bathroom |
  | Food / beverage / kitchen | a kitchen |
  | Protein / supplements / sports nutrition | a home gym, or a kitchen |
  | Clothing / accessories / jewelry | a bedroom or a walk-in closet |
  | Fitness gear | a home gym or a workout corner |
  | Cars | a driveway, a sunlit road, or a garage |
  | Outdoor / sunglasses / sunscreen | an outdoor café, a park, or a bright street |
  | Tech / electronics | a desk at home, a living room, or a small studio corner |
  | Home / decor | a living room or a bedroom |

- **Lighting fallback:** soft, neutral daylight from one clear direction (a window on the left or
  right). **Never golden hour or warm sunset** unless the user asks, and never harsh studio strobes.

### Slot variety — actions and distances

Every slot must be visibly different from every other. Mandatory, not stylistic.

- **Different actions.** Each slot shows a genuinely different physical action. Same pose with a
  micro-tweak does not count — rewrite it. Same hand holding the same object in every slot is also a
  rewrite.
- **Different camera distances.** The set of slots must span three distance bands:
  - **Tight** — tight close-up / macro (face dominant, or hands + product filling frame)
  - **Mid** — medium close-up / medium
  - **Wide** — three-quarter / waist-up / full-body wide / product-extended

  If every slot lands in the same band, rewrite.

### Camera POV & the two-hand rule

The character has **exactly two hands**. POV decides how many are free:

- **Selfie POV** — one hand holds the phone (off-frame or just visible at the edge). Only the **other**
  hand is free. Never depict two objects held in selfie POV.
- **Tripod POV** — phone not in frame, **both** hands free.

**Any action needing two free hands forces tripod POV.** POV may change slot to slot, but **every POV
change is a hard cut** — never a smooth transition. No third arm, no extra hand, no impossible grip.

| Situation | POV |
| --------- | --- |
| on the move outdoors, hands empty | selfie |
| on the move outdoors, carrying one bag | selfie (bag in the free hand) |
| on the move outdoors, a bag **and** a product on show | not allowed — stow the product in the bag (selfie), set the bag down, or switch to tripod if both must be seen |
| indoors, holding the product while speaking | selfie or tripod |
| indoors, popping a cap / turning a dropper / pumping | tripod |
| indoors, applying to skin, lips, or hair while still holding the bottle | tripod |
| a palm-level close-up of the product | tripod, close in |
| a reaction, grin, or CTA with the product in one hand | selfie or tripod |

Include this constraint verbatim in the prompt: *the character has exactly two hands; in selfie POV one
hand holds the phone so only one hand is free — never two objects in selfie POV; two-handed actions
must be tripod POV with the phone out of frame; every POV change aligns with a hard cut; no third arm,
no extra hand, no impossible grip.*

### Safe interaction verbs by material

Match the verb to what the container can survive. When unsure, **hold-and-present only.**

| Material | Safe | Forbidden |
| -------- | ---- | --------- |
| Glass / hard plastic / metal | balances on an open palm, keeps a light grip, cups it, holds it up to show, taps it softly, gestures toward it | squeezing, crushing, gripping hard enough to dent, wringing the body, warping it |
| Soft tube | keeps a loose hold, gives a gentle press, dabs lightly | mangling, wringing out, twisting hard |
| Fabric / clothing | puts it on, tugs it into place, runs a hand to flatten it, lets it hang, lifts it up | pulling it out of shape, jerking at it, wringing |
| Cardboard box | grips it by the edges, faces the front toward camera, lifts an existing flap | flattening, folding against the grain, buckling, tearing |
| Food | takes a bite, pours, spoons out, mixes, plates it | tossing, juggling, warping, cloning |
| Tech / electronics | holds it, angles it to camera, indicates a screen or feature | prying open panels, connecting cords |
| Any product | holds, displays, raises, offers to camera, points to it | tossing, snatching from the air, juggling, twirling, letting it fall |

### Product angle-lock & real-world scale

**Angle lock** (whenever a product image is supplied): show only the side visible in the reference, and
keep that same side in every slot the product appears in. It may move closer or farther, but the
visible face stays consistent. Never invent back labels, side panels, or internal parts. Camera
movement is not product rotation.

**Real scale.** The product appears at its true physical size relative to the hand and body. If the
label is too small to read, **move the camera closer — never enlarge the product.** Put this in the
prompt: *the product is rendered at realistic real-world scale relative to the hand and body,
approximately [X cm], fitting naturally in the hand without enlargement; if the label is small, the
camera moves closer rather than scaling the product up.*

| Product | Real size |
| ------- | --------- |
| Perfume / EDP (50–100 ml) | ~10–12 cm tall, sits in a single palm |
| Cologne (large, 100–200 ml) | ~13–16 cm tall |
| Serum dropper (30 ml) | ~8–10 cm tall, spans a few fingers |
| Cream jar (30–50 ml) | ~6–8 cm across, rests on the palm |
| Soft tube (cream, lotion) | 12–18 cm end to end |
| Lipstick / twist-up balm | 7–9 cm tall |
| Mascara / lip-gloss tube | 10–12 cm tall |
| Pump bottle (250 ml lotion / shampoo) | 18–22 cm tall, a two-handed grip reads as natural |
| Compact / powder | 7–10 cm across, tucks into the palm |
| Spray bottle (mist, body spray) | 15–20 cm tall |
| Energy drink / soda can | ~12 cm for a standard can, ~16 cm for a slim one |
| Snack bag (single serve) | 15–20 cm tall, about hand height |
| Tech (phone-sized device) | judge it against a nearby smartphone |

### Product placement & visibility

The product is visible in a slot **only if that slot's action needs it.** Show/present/interact beats →
fully visible. Transit, setup, problem, or talking-head beats → hidden or absent. A final reaction/CTA
with no product → the product may be absent.

Every appearance is one of exactly three clean states — **never partial:**

1. **Fully hidden** inside a closed bag / box / pocket — not visible at all.
2. **Fully visible**, held cleanly in one hand, vertical, full grip — the whole product, not inside a bag.
3. **Absent** from the frame.

**Forbidden** (state this in the rendering rules): jutting halfway out of a bag, perched on the rim of
an open bag, jammed between other objects, hovering unsupported, poking out of a pocket with its cap
showing, or half-seen inside a box.

### Product interaction sequences

Every interaction uses exact, visible hand mechanics — never vague "opens it / uses it / applies it."

| Product | Sequence |
| ------- | -------- |
| Perfume / cologne | grip the base → draw the cap straight off → cap gone → depress the sprayer → fine mist onto wrist or neck |
| Serum dropper | steady the bottle → twist the dropper open (counterclockwise) → raise the pipette clear → pinch the bulb → droplets onto fingertips |
| Cream jar | steady the base → unthread the lid (counterclockwise) → lid gone → dip a fingertip in |
| Soft tube | grip the middle → flip up or unthread the cap → a gentle press → a dab lands on a fingertip |
| Pump bottle | steady the base → push the pump down with two fingers → product pools on the palm |
| Lipstick / twist-up balm | grip the base → pull the cap straight off → cap gone → wind the base up → glide across the lips |
| Mascara / lip-gloss wand | grip the tube → unthread the wand → withdraw it slowly → apply |
| Compact / powder | hold the compact → open the hinged lid (it stays joined) → load the brush or sponge → apply |
| Spray bottle / mist | hold the bottle → take the cap off if there is one → squeeze the trigger or nozzle → mist |
| Food / drink | present the packaging → open it where believable → pour, spoon, bite, or sip as fits |
| Clothing / shoes | raise it up → put it on → settle the fit → smooth the fabric → indicate one detail |
| Tech / electronics | hold it up and present; point out a screen or an exterior feature; skip fiddly buttons and cables |

General rules: **at most one product state change per slot**; a removed cap or lid disappears after
removal; two hands maximum; any two-handed step forces tripod POV.

**Cross-board continuity (second board onward):** if the previous board's last slot left the product
open (cap off, applicator extended, lid flipped), this board keeps it open — never re-close a product a
prior board opened. Applies only to cap/lid/applicator state; outfit, location, and lighting continuity
are handled by the setting and rendering rules.

### Human performance — energy and micro-behaviour

**Default register is high-energy / hyped** — explosive expressions, mock-shock, big enthusiasm. Switch
to a calmer register only when the brief signals a calm aesthetic (cues such as goth, vampire, noir,
cold, deadpan, clinical, refined, minimal, somber, or otherwise dark/passive styling). Read the four
registers as a shape from the opening slot to the closing slot:

- **High-energy (default):** open on a big, mouth-flung-open gasp that lands right on the
  product/action; keep the intensity pinned through the middle (fists tight, no easing off); close on a
  huge grin, a burst of laughter, or a head-back triumphant recommendation.
- **Warm / restrained:** open on a curious, low-key note; grow lively and locked onto the action;
  finish warm, pleased, and self-assured.
- **Dry / cool:** open on a straight-faced, deadpan look into the lens; crack partway through with a
  grin or a laugh; wrap loose and easy on a quick grin.
- **Passive / restrained (calm briefs):** open flat and calm, eyes half-lowered, no burst; keep
  reactions small and movements slow and deliberate through the middle; end on a faint half-smile or an
  even, neutral close.

**Micro-behaviour menu** — draw on beats like the ones below (and invent your own in the same spirit),
and **never repeat the same beat across slots:**

> for example — leaning in toward the lens, dropping the eyes then flicking back up, a raised brow, a
> cocked head, a quick hand gesture, a shoulder roll, tucking hair back, a fast grin, a pleased sigh, a
> little nod, an offhand laugh, jabbing a finger at the product, pushing the product nearer the lens, a
> tap on the label, a shift of stance, a beat of stillness before a reveal, a wide-eyed fake gasp,
> mouth caught open mid-"wait", jaw dropping on the hook line, a flat unblinking stare down the lens, an
> eye-roll that snaps back into a grin, a startled jerk of the head, a tucked chin under a lifted brow,
> a puzzled squint, cheeks puffed mid-reaction, lips pinched into a mock chef's-kiss, brows flying up, a
> mid-bite expression for food or drink, a thumb wiped at the corner of the mouth.

Avoid as a slot's **only** descriptor: "smiles at the camera," "looks at the camera," "holds product
and talks," or the same expression in every slot.

### iPhone UGC visual style (every slot)

Each slot is a photoreal iPhone still: natural light, slight phone-camera grain, real skin texture, a
real home / everyday setting, and slightly imperfect framing. No studio lighting, no glossy retouching,
no cinematic lens, no mirror shots unless the user asks.

### Sheet layout

Describe the sheet as: **one wide landscape storyboard sheet of equal-size vertical slots in a single
left-to-right row**, separated by thin white gutters on a clean white background. Every slot is an
active photoreal iPhone still; they read as one continuous story across the clip (first slot = opening
moment, last slot = closing moment). **No placeholder slots, and no header, footer, caption, or chrome
of any kind.** The mode pack tells you how many slots and which beat each carries.

## Hard restrictions

- Never describe the character's age, ethnicity, attractiveness, makeup, or features beyond what the
  reference supplies.
- Never deviate from the slot count and per-slot arc the mode pack sets.
- Never make slots different sizes from each other, or depart from equal tall vertical slots.
- Never leave a slot as a placeholder — every slot is active.
- Never put text, a header, metadata, a caption, a badge, a number, pop-text, a subtitle, or a
  watermark on the sheet.
- Never invent unseen sides of the product when a product reference is supplied.
- Never enlarge the product past its real-world size — move the camera closer instead.
- Never show the product half-sticking out, balancing awkwardly, peeking partially, wedged, or floating.
- Never show more than two hands. Selfie POV = one phone-hand + one free hand; two objects in selfie POV
  are forbidden — switch to tripod.
- Never use mirror or reflection shots.
- Never use unsafe or physically impossible product interactions.
- Never invent legal, medical, certification, or superiority claims about the product.
- Never include unrelated real-world brands or IP.
- Never ignore a user-specified setting, action, or duration.
- Never change the outfit inside a single location.
- Never force the product into the first slot — the first slot is the opening moment; the reveal lands
  wherever the story delivers it.
- Never break the previous-board match (second board onward) unless the story explicitly demands a
  location change.
