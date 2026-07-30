#!/usr/bin/env python3
"""Generate the SUZUKA Explorer Update from the shared release catalog."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


BASE = "https://bellflower1209.github.io/suzuka-official-music"
CHANNEL = "https://www.youtube.com/@suzuka1209"
INSTAGRAM = "https://www.instagram.com/suzuka12090511/"
UPDATED_AT = "2026-07-30T19:30:00+09:00"

ARTISTS = {
    "enomoto-mia": {
        "name": "榎本魅愛",
        "reading": "ENOMOTO MIA",
        "type": "Person",
        "image": "images/mv-mia.jpg",
        "world": "恋する瞬間のときめき、迷い、勇気を、色彩豊かな物語として歌う。",
        "music": "J-POP、ロマンティックポップ、バラードを軸に、日常の感情をまっすぐなメロディへ変える。",
        "profile": "恋するすべての瞬間を歌にする、SUZUKAのVirtual AI Artist。",
    },
    "koga-kamishiro": {
        "name": "神代煌牙",
        "reading": "KOGA KAMISHIRO",
        "type": "Person",
        "image": "images/koga-kamishiro.webp",
        "world": "大切な人を守る黒の騎士。静けさの奥にある誓いと、消えない記憶を描く。",
        "music": "シネマティックJ-POP、ロック、ダークポップを融合した重厚な物語音楽。",
        "profile": "愛する人を守るために歌う、SUZUKAの男性ソロAIアーティスト。",
    },
    "eclypse": {
        "name": "ECLYPSE",
        "reading": "ECLYPSE",
        "type": "MusicGroup",
        "image": "images/eclypse-group.webp",
        "world": "光と闇が交わる近未来で、5つの運命がコードを書き換えていく。",
        "music": "ダークK-POP、EDM、Trapを基調に、ボーカル、ラップ、ダンスの緊張感を重ねる。",
        "profile": "運命を自ら書き換える5人組男性AIグループ。",
    },
    "nox": {
        "name": "NOX",
        "reading": "NOX",
        "type": "MusicGroup",
        "image": "images/nox-chimpanzee-no-rakuen.jpg",
        "world": "人間の本能、社会の矛盾、夜の奥に潜む衝動を、黒い寓話として描く。",
        "music": "V系、ダークロックを中心に、挑発的な問いと物語性を強いバンドサウンドへ刻む。",
        "profile": "黒羽狂司がVocal・作詞・世界観構築を担う5人組ヴィジュアル系AIバンド。",
    },
    "rangili": {
        "name": "RANGILI",
        "reading": "RANGILI",
        "type": "MusicGroup",
        "image": "images/rangili-namaste-galaxy.jpg",
        "world": "インドと日本、地上と宇宙を鮮やかな色彩で結ぶ祝祭の世界。",
        "music": "インド音楽の情熱とJ-POPの親しみやすいメロディを融合したダンスポップ。",
        "profile": "インドと日本の文化を音楽でつなぐ3人組AIガールグループ。",
    },
    "asagiri-shinobu": {
        "name": "朝霧しのぶ",
        "reading": "ASAGIRI SHINOBU",
        "type": "Person",
        "image": "images/asagiri-wasurenai-kokoro.jpg",
        "world": "家族、記憶、人生の別れとぬくもりに寄り添う、日本の原風景。",
        "music": "演歌と歌謡曲を軸に、人生の機微を落ち着いた語りと旋律で届ける。",
        "profile": "忘れても残る愛を歌う、SUZUKAの演歌AIアーティスト。",
    },
    "revive": {
        "name": "RE:VIVE",
        "reading": "RE:VIVE",
        "type": "MusicGroup",
        "image": "images/revive-heal-you-again.jpg",
        "world": "傷ついた心に光を戻し、もう一度立ち上がる瞬間を仲間と分かち合う。",
        "music": "応援、回復、再生をテーマにしたJ-POPとアイドルポップ。",
        "profile": "前へ進む力を届ける5人組AIガールズグループ。",
    },
}

FEATURES = {
    "love-songs": ("恋愛ソング", "恋する気持ち、愛、誓いを描く作品。", lambda x: any(v in x["themes"] for v in ("恋愛", "愛", "誓い")) or x["artistSlug"] == "enomoto-mia"),
    "cheer-songs": ("応援ソング", "希望、再生、明日へ進む力を届ける作品。", lambda x: any(v in x["themes"] for v in ("希望", "再生", "明日", "祈り"))),
    "tearjerkers": ("泣ける曲", "別れ、記憶、痛みを静かに受け止める作品。", lambda x: any(v in x["themes"] for v in ("別れ", "記憶", "痛み", "忘却"))),
    "summer-songs": ("夏ソング", "花火や海など、夏の情景が広がる作品。", lambda x: "夏" in x["themes"] or "サマーポップ" in x["genres"] or "海" in x["themes"]),
    "winter-songs": ("冬ソング", "冬の空気や季節の記憶を描く作品。", lambda x: "冬" in x["themes"]),
    "dark": ("ダーク", "影、反逆、社会への問いを描くダークな作品。", lambda x: "ダーク" in x["moods"] or any("ダーク" in v for v in x["genres"])),
    "k-pop": ("K-POP風", "K-POPの構成やビジュアル感覚を取り入れた作品。", lambda x: "K-POP風" in x["genres"]),
    "enka": ("演歌", "人生、家族、記憶に寄り添う演歌作品。", lambda x: "演歌" in x["genres"]),
    "visual-kei": ("V系", "ヴィジュアル系の美意識とダークロックを持つ作品。", lambda x: "V系" in x["genres"]),
    "ai-idols": ("AIアイドル", "AIアイドル／ガールグループの物語と音楽。", lambda x: x["artistSlug"] in {"revive", "rangili"}),
    "ai-bands": ("AIバンド", "AIバンド／グループが鳴らす物語性の強い作品。", lambda x: x["artistSlug"] in {"nox", "eclypse"}),
}

WIKI_PAGES = {
    "artists": ("アーティスト", "7組のAIアーティストを、五十音・アルファベットから探せます。"),
    "works": ("作品", "公開作品を作品名から探せるSUZUKA作品事典です。"),
    "terms": ("用語", "SUZUKAの世界観を理解するための主要用語を紹介します。"),
    "genres": ("ジャンル", "SUZUKA作品のジャンルと関連作品を整理します。"),
    "timeline": ("公開年表", "SUZUKA作品を公開日順にたどる年表です。"),
    "ai-artists": ("AIアーティストについて", "SUZUKAにおけるAIアーティスト表現と制作方針を説明します。"),
}


def dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def clean_block(text: str, name: str) -> str:
    return re.sub(
        rf"\s*<!-- EXPLORER:{re.escape(name)}:START -->.*?<!-- EXPLORER:{re.escape(name)}:END -->\s*",
        "\n",
        text,
        flags=re.DOTALL,
    )


def breadcrumb(route: str, label: str, parent: tuple[str, str] | None = None) -> tuple[str, dict]:
    depth = len([part for part in route.split("/") if part])
    p = "../" * depth
    links = [f'<a href="{p}">Home</a>']
    elements = [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"}]
    if parent:
        links.append(f'<a href="{p}{parent[0]}/">{html.escape(parent[1])}</a>')
        elements.append({"@type": "ListItem", "position": 2, "name": parent[1], "item": f"{BASE}/{parent[0]}/"})
    links.append(f"<span>{html.escape(label)}</span>")
    elements.append({"@type": "ListItem", "position": len(elements) + 1, "name": label, "item": f"{BASE}/{route}"})
    return f'<nav class="explorer-breadcrumb" aria-label="パンくず">{"<b>/</b>".join(links)}</nav>', {
        "@type": "BreadcrumbList",
        "itemListElement": elements,
    }


def header(p: str) -> str:
    primary = (
        ("Home", ""), ("Artists", "artists/"), ("Releases", "releases/"), ("Search", "search/"),
        ("Ranking", "rankings/"), ("Features", "features/"), ("Gallery", "gallery/"),
        ("Universe", "universe/"), ("Wiki", "wiki/"), ("Social", "social/"),
    )
    links = "".join(f'<a href="{p}{path}">{label}</a>' for label, path in primary)
    return (
        '<header class="site-header inner-site-header">'
        f'<a class="brand" href="{p}">SUZUKA<span class="brand-dot">●</span></a>'
        f'<nav class="desktop-nav explorer-primary-nav" aria-label="メインナビゲーション">{links}</nav>'
        f'<a class="header-channel" href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTube ↗</a>'
        f'<details class="mobile-menu"><summary>Menu</summary><nav>{links}'
        f'<a href="{p}genres/">Genres</a><a href="{p}discography/">Discography</a>'
        f'<a href="{p}news/">News</a></nav></details></header>'
    )


def footer(p: str) -> str:
    return (
        '<footer class="site-footer inner-footer"><div class="footer-top">'
        f'<a class="footer-brand" href="{p}">SUZUKA</a><p>Original AI Music Project</p>'
        f'<a href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTube ↗</a></div>'
        '<nav class="site-footer-nav" aria-label="フッターナビゲーション">'
        f'<a href="{p}rankings/">Ranking</a><a href="{p}features/">Features</a>'
        f'<a href="{p}gallery/">Gallery</a><a href="{p}universe/">Universe</a><a href="{p}wiki/">Wiki</a>'
        f'<a href="{p}search/">Search</a><a href="{p}genres/">Genres</a>'
        f'<a href="{p}discography/">Discography</a><a href="{p}social/">Social</a></nav>'
        '<p class="ai-footer-disclosure">SUZUKAに登場するアーティスト・人物は架空です。'
        "本プロジェクトではAIを制作支援に活用しています。</p></footer>"
    )


def shell(
    route: str,
    title: str,
    description: str,
    heading: str,
    body: str,
    graph_nodes: list[dict],
    parent: tuple[str, str] | None = None,
    page_type: str = "CollectionPage",
) -> str:
    depth = len([part for part in route.split("/") if part])
    p = "../" * depth
    canonical = f"{BASE}/{route}"
    crumb_html, crumb_schema = breadcrumb(route, heading, parent)
    ai_description = description if "AI" in description else f"{description} SUZUKAの架空のAIアーティスト作品を紹介します。"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": page_type, "@id": f"{canonical}#page", "url": canonical, "name": title, "description": ai_description},
            crumb_schema,
            *graph_nodes,
        ],
    }
    return (
        '<!doctype html><html lang="ja"><head><meta charset="UTF-8"/>'
        '<meta name="viewport" content="width=device-width,initial-scale=1"/>'
        f"<title>{html.escape(title)}</title>"
        f'<meta name="description" content="{html.escape(ai_description)}"/>'
        '<meta name="robots" content="index, follow"/>'
        f'<link rel="canonical" href="{canonical}"/>'
        '<meta property="og:type" content="website"/><meta property="og:site_name" content="SUZUKA"/>'
        f'<meta property="og:title" content="{html.escape(title)}"/>'
        f'<meta property="og:description" content="{html.escape(ai_description)}"/>'
        f'<meta property="og:url" content="{canonical}"/>'
        f'<meta property="og:image" content="{BASE}/images/suzuka-channel.jpg"/>'
        '<meta name="twitter:card" content="summary_large_image"/>'
        f'<meta name="twitter:title" content="{html.escape(title)}"/>'
        f'<meta name="twitter:description" content="{html.escape(ai_description)}"/>'
        f'<meta name="twitter:image" content="{BASE}/images/suzuka-channel.jpg"/>'
        f'<link rel="stylesheet" href="{p}assets/styles.css"/>'
        f'<link rel="stylesheet" href="{p}assets/explore.css"/>'
        f'<link rel="stylesheet" href="{p}assets/explorer-update.css"/>'
        f'<link rel="stylesheet" href="{p}assets/player.css"/>'
        f'<link rel="stylesheet" href="{p}assets/ai-disclosure.css"/>'
        f'<script type="application/ld+json">{dump(graph)}</script></head><body><main>'
        f'<a class="skip-link" href="#content">本文へ移動</a>{header(p)}'
        '<section class="explorer-hero"><p class="section-kicker">SUZUKA EXPLORER UPDATE</p>'
        f"<h1>{html.escape(heading)}</h1><p>{html.escape(ai_description)}</p></section>"
        f'{crumb_html}<div id="content">{body}</div>{footer(p)}</main>'
        f'<script defer src="{p}assets/main.js"></script>'
        f'<script defer src="{p}assets/explorer-update.js"></script></body></html>\n'
    )


def card(item: dict, p: str, rank: int | None = None) -> str:
    news = f'<a href="{p}{item["newsUrl"]}">News</a>' if item.get("newsUrl") else ""
    rank_html = f'<strong class="explorer-rank-number">{rank:02d}</strong>' if rank else ""
    return (
        f'<article class="explorer-release-card">{rank_html}'
        f'<img src="{p}{item["coverImage"]}" alt="{html.escape(item["coverAlt"])}" '
        'width="1280" height="720" loading="lazy"/>'
        f'<div><time datetime="{item["releaseDate"]}">{item["releaseDate"].replace("-", ".")}</time>'
        f'<h3>{html.escape(item["displayTitle"])}</h3><p>{html.escape(item["artist"])}</p>'
        '<div class="explore-actions">'
        f'<a href="{p}{item["releaseUrl"]}">作品ページ</a>'
        f'<a href="{item["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">MV ↗</a>{news}'
        "</div></div></article>"
    )


def load_rank_source(root: Path) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    json_path = root / "assets/data/ranking-source.json"
    if json_path.exists():
        source = json.loads(json_path.read_text(encoding="utf-8"))
        for slug, values in source.get("releases", {}).items():
            result[slug] = {key: int(value) for key, value in values.items() if str(value).isdigit()}
    csv_path = root / "assets/data/ranking-source.csv"
    if csv_path.exists():
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                slug = row.get("slug", "")
                if slug:
                    result.setdefault(slug, {}).update({
                        key: int(row[key]) for key in ("popularity", "trend", "mvViews")
                        if row.get(key, "").isdigit()
                    })
    return result


def build_rankings(root: Path, releases: list[dict]) -> dict:
    source = load_rank_source(root)
    newest = {item["slug"]: len(releases) - index for index, item in enumerate(releases)}

    def score(item: dict, key: str) -> int:
        explicit = source.get(item["slug"], {}).get(key)
        if explicit is not None:
            return explicit
        base = item["recommendationWeight"] * 100 + (40 if item.get("featured") else 0)
        return base + newest[item["slug"]]

    popular = sorted(releases, key=lambda x: (score(x, "popularity"), x["releaseDate"]), reverse=True)[:10]
    love = [x for x in releases if any(v in x["themes"] for v in ("恋愛", "愛", "誓い")) or x["artistSlug"] == "enomoto-mia"]
    love = sorted(love, key=lambda x: (score(x, "popularity"), x["releaseDate"]), reverse=True)[:10]
    mv = sorted(releases, key=lambda x: (score(x, "mvViews"), x["releaseDate"]), reverse=True)[:10]
    latest = releases[:10]
    artist_counts = Counter(slug for item in releases for slug in item["artistSlugs"])
    artists = sorted(
        (
            {"slug": slug, "name": data["name"], "count": artist_counts[slug], "image": data["image"]}
            for slug, data in ARTISTS.items()
        ),
        key=lambda x: (x["count"], x["name"]),
        reverse=True,
    )
    trending = sorted(releases, key=lambda x: (score(x, "trend"), x["releaseDate"]), reverse=True)[:10]
    rankings = {
        "popular": {"label": "人気作品TOP10", "items": [x["slug"] for x in popular]},
        "love": {"label": "恋愛ソングTOP10", "items": [x["slug"] for x in love]},
        "mv": {"label": "MV再生数順", "items": [x["slug"] for x in mv], "fallback": "再生数未登録時はrecommendationWeightを使用"},
        "latest": {"label": "最新作品ランキング", "items": [x["slug"] for x in latest]},
        "artists": {"label": "アーティストランキング", "items": [x["slug"] for x in artists]},
        "trending": {"label": "人気急上昇", "items": [x["slug"] for x in trending]},
    }
    payload = {"updatedAt": UPDATED_AT, "source": "ranking-source.json / ranking-source.csv", "rankings": rankings}
    write(root / "assets/data/rankings.json", json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return payload


def rankings_page(root: Path, releases: list[dict], payload: dict) -> None:
    by_slug = {item["slug"]: item for item in releases}
    sections = []
    item_list = []
    for key, ranking in payload["rankings"].items():
        if key == "artists":
            artist_cards = []
            for position, slug in enumerate(ranking["items"], 1):
                artist = ARTISTS[slug]
                count = sum(slug in item["artistSlugs"] for item in releases)
                artist_cards.append(
                    f'<article class="explorer-artist-rank"><strong>{position:02d}</strong>'
                    f'<img src="../{artist["image"]}" alt="{html.escape(artist["name"])} 代表画像" loading="lazy"/>'
                    f'<div><h3>{html.escape(artist["name"])}</h3><p>公開作品 {count}件</p>'
                    f'<a href="../artists/{slug}/">プロフィール ↗</a></div></article>'
                )
            content = "".join(artist_cards)
        else:
            items = [by_slug[slug] for slug in ranking["items"]]
            content = "".join(card(item, "../", i) for i, item in enumerate(items, 1))
            item_list.extend(items)
        note = f'<p class="explorer-data-note">{html.escape(ranking.get("fallback", ""))}</p>' if ranking.get("fallback") else ""
        sections.append(
            f'<section class="explorer-ranking-section" id="{key}"><div class="explorer-section-heading">'
            f'<p>RANKING / {key.upper()}</p><h2>{html.escape(ranking["label"])}</h2>{note}</div>'
            f'<div class="explorer-ranking-grid">{content}</div></section>'
        )
    unique_items = [by_slug[slug] for slug in dict.fromkeys(item["slug"] for item in item_list)]
    schema_items = [
        {"@type": "ListItem", "position": i, "name": item["displayTitle"], "url": f'{BASE}/{item["releaseUrl"]}'}
        for i, item in enumerate(unique_items, 1)
    ]
    body = (
        '<section class="explorer-index-links" aria-label="ランキング種類">'
        + "".join(f'<a href="#{key}">{html.escape(value["label"])}</a>' for key, value in payload["rankings"].items())
        + "</section>"
        + "".join(sections)
    )
    write(
        root / "rankings/index.html",
        shell(
            "rankings/", "人気ランキング｜SUZUKA Official Music",
            "公開作品とアーティストを、人気、恋愛、MV、最新、急上昇の視点で紹介するランキングです。",
            "RANKING", body,
            [{"@type": "ItemList", "name": "SUZUKA人気ランキング", "numberOfItems": len(schema_items), "itemListElement": schema_items}],
        ),
    )


def features_pages(root: Path, releases: list[dict]) -> dict[str, list[dict]]:
    generated: dict[str, list[dict]] = {}
    index_cards = []
    for slug, (label, description, predicate) in FEATURES.items():
        matches = [item for item in releases if predicate(item)]
        if not matches:
            continue
        generated[slug] = matches
        artists = sorted({item["artistSlug"] for item in matches})
        genres = sorted({genre for item in matches for genre in item["genres"]})
        related_artists = "".join(
            f'<a href="../../artists/{artist}/">{html.escape(ARTISTS[artist]["name"])}</a>' for artist in artists
        )
        related_genres = "".join(
            f'<a href="../../search/?genre={html.escape(genre)}">{html.escape(genre)}</a>' for genre in genres[:8]
        )
        body = (
            f'<section class="explorer-intro"><p>{html.escape(description)}</p>'
            f'<div class="explore-actions"><a href="../../search/?q={html.escape(label)}">検索で探す</a>'
            '<a href="../../genres/">ジャンル一覧</a><a href="../../discography/">公開年表</a></div></section>'
            f'<section class="explorer-card-grid">{"".join(card(item, "../../") for item in matches)}</section>'
            f'<section class="explorer-related"><h2>関連ジャンル</h2><div>{related_genres}</div>'
            f'<h2>関連アーティスト</h2><div>{related_artists}</div></section>'
        )
        elements = [
            {"@type": "ListItem", "position": i, "name": item["displayTitle"], "url": f'{BASE}/{item["releaseUrl"]}'}
            for i, item in enumerate(matches, 1)
        ]
        write(
            root / f"features/{slug}/index.html",
            shell(
                f"features/{slug}/", f"{label}特集｜SUZUKA Official Music", description,
                label, body,
                [{"@type": "ItemList", "name": label, "numberOfItems": len(matches), "itemListElement": elements}],
                ("features", "Features"),
            ),
        )
        index_cards.append(
            f'<a class="explorer-feature-card" href="./{slug}/"><span>{len(matches):02d} WORKS</span>'
            f'<h2>{html.escape(label)}</h2><p>{html.escape(description)}</p></a>'
        )
    index_body = (
        '<section class="explorer-feature-grid">' + "".join(index_cards) + "</section>"
        '<section class="explorer-crosslinks"><a href="../search/">楽曲検索</a>'
        '<a href="../rankings/">人気ランキング</a><a href="../gallery/">MVギャラリー</a></section>'
    )
    write(
        root / "features/index.html",
        shell(
            "features/", "おすすめ特集｜SUZUKA Official Music",
            "恋愛、応援、泣ける曲、季節、ダーク、K-POP風、演歌、V系など、テーマ別に作品を紹介します。",
            "FEATURES", index_body,
            [{"@type": "ItemList", "numberOfItems": len(generated), "itemListElement": [
                {"@type": "ListItem", "position": i, "name": FEATURES[slug][0], "url": f"{BASE}/features/{slug}/"}
                for i, slug in enumerate(generated, 1)
            ]}],
        ),
    )
    return generated


def gallery_pages(root: Path, releases: list[dict], release_links: dict) -> None:
    links = {item["slug"]: item for item in release_links["releases"]}
    index_cards = []
    for item in releases:
        youtube_id = item["youtubeUrl"].split("=")[-1]
        source = links.get(item["slug"], {})
        shorts = source.get("shortsUrl")
        shorts_link = (
            f'<a href="{shorts}" target="_blank" rel="noopener noreferrer">YouTube Shorts ↗</a>'
            if shorts else '<span class="explorer-muted">Shorts：公式URL未登録</span>'
        )
        page = f"{BASE}/gallery/{item['slug']}/"
        body = (
            '<section class="explorer-gallery-detail">'
            f'<button class="explorer-lightbox-trigger" type="button" data-lightbox-src="../../{item["coverImage"]}" '
            f'data-lightbox-alt="{html.escape(item["coverAlt"])}">'
            f'<img src="../../{item["coverImage"]}" alt="{html.escape(item["coverAlt"])}" '
            'width="1280" height="720" loading="lazy"/><span>画像を拡大</span></button>'
            '<div class="explorer-gallery-copy"><p class="section-kicker">OFFICIAL MV</p>'
            f'<h2>{html.escape(item["displayTitle"])}</h2><p>{html.escape(item["artist"])}</p>'
            f'<p>{html.escape(item["description"])}</p>'
            f'<iframe src="https://www.youtube-nocookie.com/embed/{youtube_id}" '
            f'title="{html.escape(item["title"])} 公式MV" loading="lazy" allowfullscreen></iframe>'
            '<div class="explore-actions">'
            f'<a href="{item["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">YouTubeでMV ↗</a>'
            f'<a href="../../{item["releaseUrl"]}">作品ページへ戻る</a>{shorts_link}</div></div></section>'
            '<section class="explorer-production-note"><h2>制作画像・サムネイル</h2>'
            f'<div><img src="../../{item["coverImage"]}" alt="{html.escape(item["title"])} 制作画像・公式ジャケット" loading="lazy"/>'
            f'<img src="https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg" '
            f'alt="{html.escape(item["title"])} YouTubeサムネイル" loading="lazy"/></div>'
            f'<h2>制作メモ</h2><p>{html.escape(item["description"])} '
            "本ページでは公開確認済みの公式画像と公式YouTubeのみを掲載しています。</p></section>"
            '<dialog class="explorer-lightbox"><button type="button" data-lightbox-close aria-label="閉じる">×</button>'
            f'<img alt="{html.escape(item["coverAlt"])} 拡大表示" loading="lazy"/></dialog>'
        )
        graph = [{
            "@type": "VideoObject", "name": f'{item["title"]} Official MV', "url": item["youtubeUrl"],
            "thumbnailUrl": f"https://i.ytimg.com/vi/{youtube_id}/maxresdefault.jpg",
            "uploadDate": item["releaseDate"], "embedUrl": f"https://www.youtube.com/embed/{youtube_id}",
        }]
        write(
            root / f"gallery/{item['slug']}/index.html",
            shell(
                f"gallery/{item['slug']}/", f"{item['title']} MVギャラリー｜SUZUKA",
                f"{item['artist']}「{item['title']}」の公式MV、ジャケット、サムネイル、制作メモを紹介します。",
                f"{item['title']} MV GALLERY", body, graph, ("gallery", "Gallery"), "WebPage",
            ),
        )
        index_cards.append(
            f'<a class="explorer-gallery-card" href="./{item["slug"]}/">'
            f'<img src="../{item["coverImage"]}" alt="{html.escape(item["coverAlt"])}" loading="lazy"/>'
            f'<span>{item["releaseDate"]}</span><h2>{html.escape(item["displayTitle"])}</h2>'
            f'<p>{html.escape(item["artist"])}</p></a>'
        )
    elements = [
        {"@type": "ListItem", "position": i, "name": item["displayTitle"], "url": f"{BASE}/gallery/{item['slug']}/"}
        for i, item in enumerate(releases, 1)
    ]
    body = (
        '<section class="explorer-gallery-grid">' + "".join(index_cards) + "</section>"
        '<section class="explorer-crosslinks"><a href="../rankings/">人気ランキング</a>'
        '<a href="../features/">おすすめ特集</a><a href="../search/">作品を検索</a></section>'
    )
    write(
        root / "gallery/index.html",
        shell(
            "gallery/", "MVギャラリー｜SUZUKA Official Music",
            "公開25作品の公式MV、ジャケット、サムネイル、制作メモをモバイル対応のギャラリーで紹介します。",
            "MV GALLERY", body,
            [{"@type": "ItemList", "numberOfItems": len(releases), "itemListElement": elements}],
        ),
    )


def universe_page(root: Path, releases: list[dict]) -> None:
    artist_sections = []
    for slug, artist in ARTISTS.items():
        works = [item for item in releases if slug in item["artistSlugs"]]
        representative = works[0] if works else None
        related = "".join(
            f'<a href="../{item["releaseUrl"]}">{html.escape(item["displayTitle"])}</a>' for item in works[:3]
        )
        representative_html = (
            f'<a class="explorer-universe-work" href="../{representative["releaseUrl"]}">'
            f'<img src="../{representative["coverImage"]}" alt="{html.escape(representative["coverAlt"])}" loading="lazy"/>'
            f'<span>代表作品</span><strong>{html.escape(representative["displayTitle"])}</strong></a>'
            if representative else ""
        )
        artist_sections.append(
            f'<article class="explorer-universe-artist" id="{slug}"><img src="../{artist["image"]}" '
            f'alt="{html.escape(artist["name"])} 代表画像" loading="lazy"/><div>'
            f'<p class="section-kicker">{html.escape(artist["reading"])}</p><h2>{html.escape(artist["name"])}</h2>'
            f'<h3>世界観</h3><p>{html.escape(artist["world"])}</p>'
            f'<h3>音楽性</h3><p>{html.escape(artist["music"])}</p>'
            f'<div class="explore-actions"><a href="../artists/{slug}/">Artist Profile</a>{related}</div></div>'
            f"{representative_html}</article>"
        )
    body = (
        '<section class="explorer-universe-intro"><h2>SUZUKAとは</h2>'
        '<p>SUZUKAは、音楽から新しい物語を始めるオリジナルAI音楽プロジェクトです。'
        "架空のAIアーティストそれぞれが異なる世界観を持ち、作品、映像、Newsがひとつの音楽世界を形づくります。</p>"
        '<div class="explorer-universe-map"><span>恋と日常</span><b>SUZUKA</b><span>光と闇</span>'
        '<span>記憶と再生</span><span>文化と宇宙</span></div></section>'
        '<section class="explorer-universe-list">' + "".join(artist_sections) + "</section>"
        '<section class="explorer-future"><h2>作品世界と今後の展開</h2>'
        "<p>公開作品、ジャンル、アーティスト同士の関係を継続的に接続し、新しい楽曲と物語を追加していきます。</p>"
        '<div class="explore-actions"><a href="../rankings/">おすすめ作品</a><a href="../genres/">ジャンル</a>'
        '<a href="../wiki/">SUZUKA Wiki</a></div></section>'
    )
    write(
        root / "universe/index.html",
        shell(
            "universe/", "SUZUKAの世界観｜AI音楽プロジェクト",
            "SUZUKAとは何か、AI音楽プロジェクトの世界観、7組のアーティスト、代表作品、関係性、今後の展開を紹介します。",
            "SUZUKA UNIVERSE", body,
            [{"@type": "ItemList", "name": "SUZUKA Artists", "numberOfItems": len(ARTISTS), "itemListElement": [
                {"@type": "ListItem", "position": i, "name": artist["name"], "url": f"{BASE}/artists/{slug}/"}
                for i, (slug, artist) in enumerate(ARTISTS.items(), 1)
            ]}], page_type="WebPage",
        ),
    )


def wiki_pages(root: Path, releases: list[dict]) -> None:
    artist_links = sorted(ARTISTS.items(), key=lambda pair: pair[1]["name"])
    alphabet_links = sorted(ARTISTS.items(), key=lambda pair: pair[1]["reading"])
    artist_body = (
        '<section class="explorer-wiki-search"><label for="wiki-filter-artists">アーティストを検索</label>'
        '<input id="wiki-filter-artists" type="search" data-wiki-filter placeholder="名前を入力"/></section>'
        '<section class="explorer-wiki-list" data-wiki-list><h2>五十音</h2>'
        + "".join(
            f'<article data-wiki-entry="{html.escape(artist["name"] + " " + artist["reading"])}">'
            f'<a href="../../artists/{slug}/"><strong>{html.escape(artist["name"])}</strong>'
            f'<span>{html.escape(artist["reading"])}</span></a><p>{html.escape(artist["profile"])}</p></article>'
            for slug, artist in artist_links
        )
        + '<h2>アルファベット</h2>'
        + "".join(
            f'<a class="explorer-wiki-alpha" href="../../artists/{slug}/">{html.escape(artist["reading"])}</a>'
            for slug, artist in alphabet_links
        ) + "</section>"
    )
    works_body = (
        '<section class="explorer-wiki-search"><label for="wiki-filter-works">作品を検索</label>'
        '<input id="wiki-filter-works" type="search" data-wiki-filter placeholder="作品名・アーティスト名"/></section>'
        '<section class="explorer-wiki-list" data-wiki-list>'
        + "".join(
            f'<article data-wiki-entry="{html.escape(item["title"] + " " + item["artist"])}">'
            f'<a href="../../{item["releaseUrl"]}"><strong>{html.escape(item["displayTitle"])}</strong>'
            f'<span>{html.escape(item["artist"])} · {item["releaseDate"]}</span></a></article>'
            for item in sorted(releases, key=lambda x: x["displayTitle"])
        ) + "</section>"
    )
    terms = [
        ("SUZUKA", "音楽から新しい物語を始めるオリジナルAI音楽プロジェクト。"),
        ("AIアーティスト", "SUZUKAの作品世界に登場する架空のアーティスト表現。"),
        ("Weekly Pick", "公開作品の正本データから週ごとに決定的に選ばれるおすすめ作品。"),
        ("recommendationWeight", "再生数データがないときにランキングの基準として使う推薦値。"),
        ("Official MV", "SUZUKA公式YouTubeで公開または公開予定として確認した映像。"),
    ]
    terms_body = '<section class="explorer-wiki-list">' + "".join(
        f'<article><h2>{html.escape(term)}</h2><p>{html.escape(description)}</p></article>' for term, description in terms
    ) + "</section>"
    genres = sorted({genre for item in releases for genre in item["genres"]})
    genres_body = '<section class="explorer-wiki-list">' + "".join(
        f'<article><a href="../../search/?genre={html.escape(genre)}"><strong>{html.escape(genre)}</strong>'
        f'<span>{sum(genre in item["genres"] for item in releases)}作品</span></a></article>' for genre in genres
    ) + "</section>"
    timeline_body = '<section class="explorer-wiki-timeline">' + "".join(
        f'<article><time datetime="{item["releaseDate"]}">{item["releaseDate"]}</time>'
        f'<a href="../../{item["releaseUrl"]}">{html.escape(item["artist"])}「{html.escape(item["displayTitle"])}」</a></article>'
        for item in releases
    ) + '</section><a class="explorer-wide-link" href="../../discography/">詳細なディスコグラフィーを見る ↗</a>'
    ai_body = (
        '<section class="explorer-wiki-prose"><h2>SUZUKAのAIアーティスト表現</h2>'
        "<p>SUZUKAに登場するアーティスト・人物は架空です。AIを制作支援に活用しながら、"
        "各アーティストの音楽性、物語、ビジュアルを一貫したオリジナル作品として制作しています。</p>"
        "<h2>表示方針</h2><p>アーティストページ、作品ページ、News、検索、ランキング、特集、"
        "ギャラリー、WikiでAIアーティストであることを明記します。</p>"
        "<h2>公式情報</h2><p>作品名、公開日、MV URLなどは、公開確認済みの正本データを使用します。</p></section>"
    )
    bodies = {
        "artists": artist_body, "works": works_body, "terms": terms_body,
        "genres": genres_body, "timeline": timeline_body, "ai-artists": ai_body,
    }
    for slug, (label, description) in WIKI_PAGES.items():
        write(
            root / f"wiki/{slug}/index.html",
            shell(
                f"wiki/{slug}/", f"{label}｜SUZUKA Wiki", description,
                label, bodies[slug], [], ("wiki", "SUZUKA Wiki"), "WebPage",
            ),
        )
    index_cards = "".join(
        f'<a class="explorer-wiki-card" href="./{slug}/"><span>WIKI</span>'
        f'<h2>{html.escape(label)}</h2><p>{html.escape(description)}</p></a>'
        for slug, (label, description) in WIKI_PAGES.items()
    )
    index_body = (
        '<section class="explorer-wiki-search"><label for="wiki-global-search">Wiki内検索</label>'
        '<input id="wiki-global-search" type="search" data-wiki-filter placeholder="アーティスト、作品、用語、ジャンル"/></section>'
        f'<section class="explorer-wiki-grid" data-wiki-list>{index_cards}</section>'
        '<section class="explorer-crosslinks"><a href="../search/">楽曲検索</a>'
        '<a href="../universe/">世界観</a><a href="../discography/">公開年表</a></section>'
    )
    write(
        root / "wiki/index.html",
        shell(
            "wiki/", "SUZUKA Wiki｜アーティスト・作品・用語・年表",
            "SUZUKAのAIアーティスト、作品、用語、ジャンル、公開年表を検索できる公式Wikiです。",
            "SUZUKA WIKI", index_body,
            [{"@type": "ItemList", "numberOfItems": len(WIKI_PAGES), "itemListElement": [
                {"@type": "ListItem", "position": i, "name": label, "url": f"{BASE}/wiki/{slug}/"}
                for i, (slug, (label, _)) in enumerate(WIKI_PAGES.items(), 1)
            ]}],
        ),
    )


def enhance_artist_pages(root: Path, releases: list[dict]) -> None:
    for slug, artist in ARTISTS.items():
        path = root / f"artists/{slug}/index.html"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        text = clean_block(text, f"ARTIST-{slug}")
        works = [item for item in releases if slug in item["artistSlugs"]]
        works.sort(key=lambda x: x["releaseDate"], reverse=True)
        if not works:
            continue
        latest = works[0]
        top = sorted(
            works,
            key=lambda x: (x["recommendationWeight"], x.get("featured", False), x["releaseDate"]),
            reverse=True,
        )[:3]
        news = [item for item in works if item.get("newsUrl")][:3]
        genres = sorted({genre for item in works for genre in item["genres"]})
        top_cards = "".join(card(item, "../../", i) for i, item in enumerate(top, 1))
        news_cards = "".join(
            f'<a class="explorer-news-link" href="../../{item["newsUrl"]}"><time>{item["releaseDate"]}</time>'
            f'<strong>{html.escape(item["title"])}</strong><span>Newsを読む ↗</span></a>' for item in news
        ) or '<p class="explorer-muted">公開済みの関連Newsはありません。</p>'
        work_rows = "".join(
            f'<article><time>{item["releaseDate"]}</time><img src="../../{item["coverImage"]}" '
            f'alt="{html.escape(item["coverAlt"])}" loading="lazy"/><div><h3>{html.escape(item["displayTitle"])}</h3>'
            f'<p>{" / ".join(map(html.escape, item["genres"]))}</p></div>'
            f'<a href="../../{item["releaseUrl"]}">作品ページ ↗</a></article>' for item in works
        )
        section = (
            f'<!-- EXPLORER:ARTIST-{slug}:START --><section class="explorer-artist-hub">'
            '<div class="explorer-artist-hub-hero"><div><p class="section-kicker">LATEST MV / PUBLIC RELEASE</p>'
            f'<h2>{html.escape(latest["displayTitle"])}</h2><p>{html.escape(latest["description"])}</p>'
            '<div class="explore-actions">'
            f'<a href="{latest["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">最新MV ↗</a>'
            f'<a href="../../{latest["releaseUrl"]}">最新公開曲</a>'
            f'<a href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTube ↗</a>'
            f'<a href="{INSTAGRAM}" target="_blank" rel="noopener noreferrer">Instagram ↗</a>'
            '<a href="../../">公式サイト</a></div></div>'
            f'<img src="../../{artist["image"]}" alt="{html.escape(artist["name"])} 代表画像" loading="lazy"/></div>'
            '<section class="explorer-artist-section"><div class="explorer-section-heading"><p>AUTOMATIC TOP 3</p>'
            f'<h2>{html.escape(artist["name"])} 代表曲TOP3</h2></div>'
            f'<div class="explorer-card-grid">{top_cards}</div></section>'
            '<section class="explorer-artist-section"><div class="explorer-section-heading"><p>LATEST</p>'
            f'<h2>最新News</h2></div><div class="explorer-news-grid">{news_cards}</div></section>'
            '<section class="explorer-artist-section"><div class="explorer-section-heading"><p>PUBLIC DISCOGRAPHY</p>'
            f'<h2>公開作品一覧</h2></div><div class="explorer-artist-works">{work_rows}</div>'
            '<div class="explore-actions"><a href="../../search/?artist=' + slug + '">検索で絞り込む</a>'
            '<a href="../../genres/">ジャンル</a><a href="../../discography/">ディスコグラフィー</a></div></section>'
            '<section class="explorer-artist-profile"><div><p class="section-kicker">PROFILE / WORLD</p>'
            f'<h2>{html.escape(artist["name"])}</h2><p class="ai-project-note">SUZUKA Original AI Artist</p>'
            f'<p>{html.escape(artist["profile"])}</p></div><div><h3>世界観</h3><p>{html.escape(artist["world"])}</p>'
            f'<h3>音楽性</h3><p>{html.escape(artist["music"])}</p>'
            f'<p>関連ジャンル：{" / ".join(map(html.escape, genres))}</p></div></section></section>'
            f'<!-- EXPLORER:ARTIST-{slug}:END -->'
        )
        header_end = text.find("</header>")
        if header_end >= 0:
            text = text[:header_end + 9] + section + text[header_end + 9:]
        schema = {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "ProfilePage", "url": f"{BASE}/artists/{slug}/", "name": artist["name"],
                 "description": f'{artist["profile"]} 架空のAIアーティストです。'},
                {"@type": artist["type"], "name": artist["name"], "image": f'{BASE}/{artist["image"]}',
                 "description": f'{artist["world"]} SUZUKAの作品世界に登場する架空のAIアーティストです。'},
                {"@type": "ItemList", "numberOfItems": len(works), "itemListElement": [
                    {"@type": "ListItem", "position": i, "name": item["displayTitle"], "url": f'{BASE}/{item["releaseUrl"]}'}
                    for i, item in enumerate(works, 1)
                ]},
                {"@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Artists", "item": f"{BASE}/artists/"},
                    {"@type": "ListItem", "position": 3, "name": artist["name"], "item": f"{BASE}/artists/{slug}/"},
                ]},
            ],
        }
        text = re.sub(r'<script id="explorer-artist-schema".*?</script>', "", text, flags=re.DOTALL)
        text = text.replace(
            "</head>",
            f'<link rel="stylesheet" href="../../assets/explorer-update.css"/>'
            f'<script id="explorer-artist-schema" type="application/ld+json">{dump(schema)}</script></head>',
            1,
        ) if "assets/explorer-update.css" not in text else text.replace(
            "</head>", f'<script id="explorer-artist-schema" type="application/ld+json">{dump(schema)}</script></head>', 1
        )
        path.write_text(text, encoding="utf-8")


def enhance_home(root: Path, releases: list[dict], rankings: dict, features: dict[str, list[dict]]) -> None:
    path = root / "index.html"
    text = clean_block(path.read_text(encoding="utf-8"), "HOME")
    by_slug = {item["slug"]: item for item in releases}
    popular = [by_slug[slug] for slug in rankings["rankings"]["popular"]["items"][:5]]
    feature_cards = "".join(
        f'<a class="explorer-feature-card" href="./features/{slug}/"><span>{len(items):02d} WORKS</span>'
        f'<h3>{html.escape(FEATURES[slug][0])}</h3><p>{html.escape(FEATURES[slug][1])}</p></a>'
        for slug, items in list(features.items())[:6]
    )
    latest_news = [item for item in releases if item.get("newsUrl")][:3]
    block = (
        '<!-- EXPLORER:HOME:START --><section class="explorer-home-update">'
        '<div class="explorer-section-heading"><p>SUZUKA EXPLORER UPDATE</p><h2>音楽世界を、もっと深く。</h2>'
        '<p>ランキング、特集、MV、世界観、Wikiから、25作品と7組のAIアーティストを横断できます。</p></div>'
        '<section><div class="explorer-home-heading"><h3>人気ランキング</h3><a href="./rankings/">すべて見る ↗</a></div>'
        f'<div class="explorer-ranking-grid">{"".join(card(item, "./", i) for i, item in enumerate(popular, 1))}</div></section>'
        '<section><div class="explorer-home-heading"><h3>おすすめ特集</h3><a href="./features/">すべて見る ↗</a></div>'
        f'<div class="explorer-feature-grid">{feature_cards}</div></section>'
        '<section class="explorer-home-portals">'
        '<a href="./gallery/"><span>25 WORKS</span><h3>MV GALLERY</h3><p>公式MVと制作ビジュアル</p></a>'
        '<a href="./universe/"><span>7 ARTISTS</span><h3>UNIVERSE</h3><p>SUZUKAの世界観と関係性</p></a>'
        '<a href="./wiki/"><span>OFFICIAL GUIDE</span><h3>SUZUKA WIKI</h3><p>作品・用語・公開年表</p></a></section>'
        '<section><div class="explorer-home-heading"><h3>最新News</h3><a href="./news/">News一覧 ↗</a></div>'
        '<div class="explorer-news-grid">' + "".join(
            f'<a class="explorer-news-link" href="./{item["newsUrl"]}"><time>{item["releaseDate"]}</time>'
            f'<strong>{html.escape(item["artist"])}「{html.escape(item["title"])}」</strong><span>Newsを読む ↗</span></a>'
            for item in latest_news
        ) + "</div></section>"
        '<nav class="explorer-home-search" aria-label="作品を探す">'
        '<a href="./search/">検索</a><a href="./genres/">ジャンル</a>'
        '<a href="./discography/">ディスコグラフィー</a><a href="./rankings/">ランキング</a></nav>'
        "</section><!-- EXPLORER:HOME:END -->"
    )
    marker = '<section class="weekly-pick"'
    position = text.find(marker)
    text = text[:position] + block + text[position:] if position >= 0 else text.replace("</footer>", block + "</footer>", 1)
    if "assets/explorer-update.css" not in text:
        text = text.replace("</head>", '<link rel="stylesheet" href="./assets/explorer-update.css"/></head>', 1)
    path.write_text(text, encoding="utf-8")


def inject_navigation(root: Path) -> None:
    extra_labels = (
        ("Ranking", "rankings/"), ("Features", "features/"), ("Gallery", "gallery/"),
        ("Universe", "universe/"), ("Wiki", "wiki/"),
    )
    for path in root.glob("**/index.html"):
        text = path.read_text(encoding="utf-8")
        depth = len(path.relative_to(root).parent.parts)
        p = "../" * depth
        if "assets/explorer-update.css" not in text:
            text = text.replace(
                "</head>",
                f'<link rel="stylesheet" href="{p}assets/explorer-update.css"/></head>',
                1,
            )
        for pattern in (
            r'<nav class="desktop-nav[^"]*"[^>]*>.*?</nav>',
            r'<nav class="site-footer-nav[^"]*"[^>]*>.*?</nav>',
            r'<details class="mobile-menu".*?<nav[^>]*>.*?</nav>.*?</details>',
        ):
            matches = list(re.finditer(pattern, text, re.DOTALL))
            for match in reversed(matches):
                block = match.group(0)
                if "rankings/" in block:
                    continue
                links = "".join(f'<a href="{p}{route}">{label}</a>' for label, route in extra_labels)
                close = block.rfind("</nav>")
                block = block[:close] + links + block[close:]
                text = text[:match.start()] + block + text[match.end():]
        path.write_text(text, encoding="utf-8")


def css() -> str:
    return """/* SUZUKA Explorer Update — generated shared styles */
