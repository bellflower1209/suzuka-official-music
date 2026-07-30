#!/usr/bin/env python3
"""Local Rich Results-equivalent audit for SUZUKA structured data."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from structured_data_dates import (
    ISO_DATETIME_TZ_RE,
    JSONLD_RE,
    iter_nodes,
    scan,
    types_of,
    video_id_from_node,
)

REQUIRED_VIDEO = ("name", "description", "thumbnailUrl", "uploadDate")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    evidence = json.loads((root / "assets/data/youtube-publish-dates.json").read_text(encoding="utf-8"))
    evidence_by_video = {item["youtubeId"]: item for item in evidence["records"]}
    upcoming_ids = {
        re.search(r"(?:v=|youtu\.be/)([\w-]+)", item.get("youtubeUrl", "")).group(1)
        for item in cms["upcoming"]
        if re.search(r"(?:v=|youtu\.be/)([\w-]+)", item.get("youtubeUrl", ""))
    }
    errors = []
    metrics = scan(root)
    errors.extend(f"JSON-LD syntax: {item}" for item in metrics["jsonErrors"])
    errors.extend(f"invalid uploadDate: {item}" for item in metrics["invalidUploadDates"])
    errors.extend(f"invalid datePublished: {item}" for item in metrics["invalidDatePublished"])
    video_count = 0

    for path in sorted(root.glob("**/index.html")):
        relative = path.relative_to(root).as_posix()
        if relative.startswith("admin/"):
            continue
        text = path.read_text(encoding="utf-8")
        canonical = re.findall(r'<link\s+rel="canonical"\s+href="([^"]+)"', text)
        if len(canonical) != 1:
            errors.append(f"{relative}: canonical count {len(canonical)}")
        if canonical and ("?" in canonical[0] or "#" in canonical[0]):
            errors.append(f"{relative}: canonical contains parameters")
        seen_videos = set()
        for block in JSONLD_RE.finditer(text):
            data = json.loads(block.group(2))
            for node in iter_nodes(data):
                if "VideoObject" not in types_of(node):
                    continue
                video_count += 1
                missing = [key for key in REQUIRED_VIDEO if not node.get(key)]
                if missing:
                    errors.append(f"{relative}: VideoObject missing {','.join(missing)}")
                if not node.get("contentUrl") and not node.get("embedUrl"):
                    errors.append(f"{relative}: VideoObject missing contentUrl/embedUrl")
                identifier = video_id_from_node(node)
                if not identifier:
                    errors.append(f"{relative}: VideoObject YouTube ID missing")
                    continue
                if identifier in seen_videos:
                    errors.append(f"{relative}: duplicate VideoObject {identifier}")
                seen_videos.add(identifier)
                if identifier in upcoming_ids:
                    errors.append(f"{relative}: upcoming video exposed {identifier}")
                record = evidence_by_video.get(identifier)
                if not record or record.get("status") != "verified-datetime":
                    errors.append(f"{relative}: unverified public VideoObject {identifier}")
                elif node.get("uploadDate") != record.get("verifiedPublishedAt"):
                    errors.append(f"{relative}: uploadDate differs from official evidence {identifier}")
                if not ISO_DATETIME_TZ_RE.fullmatch(str(node.get("uploadDate", ""))):
                    errors.append(f"{relative}: uploadDate lacks ISO timezone {identifier}")

    sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_urls = re.findall(r"<loc>(.*?)</loc>", sitemap)
    if (
        "googletagmanager" in sitemap
        or "google-analytics" in sitemap
        or any("?" in url or "#" in url for url in sitemap_urls)
    ):
        errors.append("sitemap contains analytics URL or query parameters")
    if video_count != metrics["videoObjects"]:
        errors.append("VideoObject count mismatch")

    result = {
        "status": "PASS" if not errors else "FAIL",
        "jsonLdBlocks": metrics["jsonLdBlocks"],
        "videoObjects": video_count,
        "invalidUploadDates": metrics["invalidUploadDateCount"],
        "invalidDatePublished": len(metrics["invalidDatePublished"]),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
