#!/usr/bin/env python3
"""Safely sync official YouTube release state and derived Lyrics publication."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_changed_content import apply_transaction, compare, copy_source, run_generator
from release_state import youtube_state_allows_publish


JST = ZoneInfo("Asia/Tokyo")
AUDITS = (
    "audit_release_automation.py",
    "audit_release_state.py",
    "audit_lyrics_publish_state.py",
    "audit_holds.py",
    "audit_public_counts.py",
    "audit_growth_routes.py",
    "audit_analytics.py",
    "audit_seo.py",
    "audit_structured_entity_ids.py",
    "audit_rich_results.py",
    "validate_sitemap.py",
    "audit_sitemaps.py",
    "audit_feed.py",
    "audit_indexnow.py",
    "audit_dashboard.py",
    "audit_actions_node24.py",
)


def indexnow_candidates(stage: Path, changed: list[str], deleted: list[str]) -> list[str]:
    candidates = []
    for name in [*changed, *deleted]:
        if name != "index.html" and not name.endswith("/index.html"):
            continue
        if name.startswith("admin/"):
            continue
        path = stage / name
        if path.is_file() and 'content="noindex' in path.read_text(encoding="utf-8"):
            continue
        route = "" if name == "index.html" else name.removesuffix("index.html")
        candidates.append(f"https://www.suzukaofficial.com/{route}")
    return sorted(set(candidates))


def atomic_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_youtube(url: str, executable: str) -> dict:
    result = subprocess.run(
        [executable, "--ignore-no-formats-error", "--skip-download", "--dump-single-json", url],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"Official YouTube check failed for {url}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def load_evidence(cms: dict, evidence_file: Path | None, executable: str) -> dict[str, dict]:
    if evidence_file:
        source = json.loads(evidence_file.read_text(encoding="utf-8"))
        entries = source.get("entries", source)
        if isinstance(entries, list):
            return {item["id"]: item for item in entries}
        return dict(entries)
    result = {}
    for item in cms.get("upcoming", []):
        video_id = item["youtubeUrl"].split("v=", 1)[-1].split("&", 1)[0]
        result[video_id] = fetch_youtube(item["youtubeUrl"], executable)
    return result


def published_record(item: dict, evidence: dict, cms: dict, now: datetime) -> dict:
    timestamp = evidence.get("actual_start_timestamp") or evidence.get("release_timestamp")
    published_at = datetime.fromtimestamp(int(timestamp), JST).isoformat(timespec="seconds")
    artist = next(record for record in cms["artists"] if record["slug"] == item["artistSlug"])
    image = item.get("image", "")
    genres = list(item.get("genres", []))
    themes = list(item.get("themes", []))
    tags = list(dict.fromkeys([*item.get("tags", []), *genres, *themes]))
    description = str(item.get("description", "")).replace("公開予定", "")
    canonical = {key: value for key, value in item.items() if key not in {"scheduledAt", "note"}}
    return {
        **canonical,
        "id": item["slug"],
        "displayTitle": item["title"],
        "englishTitle": item.get("englishTitle", item["title"]),
        "artistSlugs": [item["artistSlug"]],
        "artistType": artist["type"],
        "releaseAt": published_at,
        "releaseDate": published_at[:10],
        "releaseYear": int(published_at[:4]),
        "releaseType": item.get("releaseType", "single"),
        "genres": genres,
        "moods": list(item.get("moods", [])),
        "themes": themes,
        "tags": tags,
        "language": item.get("language", "ja"),
        "coverImage": image,
        "coverAlt": f'{item["artist"]}「{item["title"]}」公式YouTubeサムネイル',
        "releaseUrl": f'releases/{item["slug"]}/',
        "newsUrl": item.get("newsUrl", ""),
        "duration": int(evidence["duration"]),
        "status": "published",
        "featured": bool(item.get("featured", False)),
        "recommendationWeight": int(item.get("recommendationWeight") or 1),
        "weeklyPickEligible": True,
        "analyticsEnabled": True,
        "upcomingPriority": 0,
        "relatedReleases": list(item.get("relatedReleases", [])),
        "searchKeywords": list(dict.fromkeys([item["title"], item["artist"], *tags])),
        "aiArtistType": "fictional AI artist",
        "publishedAt": published_at,
        "description": description,
        "introduction": description,
        "galleryImages": list(item.get("galleryImages", [])),
        "galleryPublished": bool(item.get("galleryPublished", False)),
        "productionNote": str(item.get("productionNote") or description).replace("公開予定", ""),
        "seo": {
            "title": f'{item["title"]}｜{item["artist"]}｜SUZUKA Official Music',
            "description": f'{description} SUZUKAの架空のAIアーティスト作品です。',
            "jsonLdEnabled": True,
        },
        "videoPublishDate": published_at[:10],
        "videoPublishedAt": published_at,
        "videoPublishedAtSource": "official-youtube-liveBroadcastDetails.startTimestamp",
        "videoStructuredDataStatus": "published",
        "officialSource": item["youtubeUrl"],
        "promotionVerifiedAt": now.isoformat(timespec="seconds"),
    }


def update_youtube_publish_dates(
    stage: Path,
    cms: dict,
    evidence: dict[str, dict],
    promoted: list[str],
    now: datetime,
) -> None:
    """Persist the verified YouTube timestamp used by structured-data generation."""
    if not promoted:
        return
    path = stage / "assets/data/youtube-publish-dates.json"
    source = json.loads(path.read_text(encoding="utf-8"))
    records = {
        (item["releaseSlug"], item.get("youtubeId", "")): item
        for item in source["records"]
    }
    upcoming_by_slug = {item["slug"]: item for item in cms.get("upcoming", [])}
    for slug in promoted:
        item = upcoming_by_slug[slug]
        video_id = item["youtubeUrl"].split("v=", 1)[-1].split("&", 1)[0]
        current = evidence[video_id]
        timestamp = current.get("actual_start_timestamp") or current.get("release_timestamp")
        published_at = datetime.fromtimestamp(int(timestamp), JST).isoformat(timespec="seconds")
        records[(slug, video_id)] = {
            "releaseSlug": slug,
            "youtubeId": video_id,
            "youtubeUrl": item["youtubeUrl"],
            "catalogReleaseDate": published_at[:10],
            "officialTitle": current.get("title") or item["title"],
            "channelId": current.get("channel_id"),
            "channelVerified": current.get("channel_id") == cms["site"]["youtubeChannelId"],
            "youtubePublishDate": published_at,
            "youtubeUploadDate": published_at,
            "liveStartTimestamp": published_at,
            "playabilityStatus": "OK",
            "durationSeconds": int(current["duration"]),
            "verifiedPublishedAt": published_at,
            "verificationSource": "official-youtube-liveBroadcastDetails.startTimestamp",
            "status": "verified-datetime",
        }
    source["checkedAt"] = now.isoformat(timespec="seconds")
    source["records"] = sorted(
        records.values(), key=lambda item: (item["releaseSlug"], item.get("youtubeId", ""))
    )
    atomic_json(path, source)


def apply_release_state(stage: Path, evidence: dict[str, dict], now: datetime) -> list[str]:
    cms_path = stage / "assets/data/creator-cms.json"
    cms = json.loads(cms_path.read_text(encoding="utf-8"))
    official_channel_id = cms["site"]["youtubeChannelId"]
    promoted: list[str] = []
    remaining = []
    releases = {item["slug"]: item for item in cms["releases"]}
    normalized = False
    for record in releases.values():
        if record.get("status") != "published" or not record.get("promotionVerifiedAt"):
            continue
        before = json.dumps(record, ensure_ascii=False, sort_keys=True)
        record.pop("scheduledAt", None)
        record.pop("note", None)
        for field in ("description", "introduction", "productionNote"):
            if field in record:
                record[field] = str(record[field]).replace("公開予定", "")
        if isinstance(record.get("seo"), dict) and "description" in record["seo"]:
            record["seo"]["description"] = str(record["seo"]["description"]).replace("公開予定", "")
        normalized = normalized or before != json.dumps(record, ensure_ascii=False, sort_keys=True)
    evidence_log = []
    for item in cms.get("upcoming", []):
        video_id = item["youtubeUrl"].split("v=", 1)[-1].split("&", 1)[0]
        current = evidence.get(video_id)
        if not current:
            raise RuntimeError(f"YouTube evidence missing for upcoming release: {item['slug']}")
        evidence_log.append({
            "slug": item["slug"],
            "videoId": video_id,
            "availability": current.get("availability"),
            "liveStatus": current.get("live_status"),
            "releaseTimestamp": current.get("release_timestamp"),
            "channelId": current.get("channel_id"),
        })
        if youtube_state_allows_publish(item, current, now=now, official_channel_id=official_channel_id):
            releases[item["slug"]] = published_record(item, current, cms, now)
            promoted.append(item["slug"])
        else:
            remaining.append(item)
    if promoted or normalized:
        cms["releases"] = sorted(
            releases.values(),
            key=lambda item: (item.get("publishedAt", item.get("releaseDate", "")), item["slug"]),
            reverse=True,
        )
        cms["upcoming"] = sorted(remaining, key=lambda item: (item["scheduledAt"], item["slug"]))
        cms["updatedAt"] = now.isoformat(timespec="seconds")
        atomic_json(cms_path, cms)
        if promoted:
            atomic_json(stage / "assets/data/official-youtube-release-state.json", {
                "schemaVersion": "1.0",
                "verifiedAt": now.isoformat(timespec="seconds"),
                "officialChannelId": official_channel_id,
                "promoted": promoted,
                "evidence": evidence_log,
            })
    return promoted


def run_audits(root: Path) -> None:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    for name in AUDITS:
        subprocess.run([sys.executable, str(root / "scripts" / name)], cwd=root, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--now", help="ISO 8601 timestamp with timezone; defaults to current JST")
    parser.add_argument("--evidence-file", type=Path, help="Validated yt-dlp JSON fixture for offline testing")
    parser.add_argument("--yt-dlp", default="yt-dlp")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.now:
        parsed_now = datetime.fromisoformat(args.now)
        if parsed_now.tzinfo is None or parsed_now.utcoffset() is None:
            raise SystemExit("--now requires a timezone")
        now = parsed_now.astimezone(JST)
    else:
        now = datetime.now(JST)
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    evidence = load_evidence(cms, args.evidence_file, args.yt_dlp)
    with tempfile.TemporaryDirectory(prefix="suzuka-release-sync-") as tmp:
        stage = Path(tmp) / "site"
        copy_source(root, stage)
        promoted = apply_release_state(stage, evidence, now)
        update_youtube_publish_dates(stage, cms, evidence, promoted, now)
        run_generator(stage)
        run_audits(stage)
        changed, deleted, digest = compare(root, stage)
        if not args.dry_run and (changed or deleted):
            apply_transaction(root, stage, changed, deleted)
        result = {
            "status": "dry-run" if args.dry_run else "applied",
            "checkedAt": now.isoformat(timespec="seconds"),
            "promoted": promoted,
            "upcomingChecked": len(cms.get("upcoming", [])),
            "changedCount": len(changed),
            "deletedCount": len(deleted),
            "changedFiles": changed,
            "deletedFiles": deleted,
            "indexNowCandidates": indexnow_candidates(stage, changed, deleted),
            "sha256": digest,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
