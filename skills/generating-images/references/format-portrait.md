# Portrait format

Use this recipe when the deliverable is an image of a person — one subject or a small group — generated fresh or refined from existing images.

## What every prompt must carry

1. **Generate intent** — open with a phrase such as "create an image of" or "generate an image of", or you may get a text answer instead of a picture.
2. **Subject** — who is in the frame. Be specific.
3. **Composition** — the frame type and the camera angle the shot is taken from.
4. **Action** — what the subject is doing at the moment captured.
5. **Location** — the setting and the environment around the subject.
6. **Style** — the overall aesthetic direction the image should read as.
7. **Context** — the purpose the image serves, not just the object to be drawn.
8. **Editing instructions** — the direct modifications to make, used when you are refining an existing image rather than generating a new one.

## How to write it

Write conversational natural language, full sentences describing mood, style and context. The prompt is interpreted as description, not matched as keywords.

Build it in layers: lay down the elements above first, then add refinements.

- **Camera angle and depth of field** — where the lens sits and how much of the frame stays sharp.
- **Lighting** — the direction, quality and time of day of the light, and the shadows it casts.
- **Colour grading** — the tonal treatment applied over the whole image.
- **Aspect ratio** — the frame shape; match it to where the portrait will run.
- **Text integration** — any words that appear on the image. Put the exact wording in quotes and name the typography you want.
- **Factual constraints** — anything in the image that has to be accurate rather than plausible.

Split a complicated request into step-by-step instructions. Specify densely and do not trim detail to keep the prompt short.

## Portrait specifics

Describe the face you want — an attractive, editorial-grade structure and its specific features — rather than leaving it to the model's default. Call for pores and fine surface detail on the skin, or it renders smoothed and synthetic. Never leave the outfit open — unstated, it gets invented; describe it concretely, by garment, cut, fabric and colour. Set the pose and expression, and build the palette on a dominant tone plus one accent. Keep the hands empty of products and props, and name the concrete thing rather than reach for a vague adjective.

## Keeping things out of the frame

Describe what you want, not what you don't. There is no negative-prompt field; exclusion happens in positive prose — name the state of the frame you want rather than the thing to leave out. For example, "an empty, deserted street with no signs of traffic" works where "no cars" does not. When you are removing something from an image you already have, be direct and specific about the element to take out.

## Unsafe requests

Where a brief calls for something off-limits — sexual or exploitative content, minors depicted unsafely, self-harm or extreme injury, extremist insignia — drop that part, substitute workable clothing or framing, and produce the clean version instead of refusing.

## Holding one subject across several images

The model holds character consistency well, though not perfectly — check every frame rather than assuming a set matches. Blend reference images of the subject into each generation to carry resemblance forward, and lead with the references that matter most.

If the brief needs several images of the **same** person, repeat the appearance and wardrobe
**verbatim** in every prompt and change only the shot and framing — a back-reference like "the same
woman" produces a different face each time.
