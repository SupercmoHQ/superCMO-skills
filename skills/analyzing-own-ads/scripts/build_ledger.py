#!/usr/bin/env python3
"""Turn meta_ad_library pulls into one ledger.

    python3 build_ledger.py <responses-dir> --depth quick|detailed

Point it at the directory social_research wrote its responses to — every `.json` in it is read.
Individual files work too. Nothing else is passed: each ad already names the advertiser that ran
it and says whether it is live or stopped, so the ads sort themselves into competitors.

The per-ad facts — run length, campaign, intent, creative kind — are derived by the tool. What
happens here is everything needing the whole set at once: de-duplication across pages, reference
numbering, the depth caps, and which ads are worth watching.

Writes one file, `ledger.md`, into --out or a date-and-time-stamped run folder: the counts
and campaigns per competitor, the ads to watch with their media URLs, the copy each ad ran with
(shared wording collapsed onto one line, panel copy listed per card), and every row behind it all.

Nothing is inferred that the ad does not carry. A missing field is left empty, never zero.
Stdlib only.
"""

import argparse
import datetime
import json
import os
import sys
from collections import Counter, OrderedDict, defaultdict

# Every number is per competitor: what the ledger keeps, and what gets watched. Live and stopped are
# budgeted separately so a competitor's live creative is never crowded out by what it has dropped.
DEPTHS = {
    "quick":    {"keep_live": 30, "keep_stopped": 30, "watch_live": 10, "watch_stopped": 10},
    "detailed": {"keep_live": 60, "keep_stopped": 60, "watch_live": 20, "watch_stopped": 20},
}


# The same resolution generated media uses, so a run's documents land beside everything else the
# toolchain writes. Duplicated rather than imported: this script travels with the skill and runs on
# the standard library alone.
OUTPUT_DIR_ENV = "SUPERCMO_OUTPUT_DIR"
OUTPUT_DEFAULT = "./supercmo-media"


def research_dir():
    """A fallback for a hand-run: `<output dir>/competitor-research/<YYYY-MM-DD-HHMM>`.

    Prefer `--out`, taking the value from a response's `saved.output_dir`. That one is settled where
    the working directory is the caller's project; this one resolves against whatever cwd the script
    happens to be run from."""
    root = os.path.abspath(os.path.expanduser(
        os.environ.get(OUTPUT_DIR_ENV) or OUTPUT_DEFAULT))
    base = os.path.join(root, "competitor-research",
                        datetime.datetime.now().strftime("%Y-%m-%d-%H%M"))
    candidate, n = base, 2
    while True:
        try:
            os.makedirs(candidate)
            return candidate
        except FileExistsError:
            candidate, n = f"{base}-{n}", n + 1


# --------------------------------------------------------------------------- loading


def response_files(paths):
    """Every response file behind the paths given — a directory contributes its `.json` files."""
    found = []
    for path in paths:
        if os.path.isdir(path):
            found += [os.path.join(path, n) for n in sorted(os.listdir(path))
                      if n.endswith(".json")]
        else:
            found.append(path)
    if not found:
        raise SystemExit(f"no .json response files found in {', '.join(paths)}")
    return found


def load_pull(path):
    """Return (ads, total, advertisers) from one response file, or (None, None, {}) to skip it.

    A run's directory holds every response the pull made, including ones from other endpoints.
    Anything without ads in it is skipped rather than treated as an error."""
    with open(path, encoding="utf-8") as fh:
        blob = json.load(fh)
    # The response envelope is {ok, platform, endpoint, data:{results, total, cursor}}.
    data = blob.get("data", blob)
    advertisers = data.get("advertisers") or {}
    rows = data.get("results")
    if not isinstance(rows, list):
        return None, None, {}
    if rows and "snapshot" in rows[0]:
        raise SystemExit(
            f"{os.path.basename(path)}: this is an unprojected response. `trim` defaults to false — "
            f"pull again with trim=true so the ads come back with days_running, campaign and intent "
            f"derived."
        )
    if rows and "ad_archive_id" not in rows[0]:
        return None, None, {}  # a response from another endpoint sharing the directory
    return rows, data.get("total"), advertisers


# --------------------------------------------------------------------------- fields


def one_line(text, limit=160):
    return " ".join((text or "").split())[:limit]


def asset_key(row):
    """The creative behind an ad, ignoring the signature on the URL — two ads carrying the same
    asset differ only in the query string, and sometimes not even there."""
    if not row["_media"]:
        return None
    return row["_media"][0].split("?", 1)[0]


# --------------------------------------------------------------------------- ledger


