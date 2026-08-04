#!/usr/bin/env python3
"""Audit all SUZUKA sitemaps for Google Search Console compatibility."""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


BASE_URL = "https://www.suzukaofficial.com/"
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
IMAGE_NAMESPACE = "http://www.google.com/schemas/sitemap-image/1.1"
VIDEO_NAMESPACE = "http://www.google.com/schemas/sitemap-video/1.1"
XML_DECLARATION = b'<?xml version="1.0" encoding="UTF-8"?>'
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
MAX_URLS = 50_000
MAX_BYTES = 50 * 1024 * 1024
SITEMAPS = {
    "sitemap.xml": "standard",
    "image-sitemap.xml": "image",
    "video-sitemap.xml": "video",
}


def validate_public_url(url: str, label: str) -> list[str]:
    errors: list[str] = []
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "www.suzukaofficial.com":
        errors.append(f"{label}: URL must use the canonical HTTPS host: {url}")
    if not url.startswith(BASE_URL):
        errors.append(f"{label}: URL is outside {BASE_URL}: {url}")
    if parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment:
        errors.append(f"{label}: URL contains forbidden authority, query, or fragment data: {url}")
    return errors


def validate_absolute_https_url(url: str, label: str) -> list[str]:
    errors: list[str] = []
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{label}: URL must be an absolute HTTPS URL: {url}")
    if parsed.username or parsed.password or parsed.fragment:
        errors.append(f"{label}: URL contains forbidden authority or fragment data: {url}")
    return errors


def validate_xml(name: str, data: bytes, sitemap_type: str) -> tuple[dict[str, int], list[str]]:
    errors: list[str] = []
    counts = {"urls": 0, "images": 0, "videos": 0}
    if len(data) > MAX_BYTES:
        errors.append(f"{name}: uncompressed size exceeds 50 MiB")
    if data.startswith(b"\xef\xbb\xbf"):
        errors.append(f"{name}: UTF-8 BOM is not allowed")
    if not data.startswith(XML_DECLARATION):
        errors.append(f"{name}: missing the standard UTF-8 XML declaration")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        return counts, errors + [f"{name}: invalid UTF-8: {error}"]
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        return counts, errors + [f"{name}: XML syntax error: {error}"]

    sitemap_url = f"{{{SITEMAP_NAMESPACE}}}url"
    sitemap_loc = f"{{{SITEMAP_NAMESPACE}}}loc"
    if root.tag != f"{{{SITEMAP_NAMESPACE}}}urlset":
        errors.append(f"{name}: root must be urlset in the Sitemap Protocol namespace")
    url_nodes = list(root)
    counts["urls"] = len(url_nodes)
    if not url_nodes:
        errors.append(f"{name}: urlset is empty")
    if len(url_nodes) > MAX_URLS:
        errors.append(f"{name}: URL count exceeds 50,000")

    page_urls: list[str] = []
    for position, url_node in enumerate(url_nodes, start=1):
        label = f"{name} url[{position}]"
        if url_node.tag != sitemap_url:
            errors.append(f"{label}: unexpected element {url_node.tag}")
            continue
        loc_nodes = url_node.findall(sitemap_loc)
        if len(loc_nodes) != 1 or not (loc_nodes[0].text or "").strip():
            errors.append(f"{label}: exactly one non-empty loc is required")
            continue
        page_url = (loc_nodes[0].text or "").strip()
        page_urls.append(page_url)
        errors.extend(validate_public_url(page_url, label))

        if sitemap_type == "standard":
            if len(list(url_node)) != 1:
                errors.append(f"{label}: standard sitemap entries must contain only loc")
        elif sitemap_type == "image":
            images = url_node.findall(f"{{{IMAGE_NAMESPACE}}}image")
            if not images:
                errors.append(f"{label}: image sitemap entry has no image:image")
            for image_position, image in enumerate(images, start=1):
                image_loc = image.find(f"{{{IMAGE_NAMESPACE}}}loc")
                image_url = (image_loc.text or "").strip() if image_loc is not None else ""
                if not image_url:
                    errors.append(f"{label} image[{image_position}]: image:loc is required")
                else:
                    errors.extend(validate_public_url(image_url, f"{label} image[{image_position}]"))
            counts["images"] += len(images)
        elif sitemap_type == "video":
            videos = url_node.findall(f"{{{VIDEO_NAMESPACE}}}video")
            if not videos:
                errors.append(f"{label}: video sitemap entry has no video:video")
            for video_position, video in enumerate(videos, start=1):
                video_label = f"{label} video[{video_position}]"
                for child_name in ("thumbnail_loc", "title", "description", "publication_date"):
                    child = video.find(f"{{{VIDEO_NAMESPACE}}}{child_name}")
                    if child is None or not (child.text or "").strip():
                        errors.append(f"{video_label}: video:{child_name} is required")
                content = video.find(f"{{{VIDEO_NAMESPACE}}}content_loc")
                player = video.find(f"{{{VIDEO_NAMESPACE}}}player_loc")
                if not any(node is not None and (node.text or "").strip() for node in (content, player)):
                    errors.append(f"{video_label}: content_loc or player_loc is required")
                thumbnail = video.find(f"{{{VIDEO_NAMESPACE}}}thumbnail_loc")
                if thumbnail is not None and (thumbnail.text or "").strip():
                    thumbnail_url = (thumbnail.text or "").strip()
                    errors.extend(validate_absolute_https_url(thumbnail_url, video_label))
                    if urllib.parse.urlsplit(thumbnail_url).netloc == "www.suzukaofficial.com":
                        errors.extend(validate_public_url(thumbnail_url, video_label))
                for location_name, location in (("content_loc", content), ("player_loc", player)):
                    if location is not None and (location.text or "").strip():
                        errors.extend(
                            validate_absolute_https_url((location.text or "").strip(), f"{video_label} {location_name}")
                        )
            counts["videos"] += len(videos)

    if len(page_urls) != len(set(page_urls)):
        errors.append(f"{name}: duplicate page loc values")
    return counts, errors


