#!/usr/bin/env python3
"""Register the official YouTube publications verified on 2026-09-19.

This update keeps work publication dates, streaming dates, full releases, and
promotional uploads separate.  It is intentionally idempotent so the
canonical JSON can be regenerated or audited again without duplicating work.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
DATES_PATH = ROOT / "assets/data/youtube-publish-dates.json"
STATE_PATH = ROOT / "assets/data/official-youtube-release-state.json"
SNAPSHOT_PATH = ROOT / "assets/data/official-youtube-catalog-20260919.json"
MIA_PLAYER_PATH = ROOT / "assets/data/enomoto-mia-releases.json"

OFFICIAL_ARTWORKS = {
    "over-drive": "images/enomoto-mia-over-drive.jpg",
    "september-blue": "images/enomoto-mia-september-blue.jpg",
    "mahou-ga-toketemo": "images/koga-mahou-ga-toketemo.jpg",
    "hello-hello-halloween": "images/enomoto-mia-hello-hello-halloween.jpg",
}
OFFICIAL_ARTWORK_SOURCE = "user-provided-official-asset-2026-09-19"

NOW = "2026-09-19T00:40:59+09:00"
LABEL_CHANNEL_ID = "UCVde75yhByGQMu3SkO-fzrA"
MIA_CHANNEL_ID = "UCRwW7smDoEB-UOHMQJJ1Jyg"

PUBLISHED_VIDEOS = [
    {
        "releaseSlug": "mahou-ga-toketemo",
        "title": "【Official MV】魔法が解けても ― Pumpkin Carriage ― / 神代煌牙｜KOGA KAMISHIRO",
        "artist": "神代煌牙",
        "artistSlug": "koga-kamishiro",
        "publishedAt": "2026-09-14T20:00:06+09:00",
        "videoId": "g_SmyjPGIfc",
        "youtubeUrl": "https://www.youtube.com/watch?v=g_SmyjPGIfc",
        "duration": 250,
        "channelId": LABEL_CHANNEL_ID,
    },
    {
        "releaseSlug": "hello-hello-halloween",
        "title": "【Official MV】Hello Hello Halloween／榎本魅愛（ENOMOTO MIA）🎃",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-16T20:00:07+09:00",
        "videoId": "vuZiHlpo9Ak",
        "youtubeUrl": "https://www.youtube.com/watch?v=vuZiHlpo9Ak",
        "duration": 218,
        "channelId": MIA_CHANNEL_ID,
    },
]

UPDATED_RELEASE_VIDEO = {
    "releaseSlug": "hyakumankoku",
    "title": "【MV】榎本魅愛「百万告」Anime Version｜百万回でも、君に告白する。",
    "artist": "榎本魅愛",
    "artistSlug": "enomoto-mia",
    "publishedAt": "2026-09-17T20:00:08+09:00",
    "videoId": "7FaDutNfIxo",
    "youtubeUrl": "https://www.youtube.com/watch?v=7FaDutNfIxo",
    "duration": 296,
    "channelId": MIA_CHANNEL_ID,
}

PROMOTIONAL_VIDEOS = [
    {
        "releaseSlug": "promotional-nox-henpin-sareta-ningen",
        "relatedReleaseSlug": "",
        "title": "【9/16 20:00 音源先行公開】NOX「返品された人間」｜返品理由：人間だったため。",
        "artist": "NOX",
        "artistSlug": "nox",
        "publishedAt": "2026-09-16T20:00:06+09:00",
        "videoId": "H8iljjkdNGE",
        "youtubeUrl": "https://www.youtube.com/watch?v=H8iljjkdNGE",
        "duration": 245,
        "channelId": LABEL_CHANNEL_ID,
        "contentType": "promotional-video",
    },
    {
        "releaseSlug": "promotional-asteria-kinmokusei-to-hoshifuru-yoru",
        "relatedReleaseSlug": "",
        "title": "【音源先行公開】ASTERIA「金木犀と星降る夜」｜9月15日公開 🌼🌙",
        "artist": "ASTERIA",
        "artistSlug": "asteria",
        "publishedAt": "2026-09-15T20:00:06+09:00",
        "videoId": "fyLGRZpxeUg",
        "youtubeUrl": "https://www.youtube.com/watch?v=fyLGRZpxeUg",
        "duration": 353,
        "channelId": LABEL_CHANNEL_ID,
        "contentType": "promotional-video",
    },
    {
        "releaseSlug": "hello-hello-halloween",
        "relatedReleaseSlug": "hello-hello-halloween",
        "title": "【音源先行配信】Hello Hello Halloween / 榎本魅愛｜恋するHalloween Night 🎃💗",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-13T20:00:06+09:00",
        "videoId": "wOeeMaoiDgU",
        "youtubeUrl": "https://www.youtube.com/watch?v=wOeeMaoiDgU",
        "duration": 218,
        "channelId": LABEL_CHANNEL_ID,
        "contentType": "promotional-video",
    },
    {
        "releaseSlug": "september-blue",
        "relatedReleaseSlug": "september-blue",
        "title": "【先行音源公開】榎本魅愛「September Blue」｜夏が終わるせいにした。でも本当は、君のせいなのに。",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-14T20:00:06+09:00",
        "videoId": "QTMgWAnIHv4",
        "youtubeUrl": "https://www.youtube.com/watch?v=QTMgWAnIHv4",
        "duration": 226,
        "channelId": MIA_CHANNEL_ID,
        "contentType": "promotional-video",
    },
    {
        "releaseSlug": "over-drive",
        "relatedReleaseSlug": "over-drive",
        "title": "【先行音源公開】榎本魅愛「Over Drive」Official Audio",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-15T20:00:10+09:00",
        "videoId": "2JnHqQwfC1s",
        "youtubeUrl": "https://www.youtube.com/watch?v=2JnHqQwfC1s",
        "duration": 222,
        "channelId": MIA_CHANNEL_ID,
        "contentType": "promotional-video",
    },
    {
        "releaseSlug": "hanakotoba",
        "relatedReleaseSlug": "hanakotoba",
        "title": "【カラオケ配信開始🎤】榎本魅愛「花言葉」ついにJOYSOUNDで歌えます！🌸",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-18T20:31:04+09:00",
        "videoId": "oudTEKYujZk",
        "youtubeUrl": "https://www.youtube.com/watch?v=oudTEKYujZk",
        "duration": 100,
        "channelId": MIA_CHANNEL_ID,
        "contentType": "promotional-video",
    },
]

NEW_SHORTS = [
    {
        "videoId": "Ft04wqBYD1o",
        "title": "【9/17 20:00公開】榎本魅愛「百万告」MV Anime Version｜45秒先行公開中",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-16T22:26:55+09:00",
        "relatedRelease": "hyakumankoku",
        "duration": 45,
        "description": "榎本魅愛「百万告」Anime Versionの公開を案内する公式Shorts。",
    },
    {
        "videoId": "hmnAv-OKCeI",
        "title": "榎本魅愛「Over Drive」先行音源公開中｜恋が、わたしを追い越していく。#shorts",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-15T20:00:22+09:00",
        "relatedRelease": "over-drive",
        "duration": 30,
        "description": "榎本魅愛「Over Drive」の先行音源公開を案内する公式Shorts。",
    },
    {
        "videoId": "Fk8ROGI7lrI",
        "title": "【告白の結末は…？】榎本魅愛「Hello Hello Halloween」🎃 続きは魅愛チャンネルへ #Shorts",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-14T21:45:01+09:00",
        "relatedRelease": "hello-hello-halloween",
        "duration": 31,
        "description": "榎本魅愛「Hello Hello Halloween」Official MVへ誘導する公式Shorts。",
    },
    {
        "videoId": "AsSJfBodXxw",
        "title": "夏が終わるせいにした。でも本当は、君のせいなのに。｜榎本魅愛「September Blue」💙",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-14T20:00:32+09:00",
        "relatedRelease": "september-blue",
        "duration": 30,
        "description": "榎本魅愛「September Blue」の先行音源公開を案内する公式Shorts。",
    },
    {
        "videoId": "hEQFEGH2i0w",
        "title": "「魔法が解ける、その瞬間――。｜神代煌牙 MV 9.14 20:00解禁」",
        "artist": "神代煌牙",
        "artistSlug": "koga-kamishiro",
        "publishedAt": "2026-09-13T19:47:27+09:00",
        "relatedRelease": "mahou-ga-toketemo",
        "duration": 15,
        "description": "神代煌牙「魔法が解けても ― Pumpkin Carriage ―」Official MVの公開を案内する公式Shorts。",
    },
    {
        "videoId": "DIYCbKBahDE",
        "title": "【MV先行公開】1分だけ、魔法の夜を。｜神代煌牙「魔法が解けても ― Pumpkin Carriage ―」",
        "artist": "神代煌牙",
        "artistSlug": "koga-kamishiro",
        "publishedAt": "2026-09-11T22:55:05+09:00",
        "relatedRelease": "mahou-ga-toketemo",
        "duration": 60,
        "description": "神代煌牙「魔法が解けても ― Pumpkin Carriage ―」のMV先行公開Shorts。",
    },
    {
        "videoId": "PHINmciA8rE",
        "title": "【9.11 RELEASE】榎本魅愛「花言葉」🌸｜PHOTO BOOKも無料公開",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-10T20:01:22+09:00",
        "relatedRelease": "hanakotoba",
        "duration": 20,
        "description": "榎本魅愛「花言葉」の配信とPHOTO BOOK公開を案内する公式Shorts。",
    },
    {
        "videoId": "T7qbhZpWSqQ",
        "title": "【MV先行公開】午前0時、魔法が解ける——。｜ASTERIA「午前0時のシンデレラ」",
        "artist": "ASTERIA",
        "artistSlug": "asteria",
        "publishedAt": "2026-09-08T23:38:59+09:00",
        "relatedRelease": "",
        "duration": 60,
        "description": "ASTERIA「午前0時のシンデレラ」のMV先行公開Shorts。",
    },
    {
        "videoId": "86o7glSxLKg",
        "title": "【実写版】榎本魅愛「百万告」｜好きは、何回だって更新中。💗 #shorts",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-18T20:00:31+09:00",
        "relatedRelease": "hyakumankoku",
        "duration": 46,
        "description": "榎本魅愛「百万告」を紹介する公式Shorts。",
    },
    {
        "videoId": "sbEVm7luIQs",
        "title": "【45秒先行公開】百万回でも君に告白する。｜榎本魅愛「百万告」MV Anime Ver. 9/17 20:00公開",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-16T22:20:26+09:00",
        "relatedRelease": "hyakumankoku",
        "duration": 45,
        "description": "榎本魅愛「百万告」Anime Versionの公開を案内する公式Shorts。",
    },
    {
        "videoId": "SuY_lXsluFA",
        "title": "「ずっと君が好きでした」🎃｜榎本魅愛「Hello Hello Halloween」Official MV 9月16日　20時　公開です🎃#shorts",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-14T19:27:43+09:00",
        "relatedRelease": "hello-hello-halloween",
        "duration": 31,
        "description": "榎本魅愛「Hello Hello Halloween」Official MVの公開を案内する公式Shorts。",
    },
    {
        "videoId": "HkgSPLD43Dc",
        "title": "言葉にできない「好き」を、花に託した。🌸｜榎本魅愛「花言葉」 #shorts",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-13T19:00:34+09:00",
        "relatedRelease": "hanakotoba",
        "duration": 19,
        "description": "榎本魅愛「花言葉」を紹介する公式Shorts。",
    },
    {
        "videoId": "M1QhypOf6iI",
        "title": "【先行公開】榎本魅愛『花言葉』｜8月19日20時フルMV解禁｜両親の結婚記念日に #shorts",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-09-12T21:30:24+09:00",
        "relatedRelease": "hanakotoba",
        "duration": 40,
        "description": "榎本魅愛「花言葉」の公式Shorts。",
    },
]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def short_record(item: dict) -> dict:
    video_id = item["videoId"]
    return {
        **item,
        "youtubeUrl": f"https://www.youtube.com/shorts/{video_id}",
        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        "status": "published",
        "contentType": "short",
    }


def evidence_record(item: dict, *, content_type: str = "video", release_slug: str | None = None) -> dict:
    return {
        "releaseSlug": release_slug or item["releaseSlug"],
        "youtubeId": item["videoId"],
        "youtubeUrl": item["youtubeUrl"],
        "catalogReleaseDate": item["publishedAt"][:10],
        "officialTitle": item["title"],
        "channelId": item["channelId"],
        "channelVerified": True,
        "youtubePublishDate": item["publishedAt"],
        "youtubeUploadDate": item["publishedAt"],
        "liveStartTimestamp": "",
        "playabilityStatus": "OK",
        "durationSeconds": item["duration"],
        "verifiedPublishedAt": item["publishedAt"],
        "verificationSource": "official-youtube-videos-or-shorts-tab-and-player-metadata",
        "status": "verified-datetime",
        **({"contentType": content_type} if content_type != "video" else {}),
    }


def release_from_template(cms: dict, template_slug: str, video: dict, *, description: str, seo_description: str, scheduled_streaming: dict | None = None, home_hero: dict | None = None, recommendation_weight: int = 4) -> dict:
    template = next(item for item in cms["releases"] if item["slug"] == template_slug)
    item = copy.deepcopy(template)
    artist = next(artist for artist in cms["artists"] if artist["slug"] == video["artistSlug"])
    title = "魔法が解けても" if video["releaseSlug"] == "mahou-ga-toketemo" else "Hello Hello Halloween"
    date = video["publishedAt"][:10]
    tags = [title, video["artist"], "KOGA KAMISHIRO" if video["artistSlug"] == "koga-kamishiro" else "ENOMOTO MIA", "Official MV"]
    item.update({
        "slug": video["releaseSlug"],
        "id": video["releaseSlug"],
        "title": title,
        "displayTitle": title,
        "englishTitle": title,
        "artist": video["artist"],
        "artistSlug": video["artistSlug"],
        "artistSlugs": [video["artistSlug"]],
        "artistType": artist["type"],
        "releaseAt": video["publishedAt"],
        "publishedAt": video["publishedAt"],
        "releaseDate": date,
        "releaseYear": int(date[:4]),
        "releaseType": "single",
        "genres": [],
        "moods": [],
        "themes": [],
        "tags": tags,
        "language": "ja",
        "coverImage": OFFICIAL_ARTWORKS[video["releaseSlug"]],
        "coverAlt": f'{video["artist"]}「{title}」公式ビジュアル',
        "coverWidth": 886,
        "coverHeight": 886,
        "coverSource": OFFICIAL_ARTWORK_SOURCE,
        "youtubeUrl": video["youtubeUrl"],
        "youtubeVideoTitle": video["title"],
        "videoLabel": "OFFICIAL MV",
        "videoCtaLabel": "Official MVを見る",
        "videoButtonLabel": "WATCH MV",
        "shortsUrl": {
            "mahou-ga-toketemo": "https://www.youtube.com/shorts/hEQFEGH2i0w",
            "hello-hello-halloween": "https://www.youtube.com/shorts/SuY_lXsluFA",
        }[video["releaseSlug"]],
        "releaseUrl": f'releases/{video["releaseSlug"]}/',
        "newsUrl": f'news/{video["releaseSlug"]}-release/',
        "duration": video["duration"],
        "status": "published",
        "featured": True,
        "recommendationWeight": recommendation_weight,
        "weeklyPickEligible": True,
        "analyticsEnabled": True,
        "upcomingPriority": 0,
        "relatedReleases": [],
        "searchKeywords": unique([*tags, date, "SUZUKA", "Official MV", "YouTube"]),
        "aiArtistType": "fictional AI artist",
        "description": description,
        "introduction": description,
        "galleryImages": [],
        "galleryPublished": False,
        "productionNote": description,
        "newsTitle": f'{video["artist"]}「{title}」Official MV公開',
        "newsDescription": (
            "神代煌牙「魔法が解けても ― Pumpkin Carriage ―」Official MVの公開をSUZUKA Newsでお知らせします。"
            if video["releaseSlug"] == "mahou-ga-toketemo"
            else "榎本魅愛「Hello Hello Halloween」Official MV公開と、2026年9月21日のストリーミング配信情報をSUZUKA Newsで案内します。"
        ),
        "seo": {
            "title": f'{title}｜{video["artist"]}｜SUZUKA Official Music',
            "description": seo_description,
            "jsonLdEnabled": True,
        },
        "videoPublishDate": date,
        "videoPublishedAt": video["publishedAt"],
        "videoPublishedAtSource": "official-youtube-videos-or-shorts-tab-and-player-metadata",
        "videoStructuredDataStatus": "published",
        "officialSource": video["youtubeUrl"],
        "promotionVerifiedAt": NOW,
        "lyricsAvailable": False,
        "lyricsSource": "",
        "lyricsText": "",
        "lyricsVerified": False,
        "lyricsVerifiedAt": None,
    })
    for key in ("homeHero", "scheduledAt", "source", "linkcoreUrl"):
        item.pop(key, None)
    if scheduled_streaming:
        item["scheduledStreamingRelease"] = scheduled_streaming
    if home_hero:
        item["homeHero"] = home_hero
    return item


def update_existing_video(releases: dict[str, dict]) -> None:
    item = releases["hyakumankoku"]
    item.update({
        "youtubeUrl": UPDATED_RELEASE_VIDEO["youtubeUrl"],
        "youtubeVideoTitle": UPDATED_RELEASE_VIDEO["title"],
        "coverImage": "https://i.ytimg.com/vi/7FaDutNfIxo/maxresdefault.jpg",
        "coverAlt": "榎本魅愛「百万告」Anime Version公式YouTubeビジュアル",
        "videoLabel": "OFFICIAL MV · ANIME VERSION",
        "videoCtaLabel": "Anime Versionを見る",
        "videoButtonLabel": "WATCH MV",
        "shortsUrl": "https://www.youtube.com/shorts/Ft04wqBYD1o",
        "duration": UPDATED_RELEASE_VIDEO["duration"],
        "videoVariant": "Anime Version",
        "videoPublishDate": UPDATED_RELEASE_VIDEO["publishedAt"][:10],
        "videoPublishedAt": UPDATED_RELEASE_VIDEO["publishedAt"],
        "videoPublishedAtSource": "official-youtube-videos-or-shorts-tab-and-player-metadata",
        "videoStructuredDataStatus": "published",
        "officialSource": UPDATED_RELEASE_VIDEO["youtubeUrl"],
        "promotionVerifiedAt": NOW,
    })
    item["searchKeywords"] = unique([
        *item.get("searchKeywords", []), "Anime Version", "Official MV", "百万告 Anime Version",
    ])


def update_mia_player() -> None:
    data = json.loads(MIA_PLAYER_PATH.read_text(encoding="utf-8"))
    data["updatedAt"] = "2026-09-19"
    rows = {item["slug"]: item for item in data["releases"]}
    rows["hyakumankoku"].update({
        "youtubeUrl": UPDATED_RELEASE_VIDEO["youtubeUrl"],
        "youtubeId": UPDATED_RELEASE_VIDEO["videoId"],
        "youtubeVideoTitle": UPDATED_RELEASE_VIDEO["title"],
        "duration": UPDATED_RELEASE_VIDEO["duration"],
        "uploadDate": UPDATED_RELEASE_VIDEO["publishedAt"][:10],
    })
    rows["hello-hello-halloween"] = {
        "title": "Hello Hello Halloween",
        "titleEnglish": "Hello Hello Halloween",
        "slug": "hello-hello-halloween",
        "status": "published",
        "pageUrl": "releases/hello-hello-halloween/",
        "youtubeUrl": "https://www.youtube.com/watch?v=vuZiHlpo9Ak",
        "youtubeId": "vuZiHlpo9Ak",
        "youtubeVideoTitle": "【Official MV】Hello Hello Halloween／榎本魅愛（ENOMOTO MIA）🎃",
        "image": OFFICIAL_ARTWORKS["hello-hello-halloween"],
        "duration": 218,
        "uploadDate": "2026-09-16",
        "shortDescription": "榎本魅愛「Hello Hello Halloween」Official MV。",
        "featured": True,
        "playerEnabled": False,
        "relatedSongs": ["hyakumankoku", "hanakotoba", "hajimemashite-kiseki"],
    }
    data["releases"] = [rows["hello-hello-halloween"]] + [
        item for slug, item in rows.items() if slug != "hello-hello-halloween"
    ]
    write_json(MIA_PLAYER_PATH, data)


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    artists = {item["slug"]: item for item in cms["artists"]}
    releases = {item["slug"]: item for item in cms["releases"]}

    releases["mahou-ga-toketemo"] = release_from_template(
        cms,
        "akuyaku-de-ii",
        PUBLISHED_VIDEOS[0],
        description="神代煌牙「魔法が解けても ― Pumpkin Carriage ―」Official MVを公開中。",
        seo_description="神代煌牙「魔法が解けても ― Pumpkin Carriage ―」Official MVを公開中。作品情報と公式YouTubeへの導線をSUZUKA公式サイトで紹介します。",
        recommendation_weight=4,
    )
    releases["hello-hello-halloween"] = release_from_template(
        cms,
        "hyakumankoku",
        PUBLISHED_VIDEOS[1],
        description="榎本魅愛「Hello Hello Halloween」Official MVを公開中。2026年9月21日のストリーミング配信情報も掲載します。",
        seo_description="榎本魅愛「Hello Hello Halloween」Official MVを公開中。2026年9月21日のストリーミング配信情報と公式YouTubeをSUZUKA公式サイトで確認できます。",
        scheduled_streaming={
            "releaseDate": "2026-09-21",
            "timezone": "Asia/Tokyo",
            "label": "SUZUKA",
            "status": "upcoming",
            "source": "user-confirmed-tunecore-management-screen",
            "linkcoreUrl": "https://linkco.re/QfzZUy6f",
        },
        home_hero={
            "title": "SUZUKA Official | 榎本魅愛「Hello Hello Halloween」公開中",
            "description": "榎本魅愛「Hello Hello Halloween」Official MVを公開中。2026年9月21日のストリーミング配信情報も紹介します。",
            "subtitle": "ENOMOTO MIA · Official MV",
            "status": "NEW RELEASE",
            "lead": "榎本魅愛「Hello Hello Halloween」Official MV。",
            "projectLabel": "SUZUKA Official · Original AI Music Project",
            "primaryLabel": "Official MVを見る",
            "secondaryLabel": "作品を見る",
        },
        recommendation_weight=5,
    )
    update_existing_video(releases)
    cms["releases"] = sorted(releases.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True)
    cms["upcoming"] = [item for item in cms.get("upcoming", []) if item["slug"] != "hello-hello-halloween"]
    cms["comingSoon"] = [item for item in cms.get("comingSoon", []) if item["slug"] != "mahou-ga-toketemo"]

    for item in cms["upcoming"]:
        if item["slug"] in {"september-blue", "over-drive"}:
            item.update({
                "image": OFFICIAL_ARTWORKS[item["slug"]],
                "imageAlt": f'榎本魅愛「{item["title"]}」公式ビジュアル',
                "imageWidth": 886,
                "imageHeight": 886,
                "imageSource": OFFICIAL_ARTWORK_SOURCE,
            })

    mia = artists["enomoto-mia"]
    mia.update({
        "artistFeaturedTracks": ["hello-hello-halloween", "hyakumankoku", "hanakotoba"],
        "image": OFFICIAL_ARTWORKS["hello-hello-halloween"],
        "imageAlt": "榎本魅愛「Hello Hello Halloween」公式ビジュアル",
        "imageWidth": 886,
        "imageHeight": 886,
        "imageSource": OFFICIAL_ARTWORK_SOURCE,
    })
    koga = artists["koga-kamishiro"]
    koga.update({
        "artistFeaturedTracks": ["mahou-ga-toketemo", "akuyaku-de-ii", "wakareta-michi"],
        "image": OFFICIAL_ARTWORKS["mahou-ga-toketemo"],
        "imageAlt": "神代煌牙「魔法が解けても ― Pumpkin Carriage ―」公式ビジュアル",
        "imageWidth": 886,
        "imageHeight": 886,
        "imageSource": OFFICIAL_ARTWORK_SOURCE,
    })
    cms["artists"] = sorted(artists.values(), key=lambda item: item["slug"])

    news = {item["slug"]: item for item in cms.get("news", [])}
    for item in (releases["mahou-ga-toketemo"], releases["hello-hello-halloween"]):
        news[item["slug"] + "-release"] = {
            "slug": item["slug"] + "-release",
            "title": item["newsTitle"],
            "artistSlug": item["artistSlug"],
            "releaseSlug": item["slug"],
            "publishedAt": item["publishedAt"],
            "description": item["newsDescription"],
            "image": item["coverImage"],
            "status": "published",
            "searchKeywords": [item["artist"], item["title"], "Official MV", "YouTube"],
        }
    campaign = news.get("enomoto-mia-september-21-double-release")
    if campaign:
        campaign["description"] = "榎本魅愛「百万告」「Hello Hello Halloween」は2026年9月21日にストリーミング配信予定。「Hello Hello Halloween」は2026年9月16日にOfficial MVを公開し、「百万告」はAnime Versionを9月17日に公開しました。"
        campaign["searchKeywords"] = unique([*campaign.get("searchKeywords", []), "Official MV", "Anime Version"])
    anime_news = news.get("enomoto-mia-anime-opening-theme")
    if anime_news:
        anime_news["homeFeatured"] = True
    cms["news"] = sorted(news.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True)

    schedule = cms.setdefault("miaReleaseSchedule", {})
    for activity in schedule.get("activities", []):
        if activity.get("title") == "Hello Hello Halloween":
            activity["kind"] = "STREAMING RELEASE"
            activity["officialReleaseDate"] = "2026-09-16"

    youtube = cms.setdefault("youtubeSnapshot", {})
    shorts = {item["videoId"]: item for item in youtube.get("shortVideos", [])}
    shorts.update({item["videoId"]: short_record(item) for item in NEW_SHORTS})
    youtube.update({
        "officialVideos": 84,
        "shorts": 61,
        "totalPublishedVideos": 145,
        "verifiedAt": NOW,
        "source": "公式YouTube videos/shortsタブ・各動画の公開メタデータを照合",
        "shortVideos": sorted(shorts.values(), key=lambda item: (item["publishedAt"], item["videoId"]), reverse=True),
        "promotionalVideos": PROMOTIONAL_VIDEOS,
        "channels": [
            {
                "name": "SUZUKA",
                "role": "Label / Project Official",
                "channelUrl": "https://www.youtube.com/@suzuka1209",
                "channelId": LABEL_CHANNEL_ID,
                "officialVideos": 77,
                "shorts": 56,
                "totalPublishedVideos": 133,
            },
            {
                "name": "榎本魅愛",
                "role": "Artist Official",
                "channelUrl": "https://www.youtube.com/@enomotomia",
                "channelId": MIA_CHANNEL_ID,
                "officialVideos": 7,
                "shorts": 5,
                "totalPublishedVideos": 12,
            },
        ],
    })
    cms["updatedAt"] = NOW
    write_json(CMS_PATH, cms)

    dates = json.loads(DATES_PATH.read_text(encoding="utf-8"))
    records = {(item["releaseSlug"], item.get("youtubeId", "")): item for item in dates["records"]}
    for item in [*PUBLISHED_VIDEOS, UPDATED_RELEASE_VIDEO]:
        row = evidence_record(item)
        records[(row["releaseSlug"], row["youtubeId"])] = row
    for item in PROMOTIONAL_VIDEOS:
        row = evidence_record(item, content_type=item["contentType"])
        records[(row["releaseSlug"], row["youtubeId"])] = row
    for item in NEW_SHORTS:
        row = evidence_record(
            {**item, "releaseSlug": item.get("relatedRelease", "promotional-short"), "channelId": MIA_CHANNEL_ID if item["artistSlug"] == "enomoto-mia" else LABEL_CHANNEL_ID, "youtubeUrl": f'https://www.youtube.com/shorts/{item["videoId"]}'},
            content_type="short",
        )
        records[(row["releaseSlug"], row["youtubeId"])] = row
    dates.update({
        "checkedAt": NOW,
        "records": sorted(records.values(), key=lambda item: (item["releaseSlug"], item.get("youtubeId", ""))),
    })
    write_json(DATES_PATH, dates)

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state_evidence = {(item["slug"], item["videoId"]): item for item in state.get("evidence", [])}
    state_evidence[("mahou-ga-toketemo", "g_SmyjPGIfc")] = {
        "slug": "mahou-ga-toketemo",
        "videoId": "g_SmyjPGIfc",
        "releaseTimestamp": "2026-09-14T20:00:06+09:00",
        "availability": "public",
        "liveStatus": "not_live",
        "channelId": LABEL_CHANNEL_ID,
    }
    state.update({
        "verifiedAt": NOW,
        "promoted": sorted(set(state.get("promoted", [])) | {"mahou-ga-toketemo", "hello-hello-halloween"}),
        "evidence": sorted(state_evidence.values(), key=lambda item: (item["slug"], item["videoId"])),
        "upcomingHeld": [],
    })
    write_json(STATE_PATH, state)

    write_json(SNAPSHOT_PATH, {
        "schemaVersion": "1.2",
        "verifiedAt": NOW,
        "officialChannelId": LABEL_CHANNEL_ID,
        "channelUrl": "https://www.youtube.com/@suzuka1209",
        "verificationMethod": "公式YouTube videos/shortsタブ・各動画の公開メタデータを照合",
        "channelSnapshot": {"officialVideos": 84, "shorts": 61, "totalPublishedVideos": 145},
        "published": PUBLISHED_VIDEOS,
        "updatedReleaseVideos": [UPDATED_RELEASE_VIDEO],
        "promotionalVideos": PROMOTIONAL_VIDEOS,
        "shorts": [short_record(item) for item in NEW_SHORTS],
        "upcomingHeld": [],
    })
    update_mia_player()

    print(json.dumps({
        "published": [item["releaseSlug"] for item in PUBLISHED_VIDEOS],
        "updatedReleaseVideo": UPDATED_RELEASE_VIDEO["releaseSlug"],
        "promotionalVideos": len(PROMOTIONAL_VIDEOS),
        "newShorts": len(NEW_SHORTS),
        "publishedReleases": len(cms["releases"]),
        "upcoming": len(cms["upcoming"]),
        "comingSoon": len(cms.get("comingSoon", [])),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
