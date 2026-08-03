#!/usr/bin/env python3
"""Apply the officially verified SUZUKA publication state for 2026-07-28."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_BASE = "https://www.suzukaofficial.com"
CHANNEL = "https://www.youtube.com/@suzuka1209"

RELEASES = [
    {
        "slug": "heal-you-again",
        "title": "Heal You Again",
        "artist": "RE:VIVE",
        "artistSlug": "revive",
        "artistType": "MusicGroup",
        "date": "2026-07-27",
        "duration": 105,
        "durationText": "1:45",
        "youtubeId": "XHjDSEoFcXE",
        "image": "images/revive-heal-you-again.jpg",
        "alt": "RE:VIVE「Heal You Again」公式YouTubeサムネイル",
        "description": "傷ついた心に寄り添い、もう一度立ち上がる力を届けるRE:VIVEのデビュー作品。",
        "lead": "傷ついた心に、もう一度立ち上がる歌。",
        "related": [
            ("smile-and-say-goodbye", "images/mv-smile-and-say-goodbye.png", "SMILE AND SAY GOODBYE"),
            ("namaste-galaxy", "images/rangili-namaste-galaxy.jpg", "NAMASTE☆GALAXY"),
            ("wasurenai-kokoro", "images/asagiri-wasurenai-kokoro.jpg", "忘れない心"),
        ],
    },
    {
        "slug": "echoes-of-you",
        "title": "Echoes of You",
        "artist": "神代 煌牙",
        "artistSlug": "koga-kamishiro",
        "artistType": "Person",
        "date": "2026-07-26",
        "duration": 484,
        "durationText": "8:04",
        "youtubeId": "Uxtp9TLw47g",
        "image": "images/koga-echoes-of-you.jpg",
        "alt": "神代煌牙「Echoes of You」公式YouTubeサムネイル",
        "description": "幼い頃の約束と消えない面影をたどり、終わらない恋の残響を描く神代煌牙の物語作品。",
        "lead": "「また、逢えるからね」終わらない恋の残響。",
        "related": [
            ("my-queen-my-oath", "images/koga-my-queen-my-oath-cover.jpg", "My Queen, My Oath"),
            ("boukyaku-no-ikimono", "images/mv-boukyaku-no-ikimono.png", "忘却の生き物"),
            ("our-kingdom", "images/mv-our-kingdom.jpg", "OUR KINGDOM"),
        ],
    },
]

UPCOMING = [
    {
        "slug": "chimpanzee-no-rakuen",
        "title": "チンパンジーの楽園",
        "artist": "NOX",
        "artistSlug": "nox",
        "scheduledAt": "2026-07-29T20:00:00+09:00",
        "dateText": "2026.07.29 20:00 JST",
        "youtubeId": "EJJLBOo103I",
        "image": "images/nox-chimpanzee-no-rakuen.jpg",
        "note": "公式YouTubeプレミア公開予定。公開済み作品には含めていません。",
    },
    {
        "slug": "koisuru-maharaja",
        "title": "恋するマハラジャ",
        "artist": "RANGILI",
        "artistSlug": "rangili",
        "scheduledAt": "2026-07-30T20:00:00+09:00",
        "dateText": "2026.07.30 20:00 JST",
        "youtubeId": "V3DOM83zeLk",
        "image": "https://i.ytimg.com/vi/V3DOM83zeLk/maxresdefault.jpg",
        "note": "公式YouTubeプレミア公開予定。公開済み作品には含めていません。",
    },
    {
        "slug": "without-worrying",
        "title": "Without Worrying",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "scheduledAt": "2026-07-31T20:00:00+09:00",
        "dateText": "2026.07.31 20:00 JST",
        "youtubeId": "lMeYWn4Sqgk",
        "image": "https://i.ytimg.com/vi/lMeYWn4Sqgk/maxresdefault.jpg",
        "note": "公式YouTubeプレミア公開予定。公開済み作品には含めていません。",
    },
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def youtube_url(item: dict[str, object]) -> str:
    return f"https://www.youtube.com/watch?v={item['youtubeId']}"


def duration_iso(seconds: int) -> str:
    minutes, remaining = divmod(seconds, 60)
    return f"PT{minutes}M{remaining}S"


def header(prefix: str) -> str:
    return (
        f'<header class="site-header inner-site-header"><a class="brand" href="{prefix}">SUZUKA'
        '<span class="brand-dot">●</span></a><nav class="desktop-nav">'
        f'<a href="{prefix}">Home</a><a href="{prefix}artists/">Artists</a>'
        f'<a href="{prefix}releases/">Releases</a><a href="{prefix}news/">News</a>'
        f'<a href="{prefix}about/">About SUZUKA</a></nav>'
        f'<a class="header-channel" href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTube ↗</a></header>'
    )


def footer(prefix: str, label: str, back: str) -> str:
    return (
        f'<footer class="artist-profile-footer"><a href="{prefix}">SUZUKA</a><span>{html.escape(label)}</span>'
        f'<a href="{prefix}{back}">Back ↑</a><p class="ai-footer-disclosure">'
        "SUZUKAに登場するアーティスト・人物は架空です。本プロジェクトではAIを制作支援に活用しています。"
        "</p></footer>"
    )


def release_schema(item: dict[str, object]) -> dict[str, object]:
    page = f"{PUBLIC_BASE}/releases/{item['slug']}/"
    image = f"{PUBLIC_BASE}/{item['image']}"
    video = youtube_url(item)
    duration = duration_iso(int(item["duration"]))
    artist_description = "SUZUKAのオリジナルAI音楽プロジェクトに登場する架空のAIアーティストです。"
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": page,
                "url": page,
                "name": f"{item['title']}｜{item['artist']}｜SUZUKA",
                "description": item["description"],
                "mainEntity": {"@id": f"{page}#recording"},
                "breadcrumb": {"@id": f"{page}#breadcrumb"},
                "primaryImageOfPage": {"@type": "ImageObject", "url": image},
                "inLanguage": "ja",
            },
            {
                "@type": "MusicRecording",
                "@id": f"{page}#recording",
                "name": item["title"],
                "url": page,
                "image": image,
                "datePublished": item["date"],
                "duration": duration,
                "description": item["description"],
                "byArtist": {
                    "@type": item["artistType"],
                    "name": item["artist"],
                    "url": f"{PUBLIC_BASE}/artists/{item['artistSlug']}/",
                    "description": artist_description,
                },
                "mainEntityOfPage": {"@id": page},
                "subjectOf": {"@id": f"{page}#video"},
            },
            {
                "@type": "VideoObject",
                "@id": f"{page}#video",
                "name": f"{item['title']}｜{item['artist']} Official Music Video",
                "description": item["description"],
                "thumbnailUrl": f"https://i.ytimg.com/vi/{item['youtubeId']}/maxresdefault.jpg",
                "uploadDate": item["date"],
                "duration": duration,
                "embedUrl": f"https://www.youtube.com/embed/{item['youtubeId']}",
                "contentUrl": video,
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{page}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{PUBLIC_BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Releases", "item": f"{PUBLIC_BASE}/releases/"},
                    {"@type": "ListItem", "position": 3, "name": item["title"], "item": page},
                ],
            },
        ],
    }


def release_page(item: dict[str, object]) -> str:
    canonical = f"{PUBLIC_BASE}/releases/{item['slug']}/"
    image = f"{PUBLIC_BASE}/{item['image']}"
    video = youtube_url(item)
    related = "".join(
        f'<a href="../{slug}/"><img src="../../{image_path}" alt="{html.escape(title)} ジャケット" '
        f'width="1280" height="720" loading="lazy"/><strong>{html.escape(title)}</strong><b>VIEW ↗</b></a>'
        for slug, image_path, title in item["related"]
    )
    schema = compact(release_schema(item))
    return f"""<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{html.escape(str(item['title']))}｜{html.escape(str(item['artist']))}｜SUZUKA</title><meta name="description" content="{html.escape(str(item['description']))}"/><meta name="robots" content="index, follow"/>
