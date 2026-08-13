---
name: generating-ad-videos
description: Makes a product ad video — a product showcase with no one on screen, or a story or lifestyle commercial where a presenter or actor plays a role in the brand's spot, with or without a voiceover. Use when the user wants a product ad, commercial, TV ad, brand film, or product-hero video. Not for a creator or customer sharing their own take on a product, like a review, unboxing, try-on or testimonial — that is generating-ugc-videos; not for a video with no product being sold — that is generating-videos.
license: Apache-2.0
metadata:
  version: "0.3.0"
  category: creative
  summary: "Produces a polished, cinematic product commercial in your brand's voice — a no-actor product showcase or an actor-led story ad, at any length. It storyboards every clip to hold your real product identical across cuts, writes the voiceover and casts the actor when the ad calls for one, then stitches it into one ready-to-run spot you approve step by step before anything expensive renders."
---

# Product ads

Turn a product into a finished commercial video. One flow, with two optional steps: a voiceover (on by default) and an actor (only where a person is on camera).

## Workflow

**The ad runs on `seedance-2.0-fast` unless the user named a model, and is delivered `9:16` unless the user explicitly asked for another ratio.**

### Step 1: Read what you have

- **A product image or URL** → hand it to `analyzing-products` for what the product is, how a person physically uses it, which parts open or move, and what must stay identical wherever it appears.
- **Run `image_analysis` on every image supplied**, not only the product — what each one shows, and whatever the product facts leave out.
- **What each image is for comes from the brief, not from its contents.** A person in a frame does not make it the presenter, and a second object does not make it a prop.
- **No product** → don't guess at one. It becomes the first thing Step 2 asks for.

### Step 2: Interview

**Skip this when the brief already settles the ad** — a clear product, a clear intent, a length.

Otherwise ask once, bundled into a single message, always with a free-text way out.

| Ask | When |
| --- | --- |
| **The product** — a link or a photo | Neither was supplied. Offer to wait for an upload; a photographed product beats a described one. |
| **How long** | The brief doesn't say. Offer 15s, 30s, 45s or 60s, and let them type their own. |
| **Whether a presenter or actor is on camera** | The brief doesn't say whether a person appears in the ad. |
| **Whether a voiceover carries it** | The brief doesn't say. The default is yes — a voiceover over the picture; they can pick music and effects only. Any words are always a voiceover, never spoken on camera. |

When the user waives questions, take 15s, no actor, a voiceover on, say in one sentence what you took, and keep going.

### Step 3: Write the product description

Write one description and reuse it unchanged in every storyboard — rephrasing it between calls reads as a different product.

- **Material and finish**, surface by surface — matte or gloss, brushed, woven, translucent, or whatever this one actually is: *"brushed steel barrel, matte soft-touch collar, a woven wrist strap"*.
- **Size** — its width and height, and how it sits against a hand: *"sits in a closed palm, roughly 9 cm tall and 4 cm across"*. Give the real measurements rather than likening it to another object, which the model renders inconsistently.
- **Two to five visual anchors** — features you can verify in the product image and nothing else: exact colours, the shape of a closure or handle, the gauge of a chain or strap, a surface finish, a distinguishing mark.
- **The product mechanism** — how it's built and how it works: the parts that move, how they open or close, and where anything dispenses: *"hinged lid at one end, folds back flat; the brush sits inside the cap"*.
- **What may be done with each part** — which parts are fixed to it, and the whole of what the moving ones allow. Nothing later does anything to the product that isn't on this list.

**Don't transcribe what the label says**, even where the product facts spell it out. Spelling out the printing invites the model to redraw it, and redrawn text comes back warped. The facts may name it; the description never repeats it.

### Step 4: Plan the concept

Follow the brief exactly wherever it is specific. The rest is yours to decide.

**4a. Read the craft and build the picture.** Read `references/commercial-craft.md` end to end — the angle, the register, the product-identity lock, the shots an ad never uses, the packshot and the sound. It governs every choice from here to the final frame.

**4b. Choose the angle.** Pick the angle the ad sells on, and with it whether anyone is on camera — the common ones, product-only and person-led, are in `references/commercial-craft.md`. Where the brief doesn't fix one, pick the angle that best fits the product — what it is, what it promises, and how it is best shown. The angle leads; the register, the setting and the arc all follow from it.

