#!/usr/bin/env python3
"""Apply official YouTube and note evidence verified on 2026-08-31."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
DATES_PATH = ROOT / "assets/data/youtube-publish-dates.json"
STATE_PATH = ROOT / "assets/data/official-youtube-release-state.json"
PHOTOBOOKS_PATH = ROOT / "assets/data/photobooks.json"
SNAPSHOT_PATH = ROOT / "assets/data/official-youtube-catalog-20260831.json"
NOW = "2026-08-31T21:30:00+09:00"
CHANNEL_ID = "UCVde75yhByGQMu3SkO-fzrA"


NEW_RELEASES = [
    {
        "slug": "akuyaku-de-ii",
        "title": "悪役でいい",
        "artist": "神代煌牙",
        "artistSlug": "koga-kamishiro",
        "releaseAt": "2026-08-31T20:00:18+09:00",
        "youtubeId": "pESx9p7lIHw",
        "youtubeUrl": "https://www.youtube.com/watch?v=pESx9p7lIHw",
        "duration": 315,
        "officialTitle": "【新曲】神代煌牙『悪役でいい』｜Official Audio｜MV制作決定",
        "description": "世界に悪と呼ばれても、大切な人が選んだ道の隣にいるという神代煌牙の護る決意を歌う新曲。",
        "genres": ["J-POP", "J-ROCK", "Dark Pop"],
        "moods": ["ダーク", "力強い"],
        "themes": ["護る", "決意", "悪役"],
        "tags": ["神代煌牙", "悪役でいい", "KOGA KAMISHIRO", "Official Audio", "Black Knight"],
        "videoLabel": "OFFICIAL AUDIO",
        "videoCtaLabel": "公式音源を聴く",
        "videoButtonLabel": "LISTEN",
        "coverAlt": "神代煌牙「悪役でいい」公式YouTubeサムネイル",
    },
    {
        "slug": "iine-sougisha",
        "title": "いいね葬儀社",
        "artist": "NOX",
        "artistSlug": "nox",
        "releaseAt": "2026-08-29T20:00:06+09:00",
        "youtubeId": "lP_OZ_6hu-0",
        "youtubeUrl": "https://www.youtube.com/watch?v=lP_OZ_6hu-0",
        "duration": 227,
        "officialTitle": "【MV】死んだ途端、みんな「大好きでした」｜NOX『いいね葬儀社』",
        "description": "死の後だけ届く優しさと、悲しみさえ投稿に変えるSNS時代を風刺するNOXのダークロック。",
        "genres": ["V系", "ダークロック", "邦ロック"],
        "moods": ["ダーク", "挑発的"],
        "themes": ["SNS", "承認欲求", "社会風刺"],
        "tags": ["NOX", "いいね葬儀社", "Visual Kei", "ブラックユーモア", "Music Video"],
        "videoLabel": "OFFICIAL MV",
        "videoCtaLabel": "公式MVを見る",
        "videoButtonLabel": "WATCH MV",
        "coverAlt": "NOX「いいね葬儀社」公式YouTubeサムネイル",
    },
]


PROMOTIONAL_VIDEO = {
    "videoId": "dKnu4aEwkIY",
    "title": "【重大発表】榎本魅愛、アニメOP決定。『また、君に恋をする』",
    "artist": "榎本魅愛",
    "artistSlug": "enomoto-mia",
    "publishedAt": "2026-08-30T20:36:02+09:00",
    "duration": 25,
    "youtubeUrl": "https://www.youtube.com/watch?v=dKnu4aEwkIY",
    "status": "published",
    "contentType": "promotional-video",
    "releaseStatus": "not-promoted-as-full-release",
    "description": "アニメ「それでも、僕は君を探していた」のオープニングテーマ決定を伝える公式映像。アニメ本編の公開日は未定。",
}


NEW_SHORTS = [
    {
        "videoId": "kIs_YvTk8hE",
        "title": "【重大発表】榎本魅愛、アニメOP決定。『また、君に恋をする』",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-08-30T20:40:37+09:00",
        "relatedRelease": "",
        "duration": 25,
        "description": "榎本魅愛が担当するアニメOP「また、君に恋をする」の公式Shorts。",
    },
    {
        "videoId": "UVKSB3-Itqw",
        "title": "死んだ途端、みんな「大好きでした」｜本日20:00公開『いいね葬儀社』",
        "artist": "NOX",
        "artistSlug": "nox",
        "publishedAt": "2026-08-29T19:37:07+09:00",
        "relatedRelease": "iine-sougisha",
        "duration": 27,
        "description": "NOX「いいね葬儀社」公閏MVの公開を告知する公式Shorts。",
    },
    {
        "videoId": "5P30pcwkd80",
        "title": "死んだ途端、みんな優しくなった。｜NOX「いいね葬儀社」フルMV制作中",
        "artist": "NOX",
        "artistSlug": "nox",
        "publishedAt": "2026-08-28T22:51:11+09:00",
        "relatedRelease": "iine-sougisha",
        "duration": 45,
        "description": "NOX「いいね葬儀社」の世界観を紹介する公式Shorts。",
    },
]


PHOTOBOOK = {
    "id": "koga-kamishiro-black-knight",
    "slug": "koga-kamishiro-black-knight",
    "title": "【神代煌牙 1st Digital Photo Book】BLACK KNIGHT ── この声は、守るためにある。",
    "artistSlug": "koga-kamishiro",
    "coverImage": "images/photobook-koga-black-knight.jpg",
    "coverAlt": "神代煌牙 1st Digital Photo Book『BLACK KNIGHT』公式表紙",
    "coverWidth": 1280,
    "coverHeight": 670,
    "noteUrl": "https://note.com/1209bellflower/n/nc291360c9532",
    "publishedAt": "2026-08-09T02:17:04+09:00",
    "status": "published",
    "description": "夜の街に立つ神代煌牙を通して、孤独、傷、弱さ、欲望、誓いと「守る」意志を描く、神代煌牙初の公式デジタル写真集。",
    "relatedReleaseSlugs": [],
    "featured": True,
    "isPaid": True,
    "priceLabel": "¥300",
    "contentType": "Digital Photo Book",
    "sourceVerifiedAt": NOW,
}


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_release(item: dict, artist_type: str) -> dict:
    release_at = item["releaseAt"]
    tags = list(dict.fromkeys([*item["tags"], *item["genres"], *item["themes"], *item["moods"]]))
    cover = f'https://i.ytimg.com/vi/{item["youtubeId"]}/maxresdefault.jpg'
    release = {
        "slug": item["slug"], "id": item["slug"], "title": item["title"],
        "displayTitle": item["title"], "englishTitle": item["title"],
        "artist": item["artist"], "artistSlug": item["artistSlug"],
        "artistSlugs": [item["artistSlug"]], "artistType": artist_type,
        "releaseAt": release_at, "publishedAt": release_at,
        "releaseDate": release_at[:10], "releaseYear": 2026, "releaseType": "single",
        "genres": item["genres"], "moods": item["moods"], "themes": item["themes"],
        "tags": tags, "language": "ja", "coverImage": cover, "coverAlt": item["coverAlt"],
        "youtubeUrl": item["youtubeUrl"], "youtubeVideoTitle": item["officialTitle"],
        "videoLabel": item["videoLabel"], "videoCtaLabel": item["videoCtaLabel"],
        "videoButtonLabel": item["videoButtonLabel"], "shortsUrl": "",
        "releaseUrl": f'releases/{item["slug"]}/', "newsUrl": f'news/{item["slug"]}-release/',
        "duration": item["duration"], "status": "published", "featured": True,
        "recommendationWeight": 4, "weeklyPickEligible": True,
        "analyticsEnabled": True, "upcomingPriority": 0, "relatedReleases": [],
        "searchKeywords": list(dict.fromkeys([item["title"], item["artist"], *tags])),
        "aiArtistType": "fictional AI artist", "description": item["description"],
        "introduction": item["description"], "galleryImages": [],
        "galleryPublished": False, "productionNote": item["description"],
        "seo": {
            "title": f'{item["title"]}｜{item["artist"]}｜SUZUKA Official Music',
            "description": f'{item["description"]} SUZUKAの架空のAIアーティスト作品です。',
            "jsonLdEnabled": True,
        },
        "videoPublishDate": release_at[:10], "videoPublishedAt": release_at,
        "videoPublishedAtSource": "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate",
        "videoStructuredDataStatus": "published", "officialSource": item["youtubeUrl"],
        "promotionVerifiedAt": NOW, "lyricsAvailable": False, "lyricsSource": "",
        "lyricsText": "", "lyricsVerified": False, "lyricsVerifiedAt": None,
    }
    if item["slug"] == "akuyaku-de-ii":
        release["homeHero"] = {
            "title": "SUZUKA Official | 神代煌牙「悪役でいい」公開中",
            "description": "神代煌牙の最新曲「悪役でいい」Official Audioを公開中。作品・Artist・NewsをSUZUKA公式サイトで紹介します。",
            "subtitle": "神代煌牙 New Single / Official Audio",
            "status": "Now Streaming",
        }
    return release


def short_record(item: dict) -> dict:
    video_id = item["videoId"]
    return {
        **item,
        "youtubeUrl": f"https://www.youtube.com/shorts/{video_id}",
        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        "status": "published", "contentType": "short",
    }


def evidence_record(slug: str, item: dict, content_type: str = "video") -> dict:
    video_id = item.get("videoId") or item["youtubeId"]
    published_at = item.get("releaseAt") or item["publishedAt"]
    url = f"https://www.youtube.com/{'shorts/' if content_type == 'short' else 'watch?v='}{video_id}"
    return {
        "releaseSlug": slug, "youtubeId": video_id, "youtubeUrl": url,
        "catalogReleaseDate": published_at[:10],
        "officialTitle": item.get("officialTitle") or item["title"],
        "channelId": CHANNEL_ID, "channelVerified": True,
        "youtubePublishDate": published_at, "youtubeUploadDate": published_at,
        "liveStartTimestamp": "", "playabilityStatus": "OK",
        "durationSeconds": item["duration"], "verifiedPublishedAt": published_at,
        "verificationSource": "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate",
        "status": "verified-datetime",
        **({"contentType": "short"} if content_type == "short" else {}),
    }


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    artists = {item["slug"]: item for item in cms["artists"]}
    releases = {item["slug"]: item for item in cms["releases"]}
    for item in NEW_RELEASES:
        releases[item["slug"]] = create_release(item, artists[item["artistSlug"]]["type"])
    releases["iine-sougisha"]["shortsUrl"] = "https://www.youtube.com/shorts/UVKSB3-Itqw"
    releases["iine-sougisha"]["promotionVerifiedAt"] = NOW
    cms["releases"] = sorted(
        releases.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True
    )

    for item in NEW_RELEASES:
        artist = artists[item["artistSlug"]]
        artist["artistFeaturedTracks"] = [
            item["slug"],
            *[slug for slug in artist.get("artistFeaturedTracks", []) if slug != item["slug"]],
        ][:3]

    news = {item["slug"]: item for item in cms.get("news", [])}
    for item in NEW_RELEASES:
        slug = f'{item["slug"]}-release'
        news[slug] = {
            "slug": slug, "title": f'{item["artist"]}「{item["title"]}」公開',
            "artistSlug": item["artistSlug"], "releaseSlug": item["slug"],
            "publishedAt": item["releaseAt"], "description": item["description"],
            "image": f'https://i.ytimg.com/vi/{item["youtubeId"]}/maxresdefault.jpg', "status": "published",
        }
    news["enomoto-mia-anime-opening-theme"] = {
        "slug": "enomoto-mia-anime-opening-theme",
        "title": "榎本魅愛「また、君に恋をする」アニメOP決定",
        "artistSlug": "enomoto-mia", "releaseSlug": "",
        "publishedAt": PROMOTIONAL_VIDEO["publishedAt"],
        "description": PROMOTIONAL_VIDEO["description"],
        "image": "https://i.ytimg.com/vi/dKnu4aEwkIY/maxresdefault.jpg", "status": "published",
        "youtubeUrl": PROMOTIONAL_VIDEO["youtubeUrl"],
    }
    cms["news"] = sorted(news.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True)

    snapshot = cms.setdefault("youtubeSnapshot", {})
    shorts = {item["videoId"]: item for item in snapshot.get("shortVideos", [])}
    shorts.update({item["videoId"]: short_record(item) for item in NEW_SHORTS})
    snapshot.update({
        "officialVideos": 66, "shorts": 45, "totalPublishedVideos": 111,
        "verifiedAt": NOW,
        "source": "公式YouTube Atomフィード・videos/shortsタブ・各動画の公開メタデータを照合",
        "shortVideos": sorted(shorts.values(), key=lambda item: (item["publishedAt"], item["videoId"]), reverse=True),
        "scheduledVideos": [],
    })
    cms["updatedAt"] = NOW
    write_json(CMS_PATH, cms)

    dates = json.loads(DATES_PATH.read_text(encoding="utf-8"))
    records = {(item["releaseSlug"], item.get("youtubeId", "")): item for item in dates["records"]}
    for item in NEW_RELEASES:
        record = evidence_record(item["slug"], item)
        records[(record["releaseSlug"], record["youtubeId"])] = record
    for item in NEW_SHORTS:
        record = evidence_record(item["relatedRelease"] or "unreleased-mata-kimi-ni-koi-wo-suru", item, "short")
        records[(record["releaseSlug"], record["youtubeId"])] = record
    dates["checkedAt"] = NOW
    dates["records"] = sorted(records.values(), key=lambda item: (item["releaseSlug"], item.get("youtubeId", "")))
    write_json(DATES_PATH, dates)

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    evidence = {(item["slug"], item["videoId"]): item for item in state.get("evidence", [])}
    for item in NEW_RELEASES:
        evidence[(item["slug"], item["youtubeId"])] = {
            "slug": item["slug"], "videoId": item["youtubeId"],
            "releaseTimestamp": item["releaseAt"], "availability": "public",
            "liveStatus": "not_live", "channelId": CHANNEL_ID,
        }
    state.update({
        "verifiedAt": NOW, "officialChannelId": CHANNEL_ID,
        "promoted": sorted(set(state.get("promoted", [])) | {item["slug"] for item in NEW_RELEASES}),
        "evidence": sorted(evidence.values(), key=lambda item: (item["slug"], item["videoId"])),
        "upcomingHeld": [],
    })
    write_json(STATE_PATH, state)

    photobooks = json.loads(PHOTOBOOKS_PATH.read_text(encoding="utf-8"))
    books = {item["slug"]: item for item in photobooks.get("photobooks", [])}
    books[PHOTOBOOK["slug"]] = PHOTOBOOK
    photobooks["updatedAt"] = NOW
    photobooks["photobooks"] = sorted(
        books.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True
    )
    write_json(PHOTOBOOKS_PATH, photobooks)

    write_json(SNAPSHOT_PATH, {
        "schemaVersion": "1.2", "verifiedAt": NOW, "officialChannelId": CHANNEL_ID,
        "channelUrl": "https://www.youtube.com/@suzuka1209",
        "verificationMethod": "公式YouTube Atomフィード、videos/shortsタブ、各動画の公開メタデータを照合",
        "channelSnapshot": {"officialVideos": 66, "shorts": 45, "totalPublishedVideos": 111},
        "published": NEW_RELEASES,
        "promotionalVideos": [PROMOTIONAL_VIDEO],
        "shorts": snapshot["shortVideos"], "upcomingHeld": [],
    })
    print(json.dumps({
        "publishedReleases": [item["slug"] for item in NEW_RELEASES],
        "promotionalVideos": [PROMOTIONAL_VIDEO["videoId"]],
        "newShorts": [item["videoId"] for item in NEW_SHORTS],
        "photobook": PHOTOBOOK["slug"], "releaseCount": len(cms["releases"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