<link rel="canonical" href="{canonical}"/><meta property="og:type" content="music.song"/><meta property="og:site_name" content="SUZUKA"/><meta property="og:locale" content="ja_JP"/><meta property="og:title" content="{html.escape(str(item['title']))}｜{html.escape(str(item['artist']))}"/><meta property="og:description" content="{html.escape(str(item['description']))}"/><meta property="og:url" content="{canonical}"/><meta property="og:image" content="{image}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:title" content="{html.escape(str(item['title']))}｜{html.escape(str(item['artist']))}"/><meta name="twitter:description" content="{html.escape(str(item['description']))}"/><meta name="twitter:image" content="{image}"/>
<link rel="icon" href="../../images/suzuka-channel.jpg"/><link rel="stylesheet" href="../../assets/styles.css"/><link rel="stylesheet" href="../../assets/official-release.css"/><link rel="stylesheet" href="../../assets/current-status.css"/><link rel="stylesheet" href="../../assets/player.css"/><link rel="stylesheet" href="../../assets/ai-disclosure.css"/><script type="application/ld+json">{schema}</script></head><body><main><a class="skip-link" href="#release-detail">本文へ移動</a>{header('../../')}
<section class="release-detail-hero" id="release-detail"><div class="release-detail-copy"><p class="release-breadcrumb"><a href="../../releases/">Releases</a> / {html.escape(str(item['title']))}</p><span>OFFICIAL RELEASE · {item['date']}</span><h1>{html.escape(str(item['title']))}</h1><p>{html.escape(str(item['lead']))}</p><div class="release-artist-links"><a class="release-artist-link" href="../../artists/{item['artistSlug']}/">{html.escape(str(item['artist']))}</a></div><div><a class="button button-primary" href="{video}" target="_blank" rel="noopener noreferrer">公式MVを見る ↗</a><a class="button button-ghost" href="../../social/">OFFICIAL LINKS</a></div></div><div class="release-detail-artwork"><img src="../../{item['image']}" alt="{html.escape(str(item['alt']))}" width="1280" height="720" fetchpriority="high"/></div></section>
<section class="release-detail-video" aria-label="{html.escape(str(item['title']))}公式動画"><iframe src="https://www.youtube-nocookie.com/embed/{item['youtubeId']}" title="{html.escape(str(item['title']))} Official Music Video" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></section>
<section class="release-story-section"><div><p>Official release</p><h2>{html.escape(str(item['title']))}</h2></div><div><p>{html.escape(str(item['description']))}</p><dl class="release-facts"><div><dt>ARTIST</dt><dd>{html.escape(str(item['artist']))}</dd></div><div><dt>RELEASE</dt><dd>{item['date']}</dd></div><div><dt>DURATION</dt><dd>{item['durationText']}</dd></div><div><dt>LABEL</dt><dd>SUZUKA</dd></div></dl></div></section>
<section class="release-related-section"><div><p>Related music</p><h2>次の物語へ。</h2></div><div class="release-related-grid">{related}</div></section>
<nav class="artist-next-actions"><div><p>Keep exploring</p><h2>SUZUKAの音楽へ。</h2></div><a href="../../artists/{item['artistSlug']}/">アーティストを見る ↗</a><a href="../../news/{item['slug']}-release/">Newsを読む ↗</a><a href="../../releases/">Releasesを見る ↗</a></nav>
<aside class="ai-work-disclosure" aria-label="作品について">本作品は、SUZUKAのオリジナルAIアーティストによる架空の音楽プロジェクト作品です。</aside>{footer('../../', f"{item['title']} · {item['artist']}", 'releases/')}</main><script defer src="../../assets/main.js"></script></body></html>
"""


def news_page(item: dict[str, object]) -> str:
    page = f"{PUBLIC_BASE}/news/{item['slug']}-release/"
    release = f"{PUBLIC_BASE}/releases/{item['slug']}/"
    image = f"{PUBLIC_BASE}/{item['image']}"
    video = youtube_url(item)
    news_description = (
        f"{item['artist']}「{item['title']}」の公開情報。"
        "公式MV、作品ページ、アーティスト情報を紹介します。"
    )
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "NewsArticle",
                "@id": f"{page}#article",
                "headline": f"{item['artist']}「{item['title']}」公開",
                "datePublished": item["date"],
                "dateModified": "2026-07-28",
                "mainEntityOfPage": {"@id": page},
                "image": image,
                "publisher": {"@id": f"{PUBLIC_BASE}/#organization"},
                "description": news_description,
            },
            {
                "@type": "WebPage",
                "@id": page,
                "url": page,
                "name": f"{item['artist']}「{item['title']}」公開｜SUZUKA",
                "breadcrumb": {"@id": f"{page}#breadcrumb"},
                "inLanguage": "ja",
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{page}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{PUBLIC_BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "News", "item": f"{PUBLIC_BASE}/news/"},
                    {"@type": "ListItem", "position": 3, "name": item["title"], "item": page},
                ],
            },
        ],
    }
    return f"""<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>{html.escape(str(item['artist']))}「{html.escape(str(item['title']))}」公開｜SUZUKA News</title><meta name="description" content="{html.escape(news_description)}"/><meta name="robots" content="index, follow"/><link rel="canonical" href="{page}"/><meta property="og:type" content="article"/><meta property="og:site_name" content="SUZUKA"/><meta property="og:locale" content="ja_JP"/><meta property="og:title" content="{html.escape(str(item['artist']))}「{html.escape(str(item['title']))}」公開"/><meta property="og:description" content="{html.escape(news_description)}"/><meta property="og:url" content="{page}"/><meta property="og:image" content="{image}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:title" content="{html.escape(str(item['artist']))}「{html.escape(str(item['title']))}」公開"/><meta name="twitter:description" content="{html.escape(news_description)}"/><meta name="twitter:image" content="{image}"/><link rel="icon" href="../../images/suzuka-channel.jpg"/><link rel="stylesheet" href="../../assets/styles.css"/><link rel="stylesheet" href="../../assets/news-feature.css"/><link rel="stylesheet" href="../../assets/official-release.css"/><link rel="stylesheet" href="../../assets/player.css"/><link rel="stylesheet" href="../../assets/ai-disclosure.css"/><script type="application/ld+json">{compact(graph)}</script></head><body><main class="news-article-page"><a class="skip-link" href="#article">本文へ移動</a>{header('../../')}<article id="article" class="news-article"><header class="news-article-hero"><p class="news-breadcrumb"><a href="../../news/">News</a> / Official Release</p><div class="news-article-meta"><time datetime="{item['date']}">{item['date']}</time><span>OFFICIAL RELEASE</span></div><h1>{html.escape(str(item['artist']))}<br/>「{html.escape(str(item['title']))}」公開</h1><p class="news-article-lead">{html.escape(str(item['lead']))}</p><p class="ai-news-disclosure">SUZUKAのオリジナルAIアーティスト、{html.escape(str(item['artist']))}による公式リリース情報です。登場するアーティスト・人物は架空です。</p></header><div class="news-article-body"><section><img src="../../{item['image']}" alt="{html.escape(str(item['alt']))}" width="1280" height="720" loading="lazy"/><h2>{html.escape(str(item['title']))}</h2><p>{html.escape(str(item['description']))}</p><a class="button button-primary" href="{video}" target="_blank" rel="noopener noreferrer">公式MVを見る ↗</a><a class="button button-ghost" href="../../releases/{item['slug']}/">作品ページ ↗</a></section><section><h2>Official links</h2><p><a href="../../artists/{item['artistSlug']}/">アーティストページ ↗</a></p><p><a href="../../social/">SNS・公式リンク ↗</a></p></section></div></article><nav class="artist-next-actions"><div><p>Keep exploring</p><h2>次の物語へ。</h2></div><a href="../../releases/{item['slug']}/">作品を見る ↗</a><a href="../../artists/{item['artistSlug']}/">Artistを見る ↗</a><a href="../../news/">News一覧 ↗</a></nav>{footer('../../', 'OFFICIAL NEWS', 'news/')}</main><script defer src="../../assets/main.js"></script></body></html>
