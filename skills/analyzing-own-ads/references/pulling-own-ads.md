# Pulling your own ads

Every call goes through `social_research` with a `platform`, an `endpoint`, and a `params` object.
**Call `list_research_sources` once**, with no query, and read every endpoint's params and
`accepted_values` off that one response. Param names are case-sensitive, and an unknown one is
rejected before any call is made.

Two endpoints on `meta_ad_library` matter here:

| Endpoint | What it's for |
| --- | --- |
| `company_ads` | one advertiser's ads — the main call, and here the advertiser is the user's own brand |
| `search_companies` | find the page id by name, when the name alone doesn't resolve |

`company_ads` takes `companyName` **or** `pageId`, plus `country`, `status`, `media_type`,
`language`, `sort_by`, `start_date`, `end_date`, `cursor` and `trim`. `list_research_sources` returns
the accepted values under `accepted_values` — read them there rather than guessing; a wrong value is
billed.

**Send `trim: true` on every pull.** It defaults to `false`, which returns the raw ad-library shape —
a wall of nested fields with no run length, campaign, intent or creative kind worked out, which the
ledger script refuses. Everything below describes what comes back with `trim: true`.

**`status` defaults to `ACTIVE`.** A pull with no `status` returns only live ads, and never says so.

## Step 1: Resolve the page id before pulling anything

**Never pull by `companyName`.** It is the cheap-looking route and it is how another company's ads
end up in the audit: the name matches whatever page the library thinks is closest — a reseller
carrying the product, a dormant page, a similarly-named business in an unrelated category — and the
ads come back looking perfectly legitimate. Short brand names collide constantly, and the same name
under a country filter can return nothing at all while the page id returns hundreds.

Call `search_companies` with the name. It returns each matching page with its id, category, follower
count, verification and country.

- **One candidate is obviously right** — verified, right country, far more followers than the rest, and
  a category that matches the brand → take it, and say in one line which page you took.
- **Nothing is obvious** → show the candidates and let the user pick.

**Always send a page id.** Neither `pageId` nor `companyName` is marked required, so a call with
neither passes validation, goes out, and bills for nothing useful.

**Where the params are uncertain, send `dry_run: true` once.** It returns the exact request that would
go out and spends nothing.

## Step 2: Prove it's the right page

Even with a page id, check the first page of ads against what the user gave you:

- **The destination domain.** Compare the domain in each ad's link against the brand's own website —
  domain only, ignoring the path and any tracking parameters.
- **The advertiser name** carried on each ad.

- **Both agree** → right page, carry on.
- **The name is right but the links point somewhere else** → a click tracker sits in between. Still the
  right page; carry on.
- **Both disagree** → wrong page. Go back to the candidate list rather than pulling more of it.
- **The links point at a retailer that stocks the brand** → a reseller's page, not the brand's own. Say
  so and go back to the candidates.

## Step 3: Reach the long-running ads, then page to the depth's limit

**There is no run-length sort.** `sort_by` takes `total_impressions` or `relevancy_monthly_grouped`,
and neither orders by how long an ad has run. One page of a large advertiser is 30 ads that skew
recent, and the long-runners are not among them.

Call `status: "ACTIVE"` with `sort_by: "total_impressions"`, then **page with the cursor until the
long-runners appear.** One call returns one page and a cursor for the next; the first page or two are
where the recent ads sit, and the ads that have run for months come later.

Check each page's `first_seen` dates as they arrive. Keep paging while every page is still returning
ads only a few weeks old, and stop at the depth cap for this run or when the account runs out.
**Each page is another call** — don't pull everything a large account has.

**`start_date` and `end_date` don't bound the ad's start date.** `end_date` set to a past date
alongside `status: "ACTIVE"` returns nothing, so it can't be used to isolate long-running ads. Don't
reach for it, and never read an empty date-filtered pull as evidence there are no long-running ads.

Where the depth cap is reached before any older ads appear, say in the audit that the sample is
recency-weighted.

## What comes back

With `trim: true`, `social_research` projects an ad-library response down to the readable fields and
one media URL per ad. Each ad comes back with its run length, its campaign, its intent and its
creative kind already worked out, so none of that is counted by hand. `shaping` says what was
dropped, and the whole response is written to a file:

