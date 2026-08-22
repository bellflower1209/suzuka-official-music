#!/usr/bin/env python3
"""Audit the current RE:VIVE lineup, member visuals, artist pages and schema."""
from __future__ import annotations

import json
import hashlib
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


EXPECTED = ["白石 陽向", "天城 結衣", "月城 蒼依", "橘 紗良", "星宮 羽音"]
IMAGES = {
    "白石 陽向": "images/revive-hinata-shiraishi-profile.png",
    "天城 結衣": "images/revive-yui-amagi-profile.png",
    "月城 蒼依": "images/revive-aoi-tsukishiro-profile.png",
    "橘 紗良": "images/revive-sara-tachibana-profile.png",
    "星宮 羽音": "images/revive-hanon-hoshimiya-profile.png",
}
BASE = "https://www.suzukaofficial.com/"
SARA_IMAGE_SHA256 = "ebe887062628806c3c22272e6a4718dccce1fe998fd5b3db9055b00b499b3fa4"


def jsonld(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', text, re.S)
    result: list[dict] = []
    for block in blocks:
        value = json.loads(block)
        result.extend(value.get("@graph", [value]))
    return result


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    artists = {item["slug"]: item for item in cms["artists"]}
    revive = artists["revive"]
    actual = [member["name"] for member in revive.get("members", [])]
    if actual != EXPECTED:
        errors.append(f"RE:VIVE member order mismatch: {actual}")
    if any(member["name"] == "星乃みう" for member in revive.get("members", [])):
        errors.append("星乃みう remains in the current RE:VIVE lineup")
    for member in revive.get("members", []):
        expected_image = IMAGES.get(member["name"])
        if member.get("image") != expected_image or not expected_image or not (root / expected_image).is_file():
            errors.append(f'profile image mismatch: {member["name"]}')
        if not member.get("imageAlt") or not member.get("imageWidth") or not member.get("imageHeight"):
            errors.append(f'image metadata missing: {member["name"]}')
    sara_image = root / IMAGES["橘 紗良"]
    if sara_image.is_file() and hashlib.sha256(sara_image.read_bytes()).hexdigest() != SARA_IMAGE_SHA256:
        errors.append("橘紗良 profile image content mismatch")

    hanon = artists.get("hoshimiya-hanon", {})
    if hanon.get("affiliation") != "RE:VIVE" or hanon.get("type") != "Person":
        errors.append("星宮羽音 Person/current affiliation mismatch")
    miu = artists.get("hoshino-miu", {})
    if miu.get("affiliation") != "ASTERIA" or "RE:VIVE" not in miu.get("formerAffiliations", []):
        errors.append("星乃みう current/history affiliation mismatch")
    asteria = artists["asteria"]
    miu_member = next((item for item in asteria.get("members", []) if item["name"] == "星乃みう"), {})
    if miu_member.get("artistSlug") != "hoshino-miu":
        errors.append("ASTERIA member link for 星乃みう is missing")

    for slug, expected_type, affiliation in (
        ("revive", "MusicGroup", None),
        ("asteria", "MusicGroup", None),
        ("hoshimiya-hanon", "Person", "RE:VIVE"),
        ("hoshino-miu", "Person", "ASTERIA"),
    ):
        page = root / f"artists/{slug}/index.html"
        if not page.is_file():
            errors.append(f"missing artist page: {slug}")
            continue
        text = page.read_text(encoding="utf-8")
        if f'<link rel="canonical" href="{BASE}artists/{slug}/"' not in text:
            errors.append(f"canonical mismatch: {slug}")
        if 'content="index, follow"' not in text:
            errors.append(f"indexability mismatch: {slug}")
        graph = jsonld(page)
        entity = next((node for node in graph if node.get("@id") == f"{BASE}artists/{slug}/#artist"), None)
        if not entity or entity.get("@type") != expected_type:
            errors.append(f"JSON-LD artist type mismatch: {slug}")
        if affiliation and (entity or {}).get("memberOf", {}).get("name") != affiliation:
            errors.append(f"JSON-LD memberOf mismatch: {slug}")

    revive_text = (root / "artists/revive/index.html").read_text(encoding="utf-8")
    for member in EXPECTED:
        if member not in revive_text:
            errors.append(f"current member missing from RE:VIVE page: {member}")
    if "星乃みう" in revive_text:
        errors.append("星乃みう appears in current RE:VIVE page")

    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "i": "http://www.google.com/schemas/sitemap-image/1.1"}
    sitemap = {node.text for node in ET.parse(root / "sitemap.xml").findall("s:url/s:loc", namespace)}
    for slug in ("hoshimiya-hanon", "hoshino-miu"):
        if f"{BASE}artists/{slug}/" not in sitemap:
            errors.append(f"sitemap URL missing: {slug}")
    image_locations = {node.text for node in ET.parse(root / "image-sitemap.xml").findall(".//i:loc", namespace)}
    for image in IMAGES.values():
        if f"{BASE}{image}" not in image_locations:
            errors.append(f"image sitemap entry missing: {image}")

    if errors:
        print(json.dumps({"status": "failed", "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({
        "status": "passed",
        "currentMembers": EXPECTED,
        "profileImages": len(IMAGES),
        "artists": len(artists),
        "hanonUrl": f"{BASE}artists/hoshimiya-hanon/",
        "miuAffiliation": "ASTERIA",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