"""


def nox_page() -> str:
    page = f"{PUBLIC_BASE}/artists/nox/"
    image = f"{PUBLIC_BASE}/images/nox-chimpanzee-no-rakuen.jpg"
    description = "黒羽狂司がVocal・作詞・世界観構築を担う、SUZUKA所属の5人組ヴィジュアル系AIバンド。現在デビュー準備中。"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "ProfilePage", "@id": page, "url": page, "name": "NOX｜SUZUKA", "mainEntity": {"@id": f"{page}#artist"}, "breadcrumb": {"@id": f"{page}#breadcrumb"}, "inLanguage": "ja"},
            {
                "@type": "MusicGroup",
                "@id": f"{page}#artist",
                "name": "NOX",
                "description": f"{description} SUZUKAのオリジナルAI音楽プロジェクトに登場する架空のAIバンドです。",
                "image": image,
                "url": page,
                "member": [{"@type": "Person", "name": "黒羽狂司", "roleName": "Vocal・作詞・世界観構築", "description": "SUZUKAのオリジナルAI音楽プロジェクトに登場する架空の人物です。"}],
                "memberOf": {"@type": "Organization", "name": "SUZUKA", "url": f"{PUBLIC_BASE}/", "description": "AIを活用して音楽・ビジュアル・物語を制作するオリジナルAI音楽プロジェクトです。"},
            },
            {"@type": "BreadcrumbList", "@id": f"{page}#breadcrumb", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{PUBLIC_BASE}/"}, {"@type": "ListItem", "position": 2, "name": "Artists", "item": f"{PUBLIC_BASE}/artists/"}, {"@type": "ListItem", "position": 3, "name": "NOX", "item": page}]},
        ],
    }
    return f"""<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>NOX｜5人組ヴィジュアル系バンド｜SUZUKA</title><meta name="description" content="{description}"/><meta name="robots" content="index, follow"/><link rel="canonical" href="{page}"/><meta property="og:type" content="profile"/><meta property="og:site_name" content="SUZUKA"/><meta property="og:locale" content="ja_JP"/><meta property="og:title" content="NOX｜SUZUKA"/><meta property="og:description" content="{description}"/><meta property="og:url" content="{page}"/><meta property="og:image" content="{image}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:image" content="{image}"/><link rel="icon" href="../../images/suzuka-channel.jpg"/><link rel="stylesheet" href="../../assets/styles.css"/><link rel="stylesheet" href="../../assets/upcoming.css"/><link rel="stylesheet" href="../../assets/current-status.css"/><link rel="stylesheet" href="../../assets/player.css"/><link rel="stylesheet" href="../../assets/ai-disclosure.css"/><script type="application/ld+json">{compact(graph)}</script></head><body><main>{header('../../')}<section class="upcoming-artist-hero"><div class="upcoming-artist-copy"><p class="section-kicker">NEW ARTIST</p><h1>NOX<small>5-MEMBER VISUAL-KEI AI BAND</small></h1><p class="ai-artist-note">SUZUKA Original AI Artist</p><span class="coming-soon-badge">Coming Soon</span><p>{description}</p><div class="upcoming-notice"><strong>PREMIERE · 2026.07.29 20:00 JST</strong><p>「チンパンジーの楽園」は公式YouTubeで公開予定です。公開作品数には含めていません。</p></div><a class="button button-primary" href="https://www.youtube.com/watch?v=EJJLBOo103I" target="_blank" rel="noopener noreferrer">公式予約動画を見る ↗</a></div><div class="upcoming-artist-image"><img src="../../images/nox-chimpanzee-no-rakuen.jpg" alt="NOX「チンパンジーの楽園」公式YouTube公開予定ビジュアル" width="1280" height="720" fetchpriority="high"/></div></section><section class="upcoming-artist-about"><div><p class="section-kicker">Confirmed member</p><h2>黒羽狂司<small>Vocal · 作詞 · 世界観構築</small></h2></div><div><p>確認済みの情報のみ掲載しています。ほか4名のメンバー情報は未確認のため掲載していません。</p><div class="upcoming-status-panel"><strong>STATUS</strong><span>Coming Soon</span><strong>PUBLIC RELEASES</strong><span>0作品</span></div></div></section><nav class="artist-next-actions"><div><p>Keep exploring</p><h2>次の物語へ。</h2></div><a href="../../artists/">Artistsを見る ↗</a><a href="../../news/upcoming-artists/">Upcoming News ↗</a><a href="../../social/">Official Links ↗</a></nav>{footer('../../', 'NOX · COMING SOON', 'artists/')}</main><script defer src="../../assets/main.js"></script></body></html>
