#!/usr/bin/env python3
"""Audit the source-confirmed ENOMOTO MIA campaign through 2026-09-24."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cms = json.loads((ROOT / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    releases = {item["slug"]: item for item in cms["releases"]}
    upcoming = {item["slug"]: item for item in cms["upcoming"] if item.get("artistSlug") == "enomoto-mia"}
    all_slugs = [item["slug"] for group in (cms["releases"], cms["upcoming"], cms.get("comingSoon", [])) for item in group]
    assert len(set(all_slugs)) == len(all_slugs)

    expected_published = {
        "hyakumankoku": ("2026-07-12", "2026-09-21", "https://linkco.re/Qd5Tzb0q"),
        "toriatsukai-chui": ("2026-07-14", "2026-09-21", "https://linkco.re/9r6szVDg"),
        "hello-hello-halloween": ("2026-09-16", "2026-09-21", "https://linkco.re/QfzZUy6f"),
        "september-blue": ("2026-09-22", "2026-09-22", "https://linkco.re/HCvApf7V"),
        "over-drive": ("2026-09-22", "2026-09-22", "https://linkco.re/3tHVbvXs"),
        "mata-kimi-ni-koi-wo-suru": ("2026-09-23", "2026-09-23", "https://linkco.re/5acNsXS6"),
        "koisuru-subete-no-shunkan": ("2026-09-23", "2026-09-23", "https://linkco.re/rGeEn03r"),
    }
    for slug, (work_date, streaming_date, linkcore) in expected_published.items():
        item = releases[slug]
        record = item["scheduledStreamingRelease"]
        assert item["status"] == record["status"] == "published"
        assert item["releaseDate"] == work_date and record["releaseDate"] == streaming_date
        assert record["linkcoreUrl"] == linkcore and record.get("verifiedAt")

    assert not upcoming
    for slug in ["eternity-of-flower-words", "renai-taishogai-kari"]:
        item = releases[slug]
        assert item["releaseDate"] == "2026-09-26" and item["status"] == "published"
        stream=item["scheduledStreamingRelease"]
        assert stream["status"] == "published" and stream["verifiedAt"]
        assert stream["linkcoreUrl"].startswith("https://linkco.re/")
        assert not item.get("youtubeUrl")  # Streaming verification does not prove an MV.

    flower = releases["hanakotoba"]
    assert flower["streamingRelease"]["releaseDate"] == "2026-09-11"
    assert flower["streamingRelease"]["linkcoreUrl"] == "https://linkco.re/0xHr8N9e"
    assert flower["karaoke"]["startDate"] == "2026-09-18"
    assert flower["lyricist"] == "JUN" and flower["composer"] == "SUNO×JUN"
    for route in ["index.html", "artists/enomoto-mia/index.html", "schedule/index.html"]:
        text = (ROOT / route).read_text(encoding="utf-8")
        for term in ["September Blue", "Over Drive", "恋するすべての瞬間", "また、君に恋をする。"]:
            assert term in text, (route, term)

    latest = (ROOT / "index.html").read_text(encoding="utf-8").split('id="latest"', 1)[1].split('</section>', 1)[0]
    assert "Without worrying - Reimagined -" in latest and "tLStIcqnWCs" in latest
    for slug in ("september-blue", "over-drive"):
        text = (ROOT / f"releases/{slug}/index.html").read_text(encoding="utf-8")
        assert 'content="noindex, follow"' not in text and "MusicRecording" in text
    print(f"MIA schedule audit passed: {len(expected_published)} confirmed releases and {len(upcoming)} future works are correctly separated.")


if __name__ == "__main__":
    main()
