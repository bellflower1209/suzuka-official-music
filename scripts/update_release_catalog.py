#!/usr/bin/env python3
"""Keep locally confirmed release cards and artist discographies in generated pages."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_BASE = "https://bellflower1209.github.io/suzuka-official-music"


def insert_grid_cards(path: Path, cards: str, slugs: tuple[str, ...]) -> None:
    text = path.read_text(encoding="utf-8")
    if all(slug in text for slug in slugs):
        return
    missing = [card for slug, card in zip(slugs, cards.split("<!--CARD-->", 1)) if slug not in text]
    text = text.replace('<div class="release-grid">', '<div class="release-grid">' + "".join(missing), 1)
    number = 0

    def renumber(match: re.Match[str]) -> str:
        nonlocal number
        number += 1
        return f"{match.group(1)}{number:02d}{match.group(2)}"

    text = re.sub(r'(<div class="release-row"><span>)\d+(</span>)', renumber, text)
    path.write_text(text, encoding="utf-8")


def upsert_release_card(path: Path, card: str, detail_href: str) -> None:
    """Move one release card to the front without creating a duplicate."""
    text = path.read_text(encoding="utf-8")
    grid = re.search(r'(<div class="release-grid">)(.*?)(</div>\s*</section>)', text, re.DOTALL)
    if not grid:
        raise RuntimeError(f"Release grid was not found in {path}.")
    cards = re.findall(r'<article class="release-card.*?</article>', grid.group(2), re.DOTALL)
    cards = [item for item in cards if detail_href not in item]
    cards.insert(0, card)
    number = 0

    def renumber(match: re.Match[str]) -> str:
        nonlocal number
        number += 1
        return f"{match.group(1)}{number:02d}{match.group(2)}"

    body = re.sub(r'(<div class="release-row"><span>)\d+(</span>)', renumber, "".join(cards))
    text = text[: grid.start(2)] + body + text[grid.end(2) :]
    path.write_text(text, encoding="utf-8")


def upsert_social_card(path: Path, card: str, detail_href: str) -> None:
    text = path.read_text(encoding="utf-8")
    grid = re.search(r'(<div class="social-hub-grid">)(.*?)(</div>\s*</section>)', text, re.DOTALL)
    if not grid:
        raise RuntimeError(f"Social release grid was not found in {path}.")
    cards = re.findall(r'<a class="social-hub-card".*?</a>', grid.group(2), re.DOTALL)
    cards = [item for item in cards if detail_href not in item]
    cards.insert(0, card)
    text = text[: grid.start(2)] + "".join(cards) + text[grid.end(2) :]
    path.write_text(text, encoding="utf-8")


def insert_after(path: Path, marker: str, content: str, sentinel: str) -> None:
    text = path.read_text(encoding="utf-8")
    if sentinel not in text:
        text = text.replace(marker, marker + content, 1)
        path.write_text(text, encoding="utf-8")


def insert_before(path: Path, marker: str, content: str, sentinel: str) -> None:
    text = path.read_text(encoding="utf-8")
    if sentinel not in text:
        text = text.replace(marker, content + marker, 1)
        path.write_text(text, encoding="utf-8")


def replace_section(path: Path, pattern: str, content: str, sentinel: str) -> None:
    text = path.read_text(encoding="utf-8")
    if sentinel in text:
        return
    updated, count = re.subn(pattern, content, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"Expected one section in {path}, found {count}.")
    path.write_text(updated, encoding="utf-8")


def update_item_list(path: Path, items: list[dict]) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r'(<script\b[^>]*type="application/ld\+json"[^>]*>)(.*?)</script>', re.DOTALL)
    changed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        try:
            data = json.loads(match.group(2))
        except json.JSONDecodeError:
            return match.group(0)
        nodes = data.get("@graph", []) if isinstance(data, dict) else []
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            nodes = [data]
        target = next((node for node in nodes if isinstance(node, dict) and node.get("@type") == "ItemList"), None)
        if not target:
            return match.group(0)
        target["numberOfItems"] = len(items)
        target["itemListElement"] = [
            {
                "@type": "ListItem",
                "position": index,
                "name": item["title"],
                "url": f"{PUBLIC_BASE}/{item['releasePage']}",
            }
            for index, item in enumerate(items, 1)
        ]
        changed = True
        return match.group(1) + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "</script>"

    text = pattern.sub(replace, text)
    if changed:
        path.write_text(text, encoding="utf-8")


def main() -> None:
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    release_data_path = ROOT / "assets/data/release-links.json"
    release_data = json.loads(release_data_path.read_text(encoding="utf-8"))
    queen_release = {
        "slug": "my-queen-my-oath",
        "title": "My Queen, My Oath",
        "subtitle": "君が、俺のすべて。",
        "artist": "神代 煌牙",
        "artistSlug": "koga-kamishiro",
        "status": "published",
        "releaseType": "single",
        "image": "images/koga-my-queen-my-oath-cover.jpg",
        "coverImage": "images/koga-my-queen-my-oath-cover.jpg",
        "coverAlt": "神代煌牙「My Queen, My Oath｜君が、俺のすべて。」正式ジャケット。夕暮れの海と城を背景に、黒いロングコート姿の神代煌牙を描いたビジュアル。",
        "releasePage": "releases/my-queen-my-oath/",
        "youtubeUrl": "https://www.youtube.com/watch?v=_TfwreiEMMM",
        "youtubeStatus": "published",
        "shortsUrl": None,
        "shortsStatus": "unconfirmed",
        "publishedDate": "2026-07-20",
        "duration": 297,
        "description": "夕暮れの海を舞台に、大切な人を守り抜く覚悟と永遠の誓いを描いた神代煌牙のラブソング。",
        "playerEnabled": False,
        "newsPage": "news/my-queen-my-oath-release/",
        "newsUrl": "news/my-queen-my-oath-release/",
        "newsStatus": "published",
        "relatedReleases": ["our-kingdom", "boukyaku-no-ikimono", "red-moon-rising", "smile-and-say-goodbye"],
        "credits": None,
        "lyricsStatus": "unconfirmed",
    }
    release_data["updatedAt"] = "2026-07-20"
    release_data["releases"] = [queen_release] + [item for item in release_data["releases"] if item.get("slug") != "my-queen-my-oath"]
    release_data_path.write_text(json.dumps(release_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    releases = release_data["releases"]
    queen_home = '<article class="release-card release-card-new"><a class="release-image" href="./releases/my-queen-my-oath/" aria-label="My Queen, My Oathの詳細を見る"><img src="./images/koga-my-queen-my-oath-cover.jpg" alt="神代煌牙「My Queen, My Oath｜君が、俺のすべて。」正式ジャケット" width="886" height="886" loading="lazy"/><span class="card-wash wash-gold"></span><span class="card-play"><span class="play-mark" aria-hidden="true"></span></span><span class="duration">4:57</span></a><div class="release-info"><div class="release-row"><span>01</span><span>OFFICIAL MV · 2026.07.20</span></div><h3>My Queen, My Oath</h3><p>君が、俺のすべて。</p><p class="release-artist-credit">神代 煌牙</p><div class="release-card-actions"><a class="release-card-cta release-card-cta-detail" href="./releases/my-queen-my-oath/">詳細を見る <span aria-hidden="true">↗</span></a><a class="release-card-cta" href="https://www.youtube.com/watch?v=_TfwreiEMMM" target="_blank" rel="noopener noreferrer" aria-label="My Queen, My Oath — MVを見る">MVを見る <span aria-hidden="true">↗</span></a></div></div></article>'
    red_home = '<article class="release-card release-card-new"><a class="release-image" href="./releases/red-moon-rising/" aria-label="RED MOON // RISINGの詳細を見る"><img src="./images/eclypse-red-moon-rising-cover.png" alt="ECLYPSE「RED MOON // RISING」正式ジャケット" width="1254" height="1254" loading="lazy"/><span class="card-wash wash-rose"></span><span class="card-play"><span class="play-mark" aria-hidden="true"></span></span><span class="duration">6:04</span></a><div class="release-info"><div class="release-row"><span>01</span><span>2ND SINGLE · 2026.07.18</span></div><h3>RED MOON // RISING</h3><p>The code is broken. Now the red moon rises.</p><p class="release-artist-credit">ECLYPSE</p><div class="release-card-actions"><a class="release-card-cta release-card-cta-detail" href="./releases/red-moon-rising/">詳細を見る <span aria-hidden="true">↗</span></a><a class="release-card-cta" href="https://www.youtube.com/watch?v=BZkMHt0P2oo" target="_blank" rel="noopener noreferrer" aria-label="RED MOON // RISING — MVを見る">MVを見る <span aria-hidden="true">↗</span></a></div></div></article>'
    smile_home = '<article class="release-card release-card-new"><a class="release-image" href="./releases/smile-and-say-goodbye/" aria-label="SMILE AND SAY GOODBYEの詳細を見る"><img src="./images/mv-smile-and-say-goodbye.png" alt="榎本魅愛「SMILE AND SAY GOODBYE」公式ジャケット" width="1672" height="941" loading="lazy"/><span class="card-wash wash-pink"></span></a><div class="release-info"><div class="release-row"><span>01</span><span>NEW RELEASE · OFFICIAL PAGE</span></div><h3>SMILE AND SAY GOODBYE</h3><p>大好きだから、笑ってさようなら。</p><p class="release-artist-credit">榎本魅愛</p><a class="release-card-cta release-card-cta-detail" href="./releases/smile-and-say-goodbye/">楽曲情報を見る <span aria-hidden="true">↗</span></a></div></article>'
    boukyaku_home = '<article class="release-card release-card-new"><a class="release-image" href="./releases/boukyaku-no-ikimono/" aria-label="忘却の生き物の詳細を見る"><img src="./images/mv-boukyaku-no-ikimono.png" alt="神代 煌牙「忘却の生き物」公式ジャケット" width="1672" height="940" loading="lazy"/><span class="card-wash wash-gold"></span></a><div class="release-info"><div class="release-row"><span>02</span><span>NEW RELEASE · OFFICIAL PAGE</span></div><h3>忘却の生き物</h3><p>時代のせいじゃない。忘れ去る人間の仕事だ。</p><p class="release-artist-credit">神代 煌牙</p><a class="release-card-cta release-card-cta-detail" href="./releases/boukyaku-no-ikimono/">楽曲情報を見る <span aria-hidden="true">↗</span></a></div></article>'
    home = ROOT / "index.html"
    upsert_release_card(home, queen_home, './releases/my-queen-my-oath/')
    insert_grid_cards(home, red_home, ("./releases/red-moon-rising/",))
    insert_grid_cards(home, smile_home + "<!--CARD-->" + boukyaku_home, ("./releases/smile-and-say-goodbye/", "./releases/boukyaku-no-ikimono/"))

    home_text = home.read_text(encoding="utf-8")
    hero_actions = '<div class="hero-release-actions reveal-up delay-4" aria-label="最新リリース My Queen, My Oathのメニュー"><p><span>LATEST RELEASE</span><strong>神代 煌牙 — My Queen, My Oath</strong></p><a class="button button-primary" href="https://www.youtube.com/watch?v=_TfwreiEMMM" target="_blank" rel="noopener noreferrer">MVを見る <span aria-hidden="true">↗</span></a><a class="button button-ghost" href="./releases/my-queen-my-oath/">楽曲情報を見る <span aria-hidden="true">▶</span></a><a class="button button-youtube" href="https://www.youtube.com/@bellflower5215" target="_blank" rel="noopener noreferrer">YouTubeでSUZUKAをフォロー <span aria-hidden="true">↗</span></a><a class="button button-ghost" data-home-social-link="true" href="./social/" aria-label="YouTube・楽曲・Newsをまとめた公式リンク一覧を見る">公式リンク一覧</a></div>'
    home_text = re.sub(r'<div class="hero-release-actions reveal-up delay-4".*?</div>', hero_actions, home_text, count=1, flags=re.DOTALL)
    latest = '<section class="section latest-section label-latest" id="latest" aria-labelledby="latest-title"><div class="section-heading section-heading-split"><div><p class="section-kicker">01 / Latest release</p><h2 id="latest-title">My Queen, My Oath</h2></div><p>君が、俺のすべて。<br/>My Queen. My Oath.</p></div><article class="featured-release"><div class="featured-media square-release-media"><img src="./images/koga-my-queen-my-oath-cover.jpg" alt="神代煌牙「My Queen, My Oath｜君が、俺のすべて。」正式ジャケット" width="886" height="886"/><div class="featured-glow"></div></div><div class="featured-copy"><div class="track-number">01</div><p class="featured-label">神代 煌牙 · OFFICIAL MV · 2026.07.20</p><h3>My Queen, My Oath</h3><p class="featured-lead">“君が、俺のすべて。”</p><p class="featured-description">夕暮れの海を舞台に、大切な人を守り抜く覚悟と永遠の誓いを描いたロイヤルロマンス。</p><div class="release-card-actions"><a class="text-link" href="https://www.youtube.com/watch?v=_TfwreiEMMM" target="_blank" rel="noopener noreferrer">WATCH OFFICIAL VIDEO <span aria-hidden="true">↗</span></a><a class="text-link" href="./releases/my-queen-my-oath/">VIEW RELEASE <span aria-hidden="true">↗</span></a></div></div></article></section>'
    home_text, count = re.subn(r'<section class="section latest-section label-latest".*?</section>', latest, home_text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("Latest release section was not found on the home page.")
    home_text = home_text.replace('./releases/shadow-code/" aria-label="SHADOW//CODEの楽曲情報">SHADOW//CODEの楽曲情報', './releases/red-moon-rising/" aria-label="RED MOON // RISINGの楽曲情報">RED MOON // RISINGの楽曲情報', 1)
    home.write_text(home_text, encoding="utf-8")

    red_index = red_home.replace('./releases/', './').replace('./images/', '../images/')
    queen_index = queen_home.replace('./releases/', './').replace('./images/', '../images/')
    upsert_release_card(ROOT / "releases/index.html", queen_index, './my-queen-my-oath/')
    smile_index = smile_home.replace('./releases/', './').replace('./images/', '../images/')
    boukyaku_index = boukyaku_home.replace('./releases/', './').replace('./images/', '../images/')
    insert_grid_cards(ROOT / "releases/index.html", red_index, ("./red-moon-rising/",))
    insert_grid_cards(ROOT / "releases/index.html", smile_index + "<!--CARD-->" + boukyaku_index, ("./smile-and-say-goodbye/", "./boukyaku-no-ikimono/"))

    mia = ROOT / "artists/enomoto-mia/index.html"
    mia_featured = '<article class="artist-featured-card artist-featured-card-new"><a href="../../releases/smile-and-say-goodbye/" aria-label="SMILE AND SAY GOODBYEの楽曲情報を見る"><div class="artist-featured-image"><img src="../../images/mv-smile-and-say-goodbye.png" alt="榎本魅愛「SMILE AND SAY GOODBYE」公式ジャケット" width="1672" height="941" loading="lazy"/></div><div class="artist-featured-copy"><span>01 / New Release</span><h3>SMILE AND SAY GOODBYE</h3><p>大好きだから、笑ってさようなら。</p></div></a></article>'
    insert_after(mia, '<div class="artist-featured-grid artist-featured-grid-expanded">', mia_featured, '../../releases/smile-and-say-goodbye/')
    mia_row = '<a class="artist-track-row artist-track-row-new" href="../../releases/smile-and-say-goodbye/"><span>01</span><img src="../../images/mv-smile-and-say-goodbye.png" alt="榎本魅愛「SMILE AND SAY GOODBYE」公式ジャケット" width="1672" height="941" loading="lazy"/><div><strong>SMILE AND SAY GOODBYE</strong><small>大好きだから、笑ってさようなら。</small></div><b aria-hidden="true">↗</b></a>'
    insert_after(mia, '<div class="artist-track-list">', mia_row, 'artist-track-row artist-track-row-new" href="../../releases/smile-and-say-goodbye/')

    koga = ROOT / "artists/koga-kamishiro/index.html"
    koga_row = '<a class="artist-track-row" href="../../releases/boukyaku-no-ikimono/"><span>01</span><img src="../../images/mv-boukyaku-no-ikimono.png" alt="神代 煌牙「忘却の生き物」公式ジャケット" width="1672" height="940" loading="lazy"/><div><strong>忘却の生き物</strong><small>Official release page</small></div><b aria-hidden="true">↗</b></a>'
    insert_after(koga, '<div class="artist-track-list">', koga_row, '../../releases/boukyaku-no-ikimono/')
    koga_text = koga.read_text(encoding="utf-8")
    koga_debut = '<section class="koga-debut-section" id="debut-single" aria-labelledby="koga-debut-heading"><div class="koga-debut-artwork"><img src="../../images/koga-my-queen-my-oath-cover.jpg" alt="神代煌牙「My Queen, My Oath｜君が、俺のすべて。」正式ジャケット" width="886" height="886" loading="lazy"/></div><div class="koga-debut-copy"><p>03 / Latest release</p><h2 id="koga-debut-heading">My Queen, My Oath</h2><span>KOGA KAMISHIRO · OFFICIAL MV · 2026.07.20</span><h3>「君が、俺のすべて。」</h3><p>夕暮れの海を舞台に、大切な人を守ると決めた覚悟と、揺るがない愛を描いた神代煌牙のラブソング。</p><p>王冠、運命、永遠の誓い。静かな情熱とともに「My Queen. My Oath.」という言葉を捧げます。</p><a class="button artist-ghost-button" href="../../releases/my-queen-my-oath/">作品ページ ↗</a><a class="button artist-ghost-button" href="../../news/my-queen-my-oath-release/">RELEASE NEWS ↗</a><a class="button artist-primary-button" href="https://www.youtube.com/watch?v=_TfwreiEMMM" target="_blank" rel="noopener noreferrer">公式MVを見る ↗</a></div></section>'
    koga_text, count = re.subn(r'<section class="koga-debut-section".*?</section>', koga_debut, koga_text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("KOGA debut section was not found.")
    queen_row = '<a class="artist-track-row" href="../../releases/my-queen-my-oath/"><span>01</span><img src="../../images/koga-my-queen-my-oath-cover.jpg" alt="神代煌牙「My Queen, My Oath｜君が、俺のすべて。」正式ジャケット" width="886" height="886" loading="lazy"/><div><strong>My Queen, My Oath</strong><small>君が、俺のすべて。 · Official MV</small></div><b aria-hidden="true">↗</b></a>'
    koga_text = re.sub(r'<a class="artist-track-row" href="#debut-single">.*?</a>', queen_row, koga_text, count=1, flags=re.DOTALL)
    koga.write_text(koga_text, encoding="utf-8")
    if 'id="koga-release-itemlist"' not in koga_text:
        koga_items = [
            ("忘却の生き物", "boukyaku-no-ikimono"),
            ("My Queen, My Oath", "my-queen-my-oath"),
            ("OUR KINGDOM", "our-kingdom"),
        ]
        schema = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "@id": f"{PUBLIC_BASE}/artists/koga-kamishiro/#releases",
            "name": "神代 煌牙 公開作品",
            "numberOfItems": len(koga_items),
            "itemListElement": [
                {"@type": "ListItem", "position": position, "name": title, "url": f"{PUBLIC_BASE}/releases/{slug}/"}
                for position, (title, slug) in enumerate(koga_items, 1)
            ],
        }
        script = '<script id="koga-release-itemlist" type="application/ld+json">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + "</script>"
        koga.write_text(koga_text.replace("</head>", script + "</head>", 1), encoding="utf-8")

    eclypse = ROOT / "artists/eclypse/index.html"
    red_section = '<section class="eclypse-debut-section eclypse-second-single-section" id="second-single" aria-labelledby="second-single-heading"><div class="eclypse-debut-cover"><img src="../../images/eclypse-red-moon-rising-cover.png" alt="ECLYPSE「RED MOON // RISING」正式ジャケット" width="1254" height="1254" loading="lazy"/></div><div class="eclypse-debut-copy"><p>03 / Latest single</p><h2 id="second-single-heading">RED MOON // RISING</h2><span>2ND SINGLE · OFFICIAL VIDEO · 2026.07.18 · SUZUKA</span><h3>The code is broken. Now the red moon rises.</h3><p>赤い月と崩壊した近未来都市を舞台に、壊れたコードの先で5人の運命が再び動き始めるECLYPSE第2章。</p><p>FIVE HEARTS. ONE DESTINY. 黒と赤のダークSFビジュアルが、覚醒と再起動の瞬間を映し出します。</p><a class="button artist-ghost-button" href="../../releases/red-moon-rising/">RED MOON // RISING 楽曲情報 ↗</a><a class="button artist-ghost-button" href="../../news/red-moon-rising-release/">RELEASE NEWS ↗</a><a class="button artist-primary-button eclypse-video-button" href="https://www.youtube.com/watch?v=BZkMHt0P2oo" target="_blank" rel="noopener noreferrer"><span class="play-mark" aria-hidden="true"></span> WATCH OFFICIAL VIDEO ↗</a></div></section>'
    insert_before(eclypse, '<section class="eclypse-debut-section" id="debut-single"', red_section, '../../releases/red-moon-rising/')
    eclypse_row = '<a class="artist-track-row" href="../../releases/red-moon-rising/"><span>01</span><img src="../../images/eclypse-red-moon-rising-cover.png" alt="ECLYPSE「RED MOON // RISING」正式ジャケット" width="1254" height="1254" loading="lazy"/><div><strong>RED MOON // RISING</strong><small>2nd Single · Official MV</small></div><b aria-hidden="true">↗</b></a>'
    insert_after(eclypse, '<div class="artist-track-list">', eclypse_row, 'artist-track-row" href="../../releases/red-moon-rising/')
    eclypse_text = eclypse.read_text(encoding="utf-8")
    eclypse_text, count = re.subn(r'<section class="eclypse-debut-section eclypse-second-single-section".*?</section>', red_section, eclypse_text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("ECLYPSE latest single section was not found.")
    eclypse_description = '音楽レーベルSUZUKA所属の5人組男性K-POPグループ、ECLYPSEの公式プロフィール。2nd Single「RED MOON // RISING」とデビューシングル「SHADOW//CODE」の公式動画、メンバー情報、グループコンセプトを紹介します。'
    eclypse_text = re.sub(
        r'音楽レーベルSUZUKA所属の5人組男性K-POPグループ、ECLYPSEの公式プロフィール。(?:2nd Single「RED MOON // RISING」と)*デビューシングル「SHADOW//CODE」の公式動画、メンバー情報、グループコンセプトを紹介します。',
        eclypse_description,
        eclypse_text,
    )
    eclypse_text = eclypse_text.replace('ECLYPSE – SHADOW//CODE | SUZUKA', 'ECLYPSE｜RED MOON // RISING・SHADOW//CODE｜SUZUKA')
    eclypse_text = eclypse_text.replace('ECLYPSEのデビューシングル「SHADOW//CODE」。公式動画を公開中。光と闇が交わる瞬間、5つの運命が動き始める。', 'ECLYPSEの2nd Single「RED MOON // RISING」公式動画を公開中。壊れたコードの先で、赤い月とともに5人の運命が再び動き始める。')
    if 'id="eclypse-release-itemlist"' not in eclypse_text:
        eclypse_items = [("RED MOON // RISING", "red-moon-rising"), ("SHADOW//CODE", "shadow-code")]
        schema = {"@context":"https://schema.org","@type":"ItemList","@id":f"{PUBLIC_BASE}/artists/eclypse/#releases","name":"ECLYPSE 公開作品","numberOfItems":len(eclypse_items),"itemListElement":[{"@type":"ListItem","position":position,"name":title,"url":f"{PUBLIC_BASE}/releases/{slug}/"} for position,(title,slug) in enumerate(eclypse_items,1)]}
        script = '<script id="eclypse-release-itemlist" type="application/ld+json">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + "</script>"
        eclypse_text = eclypse_text.replace("</head>", script + "</head>", 1)
    eclypse.write_text(eclypse_text, encoding="utf-8")

    shadow = ROOT / "releases/shadow-code/index.html"
    shadow_related = '<section class="release-related-section" aria-labelledby="shadow-related"><div><p>Related music</p><h2 id="shadow-related">ECLYPSEの次章へ。</h2></div><div class="release-related-grid"><a href="../red-moon-rising/"><span><img src="../../images/eclypse-red-moon-rising-cover.png" alt="ECLYPSE「RED MOON // RISING」正式ジャケット" width="1254" height="1254" loading="lazy"/></span><strong>RED MOON // RISING</strong><small>ECLYPSE · 2nd Single</small><b>赤い月が昇る、その先へ ↗</b></a><a href="../my-queen-my-oath/"><span><img src="../../images/koga-kamishiro.webp" alt="神代 煌牙 アーティストビジュアル" width="360" height="450" loading="lazy"/></span><strong>My Queen, My Oath</strong><small>神代 煌牙</small><b>VIEW ↗</b></a><a href="../ai-demo-wakaranai/"><span><img src="../../images/mv-ai.jpg" alt="榎本魅愛「AIでもわからない」ジャケット" width="1280" height="720" loading="lazy"/></span><strong>AIでもわからない</strong><small>榎本魅愛</small><b>VIEW ↗</b></a></div></section>'
    shadow_text = shadow.read_text(encoding="utf-8")
    shadow_text, count = re.subn(r'<section class="release-related-section".*?</section>', shadow_related, shadow_text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("SHADOW//CODE related section was not found.")
    shadow.write_text(shadow_text, encoding="utf-8")

    social = ROOT / "social/index.html"
    queen_social = '<a class="social-hub-card" href="../releases/my-queen-my-oath/"><img src="../images/koga-my-queen-my-oath-cover.jpg" alt="神代煌牙「My Queen, My Oath｜君が、俺のすべて。」正式ジャケット" width="886" height="886" loading="lazy"/><div><small>KOGA KAMISHIRO · OFFICIAL MV</small><strong>My Queen, My Oath</strong><span>作品と公式MVを見る →</span></div></a>'
    upsert_social_card(social, queen_social, '../releases/my-queen-my-oath/')
    red_social = '<a class="social-hub-card" href="../releases/red-moon-rising/"><img src="../images/eclypse-red-moon-rising-cover.png" alt="ECLYPSE「RED MOON // RISING」正式ジャケット" width="1254" height="1254" loading="lazy"/><div><small>ECLYPSE · 2ND SINGLE</small><strong>RED MOON // RISING</strong><span>作品の物語と公式MVを見る →</span></div></a>'
    insert_after(social, '<div class="social-hub-grid">', red_social, '../releases/red-moon-rising/')
    social_cards = '<a class="social-hub-card" href="../releases/smile-and-say-goodbye/"><img src="../images/mv-smile-and-say-goodbye.png" alt="榎本魅愛「SMILE AND SAY GOODBYE」公式ジャケット" width="1672" height="941" loading="lazy"/><div><small>ENOMOTO MIA</small><strong>SMILE AND SAY GOODBYE</strong><span>楽曲の物語を見る →</span></div></a><a class="social-hub-card" href="../releases/boukyaku-no-ikimono/"><img src="../images/mv-boukyaku-no-ikimono.png" alt="神代 煌牙「忘却の生き物」公式ジャケット" width="1672" height="940" loading="lazy"/><div><small>KOGA KAMISHIRO</small><strong>忘却の生き物</strong><span>楽曲の物語を見る →</span></div></a>'
    insert_after(social, '<div class="social-hub-grid">', social_cards, '../releases/smile-and-say-goodbye/')
    social_news = '<a href="../news/red-moon-rising-release/"><span>「RED MOON // RISING」の第2章</span><b aria-hidden="true">→</b></a>'
    insert_after(social, '<div class="social-hub-directory">', social_news, '../news/red-moon-rising-release/')
    queen_social_news = '<a href="../news/my-queen-my-oath-release/"><span>「My Queen, My Oath」公開News</span><b aria-hidden="true">→</b></a>'
    insert_after(social, '<div class="social-hub-directory">', queen_social_news, '../news/my-queen-my-oath-release/')

    news_home = '<article><a href="./news/red-moon-rising-release/" aria-label="RED MOON // RISINGの公式News記事を見る"><time datetime="2026-07-20">2026.07.20</time><span>RELEASE STORY</span><h3>ECLYPSE「RED MOON // RISING」公開｜赤い月とともに始まる第2章</h3><b aria-hidden="true">↗</b></a></article>'
    insert_after(home, '<div class="news-list">', news_home, './news/red-moon-rising-release/')
    queen_news_home = '<article><a href="./news/my-queen-my-oath-release/" aria-label="My Queen, My Oathの公式News記事を見る"><time datetime="2026-07-20">2026.07.20</time><span>RELEASE STORY</span><h3>神代煌牙「My Queen, My Oath」公開｜君が、俺のすべて。</h3><b aria-hidden="true">↗</b></a></article>'
    insert_after(home, '<div class="news-list">', queen_news_home, './news/my-queen-my-oath-release/')
    news_index = ROOT / "news/index.html"
    news_card = '<article class="news-directory-card"><a href="./red-moon-rising-release/"><span class="news-directory-image"><img src="../images/eclypse-red-moon-rising-cover.png" alt="ECLYPSE「RED MOON // RISING」公開記事のサムネイル" width="1254" height="1254" loading="lazy"/></span><span class="news-directory-meta"><time datetime="2026-07-20">2026.07.20</time><em>RELEASE STORY</em></span><h2>ECLYPSE「RED MOON // RISING」公開｜赤い月とともに始まる第2章</h2><p>壊れたコードの先で赤い月が昇る。ECLYPSEの2nd Single、その世界観と公式MVを紹介します。</p><b aria-hidden="true">記事を読む ↗</b></a></article>'
    insert_after(news_index, '<div class="news-list news-feature-list">', news_card, './red-moon-rising-release/')
    queen_news_card = '<article class="news-directory-card"><a href="./my-queen-my-oath-release/"><span class="news-directory-image"><img src="../images/koga-my-queen-my-oath-cover.jpg" alt="神代煌牙「My Queen, My Oath」公開記事のサムネイル" width="886" height="886" loading="lazy"/></span><span class="news-directory-meta"><time datetime="2026-07-20">2026.07.20</time><em>RELEASE STORY</em></span><h2>神代煌牙「My Queen, My Oath」公開｜君が、俺のすべて。</h2><p>夕暮れの海を舞台に、大切な人を守り抜く覚悟と永遠の誓いを描いた公式MVを紹介します。</p><b aria-hidden="true">記事を読む ↗</b></a></article>'
    insert_after(news_index, '<div class="news-list news-feature-list">', queen_news_card, './my-queen-my-oath-release/')

    for path in (mia, koga, eclypse):
        text = path.read_text(encoding="utf-8")
        number = 0
        def renumber(match: re.Match[str]) -> str:
            nonlocal number
            number += 1
            return f"{match.group(1)}{number:02d}{match.group(2)}"
        text = re.sub(r'(<a class="artist-track-row[^"]*"[^>]*><span>)\d+(</span>)', renumber, text)
        path.write_text(text, encoding="utf-8")

    update_item_list(ROOT / "releases/index.html", releases)
    update_item_list(mia, [item for item in releases if item["artistSlug"] == "enomoto-mia"])
    update_item_list(koga, [
        {"title":"My Queen, My Oath","releasePage":"releases/my-queen-my-oath/"},
        {"title":"忘却の生き物","releasePage":"releases/boukyaku-no-ikimono/"},
        {"title":"OUR KINGDOM","releasePage":"releases/our-kingdom/"},
    ])
    news_items = [
        {"title":"神代煌牙「My Queen, My Oath」公開｜君が、俺のすべて。","releasePage":"news/my-queen-my-oath-release/"},
        {"title":"ECLYPSE「RED MOON // RISING」公開｜赤い月とともに始まる第2章","releasePage":"news/red-moon-rising-release/"},
        {"title":"榎本魅愛「百万告」公開｜百万回でも伝えたい、更新され続ける恋心","releasePage":"news/hyakumankoku-release/"},
        {"title":"榎本魅愛「取り扱いチュー💋い」｜危険でも逃げたくない、小悪魔ラブソング","releasePage":"news/toriatsukai-chui-release/"},
        {"title":"榎本魅愛「もしも明日、はじめましてになっても」｜記憶を越えて、もう一度恋をする","releasePage":"news/moshimo-ashita-hajimemashite-ni-natte-mo-release/"},
        {"title":"ECLYPSE、SUZUKA所属アーティストとして始動。","releasePage":"news/eclypse-joins-suzuka/"},
        {"title":"デビューシングル「SHADOW//CODE」を発表。","releasePage":"news/shadow-code-announcement/"},
    ]
    update_item_list(news_index, news_items)
    print(f"Updated static catalogs for {len(releases)} releases.")


if __name__ == "__main__":
    main()
