# The clips

A **clip** is one model call. Inside it are several **hard cuts** — not one continuous action, but
staged shots cut together and generated in a single pass.

## How many cuts

**One cut is one primary action** — one continuous motion at one object. Take the clip's part of the
story and split it wherever a second motion starts or a second object is taken up: *picks it up*,
*tilts it to the light*, *sets it down* is three cuts, never one.

**Each cut runs two seconds where possible, three at most**, so a clip's seconds are the number of
primary actions it can carry. Where the story asks for more actions than the seconds have room for, it
is too much for that clip — cut an action rather than crowding them in.

**The count is however many actions that part of the story has, not the most the seconds allow.** Three
actions in a ten-second clip is three cuts running longer, not five cuts with two invented to fill the
space.

## Where the cut lands

Cut between actions, never inside one.

- **A cut shows a state, not the change into it** — already open, already worn, already out of the box.
  The change itself falls on the cut.
- **At most one state change lands in any cut.**
- **State runs one way.** Once something is open, worn or emptied it stays that way for the rest of the
  video — never re-closed, never taken off again, never put back where it came from.
- **Nothing appears without arriving.** Whatever is in a cut was either in the cut before it or came in
  on the cut just before.
- **What leaves is gone** from every cut after it and is never described again — a cap taken off, a
  wrapper torn away, a box emptied.

These never render, so no cut asks for them:

- Anything finer than a whole hand movement — working a clasp, a zip, a drawstring, a pump head.
- Two motions treated as one, or a second object handled in the same breath as the first.

## What each cut carries

- **One primary action**, in one place.
- **A size and an angle** — wide, medium, close, very close, over the shoulder, low, high. Vary them,
  and never use the same size twice in a row. A run of cuts that all sit at one distance needs
  reworking. Only shoot over the shoulder of a character who is actually in that clip.
- **One camera move**, named. Don't stack a move on a move, and don't repeat the last one.

### Naming the move

**Say what the camera does in every cut.** A cut that names no move comes back as a lazy horizontal
drift, and a whole clip of them reads as a slideshow of stills.

Moves to draw from:

- **Push in** — the camera closes on the subject.
- **Pull back** — the camera withdraws, revealing more around it.
- **Tilt up or down** — the camera pivots over the subject's height.
- **Arc** — the camera travels around the subject, which turns as it goes. Never arc around the
  product, and never turn it: the reference carries one side, and the far side gets invented along
  with whatever is printed on it.
- **Scale snap** — a hard jump to a much closer or much wider framing.
- **Held frame** — the camera does not move at all, and the subject moves inside it. This still counts
  as naming the move, and it is not the same as saying nothing.
- **A sideways pan** is allowed, but only where the shot has a reason for it — something crossing the
  frame that the camera is following. Never as the default.

**The first cut carries the story's strongest opening beat**, so give it a move that pushes into or
reveals that beat. It is the cut that decides whether the rest gets watched.

**Never use the same move on two cuts in a row.**

**Within a clip:** bring elements in one at a time rather than all at once, give one cut the clip's
strongest beat, and let the last cut settle without freezing — something should still be moving in it.

**Across the video:** each clip picks up where the last one left off. Don't re-establish with a wide
shot when returning to a place already seen, and don't run more than two clips in the same place
without changing the angle.

## The prompt

One prompt per clip. References declared up front, their handling instruction last.

**1. Say what each attached image is.** The images go in as `reference_images`, an ordered list, in the
order set in `cast-and-places.md`. Name them at the top of the prompt in that same order, in plain
words, and then use those names in the cuts:

```
The first reference image is the kitchen. The second is the cook. The third is the bottle.
```

This model also reads a tag form, `<IMAGE_REF_0>` for the first image, `<IMAGE_REF_1>` for the second
and so on, counting from zero. Tags are worth using in a cut where two references could be confused —
*"reaches for `<IMAGE_REF_2>`"* is unambiguous where *"reaches for the bottle"* is not. Write the plain
names as well as the tags rather than instead of them, so the prompt still reads correctly if the tags
are not honoured.

Nothing goes in as a first frame.