**4c. Fix the register and the setting.** Pick the register (`references/commercial-craft.md`) and the one setting the product lives in — a surface, a light, a palette — and hold it across the whole ad. With more than one product, decide up front whether each gets its own focus shots through the reel or they are staged together in every shot.

**4d. Decide the presenter.** Only where a person is on camera. Decide the one presenter and hold them across the whole ad, and cast them to fit the ad — the buyer the product is for, the register it's shot in, and the angle it takes: an aspirational spot wants someone the buyer wants to be, a problem-then-product spot someone the buyer recognises as themselves, a high-energy spot someone with the energy the camera chases. Fix their age, look and demeanour now; the wardrobe accent that ties them to the product is set in `references/commercial-craft.md`.

**4e. Split the length into clips.** `list_video_models` gives the clip model's shortest and longest clip. Make each clip as long as the model allows and let the leftover be the last one; where that leftover falls under the minimum, give the last clip the minimum anyway and let the ad run slightly over. On a 4–15s model: 30s is two clips of 15, 50s is 15, 15, 15 and 5, and 18s is 15 and 4.

**4f. Lay the arc across the clips.** The ad builds shot by shot, not as one held view — draw from a range of shots and keep varying them, fill the clips in order, and close on the packshot. **Never run two shots of the same scale back to back.** Where the ad is too short to hold every shot, carry fewer rather than crowding them.

- **With no one on screen** — open wide to place the product, then move through it: a couple of tight macros on different details, a hero angle that shows the whole thing, a top-down or environmental frame for scale and setting, and the packshot to close. Vary what each shot is about rather than lingering twice on the same detail. Around the middle, place **one signature shot** the ad is remembered by — a match-cut between two states, an exploded or suspended view, a slow reveal, an impact drop.
- **With a person** — a hook, the angle's middle (the problem and its turn, or the presenter with the product), a close detail shot on the product, a payoff on the result, and the packshot to close.

**4g. Write it down.** Clip 1 opens the arc, each later clip picks up the frame the one before it ended on, and the setting, palette and light hold across all of them. Every step after this reads it rather than deciding again: the register and setting, the presenter where there is one; how many clips, and how many seconds each; the shot each clip carries and where it sits in the arc; and, where the ad speaks, one line per clip of voiceover, sized to that clip's seconds.

### Step 5: Write the voiceover, if the ad has one

Most ads run on a voiceover over the picture; some run on music and effects alone. Any words are a voiceover — never spoken on camera. Where the ad speaks, trigger the `writing-video-scripts` skill workflow with a brief of what the voiceover should communicate, the concept from Step 4 — the clip durations, what happens in each clip, and a voiceover word budget of two words a second as the target and three the ceiling — heard as a voiceover over the picture, and only the claims the user supplied, used as written. 
It returns the words as text, split one segment per clip, each sized to that clip's seconds; the clip model renders them with the picture. Where the ad has no words, skip to Step 6.

### Step 6: Show the concept and wait

Nothing has been generated yet, and everything after this step costs money. Get the concept approved first.

Show, written out, in one brief, to the point message:

- **The presenter** — who they are, how they look, what they're wearing, where they are. Only where a person is on camera.
- **The product** — what it is and the look being held.
- **What's on screen in each clip** — its shot and where it sits in the arc. Keep this brief and focus on the high level concept rather than stating all small technical details.
- **What's said in each clip** — the words from Step 5, word for word. Only where the ad speaks.

Then ask whether it's right, and say plainly that they can change any of it — the setting, a shot, the register, the presenter or a line. **Expect edits.** Rewrite what they change, show it again, and keep going until they approve.

Wait for an answer. Don't cast, don't build a sheet, don't generate a clip.

Where the user has said they don't want to be asked, say in one line what you're going with and carry on.

### Step 7: Cast the presenter, if a person is on camera

