---
name: adapting-formats
description: Resizes an existing image ad into the other shapes it has to run in — reads the ad first, then regenerates it at each ratio with the original passed in as a reference, so the product, the copy and the look carry across. Each shape is recomposed rather than cropped, with the background extended into the space the new proportions open up and the headline and call to action kept clear of the buttons and captions the platform draws over the top. Use when the user has an ad and needs it in another size, in a ratio family, or in every size a channel takes. Not for making an ad that does not exist yet — that is generating-image-ads; not for writing the words of the ad — that is writing-ad-copy.
license: Apache-2.0
metadata:
  version: "0.3.0"
  category: creative
  summary: "Takes an ad you already have and remakes it in every other size you need it in. It reads your ad first, works out what has to move and what fills the space the new shape opens up, and shows you that plan before it spends anything — then rebuilds each shape around the original so your product, palette and wording stay recognisably the same rather than being stretched, cropped or letterboxed into a mess."
  related-skills: "generating-image-ads, writing-ad-copy"
---

# Resizing an ad

Take an image ad that already exists and produce it in the other shapes it has to run in.

**Each shape is regenerated, not cropped.** A crop cuts the headline in half and pushes the product out
of frame; the ad is rebuilt for the new proportions with the original passed in as a reference, so it
stays the same ad rather than becoming a different one.

## Workflow

### Step 1: Get the ad and the shapes

- **The ad** — the image file or URL, at the largest version the user has. Without it there is nothing
  to resize; ask for it and stop. Several ads at once is normal: each is read and planned separately,
  though they can all be generated in one call at the end.
- **The shapes** — the ratios, or the channel they run on. Where the user named a channel rather than
  ratios, take them from `references/ratios-and-safe-zones.md`. Where neither is given, ask which sizes
  they need, offering that table's channels and a free-text way out.
- **The product photo, where they have one** — a clean shot of the product on its own. It is worth
  asking for: the ad may show the product small, angled or partly behind copy, and the photo holds its
  identity far better than the ad can.

**Drop the shape the ad is already in.** An ad supplied at `1:1` and asked for the Meta family needs
`4:5` and `9:16` — regenerating its own `1:1` bills for a reconstruction of something the user already
has.

### Step 2: Read the ad

Run `image_analysis` on it once, and separate what the ad is made of — the parts a resize moves, not a
description of the picture:

- **The product** — what it is, and whatever has to stay identical wherever it appears: its shape,
  colour and label, the text printed on it, or anything else that would give it away as redrawn.
- **Every drawn string** — captured word for word, wherever it sits: a headline, a support line, a call
  to action, a price or a badge. These are regenerated, so a word read wrong here is a word wrong in the
  ad.
- **The background** — the surface, the scene, the light direction and the perspective, since this is
  what gets extended into any new area.
- **The look** — the palette, the character of the type, and whatever else makes it read as this
  brand's ad.
- **The layout** — what the eye lands on first, and how the parts sit relative to each other.

Take what this ad actually has rather than working down the list; an ad with no call to action doesn't
need one invented for the reading.

Read it once. A second analysis call bills again and tells you what you already have.

### Step 3: Plan each new shape

Read `references/recomposing.md` first — it owns this craft: what grows, what moves, what fills the
space that opens up, and the things that mark an ad as repurposed.

For each shape, decide and write down:

- **How far it is from the original.** A `1:1` into `4:5` is a nudge. A `1:1` into `9:16` is a real
  recomposition. A vertical into `16:9` or `21:9` inverts the frame and keeps very little — close to a
  new ad than a resize, and worth saying so before it is generated rather than after.
- **What fills the new area** — normally the background extended in keeping with its own light and
  perspective, plus deliberate negative space around the product. Never a new element invented to fill
  it.
- **Where each part goes**, including which part had to move out of the band the platform covers.
- **Whether the copy still fits.** The `9:16` safe area is roughly the middle half of the frame, so a
  copy-dense square ad often cannot move into it at a readable size. **Say that; don't shrink the type
  until it fits.** The answer is fewer words, and that is the user's call, not this skill's.

### Step 4: Show the plan and wait

Nothing has been generated yet, and everything after this costs money.

In one short message: the shapes being made, what fills the new space in each, anything significant
that had to move, and anything the shape can't carry — copy that won't fit, a ratio far enough from the
original that little survives. Then ask, and wait.

Where the user has said they don't want to be asked, say in one line what you're going with and carry
on.

### Step 5: Choose the model

**One model for every shape**, so the set comes back looking like one campaign rather than three ads.
A resize redraws every string the ad carries, so how well a model holds text is usually what decides it.

