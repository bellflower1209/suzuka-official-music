#!/usr/bin/env python3
"""Regression audit for the 2026-09-24 SUZUKA source synchronization."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from release_state import publishable_lyrics


ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 9, 24)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    cms = json.loads(read("assets/data/creator-cms.json"))
    books = json.loads(read("assets/data/photobooks.json"))["photobooks"]
    snapshot = json.loads(read("assets/data/tunecore-catalog-20260924.json"))
    search = json.loads(read("assets/data/search-v31.json"))["documents"]

    assert (len(cms["artists"]), len(cms["releases"]), len(cms["upcoming"]), len(cms["news"])) == (10, 64, 4, 44)
    assert len(publishable_lyrics(cms["releases"])) == 19
    assert len([book for book in books if book["status"] == "published"]) == 4
    assert snapshot["summary"] == {"total": 21, "published": 13, "scheduled": 7, "underReview": 1}

    release_slugs = {item["slug"] for item in cms["releases"]}
    upcoming_slugs = {item["slug"] for item in cms["upcoming"]}
    assert release_slugs.isdisjoint(upcoming_slugs)
    assert all(date.fromisoformat(item["releaseDate"]) > TODAY for item in cms["upcoming"])
    assert {"september-blue", "over-drive", "mata-kimi-ni-koi-wo-suru", "koisuru-subete-no-shunkan"} <= release_slugs
    assert upcoming_slugs == {
        "eternity-of-flower-words", "renai-taishogai-kari",
        "nando-umarekawattemo-reborn-oath", "kokoro-ni-nokoru-takaramono",
    }

    home = read("index.html")
    hero = home.split('data-home-hero', 1)[1].split('</section>', 1)[0]
    latest = home.split('id="latest"', 1)[1].split('</section>', 1)[0]
    assert "Hello Hello Halloween" in hero
    assert "また、君に恋をする。" in latest and "STREAMING RELEASE" in latest
    assert "https://linkco.re/5acNsXS6" in latest and "OFFICIAL MV" not in latest
    for marker in ('data-public-count="artists">10', 'data-public-count="releases">64', '>19</dd>', 'data-public-count="upcoming">4'):
        assert marker in home, marker

    mata = read("releases/mata-kimi-ni-koi-wo-suru/index.html")
    album = read("releases/koisuru-subete-no-shunkan/index.html")
    assert "MusicRecording" in mata and "VideoObject" not in mata and "youtube-nocookie.com" not in mata
    assert "MusicAlbum" in album and "VideoObject" not in album and "youtube-nocookie.com" not in album
    assert "https://linkco.re/5acNsXS6" in mata and "https://linkco.re/rGeEn03r" in album
    assert 'content="noindex, follow"' not in mata + album

    for slug in upcoming_slugs:
        page = read(f"releases/{slug}/index.html")
        assert 'content="noindex, follow"' in page and "UPCOMING" in page
    search_raw = json.dumps(search, ensure_ascii=False)
    for term in [
        "また、君に恋をする。", "恋するすべての瞬間", "Eternity of Flower Words",
        "恋愛対象外", "何度生まれ変わっても", "心に残る宝モノ",
        "ありのまま。", "妃みちる Official Channel",
    ]:
        assert term in search_raw, term

    news_slugs = {item["slug"] for item in cms["news"]}
    assert {
        "michiru-arinomama-photobook", "michiru-official-channel-open",
        "enomoto-mia-three-streaming-releases", "mata-kimi-ni-koi-wo-suru-streaming-release",
        "koisuru-subete-no-shunkan-streaming-release",
    } <= news_slugs
    michiru = next(item for item in cms["artists"] if item["slug"] == "michiru")
    assert michiru["instagramUrl"] == "https://www.instagram.com/suzuka12090511/"
    assert "https://www.instagram.com/suzuka12090511/" in read("artists/michiru/index.html")
    assert "https://note.com/1209bellflower/n/n599c9798e768" in read("photobooks/michiru-arinomama-just-as-i-am/index.html")

    print("2026-09-24 sync audit passed: canonical counts, dates, states, search, pages, metadata and source links are consistent.")


if __name__ == "__main__":
    main()
