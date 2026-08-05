#!/usr/bin/env python3
"""Normalize structured-data dates from verified official YouTube evidence."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

JSONLD_RE = re.compile(
    r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
    re.IGNORECASE | re.DOTALL,
)
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DATETIME_TZ_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})$"
)
DATE_TYPES = {"NewsArticle", "MusicRecording", "WebPage"}


def iter_nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_nodes(child)


def types_of(node: dict) -> set[str]:
    value = node.get("@type", [])
    return set(value if isinstance(value, list) else [value])


def youtube_id(value: str) -> str:
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        return parsed.path.strip("/").split("/")[0]
    if parsed.hostname and "youtube.com" in parsed.hostname:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [""])[0]
        match = re.search(r"/(?:embed|shorts)/([^/?#]+)", parsed.path)
        return match.group(1) if match else ""
    return ""


def video_id_from_node(node: dict) -> str:
    for key in ("contentUrl", "embedUrl", "url"):
        values = node.get(key, [])
        if not isinstance(values, list):
            values = [values]
        for value in values:
            identifier = youtube_id(str(value))
            if identifier:
                return identifier
    return ""


def is_valid_date(value: object) -> bool:
    return isinstance(value, str) and bool(
        ISO_DATE_RE.fullmatch(value) or ISO_DATETIME_TZ_RE.fullmatch(value)
    )


def top_level_jsonld_error(value: object) -> str:
    """Return a Google-facing error for JSON-LD values with no top-level item."""
    if value is None:
        return "top-level item is null"
    if isinstance(value, list):
        if not value:
            return "top-level item list is empty"
        if any(not isinstance(item, dict) for item in value):
            return "top-level item list contains a non-object value"
        return ""
    if not isinstance(value, dict):
        return f"top-level item is {type(value).__name__}, not an object"
    graph = value.get("@graph")
    if graph is not None:
        if not isinstance(graph, list) or not graph:
            return "@graph is not a non-empty list"
        if any(not isinstance(item, dict) for item in graph):
            return "@graph contains a non-object value"
    return ""


def scan(root: Path) -> dict:
    video_count = 0
    invalid_videos = []
    invalid_published = []
    json_errors = []
    invalid_top_level_items = []
    pages_with_invalid_video = set()
    jsonld_count = 0
    for path in sorted(root.glob("**/index.html")):
        relative = path.relative_to(root).as_posix()
        if relative.startswith("admin/"):
            continue
        text = path.read_text(encoding="utf-8")
        for number, match in enumerate(JSONLD_RE.finditer(text), 1):
            jsonld_count += 1
            try:
                data = json.loads(match.group(2))
            except json.JSONDecodeError as error:
                json_errors.append({"page": relative, "block": number, "error": str(error)})
                continue
            top_level_error = top_level_jsonld_error(data)
            if top_level_error:
                invalid_top_level_items.append({
                    "page": relative,
                    "block": number,
                    "error": top_level_error,
                })
                continue
            for node in iter_nodes(data):
                node_types = types_of(node)
                if "VideoObject" in node_types:
                    video_count += 1
                    upload_date = node.get("uploadDate")
                    if not isinstance(upload_date, str) or not ISO_DATETIME_TZ_RE.fullmatch(upload_date):
                        invalid_videos.append({
                            "page": relative,
                            "youtubeId": video_id_from_node(node),
                            "value": upload_date,
                        })
                        pages_with_invalid_video.add(relative)
                if node_types & DATE_TYPES and "datePublished" in node:
                    value = node.get("datePublished")
                    if not is_valid_date(value):
                        invalid_published.append({
                            "page": relative,
                            "types": sorted(node_types & DATE_TYPES),
                            "value": value,
                        })
    return {
        "jsonLdBlocks": jsonld_count,
        "videoObjects": video_count,
        "invalidUploadDates": invalid_videos,
        "invalidUploadDateCount": len(invalid_videos),
        "pagesWithInvalidUploadDate": sorted(pages_with_invalid_video),
        "invalidDatePublished": invalid_published,
        "jsonErrors": json_errors,
        "invalidTopLevelItems": invalid_top_level_items,
        "invalidTopLevelItemCount": len(invalid_top_level_items),
    }


def apply_evidence_to_cms(root: Path, cms: dict) -> tuple[dict, dict[str, dict]]:
    evidence_path = root / "assets/data/youtube-publish-dates.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    by_slug = {item["releaseSlug"]: item for item in evidence["records"]}
    for release in cms["releases"]:
        record = by_slug.get(release["slug"], {})
        verified = record.get("verifiedPublishedAt", "")
        release["videoPublishDate"] = (
            record.get("youtubePublishDate", "")[:10]
            or record.get("youtubeUploadDate", "")[:10]
            or release.get("releaseDate", "")
        )
        release["videoPublishedAt"] = verified
        release["videoPublishedAtSource"] = record.get("verificationSource", "")
        release["videoStructuredDataStatus"] = "published" if verified else "held-date-only"
        release["publishedAt"] = verified or release["videoPublishDate"]
    cms_path = root / "assets/data/creator-cms.json"
    cms_path.write_text(json.dumps(cms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evidence, by_slug


def normalize(root: Path, evidence: dict, by_slug: dict[str, dict]) -> dict:
    report_path = root / "assets/data/structured-data-date-audit.json"
    previous = {}
    if report_path.exists():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
    baseline = previous.get("baseline") or scan(root)
    by_video = {
        record["youtubeId"]: record
        for record in evidence["records"]
        if record.get("youtubeId")
    }
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    releases_by_slug = {item["slug"]: item for item in cms["releases"]}
    releases_by_title = {item["title"]: item for item in cms["releases"]}
    fixed_pages = set()
    fixed_videos = 0
    held = {}

    for path in sorted(root.glob("**/index.html")):
        relative = path.relative_to(root).as_posix()
        if relative.startswith("admin/"):
            continue
        text = path.read_text(encoding="utf-8")

        def replace_block(match: re.Match) -> str:
            nonlocal fixed_videos
            data = json.loads(match.group(2))

            def transform(value):
                nonlocal fixed_videos
                if isinstance(value, list):
                    result = []
                    for child in value:
                        transformed = transform(child)
                        if transformed is not None:
                            result.append(transformed)
                    return result
                if not isinstance(value, dict):
                    return value

                transformed = {key: transform(child) for key, child in value.items()}
                transformed = {key: child for key, child in transformed.items() if child is not None}
                node_types = types_of(transformed)
                if "VideoObject" in node_types:
                    identifier = video_id_from_node(transformed)
                    record = by_video.get(identifier)
                    verified = record.get("verifiedPublishedAt", "") if record else ""
                    if not verified:
                        slug = record.get("releaseSlug", identifier or "unknown") if record else identifier or "unknown"
                        held[slug] = {
                            "releaseSlug": slug,
                            "youtubeId": identifier,
                            "verifiedDate": (
                                (record or {}).get("youtubePublishDate", "")[:10]
                                or (record or {}).get("youtubeUploadDate", "")[:10]
                            ),
                        }
                        return None
                    if transformed.get("uploadDate") != verified:
                        transformed["uploadDate"] = verified
                        fixed_videos += 1
                        fixed_pages.add(relative)
                    release = releases_by_slug.get(record["releaseSlug"], {})
                    if not transformed.get("description") and release.get("description"):
                        transformed["description"] = release["description"]
                        fixed_pages.add(relative)
                if node_types & DATE_TYPES and "datePublished" in transformed:
                    published = transformed.get("datePublished")
                    if not is_valid_date(published):
                        release = releases_by_title.get(str(transformed.get("name", "")))
                        verified = release.get("videoPublishedAt", "") if release else ""
                        if verified:
                            transformed["datePublished"] = verified
                            fixed_pages.add(relative)
                        else:
                            transformed.pop("datePublished", None)
                            fixed_pages.add(relative)
                return transformed

            normalized = transform(data)
            if normalized is None or normalized == []:
                fixed_pages.add(relative)
                return ""
            return match.group(1) + json.dumps(
                normalized, ensure_ascii=False, separators=(",", ":")
            ) + match.group(3)

        updated = JSONLD_RE.sub(replace_block, text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    current = scan(root)
    held_releases = [
        {
            "releaseSlug": record["releaseSlug"],
            "youtubeId": record.get("youtubeId", ""),
            "verifiedDate": (
                record.get("youtubePublishDate", "")[:10]
                or record.get("youtubeUploadDate", "")[:10]
            ),
        }
        for record in evidence["records"]
        if not record.get("verifiedPublishedAt")
    ]
    known_video_ids = {record.get("youtubeId", "") for record in evidence["records"]}
    excluded_video_ids = sorted({
        item.get("youtubeId", "")
        for item in baseline["invalidUploadDates"]
        if item.get("youtubeId") and item.get("youtubeId") not in known_video_ids
    })
    removed_video_count = max(0, baseline["videoObjects"] - current["videoObjects"])
    baseline_valid_count = baseline["videoObjects"] - baseline["invalidUploadDateCount"]
    report = {
        "schemaVersion": "1.0",
        "evidenceCheckedAt": evidence["checkedAt"],
        "officialChannelId": evidence["officialChannelId"],
        "baseline": baseline,
        "current": current,
        "fixedPages": sorted(
            set(baseline["pagesWithInvalidUploadDate"])
            - set(current["pagesWithInvalidUploadDate"])
        ),
        "fixedPageCount": len(
            set(baseline["pagesWithInvalidUploadDate"])
            - set(current["pagesWithInvalidUploadDate"])
        ),
        "resolvedInvalidVideoObjectCount": (
            baseline["invalidUploadDateCount"] - current["invalidUploadDateCount"]
        ),
        "fixedVideoObjectCount": max(0, current["videoObjects"] - baseline_valid_count),
        "removedUnverifiedVideoObjectCount": removed_video_count,
        "excludedUnverifiedVideoIds": excluded_video_ids,
        "heldReleases": held_releases,
        "heldReleaseCount": len(held_releases),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