def build_rows(ads):
    """One row per ad, from the projected fields social_research already derived.

    The competitor is the advertiser the ad names, not a label passed in beside the file: an ad
    knows who ran it, so two pages of the same advertiser join up without anyone spelling the name
    the same way twice. A duplicate ad id is dropped rather than counted again."""
    seen = set()
    dupes = 0
    rows = []
    for ad in ads:
        ad_id = str(ad.get("ad_archive_id") or "")
        if not ad_id:
            continue
        if ad_id in seen:
            dupes += 1
            continue
        seen.add(ad_id)
        rows.append(
            {
                "ref": "",  # assigned once the whole set is sorted
                "competitor": ad.get("page_name") or ad.get("page_id") or "unknown",
                "status": ad.get("status") or "",
                "first_seen": ad.get("first_seen") or "",
                "last_seen": ad.get("last_seen") or "",
                "days_running": ad.get("days_running"),
                "format": ad.get("creative_kind") or "unknown",
                "platforms": "+".join(ad.get("publisher_platform") or []),
                "cta_text": ad.get("cta_text") or "",
                "cta_type": ad.get("cta_type") or "",
                "variant_group": ad.get("variant_group") or "",
                "branded": "yes" if ad.get("branded_content") else "",
                "_cards": ad.get("cards") or [],
                "landing_url": ad.get("landing_url") or "",
                "campaign": ad.get("campaign") or "",
                "intent": ad.get("intent") or "",
                "variants": ad.get("variants") or 1,
                "title": one_line(ad.get("title")),
                "body": one_line(ad.get("body_text"), 240),
                "link_description": one_line(ad.get("link_description")),
                "source_url": ad.get("library_url") or "",
                "captured": ad.get("captured") or "",
                "watch": "no",
                "_media": [ad["media_url"]] if ad.get("media_url") else [],
            }
        )
    return rows, dupes


def apply_caps(rows, cap_live, cap_stopped):
    """Keep the longest-running N per competitor per status. Report what was dropped."""
    kept, dropped = [], []
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["competitor"], row["status"])].append(row)
    for (competitor, status), group in grouped.items():
        group.sort(key=lambda r: (r["days_running"] is None, -(r["days_running"] or 0)))
        cap = cap_live if status == "live" else cap_stopped
        kept.extend(group[:cap])
        for row in group[cap:]:
            dropped.append((competitor, status))
    return kept, Counter(dropped)


def mark_watch(rows, depth):
    """Mark what to watch: the longest-running ads, up to an allowance per competitor per status.

    Nothing here decides what a run length means — it only orders by it. One creative often runs
    under several ad ids, and watching it twice bills twice and says nothing new, so a repeat gives
    its slot to the next ad."""
    caps = DEPTHS[depth]
    picked, seen_assets = [], set()

    for competitor in OrderedDict.fromkeys(r["competitor"] for r in rows):
        for status in ("live", "stopped"):
            cap = caps["watch_live" if status == "live" else "watch_stopped"]
            pool = [r for r in rows if r["competitor"] == competitor and r["status"] == status]
            pool.sort(key=lambda r: (r["days_running"] is None, -(r["days_running"] or 0)))
            taken = 0
            for row in pool:
                if taken >= cap:
                    break
                asset = asset_key(row)
                if asset and asset in seen_assets:
                    row["watch"] = "no (same creative as an ad already watched)"
                    continue
                seen_assets.add(asset)
                row["watch"] = "yes"
                picked.append(row)
                taken += 1

    for row in rows:
        if row["watch"] == "no":
            row["watch"] = "no (outside the watch allowance)"
    return picked, len(rows) - len(picked)


# --------------------------------------------------------------------------- output


def bands(rows):
    out = Counter()
    for row in rows:
        days = row["days_running"]
        if days is None:
            out["undated"] += 1
        elif days < 14:
            out["under 2 weeks"] += 1
        elif days < 42:
            out["2-6 weeks"] += 1
        else:
            out["6+ weeks"] += 1
    return out


def counts(title, counter):
    if not counter:
        return f"**{title}** — none\n"
    parts = ", ".join(f"{k} {v}" for k, v in counter.most_common())
    return f"**{title}** — {parts}\n"


