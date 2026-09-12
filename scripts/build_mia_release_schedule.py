#!/usr/bin/env python3
"""Render the confirmed ENOMOTO MIA September campaign from canonical data."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path


START = "<!-- MIA-RELEASE-SCHEDULE:START -->"
END = "<!-- MIA-RELEASE-SCHEDULE:END -->"
BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)


def schedule_panel(schedule: dict, prefix: str, *, compact: bool) -> str:
    cards = []
    for activity in schedule["activities"]:
        month_day = activity["date"][5:].replace("-", ".")
        href = prefix + activity["url"]
        cards.append(
            f'<a class="mia-schedule-item" href="{html.escape(href)}" '
            f'data-activity-date="{activity["date"]}" data-activity-kind="{html.escape(activity["kind"])}">'
            f'<time datetime="{activity["date"]}">{month_day}</time><span>'
            f'<strong>{html.escape(activity["title"])}</strong>'
            f'<small data-activity-status>{html.escape(activity["kind"])}</small></span></a>'
        )
    klass = " mia-release-schedule-compact" if compact else ""
    return (
        f'{START}<section class="mia-release-schedule{klass}" aria-labelledby="mia-release-schedule-title">'
        '<header><p>ENOMOTO MIA</p><h2 id="mia-release-schedule-title">SEPTEMBER RELEASES</h2>'
        '<span>Asia / Tokyo</span></header>'
        f'<div class="mia-schedule-grid">{"".join(cards)}</div>'
        f'<a class="mia-schedule-news" href="{prefix}{schedule["newsUrl"]}">9月21日 2作品リリースNEWSを見る ↗</a>'
        f'</section>{END}'
    )


def insert(path: Path, panel: str, marker: str, asset_prefix: str) -> None:
    text = BLOCK.sub("", path.read_text(encoding="utf-8"))
    if marker not in text:
        raise ValueError(f"Schedule insertion point missing: {path}")
    text = text.replace(marker, panel + marker, 1)
    css = f'<link rel="stylesheet" href="{asset_prefix}assets/mia-release-schedule.css"/>'
    script = f'<script defer src="{asset_prefix}assets/mia-release-schedule.js"></script>'
    if "assets/mia-release-schedule.css" not in text:
        text = text.replace("</head>", css + script + "</head>", 1)
    path.write_text(text, encoding="utf-8")


def build_news(root: Path, schedule: dict) -> None:
    slug = "enomoto-mia-september-21-double-release"
    path = root / "news" / slug / "index.html"
    text = path.read_text(encoding="utf-8")
    body = (
        '<section class="mia-campaign-news"><p>榎本魅愛の新たな2作品</p>'
        '<h2>「百万告」<br>「Hello Hello Halloween」</h2>'
        '<p>が、2026年9月21日にリリース予定です。</p>'
        '<p>9月11日の「花言葉」Streaming Release、9月18日のJOYSOUNDカラオケ配信から続く、榎本魅愛の9月の活動としてお知らせします。</p>'
        '<p>配信先URL、各配信ストア、追加クレジットは、正式情報の確認後にご案内します。</p>'
        '<div class="explore-actions"><a href="../../releases/hyakumankoku/">百万告</a>'
        '<a href="../../releases/hello-hello-halloween/">Hello Hello Halloween</a>'
        '<a href="../../releases/hanakotoba/">花言葉</a>'
        '<a href="../hanakotoba-joysound-karaoke/">JOYSOUND NEWS</a></div></section>'
    )
    text, count = re.subn(r'<section><img[^>]+/></section>', body, text, count=1)
    if count != 1:
        raise ValueError("Campaign news body insertion point missing")
    if "assets/mia-release-schedule.css" not in text:
        text = text.replace("</head>", '<link rel="stylesheet" href="../../assets/mia-release-schedule.css"/></head>', 1)
    path.write_text(text, encoding="utf-8")


def build(root: Path) -> None:
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    schedule = cms["miaReleaseSchedule"]
    insert(root / "index.html", schedule_panel(schedule, "./", compact=True), "<!-- V31:HOME-NEXT:START -->", "./")
    insert(root / "artists/enomoto-mia/index.html", schedule_panel(schedule, "../../", compact=False), '<section class="v31-artist-hero">', "../../")
    build_news(root, schedule)
    artist = next(a for a in cms["artists"] if a["slug"] == "enomoto-mia")
    url = artist.get("officialYoutubeUrl")
    if not url:
        return
    channel = (
        '<aside class="mia-official-channel" aria-label="榎本魅愛 Official YouTube Channel">'
        '<p>ENOMOTO MIA / ARTIST OFFICIAL</p><h2>OFFICIAL YOUTUBE CHANNEL</h2>'
        '<p>榎本魅愛 Official YouTube<br>Music Video / Official Audio / Shorts</p>'
        f'<a class="button button-primary" href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">Official YouTubeを見る ↗</a>'
        f'<p><a href="{html.escape(artist["youtubeUrl"])}" target="_blank" rel="noopener noreferrer">SUZUKA YouTube · Label / Project Official ↗</a></p></aside>'
    )
    paths = [root / "index.html", root / "artists/enomoto-mia/index.html"]
    paths += [root / "releases" / r["slug"] / "index.html" for r in cms["releases"] + cms.get("upcoming", []) if r.get("artistSlug") == "enomoto-mia"]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        text = re.sub(r'<!-- MIA-CHANNEL:START -->.*?<!-- MIA-CHANNEL:END -->', '', text, flags=re.S)
        content = channel if path in paths[:2] else channel.replace('Official YouTubeを見る ↗', '榎本魅愛 Official YouTube ↗')
        block = '<!-- MIA-CHANNEL:START -->' + content + '<!-- MIA-CHANNEL:END -->'
        marker = END if path in paths[:2] else '</main>'
        text = text.replace(marker, block + marker, 1)
        if 'assets/mia-release-schedule.css' not in text:
            text = text.replace('</head>', '<link rel="stylesheet" href="../../assets/mia-release-schedule.css"/></head>', 1)
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    build(Path(__file__).resolve().parents[1])
