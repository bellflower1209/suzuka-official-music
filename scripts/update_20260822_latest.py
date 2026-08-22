#!/usr/bin/env python3
"""Apply official YouTube publication evidence verified on 2026-08-22."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
DATES_PATH = ROOT / "assets/data/youtube-publish-dates.json"
MIA_CATALOG_PATH = ROOT / "assets/data/enomoto-mia-releases.json"
SNAPSHOT_PATH = ROOT / "assets/data/official-youtube-catalog-20260822.json"
STATE_PATH = ROOT / "assets/data/official-youtube-release-state.json"
NOW = "2026-08-22T21:39:45+09:00"
CHANNEL_ID = "UCVde75yhByGQMu3SkO-fzrA"


RELEASES = [
    {
        "slug": "tatta-hitori-no-kimi-e",
        "title": "たった1人の君へ",
        "artist": "妃みちる",
        "artistSlug": "michiru",
        "releaseAt": "2026-08-17T20:00:06+09:00",
        "youtubeId": "CPIDy31wnc4",
        "youtubeUrl": "https://www.youtube.com/watch?v=CPIDy31wnc4",
        "videoPublishedAt": "2026-08-17T20:00:06+09:00",
        "duration": 338,
        "shortsUrl": "https://www.youtube.com/shorts/HuWmUFlwh6s",
        "description": "過去の大切な人への感謝と、今の幸せを歌う、妃みちるのデビューシングル。",
        "genres": ["J-POP", "アコースティック"],
        "themes": ["恋愛", "感謝"],
        "tags": ["シンガーソングライター", "JPOP", "アコースティック", "恋愛ソング", "青春"],
        "relatedReleases": ["watashi-no-eranda-michi", "friendlikesong"],
    },
    {
        "slug": "watashi-no-eranda-michi",
        "title": "私の選んだ道",
        "artist": "妃みちる",
        "artistSlug": "michiru",
        "releaseAt": "2026-08-18T20:00:06+09:00",
        "youtubeId": "rsrkmzJM1kk",
        "youtubeUrl": "https://www.youtube.com/watch?v=rsrkmzJM1kk",
        "videoPublishedAt": "2026-08-18T20:00:06+09:00",
        "duration": 322,
        "shortsUrl": "https://www.youtube.com/shorts/hjqiZqPdrv8",
        "description": "好きだった人の幸せを願い、自分で選んだ道を歩いてきた過去の自分へ贈る妃みちるの作品。",
        "genres": ["J-POP", "バラード"],
        "themes": ["初恋", "別れ", "未来"],
        "tags": ["妃みちる", "失恋ソング", "恋愛ソング", "青春", "初恋", "バラード"],
        "relatedReleases": ["tatta-hitori-no-kimi-e"],
    },
    {
        "slug": "friendlikesong",
        "title": "friendlikesong",
        "artist": "妃みちる",
        "artistSlug": "michiru",
        "releaseAt": "2026-08-19T20:00:06+09:00",
        "youtubeId": "IbydSXmEyVQ",
        "youtubeUrl": "https://www.youtube.com/watch?v=IbydSXmEyVQ",
        "videoPublishedAt": "2026-08-20T20:00:06+09:00",
        "duration": 263,
        "audioUrl": "https://www.youtube.com/watch?v=8xRXgVv0Z_o",
        "shortsUrl": "https://www.youtube.com/shorts/QG2KN01CsJ4",
        "description": "大人になっても変わらない仲間との、最高の夏の一日を描く妃みちるのサマーソング。",
        "genres": ["J-POP", "サマーソング"],
        "themes": ["友情", "夏", "仲間"],
        "tags": ["妃みちる", "friendlikesong", "夏ソング", "海", "友情", "仲間"],
        "relatedReleases": ["tatta-hitori-no-kimi-e"],
    },
    {
        "slug": "wakareta-michi",
        "title": "分かれた道",
        "artist": "神代煌牙",
        "artistSlug": "koga-kamishiro",
        "releaseAt": "2026-08-21T20:00:06+09:00",
        "youtubeId": "EU_5CqN1zZw",
        "youtubeUrl": "https://www.youtube.com/watch?v=EU_5CqN1zZw",
        "videoPublishedAt": "2026-08-22T20:00:06+09:00",
        "duration": 319,
        "audioUrl": "https://www.youtube.com/watch?v=9vt1rkClDos",
        "shortsUrl": "https://www.youtube.com/shorts/ksYJEnyC284",
        "description": "愛していた相手の未来を尊重し、それぞれの道を歩き始める決断を描く神代煌牙の作品。",
        "genres": ["J-POP", "J-ROCK", "Dark Pop"],
        "themes": ["別れ", "未来", "祈り"],
        "tags": ["神代煌牙", "分かれた道", "CinematicJPOP", "JROCK", "失恋ソング", "別れの歌"],
        "relatedReleases": [],
    },
]


SHORTS = [
    {
        "videoId": "ksYJEnyC284",
        "title": "【MV】愛してるからこそ、手を離した。｜神代煌牙『分かれた道』",
        "artist": "神代煌牙",
        "artistSlug": "koga-kamishiro",
        "youtubeUrl": "https://www.youtube.com/shorts/ksYJEnyC284",
        "publishedAt": "2026-08-17T21:31:55+09:00",
        "relatedRelease": "wakareta-michi",
        "thumbnail": "https://i.ytimg.com/vi/ksYJEnyC284/maxresdefault.jpg",
        "status": "published",
        "contentType": "short",
        "duration": 40,
        "description": "神代煌牙『分かれた道』Official MVの先行公開Shorts。",
    },
    {
        "videoId": "wpzMoz2LgWE",
        "title": "【先行公開】榎本魅愛『花言葉』｜8月19日20時 フルMV解禁｜両親の結婚記念日に #shorts",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "youtubeUrl": "https://www.youtube.com/shorts/wpzMoz2LgWE",
        "publishedAt": "2026-08-19T01:54:13+09:00",
        "relatedRelease": "hanakotoba",
        "thumbnail": "https://i.ytimg.com/vi/wpzMoz2LgWE/maxresdefault.jpg",
        "status": "published",
        "contentType": "short",
        "duration": 40,
        "description": "榎本魅愛『花言葉』フルMVの公開を案内する公式Shorts。",
    },
    {
        "videoId": "hjqiZqPdrv8",
        "title": "【8/23 MV解禁】15歳の私が選んだ、好きな人を追わない道｜妃みちる『私の選んだ道』",
        "artist": "妃みちる",
        "artistSlug": "michiru",
        "youtubeUrl": "https://www.youtube.com/shorts/hjqiZqPdrv8",
        "publishedAt": "2026-08-19T22:26:01+09:00",
        "relatedRelease": "watashi-no-eranda-michi",
        "thumbnail": "https://i.ytimg.com/vi/hjqiZqPdrv8/maxresdefault.jpg",
        "status": "published",
        "contentType": "short",
        "duration": 86,
        "description": "妃みちる『私の選んだ道』MVの公開予定を案内する公式Shorts。",
    },
]


VIDEO_EVIDENCE = [
    ("tatta-hitori-no-kimi-e", "CPIDy31wnc4", "妃みちる『たった1人の君へ』Official Music ｜SUZUKA Debut Single", "2026-08-17T20:00:06+09:00", 338, "official-youtube-liveBroadcastDetails.startTimestamp"),
    ("watashi-no-eranda-michi", "rsrkmzJM1kk", "妃みちる『私の選んだ道』｜15歳の私が選んだ、好きだから離れるという恋", "2026-08-18T20:00:06+09:00", 322, "official-youtube-liveBroadcastDetails.startTimestamp"),
    ("friendlikesong", "8xRXgVv0Z_o", "friendlikesong / 妃みちる｜HEY GIRL！HEY BOY！今年の夏、仲間と騒げ", "2026-08-19T20:00:06+09:00", 262, "official-youtube-liveBroadcastDetails.startTimestamp"),
    ("friendlikesong", "IbydSXmEyVQ", "【MV】friendlikesong / 妃みちる｜何年経っても、変わらないメンツで。", "2026-08-20T20:00:06+09:00", 263, "official-youtube-liveBroadcastDetails.startTimestamp"),
    ("wakareta-michi", "9vt1rkClDos", "【8/21 20:00解禁】分かれた道 / 神代煌牙｜愛してるからこそ、手を離した。", "2026-08-21T20:00:06+09:00", 319, "official-youtube-liveBroadcastDetails.startTimestamp"),
    ("wakareta-michi", "EU_5CqN1zZw", "【Official MV】神代煌牙 - 分かれた道｜愛していた。だから、手を離した。", "2026-08-22T20:00:06+09:00", 319, "official-youtube-liveBroadcastDetails.startTimestamp"),
    ("hanakotoba", "iinLScSzA9w", "【MV】榎本魅愛『花言葉』｜両親の結婚記念日に贈る“永遠”の物語", "2026-08-19T20:00:06+09:00", 234, "official-youtube-liveBroadcastDetails.startTimestamp"),
]


def release_record(item: dict, artist_type: str) -> dict:
    release_at = item["releaseAt"]
    video_at = item["videoPublishedAt"]
    cover = f'https://i.ytimg.com/vi/{item["youtubeId"]}/maxresdefault.jpg'
    tags = list(dict.fromkeys([*item["tags"], *item["genres"], *item["themes"]]))
    result = {
        "slug": item["slug"], "id": item["slug"], "title": item["title"],
        "displayTitle": item["title"], "englishTitle": item["title"],
        "artist": item["artist"], "artistSlug": item["artistSlug"],
        "artistSlugs": [item["artistSlug"]], "artistType": artist_type,
        "releaseAt": release_at, "publishedAt": release_at,
        "releaseDate": release_at[:10], "releaseYear": 2026, "releaseType": "single",
        "genres": item["genres"], "moods": [], "themes": item["themes"],
        "tags": tags, "language": "ja", "coverImage": cover,
        "coverAlt": f'{item["artist"]}「{item["title"]}」公式YouTubeサムネイル',
        "youtubeUrl": item["youtubeUrl"], "shortsUrl": item["shortsUrl"],
        "releaseUrl": f'releases/{item["slug"]}/', "newsUrl": "", "duration": item["duration"],
        "status": "published", "featured": False, "recommendationWeight": 1,
        "weeklyPickEligible": True, "analyticsEnabled": True, "upcomingPriority": 0,
        "relatedReleases": item["relatedReleases"],
        "searchKeywords": list(dict.fromkeys([item["title"], item["artist"], *tags])),
        "aiArtistType": "fictional AI artist", "description": item["description"],
        "introduction": item["description"], "galleryImages": [], "galleryPublished": False,
        "productionNote": item["description"],
        "seo": {
            "title": f'{item["title"]}｜{item["artist"]}｜SUZUKA Official Music',
            "description": f'{item["description"]} SUZUKAの架空のAIアーティスト作品です。',
            "jsonLdEnabled": True,
        },
        "videoPublishDate": video_at[:10], "videoPublishedAt": video_at,
        "videoPublishedAtSource": "official-youtube-liveBroadcastDetails.startTimestamp",
        "videoStructuredDataStatus": "published", "officialSource": item["youtubeUrl"],
        "promotionVerifiedAt": NOW, "lyricsAvailable": False, "lyricsSource": "",
        "lyricsText": "", "lyricsVerified": False, "lyricsVerifiedAt": None,
    }
    if item.get("audioUrl"):
        result["audioUrl"] = item["audioUrl"]
    return result


def evidence_record(slug: str, video_id: str, title: str, published_at: str, duration: int, source: str, *, content_type: str = "video") -> dict:
    return {
        "releaseSlug": slug, "youtubeId": video_id,
        "youtubeUrl": f"https://www.youtube.com/{'shorts/' if content_type == 'short' else 'watch?v='}{video_id}",
        "catalogReleaseDate": published_at[:10], "officialTitle": title,
        "channelId": CHANNEL_ID, "channelVerified": True,
        "youtubePublishDate": published_at, "youtubeUploadDate": published_at,
        "liveStartTimestamp": published_at if content_type != "short" else "",
        "playabilityStatus": "OK", "durationSeconds": duration,
        "verifiedPublishedAt": published_at, "verificationSource": source,
        "status": "verified-datetime", **({"contentType": "short"} if content_type == "short" else {}),
    }


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    artists = {item["slug"]: item for item in cms["artists"]}
    releases = {item["slug"]: item for item in cms["releases"]}
    for item in RELEASES:
        releases[item["slug"]] = release_record(item, artists[item["artistSlug"]]["type"])

    hanakotoba = releases["hanakotoba"]
    hanakotoba.update({
        "youtubeUrl": "https://www.youtube.com/watch?v=iinLScSzA9w",
        "shortsUrl": "https://www.youtube.com/shorts/wpzMoz2LgWE",
        "audioUrl": "https://www.youtube.com/watch?v=mdTogs4Oiew",
        "videoPublishDate": "2026-08-19",
        "videoPublishedAt": "2026-08-19T20:00:06+09:00",
        "videoPublishedAtSource": "official-youtube-liveBroadcastDetails.startTimestamp",
        "officialSource": "https://www.youtube.com/watch?v=iinLScSzA9w",
        "promotionVerifiedAt": NOW,
    })
    cms["releases"] = sorted(releases.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True)
    promoted = {item["slug"] for item in RELEASES}
    cms["upcoming"] = [item for item in cms.get("upcoming", []) if item["slug"] not in promoted]

    for slug, featured in {
        "michiru": ["friendlikesong", "watashi-no-eranda-michi", "tatta-hitori-no-kimi-e"],
        "koga-kamishiro": ["wakareta-michi", "one-more-kiss", "echoes-of-you"],
    }.items():
        artists[slug]["artistFeaturedTracks"] = featured

    snapshot = cms.setdefault("youtubeSnapshot", {})
    short_videos = {item["videoId"]: item for item in snapshot.get("shortVideos", [])}
    short_videos.update({item["videoId"]: item for item in SHORTS})
    snapshot.update({
        "officialVideos": 58, "shorts": 37, "verifiedAt": NOW,
        "source": "公式YouTubeフィード・videos/shortsタブ・各動画のytInitialPlayerResponseを照合",
        "shortVideos": sorted(short_videos.values(), key=lambda item: (item["publishedAt"], item["videoId"]), reverse=True),
    })
    cms["updatedAt"] = NOW
    CMS_PATH.write_text(json.dumps(cms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    dates = json.loads(DATES_PATH.read_text(encoding="utf-8"))
    records = {(item["releaseSlug"], item.get("youtubeId", "")): item for item in dates["records"]}
    for values in VIDEO_EVIDENCE:
        record = evidence_record(*values)
        records[(record["releaseSlug"], record["youtubeId"])] = record
    for item in SHORTS:
        record = evidence_record(
            item["relatedRelease"], item["videoId"], item["title"], item["publishedAt"], item["duration"],
            "official-youtube-feed-and-playerMicroformatRenderer.publishDate", content_type="short",
        )
        records[(record["releaseSlug"], record["youtubeId"])] = record
    dates["checkedAt"] = NOW
    dates["records"] = sorted(records.values(), key=lambda item: (item["releaseSlug"], item.get("youtubeId", "")))
    DATES_PATH.write_text(json.dumps(dates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    mia_catalog = json.loads(MIA_CATALOG_PATH.read_text(encoding="utf-8"))
    mia_hanakotoba = next(item for item in mia_catalog["releases"] if item["slug"] == "hanakotoba")
    mia_hanakotoba.update({
        "youtubeUrl": "https://www.youtube.com/watch?v=iinLScSzA9w",
        "youtubeId": "iinLScSzA9w",
        "youtubeVideoTitle": "【MV】榎本魅愛『花言葉』｜両親の結婚記念日に贈る“永遠”の物語",
        "uploadDate": "2026-08-19",
        "shortsUrl": "https://www.youtube.com/shorts/wpzMoz2LgWE",
    })
    MIA_CATALOG_PATH.write_text(json.dumps(mia_catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    snapshot_payload = {
        "schemaVersion": "1.2", "verifiedAt": NOW, "officialChannelId": CHANNEL_ID,
        "channelUrl": "https://www.youtube.com/@suzuka1209",
        "verificationMethod": "公式YouTube Atomフィード、videos/shortsタブ、各動画のytInitialPlayerResponseを照合",
        "channelSnapshot": {"officialVideos": 58, "shorts": 37},
        "published": RELEASES,
        "updatedVideos": [{
            "releaseSlug": "hanakotoba", "videoId": "iinLScSzA9w",
            "youtubeUrl": "https://www.youtube.com/watch?v=iinLScSzA9w",
            "publishedAt": "2026-08-19T20:00:06+09:00", "duration": 234,
            "status": "published", "playabilityStatus": "OK",
        }],
        "shorts": snapshot["shortVideos"],
        "upcomingHeld": [{
            "videoId": "FC1D7-0SeBc", "title": "【MV】妃みちる『私の選んだ道』｜好きだから、追わない道を選んだ。",
            "scheduledAt": "2026-08-23T20:00:00+09:00", "relatedRelease": "watashi-no-eranda-michi",
            "status": "upcoming", "playabilityStatus": "LIVE_STREAM_OFFLINE",
        }],
    }
    SNAPSHOT_PATH.write_text(json.dumps(snapshot_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STATE_PATH.write_text(json.dumps({
        "schemaVersion": "1.0", "verifiedAt": NOW, "officialChannelId": CHANNEL_ID,
        "promoted": sorted(promoted),
        "evidence": [{
            "slug": item["slug"], "videoId": item["youtubeId"], "availability": "public",
            "liveStatus": "was_live", "releaseTimestamp": item["videoPublishedAt"], "channelId": CHANNEL_ID,
        } for item in RELEASES],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"promoted": sorted(promoted), "newShorts": [item["videoId"] for item in SHORTS], "upcoming": len(cms["upcoming"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
