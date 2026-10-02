#!/usr/bin/env python3
"""Audit canonical LinkCore data against the 2026-09-24 TuneCore snapshot."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def streaming_record(item: dict) -> dict:
    return item.get("scheduledStreamingRelease") or item.get("streamingRelease") or {}


def main() -> None:
    cms = json.loads((ROOT / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    snapshot = json.loads((ROOT / "assets/data/tunecore-catalog-20260924.json").read_text(encoding="utf-8"))
    releases = {item["slug"]: item for item in cms["releases"]}
    upcoming = {item["slug"]: item for item in cms.get("upcoming", [])}
    assert len(releases) == len(cms["releases"]), "duplicate release slug"
    assert len(upcoming) == len(cms.get("upcoming", [])), "duplicate upcoming slug"
    assert not set(releases) & set(upcoming), "release/upcoming slug overlap"
    assert snapshot["summary"] == {"total": 21, "published": 13, "scheduled": 7, "underReview": 1}

    by_linkcore = {item["linkcoreUrl"]: item for item in snapshot["releases"] if item.get("linkcoreUrl")}
    audited = 0
    for item in [*releases.values(), *upcoming.values()]:
        record = item if item["slug"] in upcoming else streaming_record(item)
        url = record.get("linkcoreUrl")
        if not url:
            continue
        source = by_linkcore.get(url)
        assert source, (item["slug"], "not found in TuneCore snapshot")
        assert source["linkcoreUrl"] == url, (item["slug"], url, source["linkcoreUrl"])
        assert source["releaseDate"] == record.get("releaseDate"), (item["slug"], record.get("releaseDate"))
        if item["slug"] in upcoming:
            assert source["status"] == "scheduled" and record["status"] == "upcoming"
            assert item["scheduledAt"].endswith("T00:00:00+09:00")
        elif record.get("status"):
            expected = "published" if source["status"] == "published" else "upcoming"
            assert record["status"] == expected, (item["slug"], record["status"], expected)
            if record["status"] == "published":
                assert record.get("verifiedAt"), item["slug"]
        page = ROOT / item.get("releaseUrl", f"releases/{item['slug']}") / "index.html"
        text = page.read_text(encoding="utf-8")
        assert re.search(
            rf'<a(?: [^>]+)? href="{re.escape(url)}" target="_blank" rel="noopener noreferrer">', text
        ), (item["slug"], url)
        assert "studio.youtube.com" not in text
        audited += 1

    assert {item["slug"] for item in cms["upcoming"]} == {
        "eternity-of-flower-words", "renai-taishogai-kari",
        "nando-umarekawattemo-reborn-oath", "kokoro-ni-nokoru-takaramono",
    }
    under_review = [item for item in snapshot["releases"] if item["status"] == "under-review"]
    assert len(under_review) == 1 and under_review[0]["title"] == "夢と、介護と、わたしたち"
    assert under_review[0]["releaseDate"] is None and under_review[0]["linkcoreUrl"] is None
    # The existing official MV remains public, but its under-review streaming
    # distribution must not be presented as scheduled or linked to LinkCore.
    dream = releases["yume-to-kaigo-to-watashitachi"]
    assert dream["slug"] not in upcoming and not streaming_record(dream).get("linkcoreUrl")
    print(f"LinkCore audit passed: {audited} canonical URLs match the TuneCore snapshot; scheduled/published states are distinct.")


if __name__ == "__main__":
    main()