body{overflow-x:hidden}.site-header{grid-template-columns:minmax(8rem,1fr) minmax(0,auto) minmax(8rem,1fr)}
.desktop-nav,.explorer-primary-nav{gap:clamp(.35rem,.75vw,.8rem);flex-wrap:wrap;justify-content:center;min-width:0;max-width:min(74vw,58rem)}
.desktop-nav a{font-size:clamp(.56rem,.6vw,.66rem);letter-spacing:.08em;white-space:nowrap}
.explorer-hero{padding:clamp(7rem,14vw,11rem) clamp(1.25rem,6vw,7rem) 4rem;background:radial-gradient(circle at 78% 22%,rgba(242,70,174,.2),transparent 32%),#08080b;border-bottom:1px solid rgba(255,255,255,.12)}
.explorer-hero h1{font-size:clamp(3.2rem,10vw,8rem);line-height:.9;letter-spacing:-.055em;margin:.5rem 0 1.5rem}.explorer-hero>p{max-width:54rem;color:#cfc8d5;font-size:clamp(1rem,2vw,1.2rem)}
.explorer-breadcrumb{display:flex;gap:.65rem;align-items:center;flex-wrap:wrap;padding:1rem clamp(1.25rem,6vw,7rem);border-bottom:1px solid rgba(255,255,255,.1);font-size:.78rem}.explorer-breadcrumb a,.explorer-breadcrumb span{color:#ddd;text-decoration:none}.explorer-breadcrumb b{color:#777}
.explorer-section-heading{margin-bottom:1.8rem}.explorer-section-heading>p{letter-spacing:.15em;color:#ff86cd;font-size:.72rem}.explorer-section-heading h2{font-size:clamp(2rem,5vw,4.5rem);margin:.25rem 0}.explorer-section-heading>p:last-child{color:#c8c0cf;max-width:50rem;letter-spacing:0;font-size:1rem}
.explorer-card-grid,.explorer-ranking-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1.2rem}
.explorer-release-card{position:relative;display:grid;grid-template-columns:8rem 1fr;gap:1rem;padding:1rem;border:1px solid rgba(255,255,255,.12);border-radius:1rem;background:rgba(255,255,255,.035);min-width:0}.explorer-release-card>img{width:8rem;aspect-ratio:1;object-fit:cover;border-radius:.65rem}.explorer-release-card h3{margin:.35rem 0;overflow-wrap:anywhere}.explorer-release-card p,.explorer-release-card time{color:#bdb4c4;font-size:.78rem}.explorer-rank-number{position:absolute;top:.45rem;left:.55rem;z-index:1;background:#08080b;color:#ff86cd;padding:.25rem .45rem;border-radius:.35rem}
.explorer-index-links,.explorer-crosslinks,.explorer-home-search{display:flex;flex-wrap:wrap;gap:.7rem;padding:2rem clamp(1.25rem,6vw,7rem)}.explorer-index-links a,.explorer-crosslinks a,.explorer-home-search a,.explorer-related a{display:inline-flex;align-items:center;min-height:2.8rem;padding:.6rem 1rem;border:1px solid rgba(255,255,255,.18);border-radius:999px;color:#fff;text-decoration:none}
.explorer-ranking-section{padding:clamp(3rem,7vw,6rem) clamp(1.25rem,6vw,7rem);border-top:1px solid rgba(255,255,255,.1)}.explorer-artist-rank{display:grid;grid-template-columns:3rem 7rem 1fr;gap:1rem;align-items:center;padding:1rem;border:1px solid rgba(255,255,255,.12);border-radius:1rem}.explorer-artist-rank>strong{font-size:1.6rem;color:#ff86cd}.explorer-artist-rank img{width:7rem;aspect-ratio:1;object-fit:cover;border-radius:50%}.explorer-artist-rank a{color:#fff}.explorer-data-note,.explorer-muted{color:#a9a1ae;font-size:.82rem}
.explorer-feature-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;padding:clamp(3rem,7vw,6rem) clamp(1.25rem,6vw,7rem)}.explorer-feature-card{display:block;min-height:15rem;padding:1.5rem;border:1px solid rgba(255,255,255,.12);border-radius:1rem;background:linear-gradient(145deg,rgba(255,75,177,.13),rgba(255,255,255,.02));color:#fff;text-decoration:none}.explorer-feature-card span{font-size:.7rem;letter-spacing:.12em;color:#ff91d1}.explorer-feature-card h2,.explorer-feature-card h3{font-size:clamp(1.6rem,3vw,2.5rem);margin:2rem 0 .7rem}.explorer-feature-card p{color:#c8c0ce}.explorer-intro,.explorer-related{padding:3rem clamp(1.25rem,6vw,7rem)}.explorer-intro>p{font-size:1.2rem;max-width:50rem}.explorer-related>div{display:flex;flex-wrap:wrap;gap:.65rem;margin-bottom:2rem}
.explorer-gallery-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem;padding:clamp(3rem,7vw,6rem) clamp(1.25rem,6vw,7rem)}.explorer-gallery-card{display:block;color:#fff;text-decoration:none;min-width:0}.explorer-gallery-card img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:.8rem}.explorer-gallery-card span{display:block;color:#aaa;font-size:.72rem;margin-top:.7rem}.explorer-gallery-card h2{font-size:1.15rem;margin:.3rem 0;overflow-wrap:anywhere}.explorer-gallery-card p{color:#bbb}
.explorer-gallery-detail{display:grid;grid-template-columns:minmax(16rem,1fr) minmax(18rem,1fr);gap:clamp(1.5rem,5vw,5rem);padding:clamp(3rem,7vw,6rem) clamp(1.25rem,6vw,7rem)}.explorer-lightbox-trigger{border:0;background:transparent;color:#fff;cursor:zoom-in;text-align:left}.explorer-lightbox-trigger img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:1rem}.explorer-gallery-copy iframe{width:100%;aspect-ratio:16/9;border:0;border-radius:1rem;margin:1rem 0}.explorer-production-note{padding:3rem clamp(1.25rem,6vw,7rem);border-top:1px solid rgba(255,255,255,.1)}.explorer-production-note>div{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.explorer-production-note img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:.8rem}.explorer-lightbox{width:min(92vw,72rem);border:0;padding:2.5rem;background:#060608;color:#fff}.explorer-lightbox::backdrop{background:rgba(0,0,0,.88)}.explorer-lightbox img{width:100%;max-height:80vh;object-fit:contain}.explorer-lightbox button{position:absolute;right:.5rem;top:.3rem;border:0;background:transparent;color:#fff;font-size:2rem;cursor:pointer}
.explorer-universe-intro,.explorer-future{padding:clamp(3rem,7vw,6rem) clamp(1.25rem,6vw,7rem)}.explorer-universe-intro>p{max-width:55rem;font-size:1.2rem}.explorer-universe-map{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;align-items:center;margin-top:3rem}.explorer-universe-map>*{display:grid;place-items:center;min-height:8rem;border:1px solid rgba(255,255,255,.12);border-radius:50%;text-align:center}.explorer-universe-map b{min-height:12rem;background:radial-gradient(circle,rgba(255,86,184,.35),transparent 65%);font-size:2rem}.explorer-universe-list{padding:0 clamp(1.25rem,6vw,7rem)}.explorer-universe-artist{display:grid;grid-template-columns:14rem 1fr 12rem;gap:2rem;padding:3rem 0;border-top:1px solid rgba(255,255,255,.12);align-items:center}.explorer-universe-artist>img,.explorer-universe-work img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:1rem}.explorer-universe-work{color:#fff;text-decoration:none}.explorer-universe-work span,.explorer-universe-work strong{display:block;margin-top:.5rem}
.explorer-wiki-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;padding:2rem clamp(1.25rem,6vw,7rem)}.explorer-wiki-card{padding:1.5rem;min-height:14rem;border:1px solid rgba(255,255,255,.12);border-radius:1rem;color:#fff;text-decoration:none}.explorer-wiki-card span{color:#ff8dcc;font-size:.7rem}.explorer-wiki-card h2{margin:2rem 0 .5rem}.explorer-wiki-card p{color:#c4bdca}.explorer-wiki-search{padding:3rem clamp(1.25rem,6vw,7rem);display:grid;gap:.5rem}.explorer-wiki-search input{min-height:3.3rem;padding:.8rem 1rem;border:1px solid rgba(255,255,255,.2);border-radius:.7rem;background:#101015;color:#fff;font:inherit}.explorer-wiki-list,.explorer-wiki-timeline,.explorer-wiki-prose{padding:0 clamp(1.25rem,6vw,7rem) 5rem}.explorer-wiki-list article{padding:1.3rem 0;border-top:1px solid rgba(255,255,255,.12)}.explorer-wiki-list article>a{display:flex;justify-content:space-between;gap:1rem;color:#fff;text-decoration:none}.explorer-wiki-list article span{color:#aaa}.explorer-wiki-alpha{display:inline-flex;margin:.3rem;padding:.5rem .75rem;border:1px solid rgba(255,255,255,.15);border-radius:999px;color:#fff;text-decoration:none}.explorer-wiki-timeline article{display:grid;grid-template-columns:8rem 1fr;gap:1rem;padding:1rem 0;border-top:1px solid rgba(255,255,255,.12)}.explorer-wiki-timeline a{color:#fff}.explorer-wide-link{display:block;margin:0 clamp(1.25rem,6vw,7rem) 5rem;color:#fff}
.explorer-artist-hub{padding:2rem clamp(1.25rem,6vw,7rem) 6rem;background:linear-gradient(180deg,rgba(255,70,175,.08),transparent 25%)}.explorer-artist-hub-hero{display:grid;grid-template-columns:1.2fr minmax(16rem,34rem);gap:clamp(2rem,6vw,6rem);align-items:center;min-height:75vh}.explorer-artist-hub-hero h2{font-size:clamp(2.6rem,7vw,6.5rem);line-height:.95}.explorer-artist-hub-hero>img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:50%}.explorer-artist-section,.explorer-artist-profile{padding:4rem 0;border-top:1px solid rgba(255,255,255,.12)}.explorer-news-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}.explorer-news-link{display:grid;gap:.6rem;padding:1.3rem;border:1px solid rgba(255,255,255,.12);border-radius:.8rem;color:#fff;text-decoration:none}.explorer-news-link time,.explorer-news-link span{color:#aaa;font-size:.75rem}.explorer-artist-works article{display:grid;grid-template-columns:7rem 6rem 1fr auto;gap:1rem;align-items:center;padding:1rem 0;border-top:1px solid rgba(255,255,255,.12)}.explorer-artist-works img{width:6rem;aspect-ratio:1;object-fit:cover;border-radius:.5rem}.explorer-artist-works a{color:#fff}.explorer-artist-profile{display:grid;grid-template-columns:1fr 1.5fr;gap:4rem}
.artist-profile-page .site-header .brand{color:#fff}.explorer-artist-hub .explore-actions a{background:var(--artist-ink,#fff);color:var(--artist-bg,#08080b);border-color:var(--artist-ink,#fff)}.explorer-artist-hub .explore-actions a+a{background:transparent;color:var(--artist-ink,#fff);border-color:var(--artist-ink,#fff)}
.explorer-home-update{padding:clamp(3rem,7vw,6rem) clamp(1.25rem,6vw,7rem)}.explorer-home-update>section{padding:4rem 0;border-top:1px solid rgba(255,255,255,.12)}.explorer-home-update .explorer-feature-grid{padding:0}.explorer-home-heading{display:flex;justify-content:space-between;align-items:end;gap:1rem;margin-bottom:1.5rem}.explorer-home-heading h3{font-size:clamp(1.8rem,4vw,3.6rem);margin:0}.explorer-home-heading a{color:#fff}.explorer-home-portals{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}.explorer-home-portals>a{min-height:18rem;padding:1.5rem;border:1px solid rgba(255,255,255,.13);border-radius:1rem;color:#fff;text-decoration:none;background:radial-gradient(circle at 85% 15%,rgba(255,70,175,.22),transparent 35%)}.explorer-home-portals span{font-size:.7rem;color:#ff8dcc;letter-spacing:.12em}.explorer-home-portals h3{font-size:2rem;margin:5rem 0 .5rem}.explorer-home-search{padding-left:0;padding-right:0}
@media(max-width:1100px){.explorer-card-grid,.explorer-ranking-grid,.explorer-feature-grid,.explorer-wiki-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.explorer-gallery-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.explorer-release-card{grid-template-columns:6rem 1fr}.explorer-release-card>img{width:6rem}.explorer-universe-artist{grid-template-columns:10rem 1fr}.explorer-universe-work{grid-column:2}}
@media(max-width:760px){.explorer-hero{padding-top:6.3rem}.explorer-card-grid,.explorer-ranking-grid,.explorer-feature-grid,.explorer-wiki-grid,.explorer-news-grid,.explorer-home-portals{grid-template-columns:1fr}.explorer-gallery-grid{grid-template-columns:repeat(2,minmax(0,1fr));padding-left:1rem;padding-right:1rem}.explorer-gallery-detail,.explorer-artist-hub-hero,.explorer-artist-profile{grid-template-columns:1fr}.explorer-production-note>div{grid-template-columns:1fr}.explorer-universe-map{grid-template-columns:1fr 1fr}.explorer-universe-artist{grid-template-columns:1fr}.explorer-universe-artist>img{max-width:15rem}.explorer-universe-work{grid-column:auto;max-width:14rem}.explorer-artist-hub-hero{padding-top:5rem}.explorer-artist-hub-hero>img{grid-row:1}.explorer-artist-works article{grid-template-columns:4.5rem 4.5rem 1fr}.explorer-artist-works img{width:4.5rem}.explorer-artist-works article>a{grid-column:3}.explorer-home-heading{align-items:start;flex-direction:column}.explorer-feature-grid{padding-left:1rem;padding-right:1rem}}
@media(max-width:420px){.explorer-gallery-grid{grid-template-columns:1fr}.explorer-release-card{grid-template-columns:5rem 1fr;padding:.75rem}.explorer-release-card>img{width:5rem}.explorer-universe-map{grid-template-columns:1fr}.explorer-artist-rank{grid-template-columns:2.5rem 5rem 1fr}.explorer-artist-rank img{width:5rem}}
"""


def javascript() -> str:
    return """(() => {
  document.querySelectorAll("[data-lightbox-src]").forEach((trigger) => {
    const dialog = trigger.closest("main")?.querySelector(".explorer-lightbox");
    if (!dialog) return;
    trigger.addEventListener("click", () => {
      const image = dialog.querySelector("img");
      image.src = trigger.dataset.lightboxSrc || "";
      image.alt = trigger.dataset.lightboxAlt || "";
      dialog.showModal();
    });
    dialog.querySelector("[data-lightbox-close]")?.addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  });
  document.querySelectorAll("[data-wiki-filter]").forEach((input) => {
    const root = input.closest("main")?.querySelector("[data-wiki-list]");
    if (!root) return;
    input.addEventListener("input", () => {
      const query = input.value.normalize("NFKC").toLowerCase().trim();
      root.querySelectorAll("[data-wiki-entry], .explorer-wiki-card").forEach((entry) => {
        entry.hidden = query && !entry.textContent.normalize("NFKC").toLowerCase().includes(query);
      });
    });
  });
})();\n"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    catalog = json.loads((root / "assets/data/releases-catalog.json").read_text(encoding="utf-8"))
    releases = [item for item in catalog["releases"] if item["status"] == "published"]
    release_links = json.loads((root / "assets/data/release-links.json").read_text(encoding="utf-8"))
    if len(releases) != 25:
        raise RuntimeError(f"Explorer Update expects 25 published releases, found {len(releases)}")
    if len(ARTISTS) != 7:
        raise RuntimeError(f"Explorer Update expects 7 artists, found {len(ARTISTS)}")
    write(root / "assets/explorer-update.css", css())
    write(root / "assets/explorer-update.js", javascript())
    rankings = build_rankings(root, releases)
    rankings_page(root, releases, rankings)
    features = features_pages(root, releases)
    gallery_pages(root, releases, release_links)
    universe_page(root, releases)
    wiki_pages(root, releases)
    enhance_artist_pages(root, releases)
    enhance_home(root, releases, rankings, features)
    inject_navigation(root)
    print(
        f"Generated SUZUKA Explorer Update: {len(releases)} releases, {len(ARTISTS)} artists, "
        f"{len(rankings['rankings'])} rankings, {len(features)} features, "
        f"{len(releases)} gallery works, {len(WIKI_PAGES) + 1} wiki pages."
    )


if __name__ == "__main__":
    main()