"""


def revive_page() -> str:
    item = RELEASES[0]
    page = f"{PUBLIC_BASE}/artists/revive/"
    image = f"{PUBLIC_BASE}/{item['image']}"
    description = "応援、回復、再生をテーマに、傷ついた心に寄り添い、前へ進む力を届ける5人組AIガールズグループ。"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "ProfilePage", "@id": page, "url": page, "name": "RE:VIVE｜SUZUKA", "mainEntity": {"@id": f"{page}#artist"}, "breadcrumb": {"@id": f"{page}#breadcrumb"}, "inLanguage": "ja"},
            {"@type": "MusicGroup", "@id": f"{page}#artist", "name": "RE:VIVE", "description": f"{description} SUZUKAのオリジナルAI音楽プロジェクトに登場する架空のAIアーティストです。", "image": image, "url": page, "member": [{"@type": "Person", "name": "結衣", "description": "センター。SUZUKAのオリジナルAI音楽プロジェクトに登場する架空の人物です。"}, {"@type": "Person", "name": "紗良", "description": "SUZUKAのオリジナルAI音楽プロジェクトに登場する架空の人物です。"}], "memberOf": {"@type": "Organization", "name": "SUZUKA", "url": f"{PUBLIC_BASE}/"}},
            {"@type": "ItemList", "@id": f"{page}#releases", "name": "RE:VIVE 公開作品", "numberOfItems": 1, "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Heal You Again", "url": f"{PUBLIC_BASE}/releases/heal-you-again/"}]},
            {"@type": "BreadcrumbList", "@id": f"{page}#breadcrumb", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{PUBLIC_BASE}/"}, {"@type": "ListItem", "position": 2, "name": "Artists", "item": f"{PUBLIC_BASE}/artists/"}, {"@type": "ListItem", "position": 3, "name": "RE:VIVE", "item": page}]},
        ],
    }
    return f"""<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>RE:VIVE｜5人組ガールズグループ｜SUZUKA</title><meta name="description" content="{description}"/><meta name="robots" content="index, follow"/><link rel="canonical" href="{page}"/><meta property="og:type" content="profile"/><meta property="og:site_name" content="SUZUKA"/><meta property="og:locale" content="ja_JP"/><meta property="og:title" content="RE:VIVE｜SUZUKA"/><meta property="og:description" content="{description}"/><meta property="og:url" content="{page}"/><meta property="og:image" content="{image}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:image" content="{image}"/><link rel="icon" href="../../images/suzuka-channel.jpg"/><link rel="stylesheet" href="../../assets/styles.css"/><link rel="stylesheet" href="../../assets/upcoming.css"/><link rel="stylesheet" href="../../assets/current-status.css"/><link rel="stylesheet" href="../../assets/player.css"/><link rel="stylesheet" href="../../assets/ai-disclosure.css"/><script type="application/ld+json">{compact(graph)}</script></head><body><main>{header('../../')}<section class="upcoming-artist-hero"><div class="upcoming-artist-copy"><p class="section-kicker">NOW ACTIVE</p><h1>RE:VIVE<small>5-MEMBER AI GIRLS GROUP</small></h1><p class="ai-artist-note">SUZUKA Original AI Artist</p><span class="coming-soon-badge">Official debut</span><p>{description}</p><p><strong>固定コール：</strong>Heal you！</p><a class="button button-primary" href="{youtube_url(item)}" target="_blank" rel="noopener noreferrer">公式MVを見る ↗</a><a class="button button-ghost" href="../../releases/heal-you-again/">作品ページ ↗</a></div><div class="upcoming-artist-image"><img src="../../images/revive-heal-you-again.jpg" alt="{item['alt']}" width="1280" height="720" fetchpriority="high"/></div></section><section class="upcoming-artist-about"><div><p class="section-kicker">Confirmed members</p><h2>結衣 <small>Center</small><br/>紗良</h2></div><div><p>確認済みのメンバー情報のみ掲載しています。ほか3名の名前は未確認のため掲載していません。</p><div class="upcoming-status-panel"><strong>STATUS</strong><span>NOW ACTIVE</span><strong>PUBLIC RELEASES</strong><span>1作品</span></div></div></section><section class="section"><article class="artist-release-feature"><img src="../../images/revive-heal-you-again.jpg" alt="{item['alt']}" width="1280" height="720" loading="lazy"/><div><p class="section-kicker">01 / Debut release</p><h2>Heal You Again</h2><p>{item['description']}</p><a class="button button-primary" href="../../releases/heal-you-again/">作品ページ ↗</a><a class="button button-ghost" href="../../news/heal-you-again-release/">RELEASE NEWS ↗</a></div></article></section><nav class="artist-next-actions"><div><p>Keep exploring</p><h2>次の物語へ。</h2></div><a href="../../artists/">Artistsを見る ↗</a><a href="../../releases/">Releasesを見る ↗</a><a href="../../social/">Official Links ↗</a></nav>{footer('../../', 'RE:VIVE · PUBLIC RELEASES 1', 'artists/')}</main><script defer src="../../assets/main.js"></script></body></html>