Only once the concept is approved, and only where a person is on camera. **Cast the presenter once and reuse the image everywhere.** Clips are generated separately, so *"the same presenter"* in a later clip returns a different person. Skip this where no one is on camera, or where the user supplied a photo of the presenter. Otherwise trigger the `generating-ai-actors` skill workflow with the presenter from the approved concept — the same look, and wardrobe whose accent picks up or cleanly contrasts the product's colour (`references/commercial-craft.md`) — and the register the ad is going for.

### Step 8: Build the storyboards

Trigger the `generating-storyboards` skill workflow — one sheet per clip — with what happens in the clip and its seconds, which sheet this is of how many, the product image (and the presenter's where a person is on camera), the product description unchanged, that clip's script segment where the ad speaks, and the register and setting as the look. With no one on camera the sheet holds only the product and its world. Panels are worked out there. The sheet is always `16:9` with vertical panels, whatever ratio the ad delivers in.

**Once every sheet is built, show them all in one message and wait.** Ask whether to go ahead with the video production, and ask them to check the product in particular — that it is rendered right in every panel it appears in. They can change any panel: rebuild only the sheet that panel is on, show it, and keep going until they approve. Where the user has said they don't want to be asked, say in one line what you're going with and carry on.

### Step 9: Write the prompts

Trigger the `writing-video-prompts` skill workflow with: one prompt per clip, the chosen model, that clip's duration and the panels of its sheet, the product description carried in unchanged, that clip's script segment where the ad speaks, and the media — the sheet from Step 8, the product image, and the presenter's image where a person is on camera. Where the ad speaks, the lines are voiceover over the picture, never lip-synced.

It returns the prompts as text and the order it labelled the media in. Nothing is generated there.

### Step 10: Generate

Call `video_generate` with a `requests` list, one object per clip, all in the same call so they render at once.

- Per object: the `prompt` from Step 9; the media it labelled, passed as `reference_images` in the order it labelled them; `duration`, `resolution`, `aspect_ratio` and `generate_audio` on — the ad's sound is built, not silent. Omit `model` to use the default; set it only if one was chosen.
- Every clip uses the same aspect ratio and resolution.
- A clip can come back as `{status: "pending", …}` — a job handle, not a failure. Pass that exact handle to `job_status`, and again if it is still pending. **Never re-run a pending clip**; that starts a second billed job.

### Step 11: Stitch and return

Wait until every clip has finished, collecting any `pending` ones with `job_status` first. Then pass them in order to `video_stitch`, which joins them with a hard cut between each and keeps each clip's audio. Where the user wanted a music bed over the whole ad, pass it to `video_stitch` too. Don't join them by hand.

A single clip needs no stitching. Return the finished ad's URL and local file path, and the individual clips if the user asks for them.

## Edge cases

**Never regenerate a clip without the user asking.** Every re-run is billed again. Hand back what came out, say what looks wrong, and wait — including in the cases below.

- **No product supplied, and the user wants to proceed anyway** — an ad for an invented product, held consistent across every clip, is worse than stopping. Ask for the product first.
- **A sheet comes back wrong** — remake only that sheet. Sheets are cheap; a clip made from a wrong sheet is not.
- **One clip in the batch fails while the others succeed** — send a new call with only that request. Re-running the whole list bills every clip again.
- **A clip doesn't match its sheet** — hand it over and say what looks off. Whether it's close enough is the user's call.
- **A safety filter rejects the presenter twice** — usually the person. Say which element is blocked so they can be recast, rather than retrying blind.
- **The user changes something after approving the concept** — redo from the earliest step the change touches. A different presenter or setting means new sheets and new clips; a different shot means only that clip's sheet and prompt; a different line means only the script and that clip's prompt.
- **`video_stitch` isn't available** — return the clips in order and say they aren't joined.
- **The brief is a general video, b-roll, or a photo to animate, with no product being sold** → `generating-videos`. **A creator or customer sharing their own take on the product** — a review, unboxing, try-on or testimonial → `generating-ugc-videos`. Route out rather than forcing it into an ad.
- **`error: "no_provider_configured"`** on any tool → relay the tool's `hint` (the user must set their key).

## Reference

- `references/commercial-craft.md` — the shared craft, read at the concept and held to the final frame: the register, the product-identity lock, on-screen text, the screen-lock, wardrobe and palette, the shots an ad never uses, the packshot, and how the sound is built.