| Model | Use it when | How it wants the prompt |
| --- | --- | --- |
| `gpt-image-2` | the ad is a designed, text-forward layout — a headline, an offer, callouts | short labelled segments on separate lines, every string quoted exactly |
| `nano-banana-pro` | the ad leads on a photoreal product or a person and carries lighter text | connected sentences in one narrative paragraph, the drawn copy quoted |
| `seedream-5` | a photoreal ad another model refused or keeps failing | a description leading with whatever matters most |

Most ads carry real copy, so `gpt-image-2` is the usual choice. Where the user has named a model, use
that instead. Call `list_image_models` for what is actually available and for each model's
`reference_images` limit rather than assuming this table is the whole roster.

### Step 6: Write each shape's prompt

One prompt per shape, built from Step 2's reading and Step 3's plan, written in the shape the model
wants. Hold the product, the palette, the type and every drawn string identical across them — **only
the arrangement changes.**

- **State the new arrangement** — where each part sits in this shape, what the background extends into,
  and where the negative space falls. Say it as regions of the frame rather than leaving the model to
  infer it from the reference.
- **Keep the copy out of the platform's furniture.** Take the margins from
  `references/ratios-and-safe-zones.md` and state them. Margin cannot be added to a finished frame, so
  this is the one thing that cannot be corrected afterwards.
- **Quote every drawn string exactly**, in single quotes, with its size and position against the
  others.
- **Say the product is the one in the reference** and reaches the image unchanged — its shape, colour,
  label and printed text as they are.

### Step 7: Generate

Call `image_generate` with a `requests` list, **all of them in the same call** so they render at once.

- **One object per shape** — `prompt`, `model`, `aspect_ratio`, `resolution`, `reference_images`.
- **The original ad goes in `reference_images` every time**, and the clean product photo alongside it
  where the user supplied one. They carry the product, the palette and the type; the prompt alone will
  not.
- **`resolution` is `1k`** unless the user asked for a higher tier — raise it where the ad is dense with
  small type, which is where the extra pixels actually show.
- **The model from Step 5 on every object.** Take the accepted `aspect_ratio` values from
  `list_image_models` rather than guessing — a wrong enum fails a billed call.
- **One image per request.** Never generate a second to compare models or to correct one you judged
  poor: every one of those bills again.

Images are polled for you, but a heavy one can come back as `{status: "pending", …}`. That is a job
handle, not a failure. Pass that exact handle to `job_status` to retrieve the finished image, and if it
comes back pending again, call `job_status` again with the same handle. **Never re-run a pending image**
through `image_generate` — that abandons the job you are already paying for and starts a second,
separately billed one.

### Step 8: Return

The image URLs and local file paths, once every shape has finished — never a partial set, and labelled
by ratio.

Say in one line what changed between the shapes and what was held, and name any shape where the plan
and the result parted company.

## Common mistakes

- Regenerating the ratio the ad was already supplied in.
- Cropping, stretching or letterboxing instead of recomposing for the new shape.
- Scaling every element up together, so the product bloats and the ad loses its composure.
- Leaving the headline or the call to action in the bottom third of a vertical, where the platform
  covers it.
- Shrinking the copy until it fits the safe area instead of saying it doesn't.
- Inventing a badge, a claim or a second product to fill the space that opened up.
- Reading the drawn copy loosely, so a word comes back changed in the new sizes.
- Letting the palette, the type or the product drift between shapes.

## Edge cases

**Never regenerate a shape without the user asking.** Every re-run bills again. Hand back what came out,
say what looks wrong, and wait.

- **No ad supplied** → ask for it. There is nothing to resize from a description.
- **The ad doesn't exist yet** → `generating-image-ads`, which makes the ad and its ratio family in one
  pass. This skill is for one that already exists.
- **Only the requested shape is the one it already is** — there is nothing to make. Say so rather than
  generating a copy.
- **A ratio no model accepts** — the accepted values come from `list_image_models`. Offer the nearest
  available shape rather than generating something that will be rejected.
- **The user wants a different product in the ad** — swapping the product, the brand or the claims for
  their own is a rebuild of someone else's ad, not a resize, and it is out of scope here.
- **The new size came back different from the plan** — a shifted layout, a redrawn label, warped type →
  hand it over and say what moved. For warped or misspelled copy, quote the strings exactly, cut the
  amount and route to `gpt-image-2`. Don't regenerate on your own judgement.
- **One shape fails while the others succeed** — send a new call with only that request. Re-running the
  list bills every one of them again.
- **The ad is a video** — a different job; this skill resizes stills.
- **`error: "no_provider_configured"`** on any tool → relay the tool's `hint`; the user has to set their
  key.

## Reference

- `references/recomposing.md` — the craft of the resize: treating the ad as parts, what grows, what
  fills the new area, going taller and going wider, and the marks of a repurposed ad.
- `references/ratios-and-safe-zones.md` — which ratios each channel takes, and the margins the platform
  draws its own furniture over.
