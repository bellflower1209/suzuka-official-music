#!/usr/bin/env python3
"""Generate SUZUKA Creator Platform 3.1 data-driven surfaces."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from build_explorer_update import BASE, card, dump, shell, write
from build_creator_platform import analytics as install_analytics


def marker_upsert(path: Path, name: str, content: str, anchor: str = "</main>") -> None:
    text = path.read_text(encoding="utf-8")
    block = f"<!-- V31:{name}:START -->{content}<!-- V31:{name}:END -->"
    pattern = rf"<!-- V31:{re.escape(name)}:START -->.*?<!-- V31:{re.escape(name)}:END -->"
    if re.search(pattern, text, flags=re.DOTALL):
        text = re.sub(pattern, block, text, count=1, flags=re.DOTALL)
    elif anchor in text:
        text = text.replace(anchor, block + anchor, 1)
    path.write_text(text, encoding="utf-8")


def eligible_lyrics(releases: list[dict]) -> list[dict]:
    return [
        item for item in releases
        if item.get("lyricsAvailable")
        and item.get("lyricsVerified") is True
        and str(item.get("lyricsVerifiedAt", "")).strip()
        and str(item.get("lyricsText") or item.get("lyrics") or "").strip()
        and str(item.get("lyricsSource", "")).strip()
    ]


def countdown_markup(item: dict, prefix: str = "") -> str:
    image = item["image"] if str(item["image"]).startswith(("http://", "https://")) else prefix + item["image"]
    return (
        f'<article class="v31-countdown-card" data-countdown data-release-at="{item["scheduledAt"]}" '
        f'data-upcoming data-release-slug="{item["slug"]}">'
        f'<img src="{image}" alt="{html.escape(item["artist"])}「{html.escape(item["title"])}」公式YouTube公開予定サムネイル" '
        'width="1280" height="720" loading="lazy"/>'
        '<div><p class="section-kicker">NEXT RELEASE / JST</p>'
        f'<h2>{html.escape(item["title"])}</h2><p>{html.escape(item["artist"])}</p>'
        f'<time datetime="{item["scheduledAt"]}">{item["scheduledAt"][:10].replace("-", ".")} {item["scheduledAt"][11:16]} JST</time>'
        '<p class="v31-countdown" data-countdown-output>公開予定時刻までを計算中</p>'
        '<div class="explore-actions">'
        f'<a href="{item["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">公式YouTube予約 ↗</a>'
        f'<a href="{prefix}releases/{item["slug"]}/">作品ページ</a>'
        f'<a href="{prefix}schedule/">スケジュール</a></div></div></article>'
    )


def schedule_page(root: Path, cms: dict, releases: list[dict], upcoming: list[dict]) -> None:
    today = date.fromisoformat(cms["updatedAt"][:10])
    current_week_end = today + timedelta(days=6 - today.weekday())
    next_week_end = current_week_end + timedelta(days=7)
    buckets: dict[str, list[dict]] = {
        "Today": [], "This Week": [], "Next Week": [], "This Month": [],
    }
    for item in sorted(upcoming, key=lambda x: (x["scheduledAt"], x["slug"])):
        scheduled = date.fromisoformat(item["scheduledAt"][:10])
        if scheduled == today:
            buckets["Today"].append(item)
        elif today < scheduled <= current_week_end:
            buckets["This Week"].append(item)
        elif current_week_end < scheduled <= next_week_end:
            buckets["Next Week"].append(item)
        elif scheduled.year == today.year and scheduled.month == today.month:
            buckets["This Month"].append(item)
    sections = []
    item_nodes = []
    position = 0
    for label, items in buckets.items():
        cards = "".join(countdown_markup(item, "../") for item in items)
        if not cards:
            cards = '<p class="v31-empty">現在該当する公開予定はありません。</p>'
        sections.append(
            f'<section class="v31-schedule-group" id="{label.lower().replace(" ", "-")}">'
            f'<h2>{label}</h2><div class="v31-schedule-list">{cards}</div></section>'
        )
        for item in items:
            position += 1
            item_nodes.append({
                "@type": "ListItem", "position": position,
                "name": item["title"], "url": f'{BASE}/releases/{item["slug"]}/',
            })
    recent = [
        item for item in releases
        if 0 <= (today - date.fromisoformat(item["releaseDate"])).days <= 14
    ]
    recent_html = "".join(card(item, "../") for item in recent)
    sections.append(
        '<section class="v31-schedule-group" id="published-recently"><h2>Published Recently</h2>'
        f'<div class="explorer-card-grid">{recent_html}</div></section>'
    )
    graph = [{
        "@type": "ItemList", "name": "SUZUKA release schedule",
        "numberOfItems": len(item_nodes), "itemListElement": item_nodes,
    }]
    body = (
        '<section class="creator-copy"><p>JST基準の公式YouTube公開予定と、最近の公開作品を表示します。'
        '時刻を迎えただけでは公開済みに変更しません。</p></section>'
        + "".join(sections)
    )
    page = shell(
        "schedule/", "公開スケジュール｜SUZUKA Official Music",
        "SUZUKAのAIアーティスト作品の公開予定と最近の公開作品をJSTで確認できます。",
        "RELEASE SCHEDULE", body, graph, page_type="CollectionPage",
    )
    page = page.replace("</body>", '<script defer src="../assets/creator-v31.js"></script></body>')
    write(root / "schedule/index.html", page)


def upcoming_pages(root: Path, upcoming: list[dict]) -> None:
    for item in upcoming:
        image = item["image"] if str(item["image"]).startswith(("http://", "https://")) else "../../" + item["image"]
        body = (
            '<section class="v31-upcoming-detail" data-upcoming>'
            f'<img src="{image}" alt="{html.escape(item["artist"])}「{html.escape(item["title"])}」公開予定サムネイル" width="1280" height="720" loading="lazy"/>'
            '<div><p class="section-kicker">UPCOMING / NOT YET PUBLISHED</p>'
            f'<h2>{html.escape(item["title"])}</h2><p>{html.escape(item["description"])}</p>'
            f'<time datetime="{item["scheduledAt"]}">{item["scheduledAt"].replace("T", " ")[:16]} JST</time>'
            '<p data-countdown data-release-at="' + item["scheduledAt"] + '"><strong data-countdown-output>公開予定時刻までを計算中</strong></p>'
            '<div class="explore-actions">'
            f'<a href="{item["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">公式YouTube予約 ↗</a>'
            f'<a href="../../artists/{item["artistSlug"]}/">Artist</a><a href="../../schedule/">Schedule</a>'
            '</div></div></section>'
        )
        page = shell(
            f'releases/{item["slug"]}/', f'{item["title"]}｜公開予定｜SUZUKA',
            f'{item["artist"]}「{item["title"]}」は公式YouTubeで公開予定のAIアーティスト作品です。',
            item["title"], body, [], ("releases", "Releases"), page_type="WebPage",
        )
        page = page.replace('content="index, follow"', 'content="noindex, follow"')
        page = page.replace("</body>", '<script defer src="../../assets/creator-v31.js"></script></body>')
        write(root / f'releases/{item["slug"]}/index.html', page)


def lyrics_pages(root: Path, releases: list[dict]) -> list[dict]:
    eligible = eligible_lyrics(releases)
    by_slug = {item["slug"]: item for item in eligible}
    for index, item in enumerate(eligible):
        lyrics_text = str(item.get("lyricsText") or item.get("lyrics") or "").strip()
        paragraphs = "".join(
            '<p>' + '<br/>'.join(
                (
                    f'<span class="v31-lyrics-cue">{html.escape(line)}</span>'
                    if re.match(r"^\s*(?:\[[^]]+\]|【[^】]+】|\([^)]*\)|（[^）]*）|⸻)\s*$", line)
                    else html.escape(line)
                )
                for line in block.splitlines()
            ) + '</p>'
            for block in re.split(r"\n\s*\n", lyrics_text)
        )
        related = [x for x in releases if x["slug"] != item["slug"] and (
            x["artistSlug"] == item["artistSlug"] or set(x.get("genres", [])) & set(item.get("genres", []))
        )][:3]
        previous = eligible[index - 1] if index else None
        following = eligible[index + 1] if index + 1 < len(eligible) else None
        paging = "".join([
            f'<a href="../{previous["slug"]}/">前の歌詞：{html.escape(previous["title"])}</a>' if previous else "",
            f'<a href="../{following["slug"]}/">次の歌詞：{html.escape(following["title"])}</a>' if following else "",
        ])
        body = (
            '<article class="v31-lyrics"><header>'
            f'<p>{html.escape(item["artist"])}</p><h2>{html.escape(item["title"])}</h2>'
            f'<p>歌詞出典：{html.escape(item["lyricsSource"])}</p></header>'
            f'<div class="v31-lyrics-text">{paragraphs}</div></article>'
            '<nav class="explore-actions">'
            f'<a href="../../{item["releaseUrl"]}">作品ページ</a><a href="{item["youtubeUrl"]}">公式MV ↗</a>'
            f'<a href="../../gallery/{item["slug"]}/">Gallery</a><a href="../../artists/{item["artistSlug"]}/">Artist</a>{paging}</nav>'
            f'<section><h2>関連作品</h2><div class="explorer-card-grid">{"".join(card(x, "../../") for x in related)}</div></section>'
        )
        graph = [{
            "@type": "MusicRecording", "@id": f'{BASE}/{item["releaseUrl"]}#recording',
            "name": item["title"], "url": f'{BASE}/{item["releaseUrl"]}',
        }]
        write(root / f'lyrics/{item["slug"]}/index.html', shell(
            f'lyrics/{item["slug"]}/', f'{item["title"]} 歌詞 | {item["artist"]} | SUZUKA Official',
            f'{item["artist"]}「{item["title"]}」の公式歌詞。MV、楽曲情報、関連作品も紹介。',
            f'{item["title"]} 歌詞', body, graph, ("lyrics", "Lyrics"), page_type="WebPage",
        ))
    entries = "".join(
        f'<article class="v31-lyrics-row" data-lyrics-entry data-search="{html.escape(" ".join([item["title"], item["artist"], *item.get("genres", [])]))}">'
        f'<time>{item["releaseDate"]}</time><h2><a href="./{item["slug"]}/">{html.escape(item["title"])}</a></h2>'
        f'<p>{html.escape(item["artist"])} / {html.escape(" / ".join(item.get("genres", [])))}</p></article>'
        for item in eligible
    ) or '<p class="v31-empty">出典を確認済みの公式歌詞は現在登録されていません。未確認歌詞は公開しません。</p>'
    body = (
        '<section class="creator-copy"><p>正本データに出典と本文が登録された公式歌詞のみ掲載します。</p>'
        '<label class="v31-filter">歌詞を探す<input type="search" data-lyrics-filter placeholder="曲名・アーティスト・ジャンル"/></label></section>'
        f'<section class="v31-lyrics-list" data-lyrics-list>{entries}</section>'
    )
    graph = [{
        "@type": "ItemList", "numberOfItems": len(eligible),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": item["title"], "url": f'{BASE}/lyrics/{item["slug"]}/'}
            for i, item in enumerate(eligible, 1)
        ],
    }]
    page = shell(
        "lyrics/", "公式歌詞｜SUZUKA Official Music",
        "SUZUKAのAIアーティスト作品のうち、出典を確認済みの公式歌詞を探せます。",
        "LYRICS", body, graph, page_type="CollectionPage",
    )
    page = page.replace("</body>", '<script defer src="../assets/creator-v31.js"></script></body>')
    write(root / "lyrics/index.html", page)
    return eligible


def lyrics_crosslinks(root: Path, lyrics: list[dict]) -> None:
    for item in lyrics:
        release_path = root / item["releaseUrl"] / "index.html"
        if not release_path.is_file():
            continue
        link = (
            '<section class="v31-release-lyrics-link" aria-label="公式歌詞">'
            '<p class="section-kicker">OFFICIAL LYRICS</p>'
            f'<h2>{html.escape(item["title"])}の公式歌詞</h2>'
            '<p>ユーザー提供のSUZUKA公式歌詞正本を、原文の改行を維持して掲載しています。</p>'
            f'<a class="v31-readable-cta" href="../../lyrics/{item["slug"]}/">公式歌詞を読む ↗</a></section>'
        )
        marker_upsert(release_path, "RELEASE-LYRICS", link)


def photobook_pages(root: Path, cms: dict, releases: list[dict]) -> list[dict]:
    source = json.loads((root / "assets/data/photobooks.json").read_text(encoding="utf-8"))
    artist_map = {item["slug"]: item for item in cms["artists"]}
    release_map = {item["slug"]: item for item in releases}
    published = [
        item for item in source.get("photobooks", [])
        if item.get("status") == "published" and item.get("noteUrl")
    ]
    published.sort(key=lambda item: (str(item.get("publishedAt") or ""), item["slug"]), reverse=True)
    cards = []
    list_items = []
    for position, item in enumerate(published, 1):
        artist = artist_map[item["artistSlug"]]
        related_slugs = [slug for slug in item.get("relatedReleaseSlugs", []) if slug in release_map]
        gallery_hub_url = f'../gallery/{related_slugs[0]}/' if related_slugs else '../gallery/'
        gallery_detail_url = f'../../gallery/{related_slugs[0]}/' if related_slugs else '../../gallery/'
        cover = item.get("coverImage")
        cover_alt = item.get("coverAlt") or f'{item["title"]} 公式写真集カバー'
        cover_width = int(item.get("coverWidth") or 1280)
        cover_height = int(item.get("coverHeight") or 720)
        cover_markup = (
            f'<img src="../{html.escape(cover)}" alt="{html.escape(cover_alt)}" '
            f'width="{cover_width}" height="{cover_height}" loading="lazy"/>' if cover else ""
        )
        cards.append(
            f'<article class="v31-photobook-card" data-photobook data-slug="{html.escape(item["slug"])}" data-title="{html.escape(item["title"])}" data-artist="{html.escape(artist["name"])}">{cover_markup}'
            f'<div><p>Visual Collection / {html.escape(artist["name"])}</p><h2><a href="./{item["slug"]}/">{html.escape(item["title"])}</a></h2>'
            f'<p>{html.escape(item.get("description") or "")}</p>'
            f'<time datetime="{html.escape(item["publishedAt"])}">{html.escape(item["publishedAt"][:10].replace("-", "."))}</time>'
            f'<div class="explore-actions">'
            f'<a href="./{item["slug"]}/">写真集詳細</a><a data-note-link href="{html.escape(item["noteUrl"])}" target="_blank" rel="noopener noreferrer">noteで見る ↗</a>'
            f'<a href="../artists/{item["artistSlug"]}/">Artist</a><a href="{gallery_hub_url}">Gallery</a>'
            '</div></div></article>'
        )
        related = [release_map[slug] for slug in related_slugs]
        related_html = "".join(card(release, "../../") for release in related)
        if item.get("isPaid") is True:
            price = item.get("priceLabel") or "有料・価格未確認"
        elif item.get("isPaid") is False:
            price = "無料"
        else:
            price = "未確認"
        detail_cover = (
            f'<img src="../../{html.escape(cover)}" alt="{html.escape(cover_alt)}" '
            f'width="{cover_width}" height="{cover_height}" loading="lazy"/>' if cover else ""
        )
        body = (
            f'<article class="v31-photobook-detail" data-photobook data-slug="{html.escape(item["slug"])}" data-title="{html.escape(item["title"])}" data-artist="{html.escape(artist["name"])}">{detail_cover}<div>'
            f'<p>SUZUKA Visual Collection</p><h2>{html.escape(item["title"])}</h2><p>{html.escape(artist["name"])}</p>'
            f'<p>{html.escape(item.get("description") or "")}</p><dl><dt>公開日</dt><dd><time datetime="{html.escape(item.get("publishedAt") or "")}">{html.escape((item.get("publishedAt") or "未確認")[:10])}</time></dd>'
            f'<dt>公開形式</dt><dd>{html.escape(price or "有料・価格未確認")}</dd></dl>'
            f'<div class="explore-actions"><a data-note-link href="{html.escape(item["noteUrl"])}" target="_blank" rel="noopener noreferrer">noteで写真集を見る ↗</a>'
            f'<a href="../../artists/{item["artistSlug"]}/">Artist</a><a href="{gallery_detail_url}">Gallery</a>'
            f'<a href="../">Photobooks</a></div></div></article>'
            + (f'<section><h2>関連作品</h2><div class="explorer-card-grid">{related_html}</div></section>' if related else "")
        )
        graph = [{
            "@type": "CreativeWork", "@id": f'{BASE}/photobooks/{item["slug"]}/#work',
            "name": item["title"], "url": f'{BASE}/photobooks/{item["slug"]}/',
            "description": item.get("description") or "", "author": {"@type": "Organization", "name": "SUZUKA"},
            "about": {
                "@type": artist["type"], "name": artist["name"],
                "description": "SUZUKAの架空のAIアーティストです。",
            },
            "image": f'{BASE}/{cover}' if cover else None,
            "datePublished": item.get("publishedAt"),
            "isAccessibleForFree": item.get("isPaid") is False,
        }]
        page = shell(
            f'photobooks/{item["slug"]}/', f'{item["title"]} | {artist["name"]} | SUZUKA Photobooks',
            item.get("description") or f'{artist["name"]}のSUZUKA公式AIアーティスト写真集。',
            item["title"], body, graph, ("photobooks", "Photobooks"), page_type="WebPage",
        )
        if cover:
            page = page.replace(f'{BASE}/images/suzuka-channel.jpg', f'{BASE}/{cover}')
        write(root / f'photobooks/{item["slug"]}/index.html', page)
        list_items.append({
            "@type": "ListItem", "position": position, "name": item["title"],
            "url": f'{BASE}/photobooks/{item["slug"]}/',
        })
    description = "SUZUKA公式AIアーティストの写真集・Visual Collection一覧。"
    content = "".join(cards) or '<p class="v31-empty">公開URLと作品情報を確認済みの写真集は現在登録されていません。</p>'
    body = f'<section class="creator-copy"><p>{description}</p></section><section class="v31-photobook-grid">{content}</section>'
    graph = [{"@type": "ItemList", "numberOfItems": len(list_items), "itemListElement": list_items}]
    hub = shell(
        "photobooks/", "SUZUKA Official Photobooks | Visual Collection", description,
        "PHOTOBOOKS", body, graph, page_type="CollectionPage",
    )
    if published and published[0].get("coverImage"):
        hub = hub.replace(f'{BASE}/images/suzuka-channel.jpg', f'{BASE}/{published[0]["coverImage"]}')
    write(root / "photobooks/index.html", hub)
    return published


def photobook_crosslinks(root: Path, photobooks: list[dict], cms: dict) -> None:
    """Link existing Gallery and News pages only when a verified photobook exists."""
    artist_names = {artist["slug"]: artist["name"] for artist in cms.get("artists", [])}
    for item in photobooks:
        artist_name = artist_names.get(item.get("artistSlug"), "")
        link = (
            '<section class="creator-copy v31-photobook-crosslink" data-photobook '
            f'data-slug="{html.escape(item["slug"])}" '
            f'data-title="{html.escape(item["title"])}" '
            f'data-artist="{html.escape(artist_name)}">'
            '<p class="section-kicker">OFFICIAL PHOTOBOOK</p>'
            f'<h2>{html.escape(item["title"])}</h2><div class="explore-actions">'
            f'<a href="../../photobooks/{item["slug"]}/">写真集を見る</a>'
            f'<a data-note-link href="{html.escape(item["noteUrl"])}" target="_blank" rel="noopener noreferrer">noteで読む ↗</a>'
            '</div></section>'
        )
        for slug in item.get("relatedReleaseSlugs", []):
            gallery = root / f"gallery/{slug}/index.html"
            if gallery.is_file():
                marker_upsert(gallery, f'PHOTOBOOK-{item["slug"]}', link)
            news = root / f"news/{slug}-release/index.html"
            if news.is_file():
                marker_upsert(news, f'PHOTOBOOK-{item["slug"]}', link)


def rankings_v31(root: Path, cms: dict, releases: list[dict]) -> dict:
    analytics_dir = root / "assets/data/analytics"
    analytics_dir.mkdir(parents=True, exist_ok=True)
    defaults = {
        "schemaVersion": "1.0", "updatedAt": None, "dataStatus": "unavailable", "releases": []
    }
    for filename in ("ga4-release-stats.json", "youtube-release-stats.json"):
        path = analytics_dir / filename
        if not path.exists():
            write(path, json.dumps(defaults, ensure_ascii=False, indent=2) + "\n")
    ga4 = json.loads((analytics_dir / "ga4-release-stats.json").read_text(encoding="utf-8"))
    youtube = json.loads((analytics_dir / "youtube-release-stats.json").read_text(encoding="utf-8"))
    by_slug = {item["slug"]: item for item in releases}
    ga4_available = ga4.get("dataStatus") == "available" and bool(ga4.get("releases"))
    youtube_available = youtube.get("dataStatus") == "available" and bool(youtube.get("releases"))
    site_popular = []
    if ga4_available:
        rows = [row for row in ga4["releases"] if row.get("slug") in by_slug]
        rows = [row for row in rows if any(row.get(key) is not None for key in ("pageViews", "releaseClicks", "officialMvClicks"))]
        rows.sort(key=lambda row: (-sum(int(row.get(key) or 0) for key in ("pageViews", "releaseClicks", "officialMvClicks")), row["slug"]))
        site_popular = [by_slug[row["slug"]] for row in rows[:10]]
    youtube_popular = []
    if youtube_available:
        rows = [row for row in youtube["releases"] if row.get("slug") in by_slug]
        rows = [row for row in rows if any(row.get(key) is not None for key in ("youtubeViews", "likes", "comments", "subscribersGained"))]
        rows.sort(key=lambda row: (-int(row.get("youtubeViews") or 0), -int(row.get("likes") or 0), -int(row.get("comments") or 0), row["slug"]))
        youtube_popular = [by_slug[row["slug"]] for row in rows[:10]]
    recommended = sorted(
        releases, key=lambda x: (-int(x.get("recommendationWeight") or 0), x["slug"])
    )[:10]
    seed = date.fromisoformat(cms["updatedAt"][:10]).isocalendar()
    ordered = sorted(releases, key=lambda x: x["slug"])
    digest = int(hashlib.sha256(f"{seed.year}-W{seed.week:02d}".encode()).hexdigest()[:12], 16)
    spotlight = (ordered[digest % len(ordered):] + ordered[:digest % len(ordered)])[:10]
    sections = [
        ("recommended", "A. SUZUKAおすすめ", recommended,
         "recommendationWeightを使った編集おすすめ順です。実人気順位ではありません。"),
        ("site-popular", "B. サイト人気", site_popular,
         "GA4実測データを使用します。データ未登録時は順位を表示しません。"),
        ("youtube-popular", "C. YouTube人気", youtube_popular,
         "YouTube Analytics実測データを使用します。再生数は推測しません。"),
        ("weekly-spotlight", "D. 今週の注目", spotlight,
         f'{seed.year}年第{seed.week}週の決定的アルゴリズム。同じ週は同じ順序です。'),
    ]
    section_html = ""
    schema_items = []
    position = 0
    for slug, label, items, note in sections:
        content = "".join(card(item, "../", i) for i, item in enumerate(items, 1))
        if not items:
            content = '<p class="v31-data-pending">データ準備中</p>'
        section_html += (
            f'<section class="explorer-ranking-section" id="{slug}" data-ranking-section="{slug}">'
            f'<div class="explorer-section-heading"><p>RANKING V3.1</p><h2>{label}</h2>'
            f'<p class="explorer-data-note">{note}</p></div><div class="explorer-ranking-grid">{content}</div></section>'
        )
        for item in items:
            position += 1
            schema_items.append({
                "@type": "ListItem", "position": position,
                "name": item["title"], "url": f'{BASE}/{item["releaseUrl"]}',
            })
    graph = [{
        "@type": "ItemList", "name": "SUZUKAおすすめと今週の注目",
        "numberOfItems": len(schema_items), "itemListElement": schema_items,
    }]
    body = (
        '<nav class="explorer-index-links" aria-label="ランキング種類">'
        + "".join(f'<a href="#{slug}">{label}</a>' for slug, label, _, _ in sections)
        + '</nav>' + section_html
    )
    write(root / "rankings/index.html", shell(
        "rankings/", "Rankings Version 3.1｜SUZUKA Official Music",
        "SUZUKAおすすめ、GA4サイト実測、YouTube Analytics実測、今週の注目を明確に分けて表示します。",
        "RANKINGS V3.1", body, graph, page_type="CollectionPage",
    ))
    result = {
        "updatedAt": cms["updatedAt"],
        "ga4DataAvailable": ga4_available,
        "youtubeDataAvailable": youtube_available,
        "rankings": {
            "recommended": [x["slug"] for x in recommended],
            "sitePopular": [x["slug"] for x in site_popular],
            "youtubePopular": [x["slug"] for x in youtube_popular],
            "weeklySpotlight": [x["slug"] for x in spotlight],
        },
    }
    write(root / "assets/data/rankings-v31.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def artist_pages(root: Path, cms: dict, releases: list[dict], upcoming: list[dict], lyrics: list[dict], photobooks: list[dict]) -> None:
    lyrics_slugs = {item["slug"] for item in lyrics}
    artist_map = {item["slug"]: item for item in cms["artists"] if item.get("status") == "published"}
    release_genres = {
        slug: {genre for item in releases if slug in item.get("artistSlugs", []) for genre in item.get("genres", [])}
        for slug in artist_map
    }
    directory_cards = []
    directory_nodes = []
    for position, (slug, artist) in enumerate(sorted(artist_map.items(), key=lambda row: row[1]["name"]), 1):
        works = [item for item in releases if slug in item.get("artistSlugs", [])]
        works.sort(key=lambda x: (x.get("publishedAt", x["releaseDate"]), x["slug"]), reverse=True)
        artist_upcoming = [item for item in upcoming if item["artistSlug"] == slug]
        latest = works[0] if works else None
        featured_slugs = artist.get("artistFeaturedTracks", [])
        top = [next(item for item in works if item["slug"] == track) for track in featured_slugs if any(item["slug"] == track for item in works)][:3]
        if len(top) < 3:
            top = sorted(works, key=lambda x: (-int(x.get("recommendationWeight") or 0), x["slug"]))[:3]
        related = sorted(
            (
                (len(release_genres[slug] & release_genres[other]), other)
                for other in artist_map if other != slug
            ), reverse=True,
        )
        related_links = "".join(
            f'<a href="../../artists/{other}/">{html.escape(artist_map[other]["name"])}</a>'
            for score, other in related[:3] if score > 0
        ) or '<span>関連ジャンルのアーティストは今後追加予定です。</span>'
        members = ""
        if artist.get("type") == "MusicGroup" and artist.get("members"):
            members = '<section><h2>確認済みメンバー</h2><div class="v31-member-grid">' + "".join(
                f'<article><h3>{html.escape(member["name"])}</h3><p>{html.escape(member["role"])}</p>'
                f'<span>{html.escape(member.get("color", ""))}</span></article>' for member in artist["members"]
            ) + '</div></section>'
        social = "".join([
            f'<a href="{artist["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">YouTube ↗</a>' if artist.get("youtubeUrl") else "",
            f'<a href="{artist["instagramUrl"]}" target="_blank" rel="noopener noreferrer">Instagram ↗</a>' if artist.get("instagramUrl") else "",
        ])
        upcoming_html = "".join(countdown_markup(item, "../../") for item in artist_upcoming) or '<p class="v31-empty">現在確認済みのUpcomingはありません。</p>'
        shorts = [item for item in works if item.get("shortsUrl")]
        news = [item for item in works if item.get("newsUrl")][:3]
        artist_photobooks = [item for item in photobooks if item["artistSlug"] == slug]
        artist_lyrics = [item for item in works if item["slug"] in lyrics_slugs]
        lyrics_section = ""
        if artist_lyrics:
            lyrics_section = '<section><h2>Official Lyrics</h2><div class="v31-lyrics-links">' + "".join(
                f'<a href="../../lyrics/{item["slug"]}/"><span>{html.escape(item["artist"])}</span>'
                f'<strong>{html.escape(item["title"])}</strong><b>歌詞を読む ↗</b></a>'
                for item in artist_lyrics
            ) + '</div></section>'
        photobook_section = ""
        if artist_photobooks:
            photobook_section = '<section><h2>Official Photobooks</h2><div class="v31-photobook-grid">' + "".join(
                f'<article class="v31-photobook-card" data-photobook data-slug="{html.escape(item["slug"])}" data-title="{html.escape(item["title"])}" data-artist="{html.escape(artist["name"])}">'
                f'<img src="../../{html.escape(item["coverImage"])}" alt="{html.escape(item.get("coverAlt") or item["title"])}" width="{int(item.get("coverWidth") or 1280)}" height="{int(item.get("coverHeight") or 720)}" loading="lazy"/>'
                f'<h3><a href="../../photobooks/{item["slug"]}/">{html.escape(item["title"])}</a></h3><div class="explore-actions">'
                f'<a href="../../photobooks/{item["slug"]}/">写真集を見る</a><a data-note-link href="{html.escape(item["noteUrl"])}" target="_blank" rel="noopener noreferrer">noteで読む ↗</a></div></article>'
                for item in artist_photobooks
            ) + '</div></section>'
        body = (
            '<section class="v31-artist-hero"><div>'
            f'<p class="v31-ai-badge ai-artist-note">SUZUKA Original AI Artist / {"Group" if artist["type"] == "MusicGroup" else "Solo"}</p>'
            f'<h2>{html.escape(artist["name"])}</h2><p>{html.escape(artist["reading"])}</p>'
            f'<p>{html.escape(artist["profile"])}</p><div class="explore-actions">{social}<a href="../../schedule/">Schedule</a>'
            f'<a href="../../search/?artist={slug}">作品を検索</a></div></div>'
            f'<img src="../../{artist["image"]}" alt="{html.escape(artist["name"])}代表画像" width="1280" height="720"/></section>'
            '<section class="v31-artist-facts"><div><h2>世界観</h2><p>' + html.escape(artist["world"]) + '</p></div>'
            '<div><h2>音楽性</h2><p>' + html.escape(artist["music"]) + '</p><p>' + html.escape(" / ".join(sorted(release_genres[slug]))) + '</p></div></section>'
            + members
            + (f'<section><h2>最新曲</h2>{card(latest, "../../")}</section>' if latest else "")
            + f'<section><h2>代表曲 / おすすめ3件</h2><div class="explorer-card-grid">{"".join(card(item, "../../") for item in top)}</div></section>'
            + f'<section><h2>公開作品一覧</h2><div class="explorer-card-grid">{"".join(card(item, "../../") for item in works)}</div></section>'
            + f'<section><h2>Upcoming</h2><div class="v31-schedule-list">{upcoming_html}</div></section>'
            + '<section><h2>Official MV / Shorts / News / Gallery</h2><div class="creator-link-grid">'
            + (f'<a class="creator-link-card" href="{latest["youtubeUrl"]}">Official MV</a>' if latest else "")
            + (f'<a class="creator-link-card" href="{shorts[0]["shortsUrl"]}">Shorts</a>' if shorts else "")
            + (f'<a class="creator-link-card" href="../../{news[0]["newsUrl"]}">News</a>' if news else "")
            + (f'<a class="creator-link-card" href="../../gallery/{latest["slug"]}/">Gallery</a>' if latest else "")
            + f'<a class="creator-link-card" href="../../lyrics/">公式歌詞（{sum(item["slug"] in lyrics_slugs for item in works)}件）</a>'
            + '<a class="creator-link-card" href="../../discography/">Discography</a><a class="creator-link-card" href="../../wiki/artists/">Wiki</a>'
            + '<a class="creator-link-card" href="../../playlists/">Playlist</a><a class="creator-link-card" href="../../schedule/">Schedule</a></div></section>'
            + lyrics_section
            + photobook_section
            + f'<section><h2>関連ジャンルのアーティスト</h2><div class="explore-actions">{related_links}</div></section>'
        )
        graph = [
            {"@type": "ProfilePage", "@id": f'{BASE}/artists/{slug}/#profile', "mainEntity": {"@id": f'{BASE}/artists/{slug}/#artist'}},
            {"@type": artist["type"], "@id": f'{BASE}/artists/{slug}/#artist', "name": artist["name"],
             "image": f'{BASE}/{artist["image"]}', "description": f'{artist["profile"]} SUZUKAの架空のAIアーティストです。',
             "sameAs": [url for url in (artist.get("youtubeUrl"), artist.get("instagramUrl")) if url]},
            {"@type": "ItemList", "@id": f'{BASE}/artists/{slug}/#releases', "numberOfItems": len(works), "itemListElement": [
                {"@type": "ListItem", "position": i, "name": item.get("displayTitle", item["title"]), "url": f'{BASE}/{item["releaseUrl"]}'}
                for i, item in enumerate(works, 1)
            ]},
        ]
        page = shell(
            f'artists/{slug}/', f'{artist["name"]}｜SUZUKA Original AI Artist',
            f'{artist["profile"]} 公開作品、Official MV、News、Galleryを紹介します。',
            artist["name"], body, graph, ("artists", "Artists"), page_type="WebPage",
        )
        page = page.replace("</body>", '<script defer src="../../assets/creator-v31.js"></script></body>')
        write(root / f'artists/{slug}/index.html', page)
        directory_cards.append(
            f'<article class="v31-artist-directory-card"><a href="./{slug}/"><img src="../{artist["image"]}" '
            f'alt="{html.escape(artist["name"])}代表画像" width="1280" height="720" loading="lazy"/>'
            f'<p>{"Group" if artist["type"] == "MusicGroup" else "Solo"} / SUZUKA Original AI Artist</p>'
            f'<h2>{html.escape(artist["name"])}</h2><span>公開作品 {len(works)}件</span></a></article>'
        )
        directory_nodes.append({
            "@type": "ListItem", "position": position, "name": artist["name"],
            "url": f'{BASE}/artists/{slug}/',
        })
    write(root / "artists/index.html", shell(
        "artists/", "Artists｜SUZUKA Official Music",
        f'SUZUKAに登録された{len(artist_map)}組のオリジナルの架空アーティストとAIグループを紹介します。',
        "ARTISTS", f'<section class="v31-artist-directory">{"".join(directory_cards)}</section>',
        [{"@type": "ItemList", "numberOfItems": len(directory_nodes), "itemListElement": directory_nodes}],
        page_type="CollectionPage",
    ))


def search_v31(root: Path, cms: dict, releases: list[dict], lyrics: list[dict], photobooks: list[dict]) -> None:
    documents = [
        {
            "type": "Lyrics", "contentType": "lyrics", "title": "公式歌詞",
            "description": "出典と本文を確認済みの公式歌詞一覧。", "url": "lyrics/",
            "keywords": ["歌詞あり", "Lyrics", "公式歌詞"],
        },
        {
            "type": "Photobook", "contentType": "photobook", "title": "Photobooks / Visual Collection",
            "description": "SUZUKA公式AIアーティストの写真集・Visual Collection一覧。", "url": "photobooks/",
            "keywords": ["Photobook", "Visual Collection", "写真集"],
        },
    ]
    for item in releases:
        documents.append({
            "type": "Release", "contentType": "release", "title": item["title"], "description": item.get("description", ""),
            "url": item["releaseUrl"], "keywords": [item["artist"], *item.get("genres", []), *item.get("themes", []), *item.get("tags", [])],
        })
    for artist in cms.get("artists", []):
        if artist.get("status") == "published":
            documents.append({
                "type": "Artist", "contentType": "artist", "title": artist["name"], "description": artist.get("profile", ""),
                "url": f'artists/{artist["slug"]}/', "keywords": artist.get("searchKeywords", []),
            })
    for item in cms.get("news", []):
        if item.get("status") == "published":
            documents.append({
                "type": "News", "contentType": "news", "title": item["title"], "description": item.get("description", ""),
                "url": f'news/{item["slug"]}/', "keywords": [item.get("artistSlug", ""), item.get("releaseSlug", "")],
            })
    for term in cms.get("wiki", {}).get("terms", []):
        documents.append({
            "type": "Wiki", "contentType": "wiki", "title": term["term"], "description": term["description"],
            "url": "wiki/terms/", "keywords": [term["term"]],
        })
    for item in lyrics:
        documents.append({
            "type": "Lyrics", "contentType": "lyrics", "title": item["title"], "description": f'{item["artist"]}公式歌詞',
            "url": f'lyrics/{item["slug"]}/', "keywords": [item["artist"], *item.get("genres", [])],
        })
    artist_map = {item["slug"]: item for item in cms["artists"]}
    for item in photobooks:
        artist = artist_map[item["artistSlug"]]
        documents.append({
            "type": "Photobook", "contentType": "photobook", "title": item["title"],
            "description": item.get("description") or "", "url": f'photobooks/{item["slug"]}/',
            "keywords": [artist["name"], "Photobook", "Visual Collection", "写真集"],
        })
    write(root / "assets/data/search-v31.json", json.dumps({
        "updatedAt": cms["updatedAt"], "documents": documents,
    }, ensure_ascii=False, indent=2) + "\n")
    search_path = root / "search/index.html"
    marker_upsert(
        search_path, "SEARCH-DOCUMENTS",
        '<section class="v31-search-documents"><h2>Release / Artist / Lyrics / Photobook / News / Wiki</h2>'
        '<p>検索語に一致する作品、アーティスト、公式歌詞、写真集、News、Wikiを表示します。</p>'
        '<div data-v31-search-results></div></section>',
    )
    text = search_path.read_text(encoding="utf-8")
    if "assets/search-v31.js" not in text:
        text = text.replace("</body>", '<script defer src="../assets/search-v31.js"></script></body>')
    search_path.write_text(text, encoding="utf-8")
    script = """(() => {
  const form=document.querySelector('[data-search-form]'), root=document.querySelector('[data-v31-search-results]');
  if(!form||!root)return;
  const norm=v=>String(v||'').normalize('NFKC').toLocaleLowerCase('ja').replace(/\\s+/g,'').trim();
  const esc=v=>String(v||'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  fetch('../assets/data/search-v31.json').then(r=>r.json()).then(data=>{
    const render=()=>{const q=norm(form.elements.q.value);const docs=q?data.documents.filter(d=>norm([d.title,d.description,...d.keywords].join(' ')).includes(q)):[];
      root.innerHTML=docs.map(d=>`<article class="v31-search-document" data-content-type="${esc(d.contentType||d.type.toLowerCase())}"><small>${esc(d.type)}</small><h3><a href="../${esc(d.url)}">${esc(d.title)}</a></h3><p>${esc(d.description)}</p></article>`).join('')||(q?'<p>該当する公式コンテンツはありません。</p>':'<p>検索語を入力すると関連コンテンツを表示します。</p>');};
    form.addEventListener('input',render);form.addEventListener('change',render);render();
  }).catch(()=>{root.textContent='検索データを読み込めませんでした。';});
})();\n"""
    write(root / "assets/search-v31.js", script)


def home_v31(root: Path, cms: dict, releases: list[dict], upcoming: list[dict], lyrics: list[dict], photobooks: list[dict]) -> None:
    home = root / "index.html"
    text = home.read_text(encoding="utf-8")
    text = re.sub(r'<section class="section latest-section', '<section data-latest-release class="section latest-section', text, count=1)
    weekly_match = re.search(r'<section class="weekly-pick".*?</section>', text, re.DOTALL)
    if weekly_match and "data-pick-artist-link" not in weekly_match.group(0):
        weekly = weekly_match.group(0).replace(
            '</div></div></div></section>',
            '<a data-pick-lyrics href="./lyrics/">Lyrics</a><a data-pick-artist-link href="./artists/">Artist</a></div></div></div></section>',
            1,
        )
        text = text[:weekly_match.start()] + weekly + text[weekly_match.end():]
    next_release = sorted(upcoming, key=lambda x: (x["scheduledAt"], x["slug"]))[0] if upcoming else None
    countdown = (
        '<section class="v31-home-next"><div class="explorer-home-heading"><h2>Next Release</h2>'
        '<a href="./schedule/">公開スケジュール ↗</a></div>'
        + (countdown_markup(next_release, "./") if next_release else '<p class="v31-empty">確認済みの次回公開予定はありません。</p>')
        + '</section>'
    )
    marker = '<section class="upcoming-section"'
    if "<!-- V31:HOME-NEXT:START -->" in text:
        text = re.sub(r'<!-- V31:HOME-NEXT:START -->.*?<!-- V31:HOME-NEXT:END -->', f'<!-- V31:HOME-NEXT:START -->{countdown}<!-- V31:HOME-NEXT:END -->', text, flags=re.DOTALL)
    else:
        text = text.replace(marker, f'<!-- V31:HOME-NEXT:START -->{countdown}<!-- V31:HOME-NEXT:END -->' + marker, 1)
    portal = (
        '<section class="v31-home-portals"><a href="./schedule/"><span>JST</span><h2>Schedule</h2><p>Upcomingと最近の公開作品</p></a>'
        f'<a href="./lyrics/"><span>{len(lyrics)} LYRICS</span><h2>Lyrics</h2><p>出典確認済みの公式歌詞</p></a>'
        '<a href="./rankings/"><span>V3.1</span><h2>Rankings</h2><p>おすすめと実測値を分離</p></a>'
        f'<a href="./photobooks/"><span>{len(photobooks)} BOOKS</span><h2>Photobooks</h2><p>公式Visual Collection</p></a></section>'
    )
    if "<!-- V31:HOME-PORTALS:START -->" in text:
        text = re.sub(r'<!-- V31:HOME-PORTALS:START -->.*?<!-- V31:HOME-PORTALS:END -->', f'<!-- V31:HOME-PORTALS:START -->{portal}<!-- V31:HOME-PORTALS:END -->', text, flags=re.DOTALL)
    else:
        text = text.replace('</div><section class="youtube-growth-section"', f'</div><!-- V31:HOME-PORTALS:START -->{portal}<!-- V31:HOME-PORTALS:END --><section class="youtube-growth-section"', 1)
    featured = [item for item in photobooks if item.get("featured")][:3]
    artist_names = {item["slug"]: item["name"] for item in cms["artists"]}
    featured_cards = "".join(
        f'<article class="v31-photobook-card" data-photobook data-slug="{html.escape(item["slug"])}" data-title="{html.escape(item["title"])}" data-artist="{html.escape(artist_names.get(item["artistSlug"], ""))}">'
        f'<img src="./{html.escape(item["coverImage"])}" alt="{html.escape(item.get("coverAlt") or item["title"])}" width="{int(item.get("coverWidth") or 1280)}" height="{int(item.get("coverHeight") or 720)}" loading="lazy"/>'
        f'<p>{html.escape(artist_names.get(item["artistSlug"], ""))}</p><h2>{html.escape(item["title"])}</h2><div class="explore-actions">'
        f'<a href="./photobooks/{item["slug"]}/">写真集を見る</a><a data-note-link href="{html.escape(item["noteUrl"])}" target="_blank" rel="noopener noreferrer">noteで読む ↗</a></div></article>'
        for item in featured
    ) or '<p class="v31-empty">公開URLを確認済みの写真集は現在登録されていません。</p>'
    photobook_home = '<section class="v31-home-photobooks" data-photobooks><div><p class="section-kicker">OFFICIAL PHOTOBOOK / VISUAL COLLECTION</p><h2>Photobooks</h2><a href="./photobooks/">写真集一覧 ↗</a></div><div class="v31-photobook-grid">' + featured_cards + '</div></section>'
    home.write_text(text, encoding="utf-8")
    marker_upsert(home, "HOME-PHOTOBOOKS", photobook_home)
    text = home.read_text(encoding="utf-8")
    if "assets/creator-v31.css" not in text:
        text = text.replace("</head>", '<link rel="stylesheet" href="./assets/creator-v31.css"/></head>', 1)
    if "assets/creator-v31.js" not in text:
        text = text.replace("</body>", '<script defer src="./assets/creator-v31.js"></script></body>', 1)
    home.write_text(text, encoding="utf-8")


def navigation_and_assets(root: Path) -> None:
    for path in root.glob("**/index.html"):
        relative = path.relative_to(root)
        text = path.read_text(encoding="utf-8").replace("CREATOR PLATFORM 3.0", "CREATOR PLATFORM 3.1")
        depth = len(relative.parts) - 1
        prefix = "../" * depth
        for pattern in (r'<nav class="desktop-nav[^\"]*"[^>]*>.*?</nav>', r'<nav class="site-footer-nav[^\"]*"[^>]*>.*?</nav>', r'<details class="mobile-menu".*?<nav[^>]*>.*?</nav>'):
            for match in reversed(list(re.finditer(pattern, text, re.DOTALL))):
                block = match.group(0)
                additions = ""
                if "schedule/" not in block:
                    additions += f'<a href="{prefix}schedule/">Schedule</a>'
                if "lyrics/" not in block:
                    additions += f'<a href="{prefix}lyrics/">Lyrics</a>'
                if "photobooks/" not in block:
                    additions += f'<a href="{prefix}photobooks/">Photobooks</a>'
                if additions:
                    block = block.replace("</nav>", additions + "</nav>")
                    text = text[:match.start()] + block + text[match.end():]
        if "assets/creator-v31.css" not in text:
            text = text.replace("</head>", f'<link rel="stylesheet" href="{prefix}assets/creator-v31.css"/></head>', 1)
        path.write_text(text, encoding="utf-8")

    css = """/* SUZUKA Creator Platform 3.1 */