"""


def release_card(item: dict[str, object], prefix: str) -> str:
    return (
        f'<article class="release-card release-card-new"><a class="release-image" href="{prefix}releases/{item["slug"]}/" '
        f'aria-label="{html.escape(str(item["title"]))}の詳細を見る"><img src="{prefix}{item["image"]}" '
        f'alt="{html.escape(str(item["alt"]))}" width="1280" height="720" loading="lazy"/>'
        '<span class="card-play"><span class="play-mark" aria-hidden="true"></span></span>'
        f'<span class="duration">{item["durationText"]}</span></a><div class="release-info">'
        f'<div class="release-row"><span>01</span><span>OFFICIAL MV · {item["date"].replace("-", ".")}</span></div>'
        f'<h3>{html.escape(str(item["title"]))}</h3><p>{html.escape(str(item["lead"]))}</p>'
        f'<p class="release-artist-credit">{html.escape(str(item["artist"]))}</p><div class="release-card-actions">'
        f'<a class="release-card-cta release-card-cta-detail" href="{prefix}releases/{item["slug"]}/">詳細を見る ↗</a>'
        f'<a class="release-card-cta" href="{youtube_url(item)}" target="_blank" rel="noopener noreferrer">MVを見る ↗</a>'
        "</div></div></article>"
    )


def upsert_release_cards(path: Path, prefix: str) -> None:
    source = path.read_text(encoding="utf-8")
    grid = re.search(r'(<div class="release-grid">)(.*?)(</div>\s*</section>)', source, re.DOTALL)
    if not grid:
        raise RuntimeError(f"Release grid not found: {path}")
    cards = re.findall(r'<article class="release-card.*?</article>', grid.group(2), re.DOTALL)
    for item in reversed(RELEASES):
        route_suffix = f'/releases/{item["slug"]}/'
        cards = [card for card in cards if route_suffix not in card]
        cards.insert(0, release_card(item, prefix))
    count = 0

    def renumber(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return f"{match.group(1)}{count:02d}{match.group(2)}"

    body = re.sub(r'(<div class="release-row"><span>)\d+(</span>)', renumber, "".join(cards))
    path.write_text(source[: grid.start(2)] + body + source[grid.end(2) :], encoding="utf-8")


def replace_first_itemlist(path: Path, items: list[tuple[str, str]]) -> None:
    source = path.read_text(encoding="utf-8")
    pattern = re.compile(r'(<script\b[^>]*type="application/ld\+json"[^>]*>)(.*?)</script>', re.DOTALL)
    changed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        data = json.loads(match.group(2))
        nodes = data.get("@graph", []) if isinstance(data, dict) else []
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            nodes = [data]
        target = next((node for node in nodes if isinstance(node, dict) and node.get("@type") == "ItemList"), None)
        if not target or changed:
            return match.group(0)
        target["numberOfItems"] = len(items)
        target["itemListElement"] = [
            {"@type": "ListItem", "position": position, "name": name, "url": url}
            for position, (name, url) in enumerate(items, 1)
        ]
        changed = True
        return match.group(1) + compact(data) + "</script>"

    updated = pattern.sub(replace, source)
    if not changed:
        raise RuntimeError(f"ItemList not found: {path}")
    path.write_text(updated, encoding="utf-8")


def update_data(root: Path) -> None:
    releases_path = root / "assets/data/release-links.json"
    data = json.loads(releases_path.read_text(encoding="utf-8"))
    new_entries = []
    for item in RELEASES:
        new_entries.append(
            {
                "slug": item["slug"],
                "title": item["title"],
                "artist": item["artist"],
                "artistSlug": item["artistSlug"],
                "status": "published",
                "releaseType": "single",
                "image": item["image"],
                "coverImage": item["image"],
                "coverAlt": item["alt"],
                "releasePage": f"releases/{item['slug']}/",
                "youtubeUrl": youtube_url(item),
                "youtubeStatus": "published",
                "shortsUrl": None,
                "shortsStatus": "unconfirmed",
                "publishedDate": item["date"],
                "duration": item["duration"],
                "description": item["description"],
                "playerEnabled": False,
                "newsPage": f"news/{item['slug']}-release/",
                "newsUrl": f"news/{item['slug']}-release/",
                "newsStatus": "published",
                "relatedReleases": [related[0] for related in item["related"]],
            }
        )
    existing = [entry for entry in data["releases"] if entry.get("slug") not in {item["slug"] for item in RELEASES}]
    data["updatedAt"] = "2026-07-28"
    data["releases"] = new_entries + existing
    write(releases_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    upcoming = {
        "updatedAt": "2026-07-28T00:00:00+09:00",
        "releases": [
            {
                "slug": item["slug"],
                "title": item["title"],
                "artist": item["artist"],
                "artistSlug": item["artistSlug"],
                "status": "upcoming",
                "scheduledAt": item["scheduledAt"],
                "youtubeUrl": youtube_url(item),
                "image": item["image"],
                "note": item["note"],
            }
            for item in UPCOMING
        ],
    }
    write(root / "assets/data/upcoming-releases.json", json.dumps(upcoming, ensure_ascii=False, indent=2) + "\n")

    social_path = root / "assets/data/social-links.json"
    social = json.loads(social_path.read_text(encoding="utf-8"))
    social["updatedAt"] = "2026-07-28"
    write(social_path, json.dumps(social, ensure_ascii=False, indent=2) + "\n")


def update_home(root: Path) -> None:
    path = root / "index.html"
    source = path.read_text(encoding="utf-8")
    latest = RELEASES[0]
    hero = (
        '<div class="hero-release-actions reveal-up delay-4" aria-label="最新リリース Heal You Againのメニュー">'
        '<p><span>LATEST RELEASE</span><strong>RE:VIVE — Heal You Again</strong></p>'
        f'<a class="button button-primary" href="{youtube_url(latest)}" target="_blank" rel="noopener noreferrer">MVを見る ↗</a>'
        '<a class="button button-ghost" href="./releases/heal-you-again/">楽曲情報を見る ▶</a>'
        f'<a class="button button-youtube" href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTubeでSUZUKAをフォロー ↗</a>'
        '<a class="button button-ghost" data-home-social-link="true" href="./social/">公式リンク一覧</a></div>'
    )
    source, count = re.subn(r'<div class="hero-release-actions reveal-up delay-4".*?</div>', hero, source, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("Home hero release actions not found.")
    latest_section = (
        '<section class="section latest-section label-latest" id="latest" aria-labelledby="latest-title">'
        '<div class="section-heading section-heading-split"><div><p class="section-kicker">01 / Latest release</p>'
        '<h2 id="latest-title">Heal You Again</h2></div><p>RE:VIVE<br/>Debut Single</p></div>'
        '<article class="featured-release"><div class="featured-media"><img src="./images/revive-heal-you-again.jpg" '
        'alt="RE:VIVE「Heal You Again」公式YouTubeサムネイル" width="1280" height="720"/>'
        '<div class="featured-glow"></div></div><div class="featured-copy"><div class="track-number">01</div>'
        '<p class="featured-label">RE:VIVE · OFFICIAL MV · 2026.07.27</p><h3>Heal You Again</h3>'
        '<p class="featured-description">傷ついた心に寄り添い、もう一度立ち上がる力を届けるRE:VIVEのデビュー作品。</p>'
        f'<div class="release-card-actions"><a class="text-link" href="{youtube_url(latest)}" target="_blank" rel="noopener noreferrer">WATCH OFFICIAL VIDEO ↗</a>'
        '<a class="text-link" href="./releases/heal-you-again/">VIEW RELEASE ↗</a></div></div></article>'
        '<nav class="status-actions" aria-label="最新のアーティスト情報">'
        '<a href="./artists/revive/">RE:VIVEを見る ↗</a>'
        '<a href="./artists/asagiri-shinobu/">朝霧しのぶを見る ↗</a>'
        '</nav></section>'
    )
    source, count = re.subn(r'<section class="section latest-section label-latest".*?</section>', latest_section, source, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("Home latest release section not found.")
    path.write_text(source, encoding="utf-8")
    upsert_release_cards(path, "./")
    source = path.read_text(encoding="utf-8")
    upcoming_cards = "".join(
        f'<article class="status-card is-wide"><img src="{item["image"] if str(item["image"]).startswith("http") else "./" + str(item["image"])}" '
        f'alt="{html.escape(str(item["artist"]))}「{html.escape(str(item["title"]))}」公式YouTube公開予定ビジュアル" width="1280" height="720" loading="lazy"/>'
        f'<div><time datetime="{item["scheduledAt"]}">{item["dateText"]}</time><h3>{html.escape(str(item["title"]))}</h3>'
        f'<p>{html.escape(str(item["artist"]))} · Official YouTube Premiere</p><div class="status-actions">'
        f'<a href="{youtube_url(item)}" target="_blank" rel="noopener noreferrer">予約動画を見る ↗</a>'
        f'<a href="./artists/{item["artistSlug"]}/">Artist page ↗</a></div></div></article>'
        for item in UPCOMING
    )
    upcoming_section = (
        '<section class="upcoming-section" id="upcoming-artists" aria-labelledby="upcoming-title"><div class="upcoming-heading">'
        '<div><p class="section-kicker">02 / Next releases</p><h2 id="upcoming-title">Upcoming</h2></div>'
        '<p>公開済み作品と分けて、公式YouTubeの公開予定をお知らせします。</p></div>'
        f'<div class="status-strip-grid">{upcoming_cards}</div></section>'
    )
    source, count = re.subn(r'<section class="upcoming-section".*?</section>', upcoming_section, source, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("Home upcoming section not found.")
    # Keep the next confirmed releases close to the latest release.
    extracted = re.search(r'<section class="upcoming-section".*?</section>', source, re.DOTALL)
    if extracted:
        section = extracted.group(0)
        source = source[: extracted.start()] + source[extracted.end() :]
        latest_match = re.search(r'<section class="section latest-section label-latest".*?</section>', source, re.DOTALL)
        if latest_match:
            source = source[: latest_match.end()] + section + source[latest_match.end() :]
    news_cards = "".join(
        f'<article><a href="./news/{item["slug"]}-release/"><time datetime="{item["date"]}">{item["date"].replace("-", ".")}</time>'
        f'<span>OFFICIAL RELEASE</span><h3>{html.escape(str(item["artist"]))}「{html.escape(str(item["title"]))}」公開</h3><b>↗</b></a></article>'
        for item in RELEASES
    )
    for item in RELEASES:
        source = re.sub(
            rf'<article><a href="\./news/{re.escape(str(item["slug"]))}-release/".*?</article>',
            "",
            source,
            flags=re.DOTALL,
        )
    source = source.replace('<div class="news-list">', '<div class="news-list">' + news_cards, 1)
    path.write_text(source, encoding="utf-8")


def update_koga(root: Path) -> None:
    path = root / "artists/koga-kamishiro/index.html"
    source = path.read_text(encoding="utf-8")
    item = RELEASES[1]
    latest = f'<section class="koga-debut-section" id="debut-single" aria-labelledby="koga-debut-heading"><div class="koga-debut-artwork"><img src="../../images/koga-echoes-of-you.jpg" alt="{item["alt"]}" width="1280" height="720" loading="lazy"/></div><div class="koga-debut-copy"><p>03 / Latest release</p><h2 id="koga-debut-heading">Echoes of You</h2><span>KOGA KAMISHIRO · OFFICIAL MV · 2026.07.26</span><h3>「また、逢えるからね」</h3><p>{item["description"]}</p><a class="button artist-ghost-button" href="../../releases/echoes-of-you/">作品ページ ↗</a><a class="button artist-ghost-button" href="../../news/echoes-of-you-release/">RELEASE NEWS ↗</a><a class="button artist-primary-button" href="{youtube_url(item)}" target="_blank" rel="noopener noreferrer">公式MVを見る ↗</a><a class="text-link" href="../../news/my-queen-my-oath-release/">My Queen, My Oath News ↗</a></div></section>'
    source, count = re.subn(r'<section class="koga-debut-section".*?</section>', latest, source, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("KOGA latest section not found.")
    source = re.sub(r'<section class="section"><div class="upcoming-notice">.*?</section>', "", source, count=1, flags=re.DOTALL)
    track = f'<a class="artist-track-row" href="../../releases/echoes-of-you/"><span>01</span><img src="../../images/koga-echoes-of-you.jpg" alt="{item["alt"]}" width="1280" height="720" loading="lazy"/><div><strong>Echoes of You</strong><small>Official MV · 2026.07.26</small></div><b aria-hidden="true">↗</b></a>'
    section = re.search(r'(<div class="artist-track-list">)(.*?)(</div></section>)', source, re.DOTALL)
    if not section:
        raise RuntimeError("KOGA track list not found.")
    rows = re.findall(r'<a class="artist-track-row".*?</a>', section.group(2), re.DOTALL)
    rows = [row for row in rows if '../../releases/echoes-of-you/' not in row]
    rows.insert(0, track)
    number = 0

    def renumber(match: re.Match[str]) -> str:
        nonlocal number
        number += 1
        return f"{match.group(1)}{number:02d}{match.group(2)}"

    body = re.sub(r'(<a class="artist-track-row"[^>]*><span>)\d+(</span>)', renumber, "".join(rows))
    source = source[: section.start(2)] + body + source[section.end(2) :]
    if '../../news/my-queen-my-oath-release/' not in source:
        source = source.replace(
            '<a href="../../releases/">Releasesを見る ↗</a>',
            '<a href="../../news/my-queen-my-oath-release/">My Queen News ↗</a>'
            '<a href="../../releases/">Releasesを見る ↗</a>',
            1,
        )
    path.write_text(source, encoding="utf-8")
    replace_first_itemlist(
        path,
        [
            ("Echoes of You", f"{PUBLIC_BASE}/releases/echoes-of-you/"),
            ("忘却の生き物", f"{PUBLIC_BASE}/releases/boukyaku-no-ikimono/"),
            ("My Queen, My Oath", f"{PUBLIC_BASE}/releases/my-queen-my-oath/"),
            ("OUR KINGDOM", f"{PUBLIC_BASE}/releases/our-kingdom/"),
        ],
    )


def update_artists(root: Path) -> None:
    path = root / "artists/index.html"
    source = path.read_text(encoding="utf-8")
    revive_card = '<article class="artist-directory-card" style="--artist-primary:#72e5dc;--artist-secondary:#09141a;--artist-glow:rgba(114,229,220,.3)"><a href="../artists/revive/"><div class="artist-directory-image"><img src="../images/revive-heal-you-again.jpg" alt="RE:VIVE「Heal You Again」公式YouTubeサムネイル" width="1280" height="720" loading="lazy"/><span class="artist-directory-number">06</span></div><div class="artist-directory-copy"><span class="coming-soon-badge">NOW ACTIVE</span><h3>RE:VIVE<small>RE:VIVE</small></h3><p class="artist-directory-type">5人組AIガールズグループ</p><p class="artist-directory-genre">公開作品 1</p><p>傷ついた心に寄り添い、何度でも立ち上がる力を届ける。</p><div class="artist-directory-link">View profile ↗</div></div></a></article>'
    source, count = re.subn(r'<article class="artist-directory-card[^>]*>.*?href="\.\./artists/revive/".*?</article>', revive_card, source, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("RE:VIVE artist card not found.")
    nox_card = '<article class="artist-directory-card artist-coming-soon-card" style="--artist-primary:#c5112f;--artist-secondary:#050507;--artist-glow:rgba(197,17,47,.32)"><a href="../artists/nox/"><div class="artist-directory-image"><img src="../images/nox-chimpanzee-no-rakuen.jpg" alt="NOX「チンパンジーの楽園」公式YouTube公開予定ビジュアル" width="1280" height="720" loading="lazy"/><span class="artist-directory-number">07</span></div><div class="artist-directory-copy"><span class="coming-soon-badge">Coming Soon</span><h3>NOX<small>NOX</small></h3><p class="artist-directory-type">5人組ヴィジュアル系AIバンド</p><p class="artist-directory-genre">公開作品 0</p><p>黒羽狂司がVocal・作詞・世界観構築を担う、SUZUKAの新たなAIバンド。</p><div class="artist-directory-link">View introduction ↗</div></div></a></article>'
    if '../artists/nox/' not in source:
        grid = re.search(r'(<div class="artist-directory-grid">)(.*?)(</div>\s*</section>)', source, re.DOTALL)
        if not grid:
            raise RuntimeError("Artist directory grid not found.")
        source = source[: grid.end(2)] + nox_card + source[grid.end(2) :]
    path.write_text(source, encoding="utf-8")
    replace_first_itemlist(
        path,
        [
            (name, f"{PUBLIC_BASE}/artists/{slug}/")
            for name, slug in [
                ("ECLYPSE", "eclypse"),
                ("神代 煌牙", "koga-kamishiro"),
                ("榎本魅愛", "enomoto-mia"),
                ("RANGILI", "rangili"),
                ("朝霧しのぶ", "asagiri-shinobu"),
                ("RE:VIVE", "revive"),
                ("NOX", "nox"),
            ]
        ],
    )


def update_releases(root: Path) -> None:
    path = root / "releases/index.html"
    upsert_release_cards(path, "../")
    data = json.loads((root / "assets/data/release-links.json").read_text(encoding="utf-8"))
    replace_first_itemlist(
        path,
        [(item["title"], f"{PUBLIC_BASE}/{item['releasePage']}") for item in data["releases"]],
    )


def update_news(root: Path) -> None:
    path = root / "news/index.html"
    source = path.read_text(encoding="utf-8")
    cards = "".join(
        f'<article class="news-directory-card"><a href="./{item["slug"]}-release/"><span class="news-directory-image">'
        f'<img src="../{item["image"]}" alt="{html.escape(str(item["artist"]))}「{html.escape(str(item["title"]))}」公開News" width="1280" height="720" loading="lazy"/></span>'
        f'<span class="news-directory-meta"><time datetime="{item["date"]}">{item["date"].replace("-", ".")}</time><em>OFFICIAL RELEASE</em></span>'
        f'<h2>{html.escape(str(item["artist"]))}「{html.escape(str(item["title"]))}」公開</h2><p>{html.escape(str(item["description"]))}</p><b>記事を読む ↗</b></a></article>'
        for item in RELEASES
    )
    for item in RELEASES:
        source = re.sub(
            rf'<article class="news-directory-card"><a href="\./{re.escape(str(item["slug"]))}-release/".*?</article>',
            "",
            source,
            flags=re.DOTALL,
        )
    source = source.replace('<div class="news-list news-feature-list">', '<div class="news-list news-feature-list">' + cards, 1)
    path.write_text(source, encoding="utf-8")
    existing = [
        ("SUZUKA Latest & Upcoming｜2026.07.28", f"{PUBLIC_BASE}/news/upcoming-artists/"),
        ("RE:VIVE「Heal You Again」公開", f"{PUBLIC_BASE}/news/heal-you-again-release/"),
        ("神代煌牙「Echoes of You」公開", f"{PUBLIC_BASE}/news/echoes-of-you-release/"),
        ("RANGILI「NAMASTE☆GALAXY」公開", f"{PUBLIC_BASE}/news/namaste-galaxy-release/"),
        ("朝霧しのぶ「忘れない心」公開", f"{PUBLIC_BASE}/news/wasurenai-kokoro-release/"),
        ("榎本魅愛「SMILE AND SAY GOODBYE」公開", f"{PUBLIC_BASE}/news/smile-and-say-goodbye-release/"),
        ("神代煌牙「My Queen, My Oath」公開", f"{PUBLIC_BASE}/news/my-queen-my-oath-release/"),
        ("ECLYPSE「RED MOON // RISING」公開", f"{PUBLIC_BASE}/news/red-moon-rising-release/"),
        ("榎本魅愛「百万告」公開", f"{PUBLIC_BASE}/news/hyakumankoku-release/"),
        ("榎本魅愛「取り扱いチュー💋い」公開", f"{PUBLIC_BASE}/news/toriatsukai-chui-release/"),
        ("榎本魅愛「もしも明日、はじめましてになっても」公開", f"{PUBLIC_BASE}/news/moshimo-ashita-hajimemashite-ni-natte-mo-release/"),
        ("ECLYPSE、SUZUKA所属アーティストとして始動。", f"{PUBLIC_BASE}/news/eclypse-joins-suzuka/"),
        ("デビューシングル「SHADOW//CODE」を発表。", f"{PUBLIC_BASE}/news/shadow-code-announcement/"),
    ]
    replace_first_itemlist(path, existing)


def update_social(root: Path) -> None:
    path = root / "social/index.html"
    source = path.read_text(encoding="utf-8")
    grid = re.search(r'(<div class="social-hub-grid">)(.*?)(</div>\s*</section>)', source, re.DOTALL)
    if not grid:
        raise RuntimeError("Social release grid not found.")
    cards = re.findall(r'<a class="social-hub-card".*?</a>', grid.group(2), re.DOTALL)
    for item in reversed(RELEASES):
        route = f'../releases/{item["slug"]}/'
        cards = [card for card in cards if route not in card]
        cards.insert(
            0,
            f'<a class="social-hub-card" href="{route}"><img src="../{item["image"]}" alt="{html.escape(str(item["alt"]))}" width="1280" height="720" loading="lazy"/><div><small>{html.escape(str(item["artist"]))} · OFFICIAL MV</small><strong>{html.escape(str(item["title"]))}</strong><span>作品と公式MVを見る →</span></div></a>',
        )
    source = source[: grid.start(2)] + "".join(cards) + source[grid.end(2) :]
    directory_entries = "".join(
        f'<a href="../releases/{item["slug"]}/"><span>{html.escape(str(item["title"]))} · {html.escape(str(item["artist"]))}</span><b>→</b></a>'
        f'<a href="../news/{item["slug"]}-release/"><span>{html.escape(str(item["title"]))} 公開News</span><b>→</b></a>'
        for item in RELEASES
    )
    for item in RELEASES:
        source = re.sub(rf'<a href="\.\./(?:releases/{item["slug"]}|news/{item["slug"]}-release)/".*?</a>', "", source, flags=re.DOTALL)
    source = source.replace('<div class="social-hub-directory">', '<div class="social-hub-directory">' + directory_entries, 1)
    source = source.replace('<a href="../artists/revive/"><span>RE:VIVE · Coming Soon</span>', '<a href="../artists/revive/"><span>RE:VIVE · 公開作品 1</span>')
    if '../artists/nox/' not in source:
        source = source.replace('</div>\n    </section>\n\n    <section class="social-hub-footer-cta"', '<a href="../artists/nox/"><span>NOX · Coming Soon</span><b aria-hidden="true">→</b></a></div>\n    </section>\n\n    <section class="social-hub-footer-cta"', 1)
    upcoming_text = " / ".join(f'{item["dateText"]} {item["artist"]}「{item["title"]}」' for item in UPCOMING)
    source = re.sub(r'<section class="status-strip">.*?</section>', "", source, flags=re.DOTALL)
    source = source.replace('<section class="social-hub-footer-cta"', f'<section class="status-strip"><div class="upcoming-notice"><strong>UPCOMING</strong><p>{html.escape(upcoming_text)}</p><a href="../news/upcoming-artists/">公開予定を見る ↗</a></div></section><section class="social-hub-footer-cta"', 1)
    path.write_text(source, encoding="utf-8")


def update_upcoming_news(root: Path) -> None:
    page = f"{PUBLIC_BASE}/news/upcoming-artists/"
    image = f"{PUBLIC_BASE}/images/nox-chimpanzee-no-rakuen.jpg"
    description = "神代煌牙「Echoes of You」とRE:VIVE「Heal You Again」の公開、NOX・RANGILI・榎本魅愛の公式YouTube公開予定をお知らせします。"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "NewsArticle", "@id": f"{page}#article", "headline": "SUZUKA Latest & Upcoming｜2026.07.28", "datePublished": "2026-07-22", "dateModified": "2026-07-28", "mainEntityOfPage": {"@id": page}, "image": image, "publisher": {"@id": f"{PUBLIC_BASE}/#organization"}, "description": description},
            {"@type": "WebPage", "@id": page, "url": page, "name": "SUZUKA Latest & Upcoming｜2026.07.28", "breadcrumb": {"@id": f"{page}#breadcrumb"}, "inLanguage": "ja"},
            {"@type": "BreadcrumbList", "@id": f"{page}#breadcrumb", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{PUBLIC_BASE}/"}, {"@type": "ListItem", "position": 2, "name": "News", "item": f"{PUBLIC_BASE}/news/"}, {"@type": "ListItem", "position": 3, "name": "Latest & Upcoming", "item": page}]},
        ],
    }
    published_sections = "".join(
        f'<section><h2>{html.escape(str(item["artist"]))}「{html.escape(str(item["title"]))}」</h2><img src="../../{item["image"]}" alt="{html.escape(str(item["alt"]))}" width="1280" height="720" loading="lazy"/><p>{html.escape(str(item["description"]))}</p><p><strong>公開済み · {item["date"]}</strong></p><a class="button button-primary" href="../../releases/{item["slug"]}/">作品を見る ↗</a></section>'
        for item in RELEASES
    )
    upcoming_sections = "".join(
        f'<section class="upcoming-schedule"><div class="upcoming-schedule-inner"><div><p class="section-kicker">Official premiere</p><h2>{item["dateText"]}</h2></div><div><h2>{html.escape(str(item["title"]))}</h2><p>{html.escape(str(item["artist"]))}</p><span class="coming-soon-badge">公開予定</span><p>公式予約動画を確認済み。公開作品一覧には含めていません。</p><a class="button button-primary" href="{youtube_url(item)}" target="_blank" rel="noopener noreferrer">公式予約動画 ↗</a></div></div></section>'
        for item in UPCOMING
    )
    source = f"""<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>SUZUKA Latest &amp; Upcoming｜2026.07.28</title><meta name="description" content="{description}"/><meta name="robots" content="index, follow"/><link rel="canonical" href="{page}"/><meta property="og:type" content="article"/><meta property="og:site_name" content="SUZUKA"/><meta property="og:locale" content="ja_JP"/><meta property="og:title" content="SUZUKA Latest &amp; Upcoming｜2026.07.28"/><meta property="og:description" content="{description}"/><meta property="og:url" content="{page}"/><meta property="og:image" content="{image}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:image" content="{image}"/><link rel="icon" href="../../images/suzuka-channel.jpg"/><link rel="stylesheet" href="../../assets/styles.css"/><link rel="stylesheet" href="../../assets/news-feature.css"/><link rel="stylesheet" href="../../assets/upcoming.css"/><link rel="stylesheet" href="../../assets/player.css"/><link rel="stylesheet" href="../../assets/ai-disclosure.css"/><script type="application/ld+json">{compact(graph)}</script></head><body><main class="news-article-page">{header('../../')}<article class="news-article"><header class="news-article-hero"><p class="news-breadcrumb"><a href="../../news/">News</a> / Latest &amp; Upcoming</p><div class="news-article-meta"><time datetime="2026-07-28">2026.07.28</time><span>OFFICIAL UPDATE</span></div><h1>SUZUKA<br/>Latest &amp; Upcoming</h1><p class="news-article-lead">{description}</p><p class="ai-news-disclosure">5人組AIガールズグループ・RE:VIVEと5人組ヴィジュアル系AIバンド・NOXを含む、SUZUKAのオリジナルAIアーティストに関する公式情報です。</p></header><div class="news-article-body">{published_sections}{upcoming_sections}</div></article><nav class="artist-next-actions"><div><p>Keep exploring</p><h2>SUZUKAの物語へ。</h2></div><a href="../../artists/">Artistsを見る ↗</a><a href="../../social/">Official Links ↗</a><a href="../../">Homeへ ↗</a></nav>{footer('../../', 'OFFICIAL NEWS', 'news/')}</main><script defer src="../../assets/main.js"></script></body></html>
