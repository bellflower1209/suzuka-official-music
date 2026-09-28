#!/usr/bin/env python3
"""Verify the public label/contact evidence needed for Spotify Label Team review."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSONLD_RE = re.compile(
    r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def main() -> None:
    brand = json.loads((ROOT / "assets/data/brand.json").read_text(encoding="utf-8"))
    about = (ROOT / "about/index.html").read_text(encoding="utf-8")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    visible = html.unescape(re.sub(r"<[^>]+>", " ", about))
    visible = re.sub(r"\s+", " ", visible)
    email = brand["officialContactEmail"]
    errors: list[str] = []

    for expected in (
        brand["labelName"],
        brand["labelDescriptor"],
        "Record Label",
        "Official Contact",
        email,
        "SUZUKAは、音楽作品の企画・制作・リリースを行う独立系音楽レーベル／音楽プロジェクトです。",
        f"レーベル名：{brand['labelName']}",
        f"公式連絡先： {email}",
    ):
        if expected not in visible:
            errors.append(f"visible text missing: {expected}")

    if f'href="mailto:{email}"' not in about:
        errors.append("mailto link missing")
    if '<meta name="robots" content="index, follow"' not in about or "noindex" in about.lower():
        errors.append("About page is not indexable")
    if '<link rel="canonical" href="https://www.suzukaofficial.com/about/"' not in about:
        errors.append("About canonical missing")
    if "User-agent: *" not in robots or "Allow: /" not in robots:
        errors.append("robots.txt does not allow public crawling")
    if "https://www.suzukaofficial.com/about/" not in sitemap:
        errors.append("About page missing from sitemap")

    nodes: list[dict] = []
    for raw in JSONLD_RE.findall((ROOT / "index.html").read_text(encoding="utf-8")):
        data = json.loads(raw)
        nodes.extend(data.get("@graph", [data]))
    organization = next(
        (node for node in nodes if isinstance(node, dict) and node.get("@id") == brand["organizationId"]),
        None,
    )
    if not organization:
        errors.append("Home Organization JSON-LD missing")
    else:
        if organization.get("email") != email:
            errors.append("Organization JSON-LD email mismatch")
        if organization.get("contactPoint", {}).get("email") != email:
            errors.append("Organization ContactPoint email mismatch")

    if errors:
        raise SystemExit("\n".join(errors))
    print(json.dumps({
        "status": "PASS",
        "publicUrl": "https://www.suzukaofficial.com/about/#official-contact",
        "label": brand["labelName"],
        "descriptor": brand["labelDescriptor"],
        "officialContact": email,
        "mailto": True,
        "indexable": True,
        "structuredData": True,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
