"""The competitor-ads ledger script holds the watch budget, so the agent can't over-watch: a quick
scan watches each competitor's longest-running 4 live and 2 stopped ads, and a detailed analysis 20
and 20. Watching is the costly part (one vision call per ad); every kept row is still read."""

import importlib.util
from collections import Counter
from pathlib import Path

_SCRIPT = (Path(__file__).resolve().parent.parent
           / "skills/researching-competitor-ads/scripts/build_ledger.py")
_spec = importlib.util.spec_from_file_location("build_ledger", _SCRIPT)
ledger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ledger)


def _ads(page, status, n):
    return [{"ad_archive_id": f"{page}-{status}-{i}", "page_name": page, "status": status,
             "days_running": 100 - i, "media_url": f"https://cdn.example/{page}/{status}/{i}.mp4"}
            for i in range(n)]


def _watched(depth, ads):
    rows, _ = ledger.build_rows(ads)
    caps = ledger.DEPTHS[depth]
    kept, _ = ledger.apply_caps(rows, caps["keep_live"], caps["keep_stopped"])
    ledger.mark_watch(kept, depth)
    return kept, Counter((r["competitor"], r["status"]) for r in kept if r["watch"] == "yes")


def test_a_quick_scan_watches_four_live_and_two_stopped_per_competitor():
    ads = _ads("Big", "live", 12) + _ads("Big", "stopped", 7) + _ads("Small", "live", 3) \
        + _ads("Small", "stopped", 1)
    kept, watched = _watched("quick", ads)
    assert watched == {("Big", "live"): 4, ("Big", "stopped"): 2,
                       ("Small", "live"): 3, ("Small", "stopped"): 1}
    # The longest-runners are the ones watched, and nothing kept is dropped from the ledger.
    assert {r["days_running"] for r in kept if r["competitor"] == "Big" and r["status"] == "live"
            and r["watch"] == "yes"} == {100, 99, 98, 97}
    assert len(kept) == len(ads)


def test_a_detailed_analysis_still_watches_twenty_and_twenty():
    _, watched = _watched("detailed", _ads("Big", "live", 25) + _ads("Big", "stopped", 25))
    assert watched == {("Big", "live"): 20, ("Big", "stopped"): 20}


def test_a_repeated_creative_gives_its_slot_to_the_next_ad():
    ads = _ads("Big", "live", 6)
    ads[1]["media_url"] = ads[0]["media_url"] + "?sig=other"  # same asset, different signature
    kept, watched = _watched("quick", ads)
    assert watched[("Big", "live")] == 4
    assert next(r for r in kept if r["days_running"] == 99)["watch"].startswith("no (same creative")