"""
    write(root / "news/upcoming-artists/index.html", source)


def update_youtube_doc(root: Path) -> None:
    path = root / "docs/youtube/youtube-seo-master.md"
    source = path.read_text(encoding="utf-8")
    marker = "## 2026-07-28 公式公開確認"
    section = f"""

{marker}

公式チャンネル `UCVde75yhByGQMu3SkO-fzrA` の動画ページを2026年7月28日に確認。

| 状態 | 作品 | アーティスト | 公開日／予定 | 時間 | 正式URL |
| --- | --- | --- | --- | --- | --- |
| 公開済み | Heal You Again | RE:VIVE | 2026-07-27 | 1:45 | {youtube_url(RELEASES[0])} |
| 公開済み | Echoes of You | 神代煌牙 | 2026-07-26 | 8:04 | {youtube_url(RELEASES[1])} |
| 公開予定 | チンパンジーの楽園 | NOX | 2026-07-29 20:00 JST | 未確定 | {youtube_url(UPCOMING[0])} |
| 公開予定 | 恋するマハラジャ | RANGILI | 2026-07-30 20:00 JST | 未確定 | {youtube_url(UPCOMING[1])} |
| 公開予定 | Without Worrying | 榎本魅愛 | 2026-07-31 20:00 JST | 未確定 | {youtube_url(UPCOMING[2])} |

