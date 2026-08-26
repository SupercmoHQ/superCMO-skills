# The production palette

How to pick the skill that builds each concept. **This is a routing table, not a filter.** It runs
after the concepts are written, and its job is to tag each concept — never to remove one.

**Route using this file alone.** The table below carries everything routing needs. Don't open a
producer skill to check what it can do, and don't trigger one — a producer skill is read later, by
whoever builds the ad, after the user approves the plan. Routing only writes a tag; nothing is
generated.

## The producers

| Skill | What it makes | What it needs |
| --- | --- | --- |
| `generating-ugc-videos` | a creator or customer on camera as themselves — review, unboxing, try-on, tutorial, talking head | product photo or URL; a length |
| `generating-ad-videos` | a produced spot in the brand's voice — product showcase with no one on screen, or an actor playing a role | product photo or URL; a length; whether anyone is on camera; whether a voiceover carries it |
| `generating-cartoon-videos` | a drawn, animated, anime or illustrated spot | product photo or URL; the art style |
| `generating-image-ads` | a static ad — one image or a set across ratios | product photo or URL; the offer and the claim; the placement |
| `cloning-video-ads` | a specific reference ad rebuilt around this product, keeping its structure and pacing | the reference video itself; the product |
| `generating-product-photos` | commercial product photography — packshots, lifestyle, on-model | product photo or URL |
| `generating-videos` | any video a concept can describe, across the full model range | the concept |
| `generating-images` | any image a concept can describe, across the full model range | the concept |

## Routing a concept

Read the concept and decide what has to exist on screen. Then work down these four moves:

1. **Match the concept to the most specific producer built for it.** The questions that decide:
   - **Whose voice is it?** A creator sharing their own take → `generating-ugc-videos`. The brand
     presenting → `generating-ad-videos`. What matters is whose voice it is, not whether a person
     is on camera.
   - **Does one image and its words carry the whole argument?** → `generating-image-ads`.
   - **Is the look drawn rather than filmed?** → `generating-cartoon-videos`.
   - **Does it rebuild a specific ad the user has?** → `cloning-video-ads`.
   - **Is it a clean product shot with no ad message?** → `generating-product-photos`.
2. **Fall back to the general generators only when no specialist fits.** `generating-videos` and
   `generating-images` can build anything a concept can describe, so every concept can still be
   routed — but they are the last resort, never a shortcut past a specialist built for the job.
   Tag the concept to the general generator for its medium, and note on the tag that it will be
   generated from the concept alone rather than through a specialist pipeline.
3. **Keep some concepts out of the pipeline entirely.** When being real is part of the claim — an
   actual customer giving their testimony, the founder speaking for themselves, footage of a real
   event, etc. — a generated version changes what the ad says, no matter how good it looks. Tag the
   concept **outside the pipeline**, say how it would actually get made — a phone shoot, real
   customer footage, a photographer — and keep it in the plan, ranked on merit like any other. A
   strong idea the pipeline can't honestly render is still a strong idea.

**A person on screen does not automatically put a concept outside the pipeline.** If the user has a
photo of a real person, the AI producers take it as a reference image and keep that face consistent
across the ad. If there is no photo, the person is generated. The deciding question is authenticity:
generate when the person is playing a role, and go outside the pipeline when the ad claims the
footage is real.

## The rule

**Route, don't reject.** Every concept leaves this step with a tag: a specialist skill, a general
generator, or outside the pipeline with a note on how it would get made. Where a fit is loose, say
so on the tag, so nobody is surprised at production time.