def write_ledger(path, rows, watched, caps_dropped, watch_dropped, dupes, depth,
                 captured, advertisers):
    """One file: what was pulled, what to watch with its URLs, and every row behind both.

    A reader needs all three before the research is done — the counts to scope it, the URLs to
    watch the ads, the rows to cite a finding — so splitting them across files buys no context
    back and costs a format and a read each."""
    caps = DEPTHS[depth]
    out = [f"# Ledger — {captured}", ""]
    out.append(f"{len(rows)} ads, {len(watched)} marked to watch ({depth} scan).")
    out.append("")

    if caps_dropped:
        detail = ", ".join(f"{c} {s} \u2212{n}" for (c, s), n in caps_dropped.items())
        out.append(f"> **Capped.** Ads past the depth limit dropped, longest-running kept: {detail}.")
    if watch_dropped:
        out.append(f"> **Not watched.** {watch_dropped} of {len(rows)} ads fell outside the {depth} "
                   f"allowance of {caps['watch_live']} live and {caps['watch_stopped']} stopped per "
                   f"competitor. They stay in every count below.")
    if dupes:
        out.append(f"> {dupes} duplicate ad ids across pages were merged.")
    if caps_dropped or watch_dropped or dupes:
        out.append("")

    for competitor in OrderedDict.fromkeys(r["competitor"] for r in rows):
        mine = [r for r in rows if r["competitor"] == competitor]
        live = [r for r in mine if r["status"] == "live"]
        stopped = [r for r in mine if r["status"] == "stopped"]
        out.append(f"## {competitor}")
        who = next((a for a in advertisers.values() if a.get("name") == competitor), {})
        facts = []
        if who.get("likes"):
            facts.append(f"{who['likes']:,} page likes")
        if who.get("categories"):
            facts.append("/".join(who["categories"]))
        out.append(f"{len(live)} live, {len(stopped)} stopped, "
                   f"{sum(1 for r in mine if r['watch'] == 'yes')} to watch"
                   + (f" · {' · '.join(facts)}" if facts else "") + ".")
        out.append("")
        out.append(counts("Format", Counter(r["format"] for r in mine)))
        out.append(counts("Run length (live)", bands(live)))
        if stopped:
            out.append(counts("Run length (stopped)", bands(stopped)))
        out.append(counts("Call to action", Counter(r["cta_type"] or r["cta_text"]
                                                    for r in mine if r["cta_type"] or r["cta_text"])))
        out.append("")
        out.append("| Campaign | Ads | Longest | Formats | Intent |")
        out.append("| --- | --- | --- | --- | --- |")
        by_campaign = defaultdict(list)
        for row in mine:
            by_campaign[row["campaign"]].append(row)
        for name, group in sorted(by_campaign.items(), key=lambda kv: -len(kv[1])):
            longest = max((g["days_running"] or 0) for g in group)
            fmts = "+".join(sorted({g["format"] for g in group}))
            intents = "+".join(sorted({g["intent"] for g in group if g["intent"]})) or "\u2014"
            out.append(f"| {name} | {len(group)} | {longest}d | {fmts} | {intents} |")
        out.append("")

    out.append("## Watch these")
    out.append("")
    out.append(f"The longest-running ads of each competitor — up to {caps['watch_live']} live and "
               f"{caps['watch_stopped']} stopped each. Send in calls of at most 10: "
               f"`video_analysis` for the videos, `image_analysis` for the stills.")
    out.append("")
    for kind, label in (("video", "Videos"), ("still", "Stills")):
        group = [r for r in watched
                 if (("video" in r["format"]) == (kind == "video")) and r["_media"]]
        if not group:
            continue
        out.append(f"**{label}**")
        out.append("")
        for row in group:
            out.append(f"- `{row['ref']}` {row['competitor']} \u00b7 {row['days_running']}d")
            out.append(f"  {row['_media'][0]}")
        out.append("")
    unwatchable = [r for r in watched if not r["_media"]]
    if unwatchable:
        out.append("**No media URL — record as unwatched:** "
                   + ", ".join(r["ref"] for r in unwatchable))
        out.append("")

    out.append("## The copy")
    out.append("")
    out.append("The words the platform carried around each ad, as the advertiser wrote them — present "
               "for every ad, watched or not. Ads sharing wording are listed once; how many refs sit "
               "on one line is how far that copy has been spread.")
    out.append("")
    shared = OrderedDict()
    for row in rows:
        key = (row["title"], row["body"], row["link_description"], row["cta_text"])
        shared.setdefault(key, []).append(row["ref"])
    for (title, body, desc, cta), refs in sorted(shared.items(), key=lambda kv: -len(kv[1])):
        parts = [f"**{title}**" if title else None, body or None, desc or None,
                 f"*{cta}*" if cta else None]
        said = " · ".join(p for p in parts if p) or "_no copy_"
        out.append(f"- {said}")
        out.append(f"  `{'` `'.join(refs)}`")
    out.append("")

    carded = [r for r in rows if r["_cards"]]
    if carded:
        out.append("Panel copy, where an ad spreads its argument across cards:")
        out.append("")
        for row in carded:
            out.append(f"- `{row['ref']}`")
            for i, card in enumerate(row["_cards"], 1):
                bits = [card.get("title"), card.get("body"), card.get("cta_text")]
                out.append(f"  {i}. " + " · ".join(b for b in bits if b))
        out.append("")

    grouped = defaultdict(list)
    for row in rows:
        if row["variant_group"]:
            grouped[row["variant_group"]].append(row)
    families = {k: v for k, v in grouped.items() if len(v) > 1}
    if families:
        out.append("## Variant groups")
        out.append("")
        out.append("Ads the library groups as variants of one another. Read a group side by side and "
                   "the difference between its ads is what that competitor is testing.")
        out.append("")
        for refs in sorted(families.values(), key=lambda v: -len(v)):
            spans = ", ".join(f"{r['ref']} ({r['days_running']}d)" for r in refs)
            out.append(f"- {refs[0]['competitor']} · {spans}")
        out.append("")

    branded = [r for r in rows if r["branded"]]
    if branded:
        out.append("Ran as a creator partnership rather than in the brand's own name: "
                   + ", ".join(f"`{r['ref']}`" for r in branded))
        out.append("")

    out.append("## Every ad")
    out.append("")
    out.append("| ref | competitor | status | first seen | last seen | days | format | campaign "
               "| intent | cta | variants | platforms | watch | landing | library |")
    out.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- "
               "| --- | --- |")
    for r in rows:
        days = "" if r["days_running"] is None else r["days_running"]
        out.append(f"| {r['ref']} | {r['competitor']} | {r['status']} | {r['first_seen']} | "
                   f"{r['last_seen']} | {days} | {r['format']} | {r['campaign']} | {r['intent']} | "
                   f"{r['cta_text']} | {r['variants']} | {r['platforms']} | {r['watch']} | "
                   f"{r['landing_url']} | {r['source_url']} |")
    out.append("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))


# --------------------------------------------------------------------------- main


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", metavar="RESPONSES_DIR",
                    help="the directory social_research wrote its response files to; "
                         "individual response files also work")
    ap.add_argument("--out", help="output directory — pass a response's `saved.output_dir` "
                                  "(default: <$SUPERCMO_OUTPUT_DIR or "
                                  "./supercmo-media>/competitor-research/<date-time>, a folder per run)")
    # Required rather than defaulted: depth is a decision the caller has already made, and a silent
    # default would quietly halve a run that was asked to go deep.
    ap.add_argument("--depth", choices=sorted(DEPTHS), required=True)
    args = ap.parse_args(argv)

    caps = DEPTHS[args.depth]

    ads = []
    advertisers = {}
    read = 0
    for path in response_files(args.paths):
        page, total, seen = load_pull(path)
        if page is None:
            continue
        read += 1
        ads += page
        advertisers.update(seen)
        if total and len(page) < total:
            names = ", ".join(sorted({a.get("page_name") or "?" for a in page}))
            print(
                f"note: {os.path.basename(path)} ({names}) holds {len(page)} of {total} "
                f"reported. Page on with the cursor if you are under the depth cap.",
                file=sys.stderr,
            )
    if not read:
        raise SystemExit(f"no ad responses among the {len(response_files(args.paths))} file(s) given")

    out = args.out or research_dir()
    # Nothing belongs inside the skill: a run launched from the skill directory would otherwise put
    # its results there, where the next install wipes them.
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.abspath(out).startswith(here + os.sep):
        raise SystemExit(
            f"refusing to write inside the skill at {here}. Pass --out, taking the value from a "
            f"response's `saved.output_dir`.")
    rows, dupes = build_rows(ads)
    if not rows:
        raise SystemExit("no ads found in any response")
    rows, caps_dropped = apply_caps(rows, caps["keep_live"], caps["keep_stopped"])

    rows.sort(
        key=lambda r: (r["competitor"], r["days_running"] is None, -(r["days_running"] or 0))
    )
    numbers = {c: i for i, c in enumerate(OrderedDict.fromkeys(r["competitor"] for r in rows), 1)}
    counters = Counter()
    for row in rows:
        n = numbers[row["competitor"]]
        counters[n] += 1
        row["ref"] = f"C{n}-{counters[n]:02d}"

    watched, watch_dropped = mark_watch(rows, args.depth)

    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "ledger.md")
    write_ledger(path, rows, watched, caps_dropped, watch_dropped, dupes,
                 args.depth, rows[0]["captured"], advertisers)

    print(f"{len(rows)} ads, {len(watched)} to watch → {path}")


if __name__ == "__main__":
    main()