:root{--text-primary:#fff7fb;--text-secondary:#ddd3df;--text-muted:#c7bbc9;--text-on-dark:#fff7fb;--text-on-light:#153f72;--surface-dark:#070408;--surface-light:#f7fbff;--surface-overlay:rgba(8,6,10,.86);--border-contrast:#746c78;--link-color:#ffd1eb;--link-hover:#fff;--button-text:#fff;--focus-ring:#8fdcff;--muted:var(--text-muted)}
body{color:var(--text-primary)}a:visited{color:inherit}a:hover{color:var(--link-hover)}:focus-visible{outline:3px solid var(--focus-ring);outline-offset:4px}input,select,textarea{color:var(--text-primary);border:1px solid var(--border-contrast);background:#101015}input::placeholder,textarea::placeholder{color:#b9afbd;opacity:1}button:disabled,[aria-disabled="true"]{color:#c9c0cd;border-color:#736b77;background:#262229;opacity:1}
.explore-actions a,.v31-readable-cta{color:var(--button-text);border-color:var(--border-contrast);background:#211825}.explore-actions a:hover,.explore-actions a:focus-visible,.v31-readable-cta:hover,.v31-readable-cta:focus-visible{color:#08060a;border-color:#fff;background:#fff}.section-kicker,.explorer-section-heading>p,.v31-ai-badge{color:#ff9bd5}.explorer-muted,.explorer-data-note,.explorer-release-card p,.explorer-release-card time,.explorer-gallery-card p,.explorer-gallery-card span{color:var(--text-muted)}
.v31-home-next,.v31-home-portals,.v31-home-photobooks,.v31-schedule-group,.v31-lyrics-list,.v31-artist-directory,.v31-artist-hero,.v31-artist-facts,.v31-member-grid,.v31-upcoming-detail,.v31-photobook-grid{padding:clamp(2.5rem,6vw,6rem) clamp(1rem,6vw,7rem)}
.v31-countdown-card,.v31-upcoming-detail,.v31-artist-hero,.v31-artist-facts{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(1.25rem,4vw,4rem);align-items:center;color:var(--text-on-dark);border:1px solid var(--border-contrast);border-radius:1.2rem;padding:clamp(1rem,3vw,2rem);background:linear-gradient(135deg,#0b0b10,#15111c)}
.v31-countdown-card img,.v31-upcoming-detail img,.v31-artist-hero img{width:100%;height:auto;border-radius:.8rem}.v31-countdown{font-size:clamp(1.2rem,3vw,2.3rem);font-weight:800;color:#9edbff}.v31-schedule-list{display:grid;gap:1.25rem}.v31-schedule-group>h2{font-size:clamp(2rem,5vw,4rem)}
.v31-home-portals,.v31-artist-directory,.v31-member-grid,.v31-photobook-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}.v31-home-portals>a,.v31-artist-directory-card,.v31-member-grid article,.v31-photobook-card{padding:1.5rem;color:var(--text-on-dark);border:1px solid var(--border-contrast);border-radius:1rem;background:#101014;text-decoration:none}.v31-home-portals h2{font-size:2.2rem}.v31-home-portals span,.v31-ai-badge{color:#9edbff;letter-spacing:.1em}.v31-artist-directory-card img,.v31-photobook-card img{width:100%;height:auto;border-radius:.7rem}.v31-artist-directory-card a{color:var(--text-on-dark);text-decoration:none}.v31-artist-facts{align-items:start}.v31-artist-facts>div{padding:1rem}
.v31-lyrics{max-width:66rem;margin:clamp(2rem,5vw,5rem) auto;padding:clamp(1.25rem,4vw,3rem);color:var(--text-on-dark);border:1px solid var(--border-contrast);border-radius:1.25rem;background:linear-gradient(145deg,rgba(19,15,22,.98),rgba(8,7,10,.98));box-shadow:0 1.5rem 5rem rgba(0,0,0,.28)}.v31-lyrics header{padding-bottom:1.5rem;border-bottom:1px solid var(--border-contrast)}.v31-lyrics header>p{color:var(--text-secondary);line-height:1.75}.v31-lyrics-text{margin-top:2rem;padding:clamp(1.1rem,4vw,3rem);color:#fffdfd;border:1px solid rgba(255,255,255,.22);border-radius:1rem;background:#0c0a0e;font-size:clamp(1rem,1.2vw,1.125rem);line-height:1.9;overflow-wrap:anywhere;word-break:normal}.v31-lyrics-text p{margin:0 0 1.8em}.v31-lyrics-text p:last-child{margin-bottom:0}.v31-lyrics-cue{color:#a9dfff;font-weight:700;font-style:italic;letter-spacing:.025em}.v31-lyrics-row,.v31-search-document{padding:1.2rem;border-bottom:1px solid var(--border-contrast);background:rgba(255,255,255,.025)}.v31-lyrics-row a,.v31-search-document a{color:var(--link-color);text-decoration:underline;text-decoration-color:rgba(255,209,235,.45);text-underline-offset:.25em}.v31-filter{display:grid;gap:.5rem;max-width:42rem}.v31-filter input{padding:1rem;border-radius:.5rem}.v31-data-pending,.v31-empty{padding:1.5rem;border:1px dashed var(--border-contrast);border-radius:.8rem;color:var(--text-secondary)}.v31-home-next{background:#08090d}.v31-home-photobooks{display:grid;grid-template-columns:minmax(12rem,.35fr) 1fr;gap:2rem}.v31-photobook-detail{max-width:72rem;margin:auto;padding:clamp(2rem,6vw,6rem);display:grid;grid-template-columns:1fr 1fr;gap:2rem}.v31-search-documents{padding:2rem 0}.v31-release-lyrics-link{margin:clamp(2rem,5vw,5rem) clamp(1rem,6vw,7rem);padding:clamp(1.4rem,4vw,3rem);color:var(--text-on-dark);border:1px solid var(--border-contrast);border-radius:1rem;background:linear-gradient(135deg,#17111b,#0a090c)}.v31-release-lyrics-link h2{font-size:clamp(1.8rem,4vw,3.5rem)}.v31-readable-cta{display:inline-flex;margin-top:1rem;padding:.85rem 1.2rem;border:1px solid;border-radius:999px;font-weight:800}.v31-lyrics-links{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,15rem),1fr));gap:.8rem}.v31-lyrics-links a{display:grid;gap:.45rem;padding:1.2rem;color:var(--text-on-dark);border:1px solid var(--border-contrast);border-radius:.8rem;background:#101014}.v31-lyrics-links span{color:var(--text-secondary);font-size:.8rem}.v31-lyrics-links b{color:#9edbff;font-size:.75rem}
@media(max-width:760px){.v31-countdown-card,.v31-upcoming-detail,.v31-artist-hero,.v31-artist-facts,.v31-home-photobooks,.v31-photobook-detail{grid-template-columns:1fr}.v31-countdown-card img,.v31-upcoming-detail img,.v31-artist-hero img{grid-row:1}.v31-home-portals,.v31-artist-directory,.v31-member-grid,.v31-photobook-grid{grid-template-columns:1fr}.v31-home-next,.v31-home-portals,.v31-home-photobooks,.v31-schedule-group,.v31-lyrics-list,.v31-artist-directory,.v31-artist-hero,.v31-artist-facts,.v31-member-grid,.v31-upcoming-detail,.v31-photobook-grid{padding-left:1rem;padding-right:1rem}.v31-countdown-card .explore-actions a{width:100%;text-align:center}.v31-lyrics{margin:1rem;padding:1rem}.v31-lyrics-text{padding:1.1rem;font-size:1rem;line-height:1.85}.v31-release-lyrics-link{margin-left:1rem;margin-right:1rem}}
"""
    write(root / "assets/creator-v31.css", css)
    js = """(() => {
  const updateCountdown=element=>{const output=element.querySelector('[data-countdown-output]')||(element.matches('[data-countdown-output]')?element:null);if(!output)return;
    const target=Date.parse(element.dataset.releaseAt);if(!Number.isFinite(target)){output.textContent='公開予定日時を確認できません';return;}
    const diff=target-Date.now();if(diff<=0){output.textContent='公開予定時刻を迎えました。公式YouTubeの公開状態を確認中です。';return;}
    const minutes=Math.floor(diff/60000),days=Math.floor(minutes/1440),hours=Math.floor((minutes%1440)/60),mins=minutes%60;
    output.textContent=`あと ${days}日 ${hours}時間 ${mins}分`;
  };document.querySelectorAll('[data-countdown]').forEach(el=>{updateCountdown(el);setInterval(()=>updateCountdown(el),60000);});
  const filter=document.querySelector('[data-lyrics-filter]'),list=document.querySelector('[data-lyrics-list]');if(filter&&list)filter.addEventListener('input',()=>{const q=filter.value.normalize('NFKC').toLocaleLowerCase('ja').replace(/\\s+/g,'');list.querySelectorAll('[data-lyrics-entry]').forEach(row=>{row.hidden=q&&!row.dataset.search.normalize('NFKC').toLocaleLowerCase('ja').replace(/\\s+/g,'').includes(q);});});
})();\n"""
    write(root / "assets/creator-v31.js", js)


def analytics_v31(root: Path) -> None:
    path = root / "assets/analytics.js"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "return {\n      work_title: title,\n      release_slug: clean(slug),\n      artist_name: artist,\n      link_url: safeLink(anchor.href),",
        "return {\n      work_title: title, title,\n      release_slug: clean(slug), slug: clean(slug),\n      artist_name: artist, artist,\n      link_url: safeLink(anchor.href), destination_url: safeLink(anchor.href),\n      current_page: safePageUrl,\n      source_section: clean(context.getAttribute?.('data-ranking-section') || context.className || 'page'),",
    )
    text = text.replace(
        "work_title: title, title,\n",
        "work_title: title, title, photobook_title: title,\n",
    )
    anchor = 'if (anchor.closest("[data-weekly-pick]")) send("weekly_pick_click", details);'
    additions = '\n    if (anchor.closest(".v31-home-next")) send("next_release_click", details);\n    if (anchor.closest("[data-countdown]")) send("countdown_click", details);\n    if (anchor.closest("[data-upcoming]")) send("upcoming_click", details);\n    if (anchor.closest("[data-latest-release]")) send("latest_release_click", details);\n    if (url.origin === location.origin && /\\/lyrics\\/(?:[^/]+\\/?)?$/.test(path)) send("lyrics_click", details);\n    if (url.origin === location.origin && /\\/rankings\\/?$/.test(path)) send("ranking_click", details);\n    if (url.origin === location.origin && /\\/schedule\\/?$/.test(path)) send("schedule_click", details);'
    if "next_release_click" not in text:
        text = text.replace(anchor, anchor + additions)
    if "photobook_click" not in text:
        text = text.replace(
            'if (url.origin === location.origin && /\\/lyrics\\/(?:[^/]+\\/?)?$/.test(path)) send("lyrics_click", details);',
            'if (url.origin === location.origin && /\\/lyrics\\/(?:[^/]+\\/?)?$/.test(path)) send("lyrics_click", details);\n'
            '    if (url.origin === location.origin && /\\/photobooks\\/(?:[^/]+\\/?)?$/.test(path)) send("photobook_click", details);\n'
            '    if (url.hostname === "note.com" || url.hostname === "www.note.com") send("note_click", details);',
        )
    text = text.replace(
        'context.querySelector("[data-pick-title],h1,h2,h3")?.textContent || schemaTitle',
        'context.dataset.title || context.querySelector("[data-pick-title],h1,h2,h3")?.textContent || schemaTitle',
    ).replace(
        'context.querySelector("[data-pick-artist],.release-card-artist,.artist-name")?.textContent ||',
        'context.dataset.artist || context.querySelector("[data-pick-artist],.release-card-artist,.artist-name")?.textContent ||',
    )
    text = text.replace(
        'const slug = releaseUrl.pathname.match(/\\/releases\\/([^/]+)\\/?/)?.[1] || pageRelease;',
        'const contentSlug = linkedPath.match(/\\/(?:releases|lyrics|photobooks)\\/([^/]+)\\/?/)?.[1] || "";\n'
        '    const slug = context.dataset.slug || contentSlug || releaseUrl.pathname.match(/\\/releases\\/([^/]+)\\/?/)?.[1] || pageRelease;',
    )
    text = text.replace(
        'linkedPath.includes("/playlists/") ? "playlist" : "link"',
        'linkedPath.includes("/playlists/") ? "playlist" :\n        linkedPath.includes("/lyrics/") ? "lyrics" :\n        linkedPath.includes("/photobooks/") ? "photobook" :\n        (new URL(anchor.href, location.href).hostname.includes("note.com")) ? "photobook" : "link"',
    )
    write(path, text)


def admin_v31(root: Path, cms: dict) -> None:
    admin = root / "admin/index.html"
    fields = (
        '<section class="creator-copy v31-admin-fields"><h2>Version 3.1管理項目</h2><p>'
        'releaseAt / status / lyricsAvailable / lyricsSource / lyricsText / featured / recommendationWeight / '
        'lyricsVerified / lyricsVerifiedAt / weeklyPickEligible / analyticsEnabled / upcomingPriority / '
        'artistFeaturedTracks / artistType / artistStatus / photobooks.json管理項目'
        '</p></section>'
    )
    marker_upsert(admin, "ADMIN-FIELDS", fields)


def not_found_page(root: Path) -> None:
    body = (
        '<section class="creator-copy"><p class="section-kicker">404 / NOT FOUND</p>'
        '<h2>ページが見つかりません。</h2><p>URLが変更されたか、公開前のページである可能性があります。</p>'
        '<div class="explore-actions"><a href="/">Home</a><a href="/search/">Search</a>'
        '<a href="/schedule/">Schedule</a><a href="/releases/">Releases</a></div></section>'
    )
    page = shell(
        "404/", "ページが見つかりません｜SUZUKA Official Music",
        "SUZUKA公式サイトで指定されたページが見つかりません。検索、作品一覧、公開スケジュールからお探しください。",
        "404", body, [], page_type="WebPage",
    )
    page = page.replace('content="index, follow"', 'content="noindex, follow"')
    page = page.replace('href="../', 'href="/').replace('src="../', 'src="/')
    write(root / "404.html", page)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    catalog = json.loads((root / "assets/data/releases-catalog.json").read_text(encoding="utf-8"))
    releases = [item for item in catalog["releases"] if item.get("status") == "published"]
    upcoming = [item for item in cms.get("upcoming", []) if item.get("status") == "upcoming"]
    schedule_page(root, cms, releases, upcoming)
    upcoming_pages(root, upcoming)
    lyrics = lyrics_pages(root, releases)
    lyrics_crosslinks(root, lyrics)
    photobooks = photobook_pages(root, cms, releases)
    photobook_crosslinks(root, photobooks, cms)
    rankings = rankings_v31(root, cms, releases)
    artist_pages(root, cms, releases, upcoming, lyrics, photobooks)
    search_v31(root, cms, releases, lyrics, photobooks)
    home_v31(root, cms, releases, upcoming, lyrics, photobooks)
    admin_v31(root, cms)
    not_found_page(root)
    navigation_and_assets(root)
    install_analytics(root)
    analytics_v31(root)
    print(json.dumps({
        "version": "3.1", "artists": len(cms["artists"]), "releases": len(releases),
        "upcoming": len(upcoming), "lyrics": len(lyrics), "photobooks": len(photobooks),
        "ga4Data": rankings["ga4DataAvailable"], "youtubeData": rankings["youtubeDataAvailable"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
