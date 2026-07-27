# Prompt guide — seedream-4.5

Strong at holding a face's identity from a reference photo, compositing several references into one
image, placing a product into a scene, and carrying text from one image to another. A prompt is
always required, even when editing with references.

## Writing the prompt

Address supplied images by figure number in `image_urls` order (`Image 1` upward) to move an element or text between them. Ten maximum; extras dropped.

- **Subject** — the focal point. for face preservation.a
- **Action or pose** — what it is doing.
- **Setting** — where it sits and what surrounds it.
- **Style** — the artistic or photographic treatment.
- **Lighting and atmosphere** — mood, which this model tracks closely.
- **Camera** — lens, perspective, framing.
- **On-image text** — the exact string in quotes, its placement, a legibility cue; keep it short.
- **Constraints** — what to hold fixed or leave out (e.g. keep the background, keep the original lighting).

When editing, write a command, not a description of the result: name the exact target and state what must stay unchanged.

Best when a subject must hold its identity across scenes.

- Lead with what matters most; earlier concepts weigh more.
- Aim for 30–100 words of description, not keywords.
- No `negative_prompt` field; phrase exclusions inside the prompt.