def fetch(url: str) -> tuple[bytes, str, str, int]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": GOOGLEBOT, "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read(), response.headers.get("Content-Type", ""), response.geturl(), response.status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--remote", action="store_true", help="validate deployed responses as Googlebot")
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []
    summary: dict[str, dict[str, int]] = {}

    for name, sitemap_type in SITEMAPS.items():
        local_data = (root / name).read_bytes()
        counts, local_errors = validate_xml(name, local_data, sitemap_type)
        summary[name] = counts
        errors.extend(local_errors)
        if not args.remote:
            continue
        url = urllib.parse.urljoin(BASE_URL, name)
        try:
            remote_data, content_type, final_url, status = fetch(url)
        except (urllib.error.URLError, TimeoutError) as error:
            errors.append(f"{name}: production fetch failed: {error}")
            continue
        if status != 200:
            errors.append(f"{name}: production returned HTTP {status}")
        if final_url != url:
            errors.append(f"{name}: production redirected to {final_url}")
        if not content_type.lower().startswith(("application/xml", "text/xml")):
            errors.append(f"{name}: production Content-Type is {content_type!r}")
        if remote_data != local_data:
            errors.append(f"{name}: production bytes differ from the repository")
        _, remote_errors = validate_xml(name, remote_data, sitemap_type)
        errors.extend(f"production {error}" for error in remote_errors)

    if errors:
        print("Sitemap compatibility audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    scope = "local and production" if args.remote else "local"
    detail = ", ".join(
        f"{name}: {counts['urls']} URLs/{counts['images']} images/{counts['videos']} videos"
        for name, counts in summary.items()
    )
    print(f"Sitemap compatibility audit passed ({scope}): {detail}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
