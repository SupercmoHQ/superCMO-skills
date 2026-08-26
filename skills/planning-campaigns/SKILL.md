---
name: planning-campaigns
description: Decides what to make next — turns the brand, the product, your own running ads and competitor research into the concepts worth testing next. Each concept is a full description of one ad, the buyer it targets, the bet it tests and the evidence it rests on — complete enough for a producer to build from directly. Nothing is generated before the plan is approved — it asks which concepts to build, and only then hands each approved concept to the skill that builds it. Use when the user asks what to make, what to test next, what hooks or angles to try, for campaign concepts, or a creative plan — or wants the whole campaign run end to end, from research to finished ads. Not for a single ad with no plan behind it — that goes straight to the producer skill.
license: Apache-2.0
metadata:
  version: "0.1.0"
  category: creative
  summary: "Decides what your next ads should be. It reads your brand, your product, the ads you already run and what competitors are doing, then writes concepts ranked by what is worth testing — each a full description of one ad, the buyer it targets and the bet it tests, with the proof it rests on and the skill that would build it. Approve the plan and it builds the concepts you pick, one by one, through the specialist skills."
---

# Campaign planning

Decide what ads to make next, write each one down as a concept a producer can build from directly,
and build the ones the user approves.

**Nothing is generated before the plan is approved.** Everything up to the plan is planning;
building is a separate decision the user makes at the end, concept by concept.

## Workflow

### Step 1: Scope the run

Ask once, bundled into a single message, always with a free-text way out. Skip any of these the brief
already answers.

| Ask | When | How |
| --- | --- | --- |
| **The product** | Always. | A URL or a photo. Where they name several, ask whether it is one campaign for all of them or one each. |
| **The objective** | The brief doesn't say. | Offer awareness, consideration and conversion, and a way to type another. |
| **The competitors** | The brief names none. | A name and a website for each. Where the user doesn't know, say you will let the research propose them and confirm before it reads anything. |
| **The market** | The brief names none and the site implies none. | Offer the likely markets, and a way to type another. |
| **How deep to go** | The brief doesn't say. | Offer the quick scan first and recommend it; say the deeper option roughly doubles what is watched, and costs accordingly. |

Ask them here, and pass the answers down. Don't go on without the product.

### Step 2: Gather the context

**Open the run's folder first.** Everything this run produces lives in one place:
`campaigns/<date-time>` under `$SUPERCMO_OUTPUT_DIR` (default `./supercmo-media`). Make it fresh for
this run — where a folder for this minute already exists, add `-2`, `-3`, … rather than writing into
it.

The plan is built from four inputs. Collect each one; skip one only where the brief already carries
what it would return.

**Every answer from Step 1 goes into the request that starts each skill** — the product, the
objective, the competitors, the market, the depth. A skill that receives them treats its own
scoping questions as already answered; one that doesn't will guess. Where something is still
unsettled, have the skill report it back rather than assume, and bring it to the user here.

- **The product.** Trigger the `analyzing-products` skill workflow with the URL or photo. This gives
  what the product is, how it is used, and what it can be shown doing.
- **The brand.** Trigger the `analyzing-brand` skill workflow with the brand's website. This gives
  the voice, the audience, the differentiators and the proof points.
- **Our own ads.** Trigger the `analyzing-own-ads` skill workflow. This gives what the account
  already covers, what is holding, and what was stopped.
- **Competitors' ads.** Trigger the `researching-competitor-ads` skill workflow. This gives the
  category's patterns, what its long-runners share, and what nobody runs.

**Each skill gets its own folder inside the run's folder, named after it, and everything it produced goes in there** — every file, not a chosen few. Tell each skill to write there; where one wrote somewhere else because a tool gave it no location, copy everything it produced across before moving on. Nothing this run rests on is left in a temporary folder.

Close the step by saying in one line which of the four inputs the plan is built on, and which are
absent — skipped, failed, or returned empty.

### Step 3: Build the concept list

Turn the gathered context into the concepts to test.

**Decide how many — don't ask.** Up to three campaigns, and up to ten concepts in each. Those are
ceilings, not targets: build as many as the evidence carries and stop there, saying what ran out.
Where the brief already asks for a specific number, or for one specific output, honor that instead.

Read `references/finding-concepts.md` and work through it — it writes the campaigns and their
concepts to `concepts.md` in the run's folder. Each concept is written in full, as the whole handoff
a producer builds from; there is no separate brief. Whether a concept can be produced is not a
criterion here — routing is Step 4.

### Step 4: Route each concept

Tag each concept in `concepts.md` with the skill that would build it, using
`references/production-palette.md`. **Every concept gets a route, and no concept is dropped for
being unroutable.**

### Step 5: Hand the plan over

**5a. Finish the file.** `concepts.md` now carries the campaigns with their concepts and routes in
order; add a short grounding header saying which inputs the plan is built on. **Everything the plan
cites is named by a path inside the run's folder or by a link** — never by a code that needs a
document the folder doesn't hold.

**5b. Present it, in one message.** Which inputs the plan is built on, then each campaign with its
concepts in order. Close with the path to `concepts.md`.

**5c. Ask about building.** Ask whether to create the assets, and if so which concepts — all of them,
some of them, or none. Say that building is billed. **Wait for the answer — an unanswered question
is not a yes.**

### Step 6: Build the approved concepts

Only after the user has named which concepts to build. Take them one at a time, in the plan's order:
trigger the skill the concept's route names and **give it the concept from `concepts.md`** — its
description and its four fields are the whole brief, so pass them and tell the producer to build from
them. Keep each producer's own approval gates — don't answer them on the user's behalf.

A concept the user didn't approve stays queued, and a concept routed outside the pipeline is never
built here.

Close with one short recap: what was built and where the files are, and which concepts remain queued.

## Edge cases

- **No product URL or photo** → ask for one and wait.
- **The user won't run the ad research** → plan without it and label the concepts reasoned rather than
  evidenced.
- **The brand isn't advertising yet, or has no competitors in the library** → that comes back as an
  empty audit, which is a real answer. Plan from the product, the brand and whichever half did return
  ads, and say the set has no coverage map behind it.
- **A product but no brand profile** → offer `analyzing-brand` first. If the user declines, ask which
  claims they will stand behind and plan from those, and say the voice is unconfirmed.
- **The user asks for one thing — "give me hooks", "what angle should I try"** → answer in that shape.
  Ranked answers with the reasoning behind each, not a set of full concepts they didn't ask for.
- **The research carries no proof the brand can stand behind** → plan the concepts that don't need proof
  and name the gap. **Never invent a statistic, rating, testimonial or result to make a concept work.**
- **The user says "make it" / "build these"** → that is Step 6's approval for those concepts. Nothing
  is built before it arrives.

## Reference

- `references/finding-concepts.md` — what the data says, drafting the concepts and selecting the set, and writing each one as the full handoff a producer builds from (Step 3).
- `references/production-palette.md` — what each producer skill makes and needs, and how to match a concept to the most specific one, with the general generators as the fallback (Step 4).
