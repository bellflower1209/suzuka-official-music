#!/usr/bin/env python3
"""Audit every public Gallery page for crawlability, discovery, and uniqueness."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.suzukaofficial.com/"
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class HtmlAuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.robots = ""
        self.canonical = ""
        self.h1: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.images: list[str] = []
        self.schemas: list[dict] = []
        self.visible: list[str] = []
        self._capture = ""
        self._buffer: list[str] = []
        self._hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag in {"script", "style", "template"}:
            self._hidden += 1
        if tag in {"title", "h1"}:
            self._capture = tag
            self._buffer = []
        if tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self._capture = "json"
            self._buffer = []
        if tag == "meta":
            name = (values.get("name") or values.get("property") or "").lower()
            if name == "description":
                self.description = values.get("content", "").strip()
            elif name in {"robots", "googlebot"}:
                self.robots += "," + values.get("content", "")
        elif tag == "link" and "canonical" in values.get("rel", "").lower().split():
            self.canonical = values.get("href", "")
        elif tag == "a" and values.get("href"):
            self.links.append((values["href"], values.get("rel", "")))
        elif tag == "img" and values.get("src"):
            self.images.append(values["src"])

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._capture == tag:
            value = " ".join("".join(self._buffer).split())
            if tag == "title":
                self.title = value
            else:
                self.h1.append(value)
            self._capture = ""
        elif tag == "script" and self._capture == "json":
            try:
                value = json.loads("".join(self._buffer))
                self.schemas.append(value)
            except json.JSONDecodeError:
                self.schemas.append({"_invalid": True})
            self._capture = ""
        if tag in {"script", "style", "template"} and self._hidden:
            self._hidden -= 1

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buffer.append(data)
        if not self._hidden and data.strip():
            self.visible.append(data.strip())


def parse_html(text: str) -> HtmlAuditParser:
    parser = HtmlAuditParser()
    parser.feed(text)
    return parser


def schema_types(values: list[dict]) -> set[str]:
    result: set[str] = set()
    for value in values:
        nodes = value.get("@graph", [value]) if isinstance(value, dict) else []
        for node in nodes:
            kinds = node.get("@type", []) if isinstance(node, dict) else []
            if isinstance(kinds, str):
                result.add(kinds)
            else:
                result.update(kinds)
    return result


def route(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    return BASE if rel == "index.html" else BASE + rel.removesuffix("index.html")


def local_pages() -> dict[str, HtmlAuditParser]:
    pages = {}
    for path in ROOT.rglob("index.html"):
        if ".git" in path.parts:
            continue
        pages[route(path)] = parse_html(path.read_text(encoding="utf-8"))
    return pages


def incoming_links(pages: dict[str, HtmlAuditParser]) -> Counter[str]:
    result: Counter[str] = Counter()
    for source, parser in pages.items():
        targets = set()
        for href, rel in parser.links:
            target = urljoin(source, href).split("#", 1)[0].split("?", 1)[0]
            if target.startswith(BASE) and "nofollow" not in rel.lower().split():
                targets.add(target)
        result.update(targets)
    return result


def fetch(url: str, agent: str) -> tuple[int, str, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": agent})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.geturl(), dict(response.headers.items()), response.read()


def similarity(left: str, right: str) -> float:
    return round(SequenceMatcher(None, " ".join(left.split()), " ".join(right.split())).ratio(), 3)


def main() -> int:
    pages = local_pages()
    incoming = incoming_links(pages)
    sitemap_root = ET.parse(ROOT / "sitemap.xml").getroot()
    sitemap: dict[str, str] = {}
    for entry in sitemap_root.findall("s:url", NS):
        loc = entry.find("s:loc", NS)
        lastmod = entry.find("s:lastmod", NS)
        if loc is not None and loc.text:
            sitemap[loc.text.strip()] = lastmod.text.strip() if lastmod is not None and lastmod.text else ""

    robots_text = (ROOT / "robots.txt").read_text(encoding="utf-8")
    gallery_paths = sorted((ROOT / "gallery").glob("*/index.html"))
    records: list[dict] = []
    title_counts: Counter[str] = Counter()
    description_counts: Counter[str] = Counter()

    for path in gallery_paths:
        slug = path.parent.name
        url = f"{BASE}gallery/{slug}/"
        release_url = f"{BASE}releases/{slug}/"
        local = pages[url]
        release = pages.get(release_url)
        status, final_url, headers, body = fetch(url, "SUZUKA Gallery index audit")
        bot_status, bot_final, _, bot_body = fetch(url, GOOGLEBOT)
        remote = parse_html(body.decode("utf-8", "replace"))
        types = schema_types(remote.schemas)
        absolute_links = {
            urljoin(url, href).split("#", 1)[0].split("?", 1)[0]
            for href, _ in remote.links
        }
        release_links = {
            urljoin(release_url, href).split("#", 1)[0].split("?", 1)[0]
            for href, _ in release.links
        } if release else set()
        # Content-quality checks must inspect the generated artifact that will be
        # deployed. HTTP, robots and Googlebot checks still use production.
        visible = " ".join(local.visible)
        release_visible = " ".join(release.visible) if release else ""
        title_ratio = similarity(remote.title, release.title if release else "")
        description_ratio = similarity(remote.description, release.description if release else "")
        body_ratio = similarity(visible, release_visible) if release else 0.0
        # Similar titles are expected for a Release/Gallery pair. Assess the
        # risk from description/body similarity rather than title alone.
        content_ratio = max(description_ratio, body_ratio)
        duplicate_level = "High" if content_ratio >= 0.75 else "Medium" if content_ratio >= 0.45 else "Low"
        indexable = (
            status == 200 and final_url == url and remote.canonical == url
            and "noindex" not in remote.robots.lower() and url in sitemap
        )
        record = {
            "url": url,
            "slug": slug,
            "httpStatus": status,
            "redirectCount": int(final_url != url),
            "finalUrl": final_url,
            "xRobotsTag": headers.get("X-Robots-Tag", ""),
            "robotsTxtAllowed": not bool(re.search(r"(?mi)^Disallow:\s*/gallery/?\s*$", robots_text)),
            "metaRobots": remote.robots.lstrip(","),
            "indexable": indexable,
            "canonical": remote.canonical,
            "selfCanonical": remote.canonical == url,
            "sitemapIncluded": url in sitemap,
            "sitemapCanonicalExact": url in sitemap and remote.canonical == url,
            "sitemapLastmod": sitemap.get(url, ""),
            "lastmodAssessment": "omitted-valid" if not sitemap.get(url) else "present",
            "incomingInternalLinks": incoming[url],
            "orphan": incoming[url] == 0,
            "galleryHubToDetail": url in {
                urljoin(f"{BASE}gallery/", href).split("#", 1)[0].split("?", 1)[0]
                for href, _ in pages[f"{BASE}gallery/"].links
            },
            "galleryToRelease": release_url in absolute_links,
            "releaseToGallery": url in release_links,
            "linksAreHtmlAnchors": True,
            "nofollowInternalLinks": sum(
                1 for href, rel in remote.links
                if urljoin(url, href).startswith(BASE) and "nofollow" in rel.lower().split()
            ),
            "title": remote.title,
            "description": remote.description,
            "h1": remote.h1,
            "h1Count": len(remote.h1),
            "jsonLdValid": all("_invalid" not in item for item in remote.schemas),
            "jsonLdTypes": sorted(types),
            "breadcrumbList": "BreadcrumbList" in types,
            "videoObject": "VideoObject" in types,
            "initialHtmlTextCharacters": len(visible),
            "bodyPresentWithoutJs": len(visible) >= 300,
            "imageCount": len(remote.images),
            "releaseUrl": release_url,
            "titleSimilarity": title_ratio,
            "descriptionSimilarity": description_ratio,
            "bodySimilarity": body_ratio,
            "releaseGallerySimilarity": duplicate_level,
            "visualArchiveMarkers": {
                "officialMv": "OFFICIAL MV" in visible,
                "productionImages": "制作画像・サムネイル" in visible,
                "productionNote": "制作メモ" in visible,
                "youtubeThumbnail": "YouTubeサムネイル" in visible,
            },
            "thinContentRisk": len(visible) < 900,
            "soft404Risk": status == 200 and (len(visible) < 300 or not remote.h1),
            "googlebotStatus": bot_status,
            "googlebotFinalUrl": bot_final,
            "googlebotMatchesNormal": (
                bot_status == status and bot_final == final_url
                and hashlib.sha256(bot_body).hexdigest() == hashlib.sha256(body).hexdigest()
            ),
        }
        title_counts[remote.title] += 1
        description_counts[remote.description] += 1
        records.append(record)

    for record in records:
        record["duplicateTitle"] = title_counts[record["title"]] > 1
        record["duplicateDescription"] = description_counts[record["description"]] > 1
        record["technicalErrors"] = [
            label for label, failed in {
                "HTTP/redirect": record["httpStatus"] != 200 or record["redirectCount"] != 0,
                "robots": not record["robotsTxtAllowed"] or "noindex" in record["metaRobots"].lower() or bool(record["xRobotsTag"]),
                "canonical": not record["selfCanonical"],
                "sitemap": not record["sitemapCanonicalExact"],
                "orphan": record["orphan"],
                "bidirectionalLinks": not record["galleryHubToDetail"] or not record["galleryToRelease"] or not record["releaseToGallery"],
                "metadata": not record["title"] or not record["description"] or record["h1Count"] != 1,
                "structuredData": not record["jsonLdValid"] or not record["breadcrumbList"] or not record["videoObject"],
                "initialHtml": not record["bodyPresentWithoutJs"],
                "googlebot": not record["googlebotMatchesNormal"],
            }.items() if failed
        ]

    summary = {
        "auditDate": "2026-09-07",
        "galleryPages": len(records),
        "sitemapGalleryPages": sum(record["sitemapIncluded"] for record in records),
        "releaseGalleryPairs": sum(record["galleryToRelease"] and record["releaseToGallery"] for record in records),
        "orphans": sum(record["orphan"] for record in records),
        "canonicalErrors": sum(not record["selfCanonical"] for record in records),
        "noindexErrors": sum("noindex" in record["metaRobots"].lower() for record in records),
        "redirectErrors": sum(record["redirectCount"] != 0 for record in records),
        "googlebotMismatches": sum(not record["googlebotMatchesNormal"] for record in records),
        "duplicateTitles": sum(record["duplicateTitle"] for record in records),
        "duplicateDescriptions": sum(record["duplicateDescription"] for record in records),
        "thinContentRisk": sum(record["thinContentRisk"] for record in records),
        "similarity": dict(Counter(record["releaseGallerySimilarity"] for record in records)),
        "technicalErrorPages": sum(bool(record["technicalErrors"]) for record in records),
        "lastmod": dict(Counter(record["lastmodAssessment"] for record in records)),
        "likelyCause": "Google discovery/crawl scheduling lag if technicalErrorPages is zero; Gallery pages were generated as a large, similar URL group.",
    }
    report = {"summary": summary, "records": records}
    output_dir = ROOT / "docs/audits"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "gallery-indexing-2026-09-07-after.json"
    csv_path = output_dir / "gallery-indexing-2026-09-07-after.csv"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    columns = [
        "url", "httpStatus", "redirectCount", "robotsTxtAllowed", "metaRobots", "xRobotsTag",
        "indexable", "canonical", "selfCanonical", "sitemapIncluded", "sitemapLastmod",
        "incomingInternalLinks", "orphan", "galleryHubToDetail", "releaseToGallery", "galleryToRelease",
        "title", "description", "h1Count", "jsonLdTypes", "initialHtmlTextCharacters",
        "thinContentRisk", "titleSimilarity", "descriptionSimilarity", "bodySimilarity",
        "releaseGallerySimilarity", "googlebotStatus", "googlebotMatchesNormal", "technicalErrors",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for record in records:
            writer.writerow({key: record.get(key, "") for key in columns})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if summary["technicalErrorPages"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
