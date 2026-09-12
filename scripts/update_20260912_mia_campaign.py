#!/usr/bin/env python3
"""Register the confirmed September 2026 ENOMOTO MIA activity schedule."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    releases = {item["slug"]: item for item in cms["releases"]}

    million = releases["hyakumankoku"]
    million["scheduledStreamingRelease"] = {
        "releaseDate": "2026-09-21",
        "timezone": "Asia/Tokyo",
        "label": "SUZUKA",
        "status": "upcoming",
        "source": "user-confirmed-tunecore-management-screen",
        "linkcoreUrl": None,
    }
    million["searchKeywords"] = list(dict.fromkeys([
        *million.get("searchKeywords", []), "2026年9月21日", "Streaming Release", "TuneCore",
    ]))

    hello = {
        "slug": "hello-hello-halloween",
        "title": "Hello Hello Halloween",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "scheduledAt": "2026-09-21T00:00:00+09:00",
        "releaseDate": "2026-09-21",
        "releaseChannel": "streaming",
        "releaseType": "single",
        "label": "SUZUKA",
        "status": "upcoming",
        "description": "榎本魅愛「Hello Hello Halloween」は2026年9月21日リリース予定です。",
        "image": "",
        "youtubeUrl": "",
        "searchKeywords": ["榎本魅愛", "ENOMOTO MIA", "Hello Hello Halloween", "2026年9月21日", "Upcoming", "TuneCore"],
        "source": "user-confirmed-tunecore-management-screen",
    }
    cms["upcoming"] = [item for item in cms.get("upcoming", []) if item["slug"] != hello["slug"]] + [hello]

    campaign_news = {
        "slug": "enomoto-mia-september-21-double-release",
        "title": "榎本魅愛、9月21日に「百万告」「Hello Hello Halloween」2作品をリリース",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-12T00:00:00+09:00",
        "description": "榎本魅愛の「百万告」「Hello Hello Halloween」が2026年9月21日にリリース予定。9月11日の「花言葉」Streaming Release、9月18日のJOYSOUND配信から続く9月の活動をお知らせします。",
        "image": "og.png",
        "status": "published",
        "miaCampaignAnnouncement": True,
        "searchKeywords": ["榎本魅愛", "ENOMOTO MIA", "百万告", "Hello Hello Halloween", "9月21日", "連続リリース"],
    }
    cms["news"] = [item for item in cms.get("news", []) if item["slug"] != campaign_news["slug"]]
    cms["news"].insert(0, campaign_news)
    cms["miaReleaseSchedule"] = {
        "artist": "榎本魅愛",
        "artistEnglish": "ENOMOTO MIA",
        "timezone": "Asia/Tokyo",
        "activities": [
            {"date": "2026-09-11", "title": "花言葉", "kind": "NOW STREAMING", "url": "releases/hanakotoba/"},
            {"date": "2026-09-18", "title": "花言葉", "kind": "KARAOKE / JOYSOUND", "url": "news/hanakotoba-joysound-karaoke/"},
            {"date": "2026-09-21", "title": "百万告", "kind": "NEW RELEASE", "url": "releases/hyakumankoku/"},
            {"date": "2026-09-21", "title": "Hello Hello Halloween", "kind": "NEW RELEASE", "url": "releases/hello-hello-halloween/"},
        ],
        "newsUrl": "news/enomoto-mia-september-21-double-release/",
    }
    cms["updatedAt"] = "2026-09-12T00:00:00+09:00"
    CMS_PATH.write_text(json.dumps(cms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
