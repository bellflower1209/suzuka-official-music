#!/usr/bin/env python3
"""Register the user-confirmed LinkCore pages without duplicating releases."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
LINKCORE_SOURCE = "user-provided LinkCore release page"


LINKCORE = {
    "hyakumankoku": "https://linkco.re/Qd5Tzb0q",
    "hello-hello-halloween": "https://linkco.re/QfzZUy6f",
    "toriatsukai-chui": "https://linkco.re/9r6szVDg",
    "september-blue": "https://linkco.re/HCvApf7V",
    "over-drive": "https://linkco.re/3tHVbvXs",
}


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    releases = {item["slug"]: item for item in cms["releases"]}

    # Preserve the historical release record and only attach the confirmed
    # future streaming destination to the existing work.
    million = releases["hyakumankoku"]
    scheduled = million.setdefault("scheduledStreamingRelease", {})
    scheduled["linkcoreUrl"] = LINKCORE["hyakumankoku"]
    million["searchKeywords"] = unique([
        *million.get("searchKeywords", []), "LinkCore", "配信", "2026年9月21日",
    ])

    toriatsukai = releases["toriatsukai-chui"]
    toriatsukai["scheduledStreamingRelease"] = {
        "releaseDate": "2026-09-21",
        "timezone": "Asia/Tokyo",
        "label": "SUZUKA",
        "status": "upcoming",
        "source": LINKCORE_SOURCE,
        "linkcoreUrl": LINKCORE["toriatsukai-chui"],
    }
    toriatsukai["searchKeywords"] = unique([
        *toriatsukai.get("searchKeywords", []), "LinkCore", "配信", "2026年9月21日",
    ])

    # Keep the existing TuneCore-confirmed upcoming record and enrich it with
    # the now-confirmed public LinkCore destination.
    hello = next(item for item in cms.get("upcoming", []) if item["slug"] == "hello-hello-halloween")
    hello["linkcoreUrl"] = LINKCORE["hello-hello-halloween"]
    hello["searchKeywords"] = unique([
        *hello.get("searchKeywords", []), "LinkCore", "配信", "2026年9月21日",
    ])

    confirmed_upcoming = [
        {
            "slug": "september-blue",
            "title": "September Blue",
            "artist": "榎本魅愛",
            "artistSlug": "enomoto-mia",
            "scheduledAt": "2026-09-22T00:00:00+09:00",
            "releaseDate": "2026-09-22",
            "status": "upcoming",
            "source": LINKCORE_SOURCE,
            "linkcoreUrl": LINKCORE["september-blue"],
            "searchKeywords": ["榎本魅愛", "ENOMOTO MIA", "September Blue", "LinkCore", "配信", "2026年9月22日"],
        },
        {
            "slug": "over-drive",
            "title": "Over Drive",
            "artist": "榎本魅愛",
            "artistSlug": "enomoto-mia",
            "scheduledAt": "2026-09-22T00:00:00+09:00",
            "releaseDate": "2026-09-22",
            "status": "upcoming",
            "source": LINKCORE_SOURCE,
            "linkcoreUrl": LINKCORE["over-drive"],
            "searchKeywords": ["榎本魅愛", "ENOMOTO MIA", "Over Drive", "LinkCore", "配信", "2026年9月22日"],
        },
    ]
    upcoming = [
        item for item in cms.get("upcoming", [])
        if item["slug"] not in {item["slug"] for item in confirmed_upcoming}
    ]
    existing_by_slug = {item["slug"]: item for item in upcoming}
    for item in confirmed_upcoming:
        existing_by_slug[item["slug"]] = item
    cms["upcoming"] = list(existing_by_slug.values())

    schedule = cms.setdefault("miaReleaseSchedule", {})
    activities = [
        item for item in schedule.get("activities", [])
        if item.get("title") not in {"September Blue", "Over Drive"}
    ]
    activities.extend([
        {"date": "2026-09-22", "title": "September Blue", "kind": "NEW RELEASE", "url": "releases/september-blue/"},
        {"date": "2026-09-22", "title": "Over Drive", "kind": "NEW RELEASE", "url": "releases/over-drive/"},
    ])
    schedule["activities"] = activities
    cms["updatedAt"] = "2026-09-13T00:00:00+09:00"
    CMS_PATH.write_text(json.dumps(cms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
