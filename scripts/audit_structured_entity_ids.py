#!/usr/bin/env python3
"""Audit structured entity IDs, page relationships and canonical domains."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSONLD_RE = re.compile(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
PAGE_TYPES = {"WebPage", "AboutPage", "CollectionPage", "ProfilePage", "SearchResultsPage", "ItemPage"}


def types_of(node: dict) -> set[str]:
    value = node.get("@type", [])
    return {value} if isinstance(value, str) else set(value)


def walk(value: object):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def main() -> None:
    brand = json.loads((ROOT / "assets/data/brand.json").read_text(encoding="utf-8"))
    errors = []
    global_definitions: dict[str, list[tuple[str, tuple]]] = defaultdict(list)
    jsonld_count = 0
    indexable = 0
    for path in sorted(ROOT.glob("**/index.html")):
        text = path.read_text(encoding="utf-8")
        if "noindex" in text.lower():
            continue
        indexable += 1
        relative = str(path.relative_to(ROOT))
        if "github.io" in text:
            errors.append(f"{relative}: old github.io URL")
        canonical_match = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', text, re.I)
        if not canonical_match or not canonical_match.group(1).startswith(brand["officialUrl"]):
            errors.append(f"{relative}: canonical mismatch")
            continue
        canonical = canonical_match.group(1)
        page_ids = []
        local_ids = []
        for raw in JSONLD_RE.findall(text):
            data = json.loads(raw)
            nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
            jsonld_count += 1
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                node_id = node.get("@id")
                if node_id:
                    local_ids.append(node_id)
                    signature = (tuple(sorted(types_of(node))), node.get("name"), node.get("url"), json.dumps(node.get("byArtist"), sort_keys=True, ensure_ascii=False))
                    global_definitions[node_id].append((relative, signature))
                if types_of(node) & PAGE_TYPES:
                    page_ids.append(node_id)
                    if node.get("isPartOf") != {"@id": brand["websiteId"]}:
                        errors.append(f"{relative}: page isPartOf mismatch")
                    if node.get("publisher") != {"@id": brand["organizationId"]}:
                        errors.append(f"{relative}: page publisher mismatch")
                for nested in walk(node):
                    if nested is node:
                        continue
                    if nested.get("@type") == "Organization" and nested.get("name") in {"SUZUKA", brand["brandName"]}:
                        errors.append(f"{relative}: inline duplicate Organization")
        duplicates = {value for value in local_ids if local_ids.count(value) > 1}
        if duplicates:
            errors.append(f"{relative}: duplicate @id {sorted(duplicates)}")
        if len(page_ids) != 1:
            errors.append(f"{relative}: page entity count={len(page_ids)}")
    for entity_id, definitions in global_definitions.items():
        if entity_id in {brand["organizationId"], brand["websiteId"]} and len(definitions) != 1:
            errors.append(f"{entity_id}: definitions={len(definitions)}")
        signatures = {signature for _, signature in definitions}
        if "/releases/" in entity_id and entity_id.endswith("#recording") and len(signatures) > 1:
            errors.append(f"{entity_id}: inconsistent MusicRecording definitions")
    if errors:
        raise SystemExit("\n".join(errors[:80]))
    print(json.dumps({
        "status": "PASS", "indexablePages": indexable, "jsonLdBlocks": jsonld_count,
        "duplicateEntityIds": 0, "canonicalMismatch": 0, "oldGithubIo": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
