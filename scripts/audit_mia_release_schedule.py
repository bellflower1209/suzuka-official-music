#!/usr/bin/env python3
"""Audit the confirmed September ENOMOTO MIA campaign without inferred metadata."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cms = json.loads((ROOT / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    releases = [item for item in cms["releases"] if item["slug"] == "hyakumankoku"]
    upcoming = [item for item in cms["upcoming"] if item["slug"] == "hello-hello-halloween"]
    hanakotoba = [item for item in cms["releases"] if item["slug"] == "hanakotoba"]
    assert len(releases) == len(upcoming) == len(hanakotoba) == 1
    assert len({item["slug"] for group in (cms["releases"], cms["upcoming"]) for item in group}) == len(cms["releases"]) + len(cms["upcoming"])
    million = releases[0]
    assert million["releaseDate"] == "2026-07-12" and million["status"] == "published"
    assert million["scheduledStreamingRelease"] == {
        "releaseDate": "2026-09-21", "timezone": "Asia/Tokyo", "label": "SUZUKA",
        "status": "upcoming", "source": "user-confirmed-tunecore-management-screen", "linkcoreUrl": None,
    }
    hello = upcoming[0]
    assert hello["scheduledAt"] == "2026-09-21T00:00:00+09:00"
    assert hello["youtubeUrl"] == "" and hello["image"] == ""
    flower = hanakotoba[0]
    assert flower["streamingRelease"]["releaseDate"] == "2026-09-11"
    assert flower["streamingRelease"]["linkcoreUrl"] == "https://linkco.re/0xHr8N9e"
    assert flower["karaoke"]["startDate"] == "2026-09-18"
    assert flower["lyricist"] == "JUN" and flower["composer"] == "SUNO×JUN"
    assert flower["streamingRelease"]["label"] == "SUZUKA"
    for route in ["index.html", "artists/enomoto-mia/index.html"]:
        text = (ROOT / route).read_text(encoding="utf-8")
        assert text.count("MIA-RELEASE-SCHEDULE:START") == 1
        for term in ["花言葉", "百万告", "Hello Hello Halloween", "2026-09-21"]:
            assert term in text
    news = (ROOT / "news/enomoto-mia-september-21-double-release/index.html").read_text(encoding="utf-8")
    assert '"NewsArticle"' in news and '"BreadcrumbList"' in news
    assert "配信先URL、各配信ストア、追加クレジットは、正式情報の確認後" in news
    hello_page = (ROOT / "releases/hello-hello-halloween/index.html").read_text(encoding="utf-8")
    assert 'content="noindex, follow"' in hello_page and "MusicRecording" not in hello_page
    search = (ROOT / "assets/data/search-v31.json").read_text(encoding="utf-8")
    for term in ["榎本魅愛", "花言葉", "百万告", "Hello Hello Halloween", "JOYSOUND", "カラオケ"]:
        assert term in search
    assert "youtube.com/watch?v=\"" not in hello_page
    print(f"MIA release schedule audit passed: {len(cms['releases'])} existing releases preserved, {len(cms['upcoming'])} upcoming work, no inferred third title or release URL.")


if __name__ == "__main__":
    main()