### 新規公開作品の運用URL

- `Heal You Again`
  - 説明欄: `{PUBLIC_BASE}/releases/heal-you-again/?utm_source=youtube&utm_medium=video_description&utm_campaign=heal-you-again`
  - 固定コメント: `{PUBLIC_BASE}/releases/heal-you-again/?utm_source=youtube&utm_medium=pinned_comment&utm_campaign=heal-you-again`
  - Instagram: `{PUBLIC_BASE}/releases/heal-you-again/?utm_source=instagram&utm_medium=social_post&utm_campaign=heal-you-again`
- `Echoes of You`
  - 説明欄: `{PUBLIC_BASE}/releases/echoes-of-you/?utm_source=youtube&utm_medium=video_description&utm_campaign=echoes-of-you`
  - 固定コメント: `{PUBLIC_BASE}/releases/echoes-of-you/?utm_source=youtube&utm_medium=pinned_comment&utm_campaign=echoes-of-you`
  - Instagram: `{PUBLIC_BASE}/releases/echoes-of-you/?utm_source=instagram&utm_medium=social_post&utm_campaign=echoes-of-you`

### タイトル・タグ案

- `Heal You Again｜RE:VIVE【Official Music Video】`
  - `RE:VIVE, Heal You Again, SUZUKA, AI Music, J-POP, 応援ソング, Official MV`
  - `#REVIVE #HealYouAgain #SUZUKA #AIMusic #OfficialMV`
