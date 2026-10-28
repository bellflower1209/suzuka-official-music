#!/usr/bin/env python3
"""Audit canonical release state separation and official-source fields."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from release_state import RELEASE_STATUSES, parse_iso8601
from video_migration import NOTICE, undo_migration, video_id


def has_historical_migration_source(item, record, artist):
    """A published work survives an intentional, evidenced channel migration."""
    if not record or not artist:
        return False
    migration = item.get("videoMigration", {})
    channel_id = artist.get("officialYoutubeChannelId")
    channel_url = "https://www.youtube.com/channel/" + str(channel_id)
    if not (
        item.get("status") == "published"
        and not item.get("youtubeUrl")
        and item.get("videoStructuredDataStatus") == "channel-migration"
        and migration.get("status") == record.get("status") == "in-progress"
        and migration.get("reason") == "official-artist-channel-separation"
        and migration.get("notice") == NOTICE
        and record.get("releaseSlug") == item.get("slug")
        and record.get("artistSlug") == item.get("artistSlug") == artist.get("slug")
        and channel_id
        and migration.get("officialChannelId") == record.get("officialChannelId") == channel_id
        and migration.get("officialChannelUrl") == record.get("officialChannelUrl") == channel_url
        and migration.get("previousUrl") == record.get("previousUrl")
        and migration.get("previousVideoId") == record.get("previousVideoId")
        and video_id(record.get("previousUrl")) == record.get("previousVideoId")
        and record.get("oldWatchStatus", {}).get("reason") == "非公開動画"
    ):
        return False
    try:
        original = undo_migration(item, record)
        parse_iso8601(migration["verifiedAt"])
        history = next(h for h in item["videoHistory"] if h["youtubeId"] == record["previousVideoId"])
        parse_iso8601(history["publishedAt"])
        return (
            original["youtubeUrl"] == history["youtubeUrl"] == record["previousUrl"]
            and original["publishedAt"] == item["publishedAt"]
            and original["releaseDate"] == item["releaseDate"]
            and history["historicalPublicationPreserved"] is True
            and history["currentAvailability"] == "private"
        )
    except (AssertionError, KeyError, StopIteration, TypeError, ValueError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    catalog = json.loads((root / "assets/data/releases-catalog.json").read_text(encoding="utf-8"))
    errors = []
    migration_path = root / "docs/channel-migration-20261026.json"
    migrations = json.loads(migration_path.read_text(encoding="utf-8"))["records"] if migration_path.is_file() else []
    migration_by_slug = {record["releaseSlug"]: record for record in migrations}
    artists = {artist["slug"]: artist for artist in cms["artists"]}
    collections = {"releases": cms.get("releases", []), "upcoming": cms.get("upcoming", [])}
    slugs = [item["slug"] for values in collections.values() for item in values]
    if len(slugs) != len(set(slugs)):
        errors.append("duplicate canonical release slug")
    for collection, items in collections.items():
        expected = "published" if collection == "releases" else "upcoming"
        for item in items:
            if item.get("status") not in RELEASE_STATUSES or item.get("status") != expected:
                errors.append(f'{item["slug"]}: invalid state for {collection}: {item.get("status")}')
            timestamp = item.get("publishedAt") if expected == "published" else item.get("scheduledAt")
            try:
                if expected=='published' and item.get('publicationDatePrecision')=='day':
                    date.fromisoformat(timestamp)
                    streaming=item.get('scheduledStreamingRelease') or item.get('streamingRelease') or {}
                    assert not item.get('youtubeUrl') and timestamp==item.get('releaseDate')==streaming.get('releaseDate')
                    assert streaming.get('status')=='published' and str(item.get('officialSource','')).startswith('https://linkco.re/')
                    parse_iso8601(item['promotionVerifiedAt'])
                else:
                    parse_iso8601(timestamp)
            except (TypeError, ValueError, AssertionError, KeyError) as error:
                errors.append(f'{item["slug"]}: invalid timestamp: {error}')
            if expected != "upcoming" or not item.get("releaseDate"):
                has_video = str(item.get("youtubeUrl", "")).startswith("https://www.youtube.com/watch?v=")
                streaming = item.get("scheduledStreamingRelease") or item.get("streamingRelease") or {}
                has_distribution = (
                    streaming.get("status") == "published"
                    and str(streaming.get("linkcoreUrl", "")).startswith("https://linkco.re/")
                )
                has_migration = has_historical_migration_source(
                    item, migration_by_slug.get(item["slug"]), artists.get(item.get("artistSlug"))
                )
                if not (has_video or has_distribution or has_migration):
                    errors.append(f'{item["slug"]}: official YouTube or published LinkCore source missing')
    catalog_published = {item["slug"] for item in catalog["releases"]}
    catalog_upcoming = {item["slug"] for item in catalog["upcoming"]}
    if catalog_published != {item["slug"] for item in collections["releases"]}:
        errors.append("published catalog differs from Creator CMS")
    if catalog_upcoming != {item["slug"] for item in collections["upcoming"]}:
        errors.append("upcoming catalog differs from Creator CMS")
    for item in collections["upcoming"]:
        path = root / f'releases/{item["slug"]}/index.html'
        if not path.is_file() or 'content="noindex, follow"' not in path.read_text(encoding="utf-8"):
            errors.append(f'{item["slug"]}: upcoming page missing or indexable')
        if (root / f'lyrics/{item["slug"]}/index.html').exists():
            errors.append(f'{item["slug"]}: upcoming Lyrics leaked')
    for item in collections["releases"]:
        path = root / f'releases/{item["slug"]}/index.html'
        if not path.is_file():
            errors.append(f'{item["slug"]}: published page missing')
            continue
        if 'content="noindex' in path.read_text(encoding="utf-8").lower():
            errors.append(f'{item["slug"]}: published page remains noindex')
    if errors:
        raise SystemExit("Release state audit failed:\n- " + "\n- ".join(errors))
    print(json.dumps({
        "status": "PASS", "published": len(collections["releases"]),
        "upcoming": len(collections["upcoming"]), "duplicateSlugs": 0,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
