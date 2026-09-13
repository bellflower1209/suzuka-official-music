#!/usr/bin/env python3
"""Apply the verified 2026-09-13 artist directory and YouTube snapshot update."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
REMOVED_ARTISTS = {"hoshino-miu", "hoshimiya-hanon"}


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    cms["artists"] = [artist for artist in cms["artists"] if artist["slug"] not in REMOVED_ARTISTS]
    artists = {artist["slug"]: artist for artist in cms["artists"]}

    visual_updates = {
        "enomoto-mia": {
            "image": "https://i.ytimg.com/vi/vw1bP_5kZuM/maxresdefault.jpg",
            "imageAlt": "榎本魅愛「Hello Hello Halloween」公式YouTubeビジュアル",
            "imageWidth": 1280,
            "imageHeight": 720,
            "imageSource": "https://www.youtube.com/watch?v=vw1bP_5kZuM",
            "officialYoutubeChannelId": "UCRwW7smDoEB-UOHMQJJ1Jyg",
        },
        "koga-kamishiro": {
            "image": "https://i.ytimg.com/vi/g_SmyjPGIfc/maxresdefault.jpg",
            "imageAlt": "神代煌牙「魔法が解けても ― Pumpkin Carriage ―」公式YouTubeビジュアル",
            "imageWidth": 1280,
            "imageHeight": 720,
            "imageSource": "https://www.youtube.com/watch?v=g_SmyjPGIfc",
        },
        "michiru": {
            "image": "https://i.ytimg.com/vi/Hho3xHOw8pg/maxresdefault.jpg",
            "imageAlt": "妃みちる「世代を超えてママへ」公式YouTubeビジュアル",
            "imageWidth": 1280,
            "imageHeight": 720,
            "imageSource": "https://www.youtube.com/watch?v=Hho3xHOw8pg",
        },
    }
    for slug, values in visual_updates.items():
        artists[slug].update(values)

    for group_slug in ("asteria", "revive"):
        for member in artists[group_slug].get("members", []):
            if member.get("artistSlug") in REMOVED_ARTISTS:
                member.pop("artistSlug", None)

    snapshot = cms.setdefault("youtubeSnapshot", {})
    snapshot.update({
        "officialVideos": 79,
        "shorts": 54,
        "totalPublishedVideos": 133,
        "verifiedAt": "2026-09-13T00:00:00+09:00",
        "source": "SUZUKA公式YouTubeと榎本魅愛Official YouTubeのvideos/shortsタブを照合",
        "channels": [
            {
                "name": "SUZUKA",
                "role": "Label / Project Official",
                "channelUrl": "https://www.youtube.com/@suzuka1209",
                "channelId": "UCVde75yhByGQMu3SkO-fzrA",
                "officialVideos": 75,
                "shorts": 52,
                "totalPublishedVideos": 127,
            },
            {
                "name": "榎本魅愛",
                "role": "Artist Official",
                "channelUrl": "https://www.youtube.com/@enomotomia",
                "channelId": "UCRwW7smDoEB-UOHMQJJ1Jyg",
                "officialVideos": 4,
                "shorts": 2,
                "totalPublishedVideos": 6,
            },
        ],
    })
    cms["updatedAt"] = "2026-09-13T00:00:00+09:00"
    CMS_PATH.write_text(json.dumps(cms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
