#!/usr/bin/env python3
"""Apply official YouTube evidence verified on 2026-09-04."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
DATES_PATH = ROOT / "assets/data/youtube-publish-dates.json"
STATE_PATH = ROOT / "assets/data/official-youtube-release-state.json"
SNAPSHOT_PATH = ROOT / "assets/data/official-youtube-catalog-20260904.json"
NOW = "2026-09-04T22:30:00+09:00"
CHANNEL_ID = "UCVde75yhByGQMu3SkO-fzrA"


RELEASES = [
    {
        "slug": "yume-to-kaigo-to-watashitachi",
        "title": "夢と、介護と、わたしたち。",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "releaseAt": "2026-09-04T21:22:14+09:00",
        "youtubeId": "PVX_5_MybgM",
        "youtubeUrl": "https://www.youtube.com/watch?v=PVX_5_MybgM",
        "duration": 315,
        "officialTitle": "榎本魅愛「夢と、介護と、わたしたち。」Official Audio｜介護WITH 応援ソング",
        "description": "介護の現場で誰かを支えながら、自分の夢も大切にするすべての人へ榎本魅愛が贈る応援歌。",
        "genres": ["J-POP", "応援歌"],
        "moods": ["希望", "あたたかい"],
        "themes": ["介護", "夢", "仕事", "応援", "希望", "未来"],
        "tags": ["介護WITH", "敬寿会", "SUZUKA WITH", "SUZUKA WITH CARE", "福祉", "介護職", "Official Audio"],
        "coverImage": "images/enomoto-mia-yume-to-kaigo-to-watashitachi.jpg",
        "coverAlt": "紺色のスクラブ姿の榎本魅愛を描いた「夢と、介護と、わたしたち。」公式ビジュアル",
        "videoLabel": "OFFICIAL AUDIO",
        "videoCtaLabel": "Official Audioを聴く",
        "videoButtonLabel": "LISTEN",
        "newsTitle": "榎本魅愛、新曲「夢と、介護と、わたしたち。」公開──介護の現場で働く人たちへ贈る、新たな応援歌",
        "newsDescription": "介護の現場で働く人たちと、仕事の中でも夢を大切にするすべての人へ贈る榎本魅愛の新曲。",
        "newsBodyParagraphs": [
            "「夢と、介護と、わたしたち。」は、誰かの暮らしを支える毎日の中にも、一人ひとりの夢があることを見つめた応援歌です。",
            "SUZUKA公式YouTubeの公開情報では、介護WITHへの応募に取り組む社会福祉法人敬寿会を応援する作品として紹介されています。",
        ],
        "specialFeatureUrl": "features/suzuka-with-care/",
        "homeHero": {
            "title": "SUZUKA Official | 榎本魅愛「夢と、介護と、わたしたち。」公開中",
            "description": "介護の現場で働く人たちへ贈る、榎本魅愛の新たな応援歌。Official Audio・作品・特集をSUZUKA公式サイトで紹介します。",
            "subtitle": "ENOMOTO MIA · Official Audio",
            "status": "NEW RELEASE",
            "lead": "夢は、誰かを支える毎日の中にもある。",
            "projectLabel": "SUZUKA WITH CARE",
            "primaryLabel": "Official Audioを聴く",
            "secondaryLabel": "作品について",
            "featureLabel": "特集を読む",
            "featureUrl": "features/suzuka-with-care/",
        },
    },
    {
        "slug": "gekka-no-chigiri",
        "title": "月下契",
        "artist": "VEILFANG",
        "artistSlug": "veilfang",
        "releaseAt": "2026-09-04T20:40:11+09:00",
        "youtubeId": "Slv8e81DJ84",
        "youtubeUrl": "https://www.youtube.com/watch?v=Slv8e81DJ84",
        "duration": 269,
        "officialTitle": "VEILFANG『月下契』Official Audio｜白狼 × 九尾狐",
        "description": "白狼・孤闘と九尾狐・九羅護が、月下の契りと運命を歌うVEILFANGのデビューシングル。",
        "genres": ["J-POP", "ダークファンタジー"],
        "moods": ["神秘的", "力強い"],
        "themes": ["契り", "運命", "月", "絆"],
        "tags": ["VEILFANG", "ヴェイルファング", "KOTOU", "KURAMA", "白狼", "九尾狐", "Official Audio"],
        "coverImage": "images/veilfang-gekka-no-chigiri.jpg",
        "coverAlt": "VEILFANG『月下契』公式YouTubeビジュアル",
        "videoLabel": "OFFICIAL AUDIO",
        "videoCtaLabel": "Official Audioを聴く",
        "videoButtonLabel": "LISTEN",
    },
]

VEILFANG = {
    "slug": "veilfang",
    "name": "VEILFANG",
    "reading": "ヴェイルファング",
    "type": "MusicGroup",
    "image": "images/veilfang-gekka-no-chigiri.jpg",
    "world": "白狼と九尾狐が、月の下で契りと運命を結ぶダークファンタジー。",
    "music": "美麗さ、神秘性、ワイルドさを重ねた物語性の高いJ-POP。",
    "profile": "白狼・孤闘（KOTOU）と九尾狐・九羅護（KURAMA）による、SUZUKAの幻想獣デュオ。",
    "status": "published",
    "youtubeUrl": "https://www.youtube.com/@suzuka1209",
    "instagramUrl": "https://www.instagram.com/suzuka12090511/",
    "searchKeywords": ["VEILFANG", "ヴェイルファング", "KOTOU", "KURAMA", "孤闘", "九羅護", "白狼", "九尾狐"],
    "seo": {
        "title": "VEILFANG｜SUZUKA Official AI Artist",
        "description": "白狼・孤闘と九尾狐・九羅護によるSUZUKAの幻想獣デュオ。SUZUKAの架空のAIアーティストです。",
        "jsonLdEnabled": True,
    },
    "artistType": "MusicGroup",
    "artistStatus": "published",
    "artistFeaturedTracks": ["gekka-no-chigiri"],
    "officialSource": "https://www.youtube.com/watch?v=Slv8e81DJ84",
}

KOGA_MV = {
    "videoId": "OldWXAS32lI",
    "youtubeUrl": "https://www.youtube.com/watch?v=OldWXAS32lI",
    "officialTitle": "【Official MV】神代煌牙『悪役でいい』｜KOGA KAMISHIRO",
    "publishedAt": "2026-09-02T21:01:37+09:00",
    "duration": 314,
}

KOGA_SHORT = {
    "videoId": "Ah4kM2T6mr0",
    "title": "世界が俺を悪と呼んでも。｜神代煌牙『悪役でいい』Official MV #Shorts",
    "artist": "神代煌牙",
    "artistSlug": "koga-kamishiro",
    "publishedAt": "2026-09-02T21:12:43+09:00",
    "relatedRelease": "akuyaku-de-ii",
    "duration": 61,
    "description": "神代煌牙『悪役でいい』Official MVの公式Shorts。",
}

ASTERIA_PREVIEW = {
    "videoId": "blXPDEriTyE",
    "title": "【先行音源解禁】ASTERIA「午前0時のシンデレラ」｜魔法が解ける、その前に。",
    "artist": "ASTERIA",
    "artistSlug": "asteria",
    "publishedAt": "2026-09-01T21:25:40+09:00",
    "duration": 179,
    "youtubeUrl": "https://www.youtube.com/watch?v=blXPDEriTyE",
    "status": "published",
    "contentType": "promotional-preview",
    "releaseStatus": "not-promoted-as-full-release",
    "description": "「午前0時のシンデレラ」の楽曲世界を先行公開した公式映像。Full MVは後日公開予定。",
}

SPECIAL_FEATURE = {
    "slug": "suzuka-with-care",
    "label": "SPECIAL FEATURE",
    "projectLabel": "SUZUKA WITH CARE",
    "title": "夢と、介護と、わたしたち。",
    "subtitle": "── 介護の現場から生まれた歌。",
    "heroCopy": "夢は、誰かを支える毎日の中にもある。",
    "releaseSlug": "yume-to-kaigo-to-watashitachi",
    "artistSlug": "enomoto-mia",
    "publishedAt": "2026-09-04T21:22:14+09:00",
    "status": "published",
    "introHeading": "INTRODUCTION",
    "introParagraphs": [
        "誰かの人生と暮らしを支える介護の仕事。その毎日の中にも、働く人一人ひとりの夢と物語があります。",
        "「夢と、介護と、わたしたち。」は、介護の現場で働く人たちに向けて、榎本魅愛が歌う応援歌です。",
    ],
    "messageHeading": "MESSAGE",
    "messageParagraphs": [
        "支えることと、自分の夢を大切にすることは、どちらか一つでなくていい。",
        "音楽が、働く毎日と未来をつなぐ小さな力になることを願っています。",
    ],
    "careHeading": "CARE WITH PROJECT",
    "careParagraphs": [
        "SUZUKA公式YouTubeの公開情報により、本作は介護WITHへの応募に取り組む社会福祉法人敬寿会を応援する作品として確認しています。",
        "介護の仕事と、そこで働く人の夢を音楽でつなぐ、SUZUKA WITHの新しい取り組みです。",
    ],
}


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def create_release(item: dict, artist_type: str) -> dict:
    release_at = item["releaseAt"]
    tags = unique([item["title"], item["artist"], *item["tags"], *item["genres"], *item["themes"], *item["moods"]])
    release = {
        "slug": item["slug"], "id": item["slug"], "title": item["title"], "displayTitle": item["title"],
        "englishTitle": item["title"], "artist": item["artist"], "artistSlug": item["artistSlug"],
        "artistSlugs": [item["artistSlug"]], "artistType": artist_type, "releaseAt": release_at,
        "publishedAt": release_at, "releaseDate": release_at[:10], "releaseYear": 2026, "releaseType": "single",
        "genres": item["genres"], "moods": item["moods"], "themes": item["themes"], "tags": tags,
        "language": "ja", "coverImage": item["coverImage"], "coverAlt": item["coverAlt"],
        "youtubeUrl": item["youtubeUrl"], "youtubeVideoTitle": item["officialTitle"],
        "videoLabel": item["videoLabel"], "videoCtaLabel": item["videoCtaLabel"],
        "videoButtonLabel": item["videoButtonLabel"], "shortsUrl": "",
        "releaseUrl": f'releases/{item["slug"]}/', "newsUrl": f'news/{item["slug"]}-release/',
        "duration": item["duration"], "status": "published", "featured": True,
        "recommendationWeight": 5 if item["slug"].startswith("yume-") else 4,
        "weeklyPickEligible": True, "analyticsEnabled": True, "upcomingPriority": 0, "relatedReleases": [],
        "searchKeywords": tags, "aiArtistType": "fictional AI artist", "description": item["description"],
        "introduction": item["description"], "galleryImages": [], "galleryPublished": False,
        "productionNote": item["description"],
        "seo": {"title": f'{item["title"]}｜{item["artist"]}｜SUZUKA Official Music',
                "description": f'{item["description"]} SUZUKAの架空のAIアーティスト作品です。', "jsonLdEnabled": True},
        "videoPublishDate": release_at[:10], "videoPublishedAt": release_at,
        "videoPublishedAtSource": "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate",
        "videoStructuredDataStatus": "published", "officialSource": item["youtubeUrl"], "promotionVerifiedAt": NOW,
        "lyricsAvailable": False, "lyricsSource": "", "lyricsText": "", "lyricsVerified": False, "lyricsVerifiedAt": None,
    }
    for key in ("newsTitle", "newsDescription", "newsBodyParagraphs", "specialFeatureUrl", "homeHero"):
        if key in item:
            release[key] = item[key]
    return release


def evidence_record(slug: str, video_id: str, title: str, published_at: str, duration: int, content_type: str = "video") -> dict:
    url = f"https://www.youtube.com/{'shorts/' if content_type == 'short' else 'watch?v='}{video_id}"
    record = {
        "releaseSlug": slug, "youtubeId": video_id, "youtubeUrl": url, "catalogReleaseDate": published_at[:10],
        "officialTitle": title, "channelId": CHANNEL_ID, "channelVerified": True,
        "youtubePublishDate": published_at, "youtubeUploadDate": published_at, "liveStartTimestamp": "",
        "playabilityStatus": "OK", "durationSeconds": duration, "verifiedPublishedAt": published_at,
        "verificationSource": "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate", "status": "verified-datetime",
    }
    if content_type == "short":
        record["contentType"] = "short"
    return record


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    artists = {item["slug"]: item for item in cms["artists"]}
    artists[VEILFANG["slug"]] = VEILFANG
    cms["artists"] = sorted(artists.values(), key=lambda item: item["slug"])

    releases = {item["slug"]: item for item in cms["releases"]}
    for item in RELEASES:
        releases[item["slug"]] = create_release(item, artists[item["artistSlug"]]["type"])
        artist = artists[item["artistSlug"]]
        artist["artistFeaturedTracks"] = unique([item["slug"], *artist.get("artistFeaturedTracks", [])])[:3]

    koga = releases["akuyaku-de-ii"]
    koga.update({
        "coverImage": "images/koga-akuyaku-de-ii-mv.jpg",
        "coverAlt": "神代煌牙『悪役でいい』Official MV公式YouTubeビジュアル",
        "youtubeUrl": KOGA_MV["youtubeUrl"], "youtubeVideoTitle": KOGA_MV["officialTitle"],
        "videoLabel": "OFFICIAL MV", "videoCtaLabel": "公式MVを見る", "videoButtonLabel": "WATCH MV",
        "duration": KOGA_MV["duration"], "videoPublishDate": KOGA_MV["publishedAt"][:10],
        "videoPublishedAt": KOGA_MV["publishedAt"], "officialSource": KOGA_MV["youtubeUrl"],
        "shortsUrl": f'https://www.youtube.com/shorts/{KOGA_SHORT["videoId"]}', "promotionVerifiedAt": NOW,
    })
    releases["akuyaku-de-ii"] = koga
    cms["releases"] = sorted(releases.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True)

    news = {item["slug"]: item for item in cms.get("news", [])}
    for item in RELEASES:
        news_slug = f'{item["slug"]}-release'
        news[news_slug] = {
            "slug": news_slug, "title": item.get("newsTitle", f'{item["artist"]}「{item["title"]}」公開'),
            "artistSlug": item["artistSlug"], "releaseSlug": item["slug"], "publishedAt": item["releaseAt"],
            "description": item.get("newsDescription", item["description"]), "image": item["coverImage"], "status": "published",
        }
    cms["news"] = sorted(news.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True)

    definitions = {item["slug"]: item for item in cms.get("featureDefinitions", [])}
    definitions["suzuka-with-care"] = {
        "slug": "suzuka-with-care", "label": "SUZUKA WITH CARE",
        "description": "介護の現場から生まれた歌。音楽と仕事、夢をつなぐSUZUKA WITHの特集。",
        "match": {"tags": ["SUZUKA WITH CARE"]},
    }
    cms["featureDefinitions"] = list(definitions.values())
    cms["specialFeatures"] = [SPECIAL_FEATURE]

    snapshot = cms.setdefault("youtubeSnapshot", {})
    short = {"youtubeUrl": f'https://www.youtube.com/shorts/{KOGA_SHORT["videoId"]}',
             "thumbnail": f'https://i.ytimg.com/vi/{KOGA_SHORT["videoId"]}/maxresdefault.jpg',
             "status": "published", "contentType": "short", **KOGA_SHORT}
    shorts = {item["videoId"]: item for item in snapshot.get("shortVideos", [])}
    shorts[short["videoId"]] = short
    snapshot.update({
        "officialVideos": 70, "shorts": 46, "totalPublishedVideos": 116, "verifiedAt": NOW,
        "source": "公式YouTube Atomフィード・videos/shortsタブ・各動画の公開メタデータを照合",
        "shortVideos": sorted(shorts.values(), key=lambda item: (item["publishedAt"], item["videoId"]), reverse=True),
        "scheduledVideos": [],
    })
    cms["updatedAt"] = NOW
    write_json(CMS_PATH, cms)

    dates = json.loads(DATES_PATH.read_text(encoding="utf-8"))
    records = {(item["releaseSlug"], item.get("youtubeId", "")): item for item in dates["records"]}
    for item in RELEASES:
        record = evidence_record(item["slug"], item["youtubeId"], item["officialTitle"], item["releaseAt"], item["duration"])
        records[(record["releaseSlug"], record["youtubeId"])] = record
    for video_id, title, published_at, duration in [
        (KOGA_MV["videoId"], KOGA_MV["officialTitle"], KOGA_MV["publishedAt"], KOGA_MV["duration"]),
        (KOGA_SHORT["videoId"], KOGA_SHORT["title"], KOGA_SHORT["publishedAt"], KOGA_SHORT["duration"]),
    ]:
        content_type = "short" if video_id == KOGA_SHORT["videoId"] else "video"
        record = evidence_record("akuyaku-de-ii", video_id, title, published_at, duration, content_type)
        records[(record["releaseSlug"], record["youtubeId"])] = record
    dates["checkedAt"] = NOW
    dates["records"] = sorted(records.values(), key=lambda item: (item["releaseSlug"], item.get("youtubeId", "")))
    write_json(DATES_PATH, dates)

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    evidence = {(item["slug"], item["videoId"]): item for item in state.get("evidence", [])}
    for item in RELEASES:
        evidence[(item["slug"], item["youtubeId"])] = {
            "slug": item["slug"], "videoId": item["youtubeId"], "releaseTimestamp": item["releaseAt"],
            "availability": "public", "liveStatus": "not_live", "channelId": CHANNEL_ID,
        }
    evidence[("akuyaku-de-ii", KOGA_MV["videoId"])] = {
        "slug": "akuyaku-de-ii", "videoId": KOGA_MV["videoId"], "releaseTimestamp": KOGA_MV["publishedAt"],
        "availability": "public", "liveStatus": "not_live", "channelId": CHANNEL_ID,
    }
    state.update({"verifiedAt": NOW, "officialChannelId": CHANNEL_ID,
                  "promoted": sorted(set(state.get("promoted", [])) | {item["slug"] for item in RELEASES}),
                  "evidence": sorted(evidence.values(), key=lambda item: (item["slug"], item["videoId"])), "upcomingHeld": []})
    write_json(STATE_PATH, state)

    write_json(SNAPSHOT_PATH, {
        "schemaVersion": "1.2", "verifiedAt": NOW, "officialChannelId": CHANNEL_ID,
        "channelUrl": "https://www.youtube.com/@suzuka1209",
        "verificationMethod": "公式YouTube Atomフィード、videos/shortsタブ、各動画の公開メタデータを照合",
        "channelSnapshot": {"officialVideos": 70, "shorts": 46, "totalPublishedVideos": 116},
        "published": RELEASES,
        "updatedReleaseVideos": [{"releaseSlug": "akuyaku-de-ii", **KOGA_MV}],
        "promotionalVideos": [ASTERIA_PREVIEW], "shorts": snapshot["shortVideos"], "upcomingHeld": [],
    })
    print(json.dumps({"publishedReleases": [item["slug"] for item in RELEASES], "artist": "veilfang",
                      "updatedReleaseVideos": [KOGA_MV["videoId"]], "newShorts": [KOGA_SHORT["videoId"]],
                      "releaseCount": len(cms["releases"]), "artistCount": len(cms["artists"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