- `Echoes of You｜神代煌牙【Official Music Video】`
  - `Echoes of You, 神代煌牙, KOGA KAMISHIRO, SUZUKA, AI Music, J-POP, バラード, Official MV`
  - `#EchoesOfYou #神代煌牙 #SUZUKA #AIMusic #OfficialMV`

YouTube Studio上のタイトル・説明欄・タグ・カード・エンド画面は、この管理表の提案であり、実反映済みとは扱わない。
"""
    if marker in source:
        source = source[: source.index(marker)].rstrip() + "\n" + section.lstrip()
    else:
        source = source.rstrip() + section
    write(path, source.rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    root = parser.parse_args().root.resolve()
    update_data(root)
    for item in RELEASES:
        write(root / "releases" / str(item["slug"]) / "index.html", release_page(item))
        write(root / "news" / f"{item['slug']}-release" / "index.html", news_page(item))
    write(root / "artists/nox/index.html", nox_page())
    write(root / "artists/revive/index.html", revive_page())
    update_home(root)
    update_koga(root)
    update_artists(root)
    update_releases(root)
    update_news(root)
    update_social(root)
    update_upcoming_news(root)
    update_youtube_doc(root)
    print("Generated verified SUZUKA publication state for 2026-07-28.")


if __name__ == "__main__":
    main()
