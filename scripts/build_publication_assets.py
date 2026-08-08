#!/usr/bin/env python3
"""Generate standards-based feed, image sitemap, video sitemap and discovery links."""
from __future__ import annotations

import argparse
import html
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from PIL import Image as PillowImage

from structured_data_dates import JSONLD_RE, iter_nodes, types_of, video_id_from_node

BASE = "https://www.suzukaofficial.com/"
ATOM = "http://www.w3.org/2005/Atom"
SITEMAP = "http://www.sitemaps.org/schemas/sitemap/0.9"
IMAGE = "http://www.google.com/schemas/sitemap-image/1.1"
VIDEO = "http://www.google.com/schemas/sitemap-video/1.1"
ET.register_namespace("", ATOM)


def local_path_from_public_url(root: Path, public_path: str) -> Path | None:
    """Map a same-origin public URL path to a repository file."""
    base_path = urlparse(BASE).path
    if not public_path.startswith(base_path):
        return None
    relative = public_path[len(base_path):].lstrip("/")
    return root / relative


class ImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.images: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "img":
            return
        values = dict(attrs)
        if values.get("src"):
            self.images.append((values["src"] or "", values.get("alt") or ""))


def xml_write(path: Path, root: ET.Element, *, standard_declaration: bool = False) -> None:
    ET.indent(root, space="  ")
    if standard_declaration:
        body = ET.tostring(root, encoding="utf-8", xml_declaration=False)
        data = b'<?xml version="1.0" encoding="UTF-8"?>\n' + body
    else:
        data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    path.write_bytes(data + b"\n")


