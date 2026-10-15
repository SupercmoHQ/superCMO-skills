---
name: identifying-competitors
description: Finds out who a brand competes with. Reads what the brand sells from its site, searches the web for the alternatives buyers compare it against, and proposes a shortlist with competitor names and websites. Use when the user asks who their competitors are, or to find or refresh their competitor list, or when another skill needs competitors named first.
license: Apache-2.0
metadata:
  version: "0.2.0"
  category: creative
  summary: "Finds who a brand competes with: searches the web for the alternatives buyers compare it against, proposes a shortlist with a source per name, and confirms the real ones for other skills to build on."
---

# Competitors

Find who a brand competes with, confirm the list, and hand it over. **Names and websites only.**

## Workflow

### Step 1: Check whether the competitors are already known

Read `competitors.md` in `./supercmo-company`, and `brand.md` for the brand's name, website and what it sells. Where `competitors.md` already holds this brand's competitors, hand them back and stop — re-searching bills again and tells the user nothing new. Carry on where it's missing, where it's a different brand, or where the user asked to refresh.

### Step 2: Settle the brand

You need **a brand name and a website**. Where you don't already have them, ask the user for whichever is missing. Do not proceed without the website.

### Step 3: Learn what the brand sells

Call `url_extraction` on the website to learn what the brand sells. Skip this where you already know.

### Step 4: Find the candidates

Search the web with queries like:

- `alternatives to <brand>` — how buyers who already know the brand shop around.
- `best <category> for <audience>` — how buyers who don't yet know the brand find the category.

The search comes back with an answer and the source it drew from. Take the competitor names from there, and each website from a result or an ad's `landing_url` that links to the competitor's own site — not
a store, marketplace or social page. Where a result names a competitor without its site, search its
name for its official site. Where nothing shows one, write "website unconfirmed" — never a
domain from memory. Where a query returns nothing, vary the category words and search again.

**Every candidate needs a source** — the search result that named it. Don't add competitors from memory.

Where search runs thin — a niche category, a non-English market — `social_research` on `meta_ad_library` / `search_ads` with the category words shows who actually advertises in the space. Pass `country` for the market the brand sells in, where its page or `brand.md` shows it; where
nothing does, leave it out. **It spends credits: say so and wait for a yes.** Under a brief that skips
confirmation, run it without asking.

### Step 5: Confirm

Show 3–5 top competitor candidates in one message — name, website, and one line on why it competes. Ask which are real, which to drop, and who is missing.

**Where the brief says to skip confirmation**, don't stop to show the candidates or ask: save the
shortlist without waiting.

### Step 6: Hand it over

Write the confirmed list to `competitors.md` in `./supercmo-company` — a heading naming the brand,
then one line each, the name then its website. Create the folder where it doesn't exist.

**Where `competitors.md` already exists for this brand**, merge into it: keep the competitors already
listed unless the user dropped them, and add the new ones. Where it holds another brand's competitors,
replace it.

Close by showing the list and giving the path — unless another skill is running this one: then skip
the hand-over, and that skill gives the reply.

## Edge cases

- **`error: "no_provider_configured"`** on any tool → relay the tool's `hint` (the user must set their key).
- **A candidate is a retailer, marketplace or comparison site** → not a competitor unless the user says so. Say why you dropped it.
- **The brand sells in several countries** → competitors differ by market. Ask which one this list is for rather than mixing them; under a brief that skips confirmation, take the market the site leads with and say which.
- **The user wants those competitors' ads researched** → that is `researching-competitor-ads`. Hand over and say which competitors you used.