```json
{"ok": true,
 "data": {"advertisers": {"<page id>": {"name": "…", "likes": 16870, "categories": ["…"]}},
          "results": [...], "total": 254, "cursor": "…"},
 "saved": {"path": "…/supercmo_research_<date-time>_<id>/meta_ad_library-company_ads-001.json",
           "output_dir": "…/supercmo-media/competitor-research/<date-time>",
           "inline": true, "count": 30, "total": 254, "cursor": "…"}}
```

**Keep two paths from the first response and reuse them all run.** The directory `saved.path` sits in
holds every pull, and is what the ledger is built from. `saved.output_dir` is where this run's files
are written. Both are the same on every response of the run.

Take the next page's cursor from `saved.cursor`. `data` holds the same content as the file, and on a
large page it is left out entirely (`inline: false`) — the file always has it.

Where you need a field the projection dropped, call again with `trim: false` for the one ad that needs
it, never for the whole page — and don't pass that response to the ledger script.

## Step 4: Pull the retired ads too

Repeat the pull with `status: "INACTIVE"`. These are the ads the brand stopped, and they carry an end
date.

Where the filter is refused, pull with `status: "ALL"` and let the ads sort themselves out — each one
already says whether it is live or stopped.

## What each ad carries

Alongside the ads, `advertisers` carries the page once — its name, follower count and self-declared
category — rather than repeating them on every ad.

Each projected ad carries:

| Field | |
| --- | --- |
| `page_id`, `page_name` | the advertiser that ran it — the identity check above |
| `status` | `live` or `stopped`, from the ad itself rather than from which call fetched it |
| `first_seen`, `last_seen` | start date, and end date once it has stopped |
| `days_running` | its run length, taken from the ad's own field where it has one |
| `campaign` | the ads pointing at one offer, grouped by landing domain and path |
| `intent` | `prospecting` or `retargeting`, where the tracking parameters say so |
| `creative_kind` | video, image, carousel or dco |
| `media_url`, `media_count` | the creative to watch, and how many the ad carries |
| `landing_url` | where it sends people, with the click trackers stripped |
| `cta_text`, `cta_type` | the button's words, and the type behind them — count on the type, which doesn't change with the ad's language |
| `title`, `body_text`, `link_description` | the copy the platform ran around the creative |
| `cards` | the per-panel copy of a carousel, where the argument is spread across cards |
| `variant_group` | ads the library groups as variants of one another |
| `branded_content` | set where the ad ran as a creator partnership rather than in the brand's own name |
| `publisher_platform` | Facebook, Instagram and the other surfaces it ran on |
| `variants` | how many near-identical ads the library groups with it |
| `library_url` | the ad's own page in the library, kept as its source |
| `ad_archive_id`, `captured` | the ad's id, and the date this pull was made |

**A field the ad doesn't carry comes back empty, never zero** — an ad with no usable date has
`days_running: null`, and it stays out of every run-length finding rather than counting as a
zero-day run.

**Don't assume a sort order.**

## When a pull comes back short

Not an error — a finding. Record it as empty **for this market**, and never widen a filter to fill
the gap.

- **No page, or no ads at all** → the brand isn't advertising in this market. **That is the audit** —
  say so.
- **Fewer ads than the depth asked for** → audit the ads there are. Every conclusion is labelled thin,
  and no percentage is quoted.
- **Live ads but no stopped ones** → carry on. The audit says what was dropped couldn't be read in this
  market.
- **A filter is refused** → pull without it and sort the ads out afterwards from the fields they carry.

## Traps

- **A wrong param name, and a wrong value for `status`, `media_type` or `sort_by`, fail before any
  call is made** and cost nothing. Everything else — a country code, a date, a language — is checked
  only by the source, and a bad one comes back as a bare request failure that still bills.
- **An empty or whitespace param is dropped**, not defaulted. A call meant to be filtered goes out
  unfiltered.
- **Every call is billed, including one that returns nothing.** A misspelled brand name costs the same
  as a good pull.
- **A missing field is a gap, not a zero.** Read what came back; don't fill a field the response
  didn't carry.
