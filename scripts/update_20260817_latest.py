#!/usr/bin/env python3
"""Register public works and Shorts verified on the official channel on 2026-08-17."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
DATES_PATH = ROOT / "assets/data/youtube-publish-dates.json"
SNAPSHOT_PATH = ROOT / "assets/data/official-youtube-catalog-20260817.json"
NOW = "2026-08-17T00:15:19+09:00"
CHANNEL_ID = "UCVde75yhByGQMu3SkO-fzrA"


RELEASES = [
    {
        "slug": "taipa-nante-shiranakatta",
        "title": "タイパなんて知らなかった",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "youtubeId": "s0zOTuR4GQI",
        "youtubeUrl": "https://www.youtube.com/watch?v=s0zOTuR4GQI",
        "shortsUrl": "https://www.youtube.com/shorts/HJugNSYcBI0",
        "publishedAt": "2026-08-16T19:00:06+09:00",
        "duration": 265,
        "image": "https://i.ytimg.com/vi/s0zOTuR4GQI/maxresdefault.jpg",
        "description": "待つこと、迷うこと、遠回りすることを、便利になった今だからこそ思い出す榎本魅愛の作品。",
        "genres": ["J-POP"],
        "themes": ["時間", "思い出", "明日"],
        "tags": ["JPOP", "平成の思い出", "令和", "タイパ", "懐かしい"],
        "source": "official-youtube-liveBroadcastDetails.startTimestamp",
    },
    {
        "slug": "family-portrait",
        "title": "FAMILY PORTRAIT",
        "artist": "NOX",
        "artistSlug": "nox",
        "youtubeId": "QOn7Jfq9t1k",
        "youtubeUrl": "https://www.youtube.com/watch?v=QOn7Jfq9t1k",
        "shortsUrl": "https://www.youtube.com/shorts/pZTC_mEwl5s",
        "publishedAt": "2026-08-15T20:00:06+09:00",
        "duration": 274,
        "image": "https://i.ytimg.com/vi/QOn7Jfq9t1k/maxresdefault.jpg",
        "description": "写真には写らない喧嘩、沈黙、涙、裏切りと、幸せな家族を演じる笑顔を描くNOXの作品。",
        "genres": ["V系", "ゴシックロック"],
        "themes": ["家族", "真実", "笑顔"],
        "tags": ["FAMILYPORTRAIT", "VisualKei", "ビジュアル系", "V系", "ゴシックロック"],
        "source": "official-youtube-liveBroadcastDetails.startTimestamp",
    },
    {
        "slug": "false-identity",
        "title": "FALSE//IDENTITY",
        "artist": "ECLYPSE",
        "artistSlug": "eclypse",
        "youtubeId": "jGyeBZmhgKc",
        "youtubeUrl": "https://www.youtube.com/watch?v=jGyeBZmhgKc",
        "shortsUrl": "",
        "publishedAt": "2026-08-14T22:10:08+09:00",
        "duration": 310,
        "image": "https://i.ytimg.com/vi/jGyeBZmhgKc/maxresdefault.jpg",
        "description": "書き換えられた記憶、失われたIDENTITY、存在しないはずの6人目を描くECLYPSE 4th Single。",
        "genres": ["K-POP風", "Dark K-POP"],
        "themes": ["記憶", "IDENTITY", "監視"],
        "tags": ["FALSEIDENTITY", "KPOP", "DarkKPOP", "Cyberpunk"],
        "relatedReleases": ["shadow-code", "red-moon-rising", "lost-signal"],
        "source": "official-youtube-playerMicroformatRenderer.publishDate",
    },
]

SHORTS = [
    {
        "videoId": "HJugNSYcBI0",
        "title": "タイパなんて知らなかった。｜榎本魅愛 #Shorts",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "youtubeUrl": "https://www.youtube.com/shorts/HJugNSYcBI0",
        "publishedAt": "2026-08-15T16:13:18+09:00",
        "relatedRelease": "taipa-nante-shiranakatta",
        "thumbnail": "https://i.ytimg.com/vi/HJugNSYcBI0/maxresdefault.jpg",
        "status": "published",
        "contentType": "short",
        "duration": 31,
        "description": "榎本魅愛「タイパなんて知らなかった」の公式Shorts。",
    },
    {
        "videoId": "pZTC_mEwl5s",
        "title": "NOX『FAMILY PORTRAIT』― この家族写真、どこかおかしい。【Official Short MV】",
        "artist": "NOX",
        "artistSlug": "nox",
        "youtubeUrl": "https://www.youtube.com/shorts/pZTC_mEwl5s",
        "publishedAt": "2026-08-14T21:38:30+09:00",
        "relatedRelease": "family-portrait",
        "thumbnail": "https://i.ytimg.com/vi/pZTC_mEwl5s/maxresdefault.jpg",
        "status": "published",
        "contentType": "short",
        "duration": 25,
        "description": "NOX「FAMILY PORTRAIT」のOfficial Short MV。",
    },
]


def release_record(item: dict, artist_type: str) -> dict:
    published = item["publishedAt"]
    tags = list(dict.fromkeys([*item["tags"], *item["genres"], *item["themes"]]))
    return {
        "slug": item["slug"], "id": item["slug"], "title": item["title"],
        "displayTitle": item["title"], "englishTitle": item["title"],
        "artist": item["artist"], "artistSlug": item["artistSlug"],
        "artistSlugs": [item["artistSlug"]], "artistType": artist_type,
        "releaseAt": published, "releaseDate": published[:10], "releaseYear": 2026,
        "releaseType": "single", "genres": item["genres"], "moods": [],
        "themes": item["themes"], "tags": tags, "language": "ja",
        "coverImage": item["image"],
        "coverAlt": f'{item["artist"]}「{item["title"]}」公式YouTubeサムネイル',
        "youtubeUrl": item["youtubeUrl"], "shortsUrl": item["shortsUrl"],
        "releaseUrl": f'releases/{item["slug"]}/', "newsUrl": "", "duration": item["duration"],
        "status": "published", "featured": False, "recommendationWeight": 1,
        "weeklyPickEligible": True, "analyticsEnabled": True, "upcomingPriority": 0,
        "relatedReleases": item.get("relatedReleases", []),
        "searchKeywords": list(dict.fromkeys([item["title"], item["artist"], *tags])),
        "aiArtistType": "fictional AI artist", "publishedAt": published,
        "description": item["description"], "introduction": item["description"],
        "galleryImages": [], "galleryPublished": False,
        "productionNote": item["description"],
        "seo": {
            "title": f'{item["title"]}｜{item["artist"]}｜SUZUKA Official Music',
            "description": f'{item["description"]} SUZUKAの架空のAIアーティスト作品です。',
            "jsonLdEnabled": True,
        },
        "videoPublishDate": published[:10], "videoPublishedAt": published,
        "videoPublishedAtSource": item["source"], "videoStructuredDataStatus": "published",
        "officialSource": item["youtubeUrl"], "promotionVerifiedAt": NOW,
        "lyricsAvailable": False, "lyricsSource": "", "lyricsText": "",
        "lyricsVerified": False, "lyricsVerifiedAt": None,
    }


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    artists = {item["slug"]: item for item in cms["artists"]}
    releases = {item["slug"]: item for item in cms["releases"]}
    for item in RELEASES:
        releases[item["slug"]] = release_record(item, artists[item["artistSlug"]]["type"])
    cms["releases"] = sorted(releases.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True)

    snapshot = cms.setdefault("youtubeSnapshot", {})
    short_videos = {item["videoId"]: item for item in snapshot.get("shortVideos", [])}
    short_videos.update({item["videoId"]: item for item in SHORTS})
    snapshot.update({
        "officialVideos": 55, "shorts": 34, "verifiedAt": NOW,
        "source": "公式YouTubeチャンネルのvideos/shortsタブと各動画をyt-dlpで照合",
        "shortVideos": sorted(short_videos.values(), key=lambda item: (item["publishedAt"], item["videoId"]), reverse=True),
    })
    cms["updatedAt"] = NOW
    CMS_PATH.write_text(json.dumps(cms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    dates = json.loads(DATES_PATH.read_text(encoding="utf-8"))
    records = {item["youtubeId"]: item for item in dates["records"]}
    for item in RELEASES:
        records[item["youtubeId"]] = {
            "releaseSlug": item["slug"], "youtubeId": item["youtubeId"],
            "youtubeUrl": item["youtubeUrl"], "catalogReleaseDate": item["publishedAt"][:10],
            "officialTitle": item["title"], "channelId": CHANNEL_ID, "channelVerified": True,
            "youtubePublishDate": item["publishedAt"], "youtubeUploadDate": item["publishedAt"],
            "liveStartTimestamp": item["publishedAt"] if "liveBroadcastDetails" in item["source"] else "",
            "playabilityStatus": "OK", "durationSeconds": item["duration"],
            "verifiedPublishedAt": item["publishedAt"], "verificationSource": item["source"],
            "status": "verified-datetime",
        }
    for item in SHORTS:
        records[item["videoId"]] = {
            "releaseSlug": item["relatedRelease"], "youtubeId": item["videoId"],
            "youtubeUrl": item["youtubeUrl"], "catalogReleaseDate": item["publishedAt"][:10],
            "officialTitle": item["title"], "channelId": CHANNEL_ID, "channelVerified": True,
            "youtubePublishDate": item["publishedAt"], "youtubeUploadDate": item["publishedAt"],
            "liveStartTimestamp": "", "playabilityStatus": "OK", "durationSeconds": item["duration"],
            "verifiedPublishedAt": item["publishedAt"],
            "verificationSource": "official-youtube-timestamp-and-description",
            "status": "verified-datetime", "contentType": "short",
        }
    dates["checkedAt"] = NOW
    dates["records"] = sorted(records.values(), key=lambda item: (item["releaseSlug"], item["youtubeId"]))
    DATES_PATH.write_text(json.dumps(dates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    SNAPSHOT_PATH.write_text(json.dumps({
        "schemaVersion": "1.1", "verifiedAt": NOW, "officialChannelId": CHANNEL_ID,
        "channelUrl": "https://www.youtube.com/@suzuka1209",
        "verificationMethod": "公式YouTubeの公開状態・タイトル・description・公開日時・再生可否をyt-dlpで照合",
        "channelSnapshot": {"officialVideos": 55, "shorts": 34},
        "published": RELEASES, "shorts": snapshot["shortVideos"],
        "upcomingHeld": [
            {"videoId": "CPIDy31wnc4", "title": "たった1人の君へ", "scheduledAt": "2026-08-17T20:00:00+09:00", "status": "upcoming"},
            {"videoId": "rsrkmzJM1kk", "title": "私の選んだ道", "status": "upcoming-time-unconfirmed"},
            {"videoId": "8xRXgVv0Z_o", "title": "friendlikesong", "status": "upcoming-time-unconfirmed"},
            {"videoId": "IbydSXmEyVQ", "title": "friendlikesong MV", "status": "upcoming-time-unconfirmed"},
            {"videoId": "9vt1rkClDos", "title": "分かれた道", "status": "upcoming-time-unconfirmed"},
        ],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"registeredReleases": [item["slug"] for item in RELEASES], "registeredShorts": [item["videoId"] for item in SHORTS]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
