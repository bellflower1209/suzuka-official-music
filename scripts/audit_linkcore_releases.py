#!/usr/bin/env python3
"""Audit the five user-confirmed LinkCore destinations and their public links."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "hyakumankoku": "https://linkco.re/Qd5Tzb0q",
    "hello-hello-halloween": "https://linkco.re/QfzZUy6f",
    "toriatsukai-chui": "https://linkco.re/9r6szVDg",
    "september-blue": "https://linkco.re/HCvApf7V",
    "over-drive": "https://linkco.re/3tHVbvXs",
}


def main() -> None:
    cms = json.loads((ROOT / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    releases = {item["slug"]: item for item in cms["releases"]}
    upcoming = {item["slug"]: item for item in cms.get("upcoming", [])}
    assert len(releases) == len(cms["releases"]), "duplicate release slug"
    assert len(upcoming) == len(cms.get("upcoming", [])), "duplicate upcoming slug"
    assert not set(releases) & set(upcoming), "release/upcoming slug overlap"

    for slug, url in EXPECTED.items():
        if slug in releases:
            item = releases[slug]
            assert item["scheduledStreamingRelease"]["linkcoreUrl"] == url
            assert item["scheduledStreamingRelease"]["status"] == "upcoming"
            assert item["scheduledStreamingRelease"]["timezone"] == "Asia/Tokyo"
            page = ROOT / item["releaseUrl"] / "index.html"
        else:
            item = upcoming[slug]
            assert item["linkcoreUrl"] == url
            assert item["status"] == "upcoming"
            assert item["scheduledAt"].endswith("T00:00:00+09:00")
            page = ROOT / f"releases/{slug}/index.html"
        text = page.read_text(encoding="utf-8")
        assert text.count(url) >= 1, (slug, url)
        assert re.search(
            rf'<a(?: [^>]+)? href="{re.escape(url)}" target="_blank" rel="noopener noreferrer">', text
        ), (slug, url)
        assert "studio.youtube.com" not in text

    assert releases["hyakumankoku"]["releaseDate"] == "2026-07-12"
    assert releases["toriatsukai-chui"]["releaseDate"] == "2026-07-14"
    assert {item["slug"] for item in cms["upcoming"]} >= {
        "hello-hello-halloween", "september-blue", "over-drive",
    }
    schedule_titles = [item["title"] for item in cms["miaReleaseSchedule"]["activities"]]
    assert schedule_titles[-2:] == ["September Blue", "Over Drive"]
    search = (ROOT / "assets/data/search-v31.json").read_text(encoding="utf-8")
    for term in ("百万告", "Hello Hello Halloween", "取り扱いチュー", "September Blue", "Over Drive", "LinkCore"):
        assert term in search, term
    print(f"LinkCore audit passed: {len(EXPECTED)} confirmed URLs, no duplicate release records, all public CTAs use noopener.")


if __name__ == "__main__":
    main()
