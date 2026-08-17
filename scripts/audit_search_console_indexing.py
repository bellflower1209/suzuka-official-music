#!/usr/bin/env python3
"""Audit Google Search Console non-indexed exports against the current site."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse


BASE = "https://www.suzukaofficial.com/"
SITEMAP_NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
REASON_FOLDERS = {
    ".": "noindex タグによって除外されました",
    "１": "ページにリダイレクトがあります",
    "２": "代替ページ（適切な canonical タグあり）",
    "４": "重複しています。Google により、ユーザーがマークしたページとは異なるページが正規ページとして選択されました",
    "５": "クロール済み - インデックス未登録",
    "６": "検出 - インデックス未登録",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonical = ""
        self.meta: dict[str, str] = {}
        self.title = ""
        self.h1 = 0
        self.links: list[str] = []
        self.images: list[str] = []
        self.json_ld: list[str] = []
        self._title = False
        self._json = False
        self._json_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag == "title":
            self._title = True
        elif tag == "h1":
            self.h1 += 1
        elif tag == "meta":
            key = (values.get("name") or values.get("property") or "").lower()
            if key:
                self.meta[key] = values.get("content", "")
        elif tag == "link":
            rel = values.get("rel", "").lower()
            href = values.get("href", "")
            if "canonical" in rel:
                self.canonical = href
            if href:
                self.links.append(href)
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"])
        elif tag == "img" and values.get("src"):
            self.images.append(values["src"])
        elif tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self._json = True
            self._json_buffer = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._title = False
        elif tag == "script" and self._json:
            self.json_ld.append("".join(self._json_buffer))
            self._json = False

    def handle_data(self, data: str) -> None:
        if self._title:
            self.title += data
        if self._json:
            self._json_buffer.append(data)


class TrackingRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        self.targets.append(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def canonical_url(url: str) -> str:
    parsed = urlparse(urldefrag(url)[0])
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def link_url(url: str) -> str:
    """Normalize a linked URL without discarding its query state."""
    parsed = urlparse(urldefrag(url)[0])
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, ""))


def page_type(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if url.endswith("feed.xml"):
        return "Feed"
    if not path:
        return "Home"
    first = path.split("/", 1)[0]
    return {
        "artists": "Artist", "gallery": "Gallery", "genres": "Genre",
        "lyrics": "Lyrics", "news": "News", "playlists": "Playlist",
        "rankings": "Ranking", "releases": "Release", "search": "Search",
        "wiki": "Wiki", "universe": "Universe",
    }.get(first, "Other")


def load_exports(csv_root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for folder, expected_reason in REASON_FOLDERS.items():
        directory = csv_root if folder == "." else csv_root / folder
        metadata = directory / "メタデータ.csv"
        table = directory / "表.csv"
        metadata_rows = list(csv.reader(metadata.open(encoding="utf-8-sig", newline="")))
        reason = next((row[1] for row in metadata_rows if row and row[0] == "問題"), "")
        if reason != expected_reason:
            raise RuntimeError(f"Unexpected Search Console reason in {folder}: {reason}")
        for row in csv.DictReader(table.open(encoding="utf-8-sig", newline="")):
            records.append({
                "url": row["URL"].strip(),
                "searchConsoleReason": reason,
                "lastCrawl": row["前回のクロール"].strip(),
                "sourceGroup": folder,
            })
    urls = [item["url"] for item in records]
    if len(records) != 61 or len(set(urls)) != 61:
        raise RuntimeError(f"Expected 61 unique Search Console URLs, got {len(records)}/{len(set(urls))}")
    return records


def route_for_file(root: Path, path: Path) -> str:
    rel = path.relative_to(root).as_posix()
    if rel == "index.html":
        return BASE
    if rel.endswith("/index.html"):
        return BASE + rel[:-10]
    return BASE + rel


def internal_link_counts(root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in root.rglob("*.html"):
        if ".git" in path.parts:
            continue
        source = route_for_file(root, path)
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        targets = set()
        for href in parser.links:
            if href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            target = link_url(urljoin(source, href))
            if target.startswith(BASE):
                targets.add(target)
        for target in targets:
            counts[target] += 1
    return counts


def exact_duplicate_map(root: Path) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for path in root.rglob("*.html"):
        if ".git" in path.parts:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        groups.setdefault(digest, []).append(route_for_file(root, path))
    result: dict[str, list[str]] = {}
    for urls in groups.values():
        for url in urls:
            result[url] = sorted(candidate for candidate in urls if candidate != url)
    return result


def fetch(url: str, user_agent: str) -> dict:
    tracker = TrackingRedirectHandler()
    opener = urllib.request.build_opener(tracker)
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with opener.open(request, timeout=30) as response:
            body = response.read()
            return {
                "status": response.status,
                "finalUrl": response.geturl(),
                "contentType": response.headers.get("Content-Type", ""),
                "redirects": tracker.targets,
                "sha256": hashlib.sha256(body).hexdigest(),
                "body": body,
            }
    except urllib.error.HTTPError as error:
        body = error.read()
        return {
            "status": error.code, "finalUrl": error.geturl(),
            "contentType": error.headers.get("Content-Type", ""),
            "redirects": tracker.targets, "sha256": hashlib.sha256(body).hexdigest(),
            "body": body,
        }


def parse_html(body: bytes) -> tuple[PageParser, bool, list[str]]:
    parser = PageParser()
    parser.feed(body.decode("utf-8", "replace"))
    json_errors = []
    for position, value in enumerate(parser.json_ld, 1):
        try:
            json.loads(value)
        except json.JSONDecodeError as error:
            json_errors.append(f"block {position}: {error}")
    return parser, not json_errors, json_errors


def expected_canonical(item: dict[str, str]) -> str | None:
    reason = item["searchConsoleReason"]
    url = item["url"]
    if reason == REASON_FOLDERS["２"]:
        return BASE + "search/"
    if reason == REASON_FOLDERS["１"]:
        return BASE
    if url.endswith("feed.xml"):
        return None
    return canonical_url(url)


def audit_record(
    item: dict[str, str], sitemap: set[str], links: Counter[str], duplicates: dict[str, list[str]]
) -> dict:
    url = item["url"]
    normal = fetch(url, "Mozilla/5.0 SUZUKA indexability audit")
    googlebot = fetch(url, "Googlebot/2.1 (+http://www.google.com/bot.html)")
    is_html = "html" in normal["contentType"].lower()
    parser = PageParser()
    json_valid = True
    json_errors: list[str] = []
    if is_html:
        parser, json_valid, json_errors = parse_html(normal["body"])
    expected = expected_canonical(item)
    canonical = parser.canonical if is_html else ""
    robots = parser.meta.get("robots", "") if is_html else ""
    reason = item["searchConsoleReason"]
    canonical_key = expected or canonical_url(url)
    exact_link_key = link_url(url)
    redirect_target = normal["redirects"][-1] if normal["redirects"] else ""
    same_googlebot = (
        normal["status"] == googlebot["status"]
        and normal["finalUrl"] == googlebot["finalUrl"]
        and normal["sha256"] == googlebot["sha256"]
    )
    tech_errors: list[str] = []
    intended_non_index = False
    action = ""

    if reason == REASON_FOLDERS["１"]:
        intended_non_index = True
        if len(normal["redirects"]) != 1 or normal["finalUrl"] != BASE or normal["status"] != 200:
            tech_errors.append("HTTP版からHTTPS正式URLへの1 hopリダイレクトが不正")
        action = "HTTP版はHTTPS正式URLへ1 hopで転送。非indexが正常。"
    elif reason == REASON_FOLDERS["２"]:
        intended_non_index = True
        if canonical != expected or urldefrag(url)[0] in sitemap:
            tech_errors.append("検索条件URLのcanonicalまたはsitemap除外が不正")
        action = "条件付き検索URLは/search/へ正規化。独立indexさせない。"
    elif url.endswith("feed.xml"):
        intended_non_index = True
        try:
            ET.fromstring(normal["body"])
        except ET.ParseError as error:
            tech_errors.append(f"Feed XML構文エラー: {error}")
        if normal["status"] != 200 or "xml" not in normal["contentType"].lower():
            tech_errors.append("FeedのHTTPまたはContent-Typeが不正")
        action = "Feedは検索結果のHTMLページではないため、非indexが正常。"
    else:
        checks = {
            "HTTP 200でない": normal["status"] != 200,
            "redirectがある": bool(normal["redirects"]),
            "index,followでない": "index" not in robots.lower() or "noindex" in robots.lower(),
            "self canonicalでない": canonical != expected,
            "og:urlが正式URLと不一致": parser.meta.get("og:url", "") != expected,
            "sitemap未掲載": canonical_key not in sitemap,
            "titleなし": not parser.title.strip(),
            "meta descriptionなし": not parser.meta.get("description", "").strip(),
            "h1が1件でない": parser.h1 != 1,
            "JSON-LDなしまたは不正": not parser.json_ld or not json_valid,
            "内部リンク0": links[canonical_key] < 1,
        }
        tech_errors.extend(label for label, failed in checks.items() if failed)
        if reason == REASON_FOLDERS["."] and not tech_errors:
            action = "現在はindex,followへ修正済み。Google再クロール待ち。"
        elif reason == REASON_FOLDERS["４"] and not tech_errors:
            action = "正式Release URLはcanonical・OG・JSON-LD・sitemapで一致済み。Google再評価待ち。"
        elif not tech_errors:
            action = "現在の技術要件は正常。Googleの初回クロール・再評価待ち。"

    if not same_googlebot:
        tech_errors.append("通常UAとGooglebotの取得結果が不一致")
    action_required = bool(tech_errors)
    classification = "A" if action_required else ("C" if intended_non_index else "B")
    if action_required:
        action = " / ".join(tech_errors)
    duplicate_candidates = duplicates.get(canonical_url(url), [])
    duplicate_status = (
        "expected-query-duplicate" if reason == REASON_FOLDERS["２"]
        else "exact-duplicate-detected" if duplicate_candidates
        else "no-exact-duplicate-detected"
    )
    return {
        "url": url,
        "searchConsoleReason": reason,
        "lastCrawl": item["lastCrawl"],
        "pageType": page_type(url),
        "httpStatus": normal["status"],
        "finalUrl": normal["finalUrl"],
        "redirectCount": len(normal["redirects"]),
        "redirectTarget": redirect_target,
        "indexable": not intended_non_index and not action_required,
        "robots": robots,
        "canonical": canonical,
        "ogUrl": parser.meta.get("og:url", ""),
        "googleExpectedCanonical": expected,
        "sitemapIncluded": urldefrag(url)[0] in sitemap,
        "internalLinkCount": links[exact_link_key],
        "canonicalTargetInternalLinkCount": links[canonical_key],
        "title": parser.title.strip(),
        "metaDescription": parser.meta.get("description", "").strip(),
        "h1Count": parser.h1,
        "jsonLd": {"count": len(parser.json_ld), "valid": json_valid, "errors": json_errors},
        "orphan": not intended_non_index and links[canonical_key] < 1,
        "duplicateStatus": duplicate_status,
        "duplicateCandidates": duplicate_candidates,
        "normalSha256": normal["sha256"],
        "googlebotStatus": googlebot["status"],
        "googlebotFinalUrl": googlebot["finalUrl"],
        "googlebotSha256": googlebot["sha256"],
        "googlebotMatchesNormal": same_googlebot,
        "actionRequired": action_required,
        "classification": classification,
        "action": action,
        "verificationResult": "PASS" if not action_required else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--csv-root", type=Path)
    parser.add_argument("--source-json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "docs/audits/search-console-indexing-2026-08-17.json"
    source_json = args.source_json or root / "assets/data/search-console-unindexed-20260810.json"
    if args.csv_root:
        records = load_exports(args.csv_root.resolve())
        source_document = {
            "schemaVersion": "1.0",
            "searchConsoleLastUpdated": "2026-08-10",
            "source": "Google Search Console user-exported CSV files",
            "urlCount": len(records),
            "records": records,
        }
        source_json.parent.mkdir(parents=True, exist_ok=True)
        source_json.write_text(
            json.dumps(source_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    else:
        if not source_json.is_file():
            raise SystemExit("--csv-root is required until the normalized source JSON has been created")
        source_document = json.loads(source_json.read_text(encoding="utf-8"))
        records = source_document["records"]
        if len(records) != 61 or len({item["url"] for item in records}) != 61:
            raise RuntimeError("Normalized Search Console source must contain 61 unique URLs")
    sitemap_root = ET.parse(root / "sitemap.xml").getroot()
    sitemap = {node.text.strip() for node in sitemap_root.findall("s:url/s:loc", SITEMAP_NS) if node.text}
    links = internal_link_counts(root)
    duplicates = exact_duplicate_map(root)
    audited = [audit_record(item, sitemap, links, duplicates) for item in records]
    reason_counts = Counter(item["searchConsoleReason"] for item in audited)
    class_counts = Counter(item["classification"] for item in audited)
    report = {
        "schemaVersion": "1.0",
        "auditDate": "2026-08-17",
        "searchConsoleLastUpdated": "2026-08-10",
        "source": source_json.relative_to(root).as_posix(),
        "sourceUrlCount": len(records),
        "reasonCounts": dict(sorted(reason_counts.items())),
        "classificationCounts": {key: class_counts.get(key, 0) for key in ("A", "B", "C")},
        "classificationLabels": {
            "A": "修正必要", "B": "現在は正常・Google再クロール待ち",
            "C": "意図的非indexで正常",
        },
        "unclassified": sum(1 for item in audited if item["classification"] not in {"A", "B", "C"}),
        "summary": {
            "actionRequired": sum(item["actionRequired"] for item in audited),
            "orphanIndexPages": sum(item["orphan"] for item in audited),
            "sitemapMissingIndexPages": sum(
                item["indexable"] and not item["sitemapIncluded"] for item in audited
            ),
            "canonicalMismatch": sum(
                item["indexable"] and item["canonical"] != item["googleExpectedCanonical"] for item in audited
            ),
            "googlebotMismatch": sum(not item["googlebotMatchesNormal"] for item in audited),
        },
        "records": audited,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output), "urls": len(audited), "reasons": report["reasonCounts"],
        "classes": report["classificationCounts"], "summary": report["summary"],
    }, ensure_ascii=False, indent=2))
    return 1 if report["unclassified"] or report["summary"]["actionRequired"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
