# What gets drawn

An asset is anything the story comes back to and that has to look the same each time. It is drawn once
and then passed into every clip that needs it. Anything the story touches only once is not an asset — it
gets described where it appears.

## What this step produces

Two pieces of text per asset, doing different jobs.

**A label** — one short noun phrase that stands for the asset everywhere it is mentioned afterwards: in
the cut list, in the clip prompts, and in the plan shown to the user. Build it from whatever tells the
asset apart at a glance, and keep it to fewer than five words.

> *the cook in green* · *the tiled bathroom* · *the dented copper pot*

Write it once and reuse it **word for word**. A label that drifts — the cook, then the chef, then the
woman in green — reads as three different things to the model. A character's label is always a
description and never a name, for the same reason: a name makes the model invent a face, and a
different one on each call.

**A design** — the full description, used once, in the prompt that draws that asset. Everything under
the asset's own heading below belongs here. It is not repeated afterwards; once the image exists it is
doing the work, and the label stands in for it.

## How every asset is drawn

These hold for every asset, so there is nothing to settle case by case:

- **`1:1`**, the subject alone, centred, on a plain flat single-colour background. No scene, no surface,
  nothing belonging to another asset. **Places are the one exception** — they are whole frames rather
  than isolated subjects, so they take the delivery ratio.
- **One view only.** Whatever side it shows is the only side that exists.
- **Nothing written anywhere** — no text, no watermark, no caption, no colour samples. The only lettering
  allowed is printing the real product already carries.
- **The style brief pasted in word for word**, and the style sample attached as a reference.

## The shape of an asset prompt

Every asset prompt runs in the same four parts, whatever it is of:

1. **How it sits in frame** — the framing and the background, first. *A single character, full body,
   centred on a plain flat single-colour background.*
2. **The style, named as exact** — say the asset is rendered in this exact style, then paste the style
   brief in word for word.
3. **The subject** — the asset's design, in its own sentence after the style.
4. **The tail** — nothing written anywhere, no watermark, no colour samples, and nothing belonging to
   another asset in the frame.

The framing goes before the style, and the style before the subject. A prompt that opens on the subject
and mentions the look at the end comes back as a picture of the thing that happens to be stylish, rather
than the thing drawn in this production's style.

## The reference order, and how many a clip can take

Every clip's `reference_images` list runs in this order, and the clip prompt names them in the same
order, each by its label:

> **place → characters → product → other props**

The clip prompt names the images in this order too. Name them in a different order than you pass them
and the model reads the wrong image into the wrong role. Lists come out different lengths because clips
hold different assets; the order holds regardless.

**Seven images is the most a clip can take.** Where a clip needs more, in this order of preference:

1. **A recurring prop moves into the clip prompt as description**, which costs no slot.
2. **The beat splits across two clips.**
3. **A character drops out of that clip** — out of the clip, not out of the video.

The place and the product never drop.

## Characters

**How many.** One is ideal, and two is the maximum for characters who move or act. Past that the model starts
miscounting people and drawing near-duplicates, and each one uses up a reference slot.

**The design.** Full body, standing, described head to foot:

- Build, height, face shape, hair and its colour, the clothes and their colours, and anything they
  always carry. Anything left out gets invented, and invented differently next time.
- **Empty-handed.** The product arrives in the clip as its own reference.

**The label.** Take it from whatever tells this character apart *structurally* — silhouette, build or
colour, not a small detail a viewer has to hunt for. That is also what keeps two characters apart in a
clip prompt, so it has to work at a glance and in fewer than five words.

### The two chains

Some characters need an existing asset attached as a reference, not just the style sample. There are two
cases, and both mean that asset can't be drawn until the one it depends on exists.

- **Across the cast** — the second character takes the first as a reference, so their proportions match.
  Without this, two characters drawn from the same style brief come back built differently and stop looking
  like one production.
- **Across a change** — where a character appears altered (older, wet, in different clothes,
  mid-transformation), the variant takes the original as a reference, with the change named. The style
  sample on its own will not hold a face. Each variant gets its own label, and only the right one goes
  into each clip.

## Places

**A place is somewhere the story comes back to, or somewhere that has to look specific.** If a clip is
set somewhere the video never returns to, and it doesn't need to look like anywhere in particular,
describe it in that clip's prompt instead.

**How many.** One per place the story visits — count them in the story, not in the clips. At the lengths
this skill works at that is usually one, and rarely more than two. Where the video spends most of its
length in a single place, a second angle of that place stops every return looking like the same framing.
It is a separate asset and counts as one.

Each place is:

- **Framed wide, and empty of people.**
- **A dressed room, not an empty box.** Say what is in it, where the light comes from, and the time of
  day.
- **Given one named anchor object** — a particular chair, a window, a hanging shape, a block of colour.
  It is described word for word in every clip set there, so the place is recognisable on return.
- **Free of writing.** No signage, no menus, no posters, no printed packaging. Anything written into a
  place comes back in every clip built on it.

## The product

Two modes, settled in the interview after the look. **Only one of them draws anything.** Either way the
product is a prop, not a character. It gets handled, worn, opened and looked at. The cast acts.

### Kept as photographed

**No asset.** The real photo is the product reference in every clip, in the product slot of the order
above.

The clip prompt has to name it as a real object, placed in the scene at the scene's own scale and
lighting, and never redrawn to match the look.

### Drawn into the look

**One asset**, generated from the real photo with the style sample alongside it.

The prompt names what has to stay the same, or it won't: the silhouette, the proportions between its
parts, the exact colours, the shape of any closure or handle, and where anything printed sits. All of
that comes from the product description.

**Only how it is drawn changes, not what it is.** Nothing is added, removed, simplified or given a face,
and nothing moves that the product description doesn't say moves.

### In both modes

**Leave the printing alone.** Keep its position, shape and colour, and never write out what it says.
Spelling out the lettering makes the model redraw it, and redrawn text comes back warped.

## Other props

Draw a prop only where an object appears in more than one clip and has to match — a vehicle, a sign,
something that gets handed over. Anything that appears once goes in that clip's prompt instead, which
saves an asset and a slot.