**2. The look.** The style brief pasted in word for word, then that the references define the finished
look: whatever they show is what the clip renders, and nothing in the frame departs from it.

**The product is exactly what its reference shows**, in every clip and every cut — same label, same
colours, same proportions, same finish, and only the sides the reference shows. Its printing rides in
from the reference; the prompt never spells out what it says and never asks for it to be drawn. Refer to
it by its label, in the same words in every clip.

**Where the product is a photograph rather than a drawing**, add that it is a real object placed in the
scene at the scene's own scale and light, never redrawn into the look.

**3. The cuts, timecoded.** One line per cut, in the model's own timecode form, each carrying a size, an
angle, a camera move and what happens:

```
[0-2s] Wide, low. Slow push in as the cook reaches for the bottle <IMAGE_REF_2> on the shelf.
[2-4s] Close, eye level. Held frame; the cap turns and lifts away.
```

Characters only emote and gesture, they do NOT talk. In the cut that frames the product largest, say
again that it matches its reference exactly — that is the cut where the label is most readable and most
likely to break.

**4. The audio.** The sound the scene itself makes, and nothing more. Name the sound the strongest cut
makes so the picture and the sound land together. The voiceover and any music arrive at the stitch, not
here.

**5. What to keep out.** Keep this short — a few plain items, not a paragraph. Always: `No dialogue.
No on-screen captions or subtitles. No lip-sync. No watermark. No redrawn or re-lettered product label.
No drift in the palette or the background.` Then add the look-specific bans below.

**6. The reference instruction, as the last line of the prompt.** Word it plainly: the attached images
say what things look like, not what the opening frame is — build the scene from them — **except the
product, which is carried across exactly as its reference shows it rather than drawn again.**

This belongs at the end — that is where the model is documented to take its reference handling, and it
is what stops the clip beginning by showing one of the images instead of the scene. Say the product
exception here as well as in part 2, because a bare "build it from them" in the last line undoes the
lock above it.

### Writing the keep-out list

It is written against the look, not copied. Two checks before it goes out.

- **Strike what the style brief needs.** A negative that contradicts the brief will fight it. Claymation
  and stylized 3D are dimensional and physically lit, so banning *3D render*, *live action*, *real
  light* or *physical texture* on those looks tells the model to undo what you asked for. On a flat or
  drawn look, ban them.
- **Where the product is a photograph, the frame is not all drawn.** Everything else obeys the style
  brief; the product deliberately does not. A blanket ban on anything photographic contradicts what the
  look section of the same prompt just said. Narrow it: no filmed people, no photographic skin, hair or
  fabric, no camera-captured footage — **except the product, which stays exactly as its reference shows
  it.**

What holds in every case: nothing else may read as *filmed*, and no lens or camera word appears anywhere.

## Words on screen

This model renders text well — a headline, a price, a short caption comes back legible and correctly
spelled — so lettering in a clip is a choice rather than something to avoid.

- **Write the exact words in quotes** in the cut that carries them. Keep the line short and set it
  against a high-contrast background.
- **English is the most reliable.** Other languages render less consistently.
- **Don't stack dense text on complex motion.** Text plus a busy moving frame is where it still breaks.
  A few words on a settled shot is the safe case.
- **The product's own printing** arrives because the reference image carries it, never because a prompt
  spells out what it says.
- **No brand but the product's own.** No other company's name, logo, wordmark or livery, and no
  recognisable character, vehicle or property from a film, game or show — not in a clip, not in an
  asset, and not named in a prompt as something to imitate.

Assets are a different matter: they are drawn on a different model and carry no lettering at all — see
`cast-and-places.md`.

## Three things the model does

- **It cuts by default.** Left to itself it breaks a clip into a few shots and invents a little narrative
  across them. The timecoded cut list is there to take that over, not to switch it on — you are
  directing something it already wants to do.
- **It under-delivers cuts.** A clip written for five often comes back with four. The timecoded form is
  what lands the count, which is the reason to write it that way rather than in prose.
- **It refuses clips it shouldn't.** A refusal here is usually a false positive rather than a real
  objection to the content, which is why the same prompt on a new seed is the first thing to offer.
