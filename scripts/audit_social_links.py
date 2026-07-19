#!/usr/bin/env python3
"""Validate SUZUKA's official SNS/release link registry and write UTM guidance."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_BASE = "https://bellflower1209.github.io/suzuka-official-music"
OLD_DOMAIN = "suzuka-official-music.ria20210815.chatgpt.site"
SOCIAL_PATH = ROOT / "assets/data/social-links.json"
RELEASE_PATH = ROOT / "assets/data/release-links.json"
REPORT_PATH = ROOT / "docs/social/official-link-plan.md"


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.anchors.append({key: value or "" for key, value in attrs})


def campaign_url(path: str, source: str, medium: str, campaign: str) -> str:
    base = f"{PUBLIC_BASE}/{path.lstrip('/')}"
    query = urllib.parse.urlencode({"utm_source": source, "utm_medium": medium, "utm_campaign": campaign})
    return f"{base}?{query}"


def validate() -> tuple[list[str], dict, list[dict]]:
    errors: list[str] = []
    social = json.loads(SOCIAL_PATH.read_text(encoding="utf-8"))
    releases = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))["releases"]
    if len(releases) != 16:
        errors.append(f"release link registry must contain 16 works, found {len(releases)}")
    slugs = [item["slug"] for item in releases]
    if len(slugs) != len(set(slugs)):
        errors.append("release link registry contains duplicate slugs")
    for item in releases:
        for field in ("slug", "title", "artist", "artistSlug", "releasePage", "youtubeStatus", "shortsStatus", "newsStatus"):
            if not item.get(field):
                errors.append(f"{item.get('slug', '(unknown)')}: missing {field}")
        page = ROOT / item["releasePage"] / "index.html"
        artist = ROOT / "artists" / item["artistSlug"] / "index.html"
        if not page.is_file():
            errors.append(f"{item['slug']}: release page is missing")
        if not artist.is_file():
            errors.append(f"{item['slug']}: artist page is missing")
        for url_field, status_field in (("youtubeUrl", "youtubeStatus"), ("shortsUrl", "shortsStatus")):
            url = item.get(url_field)
            status = item[status_field]
            if status == "published" and not str(url).startswith("https://www.youtube.com/"):
                errors.append(f"{item['slug']}: published {url_field} is not an official YouTube URL")
            if status != "published" and url:
                errors.append(f"{item['slug']}: unconfirmed {url_field} must not contain a URL")
        if item["newsStatus"] == "published" and not (ROOT / item["newsPage"] / "index.html").is_file():
            errors.append(f"{item['slug']}: News page is missing")
    for item in social["links"]:
        if item["status"] == "published" and not str(item.get("url", "")).startswith("https://"):
            errors.append(f"social link {item['slug']} is published without HTTPS URL")
        if item["status"] != "published" and item.get("url"):
            errors.append(f"social link {item['slug']} is unconfirmed but contains a URL")
    for page in ROOT.rglob("*.html"):
        if ".git" in page.parts:
            continue
        text = page.read_text(encoding="utf-8")
        if OLD_DOMAIN in text:
            errors.append(f"{page.relative_to(ROOT)}: contains old domain")
        parser = AnchorParser()
        parser.feed(text)
        for anchor in parser.anchors:
            href = anchor.get("href", "")
            if not href or href == "#":
                errors.append(f"{page.relative_to(ROOT)}: empty or placeholder link")
            if href.startswith("http://"):
                errors.append(f"{page.relative_to(ROOT)}: insecure external link {href}")
            if "utm_" in href and (href.startswith((".", "/")) or PUBLIC_BASE in href):
                errors.append(f"{page.relative_to(ROOT)}: internal link contains UTM parameters")
            if anchor.get("target") == "_blank":
                rel = set(anchor.get("rel", "").split())
                if not {"noopener", "noreferrer"}.issubset(rel):
                    errors.append(f"{page.relative_to(ROOT)}: target=_blank is missing noopener noreferrer")
    return errors, social, releases


def render_report(social: dict, releases: list[dict]) -> str:
    lines = [
        "# SUZUKA公式SNS・作品リンク運用表",
        "",
        "## 正式な入口",
        "",
        f"- Instagramプロフィール代表URL: `{PUBLIC_BASE}/social/`",
        f"- InstagramプロフィールUTM: `{campaign_url('social/', 'instagram', 'profile', 'official_links')}`",
        f"- YouTubeチャンネル: `{next(item['url'] for item in social['links'] if item['platform'] == 'youtube')}`",
        f"- Releases一覧: `{PUBLIC_BASE}/releases/`",
        f"- News一覧: `{PUBLIC_BASE}/news/`",
        "- Instagram公式URL: 未確認。確認できるまでサイト・構造化データへ掲載しない。",
        "",
        "## 作品別 YouTube・Instagram案内URL",
        "",
        "| 作品 | リリースページ | News | MV | Shorts | YouTube説明欄UTM | 固定コメントUTM | Instagram投稿UTM |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in releases:
        release_url = f"{PUBLIC_BASE}/{item['releasePage']}"
        news_url = f"{PUBLIC_BASE}/{item['newsPage']}" if item.get("newsPage") else "未設定"
        mv = item.get("youtubeUrl") or "未確認"
        shorts = item.get("shortsUrl") or "未確認"
        description = campaign_url(item["releasePage"], "youtube", "video_description", item["slug"])
        pinned = campaign_url(item["releasePage"], "youtube", "pinned_comment", item["slug"])
        instagram = campaign_url(item["releasePage"], "instagram", "social_post", item["slug"])
        lines.append(f"| {item['title']} | {release_url} | {news_url} | {mv} | {shorts} | {description} | {pinned} | {instagram} |")
    lines.extend([
        "",
        "## 運用ルール",
        "",
        "- canonical、sitemap、サイト内リンクにはUTMを付けない。",
        "- YouTube説明欄は `video_description`、固定コメントは `pinned_comment`、Shortsは `shorts` を使用する。",
        "- Instagram楽曲投稿はリリースページ、歌詞・世界観投稿はNews、アーティスト投稿はプロフィールへ案内する。",
        "- URL未確認のMV・Shorts・Instagramは推測せず、正本JSONで `unconfirmed` を維持する。",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the Markdown operations report")
    args = parser.parse_args()
    errors, social, releases = validate()
    if errors:
        print("Social link audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    if args.write:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(render_report(social, releases), encoding="utf-8")
    print(f"Social link audit passed: {len(releases)} works, {sum(bool(item.get('youtubeUrl')) for item in releases)} MVs, {sum(bool(item.get('shortsUrl')) for item in releases)} Shorts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