def public_pages(root: Path) -> list[tuple[Path, str]]:
    pages = []
    for path in sorted(root.glob("**/index.html")):
        text = path.read_text(encoding="utf-8")
        if re.search(r'<meta[^>]+name="robots"[^>]+content="[^"]*noindex', text, re.I):
            continue
        canonical = re.findall(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', text, re.I)
        if len(canonical) == 1:
            pages.append((path, canonical[0]))
    return pages


def inject_feed_discovery(root: Path) -> None:
    pattern = re.compile(r'\s*<link[^>]+type="application/atom\+xml"[^>]*>\s*', re.I)
    for path in sorted(root.glob("**/index.html")):
        relative = path.relative_to(root)
        if relative.parts[0] == "admin":
            continue
        text = pattern.sub("", path.read_text(encoding="utf-8"))
        depth = len(relative.parts) - 1
        prefix = "../" * depth
        link = f'<link rel="alternate" type="application/atom+xml" title="SUZUKA Updates" href="{prefix}feed.xml"/>'
        text = text.replace("</head>", link + "</head>", 1)
        path.write_text(text, encoding="utf-8")


def normalize_image_markup(root: Path) -> None:
    """Add intrinsic dimensions to prevent layout shifts without changing artwork."""
    pattern = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
    for path in sorted(root.glob("**/index.html")):
        text = path.read_text(encoding="utf-8")

        def replace(match: re.Match) -> str:
            tag = match.group(0)
            if re.search(r"\bwidth=", tag, re.I) and re.search(r"\bheight=", tag, re.I):
                return tag
            source = re.search(r'\bsrc=["\']([^"\']*)["\']', tag, re.I)
            src = html.unescape(source.group(1)) if source else ""
            width, height = 1280, 720
            if "i.ytimg.com" in src and "/hqdefault." in src:
                width, height = 480, 360
            elif src:
                parsed = urlparse(src)
                local = None
                if parsed.scheme in {"http", "https"} and parsed.netloc == urlparse(BASE).netloc:
                    local = local_path_from_public_url(root, parsed.path)
                elif not parsed.scheme and not parsed.netloc:
                    local = (path.parent / parsed.path).resolve()
                if local and local.is_file():
                    with PillowImage.open(local) as image:
                        width, height = image.size
            dimensions = f' width="{width}" height="{height}"'
            return tag[:-2] + dimensions + "/>" if tag.endswith("/>") else tag[:-1] + dimensions + ">"

        updated = pattern.sub(replace, text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def build_feed(root: Path, cms: dict) -> None:
    feed = ET.Element(f"{{{ATOM}}}feed")
    ET.SubElement(feed, f"{{{ATOM}}}id").text = BASE
    ET.SubElement(feed, f"{{{ATOM}}}title").text = "SUZUKA Official Music Updates"
    ET.SubElement(feed, f"{{{ATOM}}}updated").text = cms["updatedAt"]
    ET.SubElement(feed, f"{{{ATOM}}}link", {"rel": "self", "href": f"{BASE}feed.xml"})
    ET.SubElement(feed, f"{{{ATOM}}}link", {"rel": "alternate", "href": BASE})
    author = ET.SubElement(feed, f"{{{ATOM}}}author")
    ET.SubElement(author, f"{{{ATOM}}}name").text = "SUZUKA"

    rows = []
    for item in cms["releases"]:
        rows.append((item["publishedAt"], "release", item))
    for item in cms["news"]:
        if item.get("status") == "published":
            rows.append((item.get("publishedAt", cms["updatedAt"]), "news", item))
    for item in cms["upcoming"]:
        rows.append((cms["updatedAt"], "upcoming", item))
    for item in cms["releases"]:
        if item.get("lyricsAvailable") and item.get("lyricsVerified") is True and item.get("lyricsVerifiedAt"):
            rows.append((item["lyricsVerifiedAt"], "lyrics", item))
    photobooks_path = root / "assets/data/photobooks.json"
    if photobooks_path.exists():
        photobooks = json.loads(photobooks_path.read_text(encoding="utf-8"))
        for item in photobooks.get("photobooks", []):
            if item.get("status") == "published" and item.get("publishedAt") and item.get("noteUrl"):
                rows.append((item["publishedAt"], "photobook", item))
    rows.sort(key=lambda row: (row[0], row[1], row[2]["slug"]), reverse=True)

    for timestamp, kind, item in rows:
        entry = ET.SubElement(feed, f"{{{ATOM}}}entry")
        if kind == "release":
            url = f'{BASE}{item["releaseUrl"]}'
            title = f'{item["artist"]}「{item["title"]}」'
            summary = item["description"]
            ET.SubElement(entry, f"{{{ATOM}}}published").text = item["publishedAt"]
        elif kind == "news":
            url = f'{BASE}news/{item["slug"]}/'
            title = item["title"]
            summary = item["description"]
            if "T" in item.get("publishedAt", ""):
                ET.SubElement(entry, f"{{{ATOM}}}published").text = item["publishedAt"]
        elif kind == "lyrics":
            url = f'{BASE}lyrics/{item["slug"]}/'
            title = f'公式歌詞｜{item["artist"]}「{item["title"]}」'
            summary = f'{item["artist"]}「{item["title"]}」の出典確認済み公式歌詞。'
            ET.SubElement(entry, f"{{{ATOM}}}published").text = item["lyricsVerifiedAt"]
        elif kind == "photobook":
            url = f'{BASE}photobooks/{item["slug"]}/'
            title = item["title"]
            summary = item.get("description") or "SUZUKA公式AIアーティストのVisual Collection。"
            ET.SubElement(entry, f"{{{ATOM}}}published").text = item["publishedAt"]
        else:
            url = item["youtubeUrl"]
            title = f'Upcoming｜{item["artist"]}「{item["title"]}」'
            summary = f'{item["scheduledAt"]} 公開予定。公開済み作品とは分離しています。'
        ET.SubElement(entry, f"{{{ATOM}}}id").text = url
        ET.SubElement(entry, f"{{{ATOM}}}title").text = title
        ET.SubElement(entry, f"{{{ATOM}}}updated").text = timestamp
        ET.SubElement(entry, f"{{{ATOM}}}link", {"href": url})
        ET.SubElement(entry, f"{{{ATOM}}}category", {"term": kind})
        ET.SubElement(entry, f"{{{ATOM}}}summary").text = summary
    xml_write(root / "feed.xml", feed)


def build_image_sitemap(root: Path) -> int:
    ET.register_namespace("", SITEMAP)
    ET.register_namespace("image", IMAGE)
    urlset = ET.Element(f"{{{SITEMAP}}}urlset")
    total = 0
    for path, canonical in public_pages(root):
        parser = ImageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        local_images = []
        for src, alt in parser.images:
            absolute = urljoin(canonical, src)
            parsed = urlparse(absolute)
            if parsed.netloc != urlparse(BASE).netloc:
                continue
            local = local_path_from_public_url(root, parsed.path)
            if local and local.is_file():
                local_images.append((absolute, alt))
        unique = list(dict.fromkeys(local_images))
        if not unique:
            continue
        url = ET.SubElement(urlset, f"{{{SITEMAP}}}url")
        ET.SubElement(url, f"{{{SITEMAP}}}loc").text = canonical
        for image_url, alt in unique:
            image = ET.SubElement(url, f"{{{IMAGE}}}image")
            ET.SubElement(image, f"{{{IMAGE}}}loc").text = image_url
            if alt:
                ET.SubElement(image, f"{{{IMAGE}}}title").text = alt
            total += 1
    xml_write(root / "image-sitemap.xml", urlset, standard_declaration=True)
    return total


def build_video_sitemap(root: Path) -> int:
    ET.register_namespace("", SITEMAP)
    ET.register_namespace("video", VIDEO)
    urlset = ET.Element(f"{{{SITEMAP}}}urlset")
    total = 0
    for path, canonical in public_pages(root):
        text = path.read_text(encoding="utf-8")
        videos = []
        for match in JSONLD_RE.finditer(text):
            data = json.loads(match.group(2))
            videos.extend(node for node in iter_nodes(data) if "VideoObject" in types_of(node))
        if not videos:
            continue
        url = ET.SubElement(urlset, f"{{{SITEMAP}}}url")
        ET.SubElement(url, f"{{{SITEMAP}}}loc").text = canonical
        for node in videos:
            video = ET.SubElement(url, f"{{{VIDEO}}}video")
            thumbnail_value = node["thumbnailUrl"]
            if isinstance(thumbnail_value, list):
                thumbnail_url = next((str(value) for value in thumbnail_value if str(value).strip()), "")
            else:
                thumbnail_url = str(thumbnail_value)
            if not thumbnail_url:
                raise ValueError(f"VideoObject has no usable thumbnailUrl: {canonical}")
            ET.SubElement(video, f"{{{VIDEO}}}thumbnail_loc").text = thumbnail_url
            ET.SubElement(video, f"{{{VIDEO}}}title").text = str(node["name"])[:100]
            ET.SubElement(video, f"{{{VIDEO}}}description").text = str(node["description"])[:2048]
            if node.get("contentUrl"):
                ET.SubElement(video, f"{{{VIDEO}}}content_loc").text = str(node["contentUrl"])
            elif node.get("embedUrl"):
                ET.SubElement(video, f"{{{VIDEO}}}player_loc").text = str(node["embedUrl"])
            ET.SubElement(video, f"{{{VIDEO}}}publication_date").text = str(node["uploadDate"])
            if node.get("duration"):
                match = re.fullmatch(r"PT(?:(\d+)M)?(?:(\d+)S)?", str(node["duration"]))
                if match:
                    seconds = int(match.group(1) or 0) * 60 + int(match.group(2) or 0)
                    if seconds:
                        ET.SubElement(video, f"{{{VIDEO}}}duration").text = str(seconds)
            identifier = video_id_from_node(node)
            if identifier:
                ET.SubElement(video, f"{{{VIDEO}}}tag").text = "SUZUKA"
            total += 1
    xml_write(root / "video-sitemap.xml", urlset, standard_declaration=True)
    return total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    normalize_image_markup(root)
    inject_feed_discovery(root)
    build_feed(root, cms)
    images = build_image_sitemap(root)
    videos = build_video_sitemap(root)
    expected_robots = (
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: {BASE}sitemap.xml\n"
    )
    if (root / "robots.txt").read_text(encoding="utf-8") != expected_robots:
        raise RuntimeError("robots.txt differs from the approved public policy")
    feed = ET.parse(root / "feed.xml").getroot()
    print(json.dumps({"feedEntries": len(feed.findall(f'{{{ATOM}}}entry')), "images": images, "videos": videos}))


if __name__ == "__main__":
    main()
