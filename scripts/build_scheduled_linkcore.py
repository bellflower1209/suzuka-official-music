#!/usr/bin/env python3
"""Render confirmed future LinkCore destinations on existing release pages."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.suzukaofficial.com/"
MARKER_RE = re.compile(r"<!-- SCHEDULED-LINKCORE:([^:]+):START -->.*?<!-- SCHEDULED-LINKCORE:\1:END -->", re.S)


def panel(item: dict, scheduled: dict) -> str:
    release_date = scheduled["releaseDate"]
    year, month, day = map(int, release_date.split("-"))
    japanese_date = f"{year}年{month}月{day}日"
    display_date = release_date.replace("-", ".")
    url = html.escape(scheduled["linkcoreUrl"], quote=True)
    title = html.escape(item["title"])
    artist = html.escape(item["artist"])
    slug = html.escape(item["slug"])
    live = scheduled.get("status") == "published" and bool(scheduled.get("verifiedAt"))
    state = "NOW STREAMING" if live else "SCHEDULED"
    label = "配信開始" if live else "配信予定"
    return (
        f'<!-- SCHEDULED-LINKCORE:{slug}:START -->'
        f'<section class="streaming-release scheduled-streaming-release" aria-label="Streaming Release {label}">'
        f'<div><p class="streaming-kicker">STREAMING RELEASE / {state}</p>'
        f'<p class="streaming-status" data-streaming-date="{release_date}" aria-live="polite">{japanese_date}{label}</p>'
        f'<h2>{title}</h2><p class="streaming-artist">{artist}</p>'
        f'<p>OFFICIAL RELEASE · <time datetime="{item["releaseDate"]}">{item["releaseDate"].replace("-", ".")}</time> · SUZUKA作品公開</p>'
        f'<p>STREAMING RELEASE · <time datetime="{release_date}">{display_date}</time> — {japanese_date} {label}</p>'
        '<p class="streaming-credit">Label：SUZUKA</p></div>'
        '<div class="streaming-actions">'
        f'<a class="streaming-primary" href="{url}" target="_blank" rel="noopener noreferrer">LinkCoreで配信情報を見る ↗</a>'
        f'<a href="../../artists/{html.escape(item["artistSlug"])}/">アーティストページ</a>'
        '<p>配信状況はLinkCoreでご確認ください。</p></div></section>'
        f'<!-- SCHEDULED-LINKCORE:{slug}:END -->'
    )


def build(root: Path = ROOT) -> None:
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    for item in cms.get("releases", []):
        scheduled = item.get("scheduledStreamingRelease") or {}
        if not scheduled.get("linkcoreUrl") or not item.get("releaseUrl"):
            continue
        path = root / item["releaseUrl"] / "index.html"
        if not path.is_file():
            raise FileNotFoundError(path)
        text = MARKER_RE.sub("", path.read_text(encoding="utf-8"))
        anchor = "<!-- CREATOR:RECOMMENDATIONS:START -->"
        if anchor not in text:
            raise ValueError(f"Scheduled LinkCore insertion point missing: {path}")
        text = text.replace(anchor, panel(item, scheduled) + anchor, 1)
        if "assets/streaming-release.css" not in text:
            text = text.replace(
                "</head>",
                '<link rel="stylesheet" href="../../assets/streaming-release.css"/></head>',
                1,
            )
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    build()
