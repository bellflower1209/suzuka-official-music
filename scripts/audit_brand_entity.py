#!/usr/bin/env python3
"""Audit SUZUKA Brand Discovery 1.1 identity consistency."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
JSONLD_RE = re.compile(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)


def nodes(path: Path) -> list[dict]:
    result = []
    for raw in JSONLD_RE.findall(path.read_text(encoding="utf-8")):
        data = json.loads(raw)
        result.extend(data.get("@graph", [data]) if isinstance(data, dict) else data)
    return [node for node in result if isinstance(node, dict)]


def main() -> None:
    brand = json.loads((ROOT / "assets/data/brand.json").read_text(encoding="utf-8"))
    cms = json.loads((ROOT / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    about = (ROOT / "about/index.html").read_text(encoding="utf-8")
    errors = []
    home_nodes = nodes(ROOT / "index.html")
    website = [node for node in home_nodes if node.get("@type") == "WebSite"]
    organizations = [node for node in home_nodes if node.get("@type") == "Organization"]
    if len(website) != 1:
        errors.append(f"Home WebSite definitions={len(website)}")
    elif any((website[0].get("name") != brand["brandName"], website[0].get("alternateName") != brand["alternateNames"], website[0].get("@id") != brand["websiteId"])):
        errors.append("Home WebSite identity mismatch")
    if len(organizations) != 1:
        errors.append(f"Home Organization definitions={len(organizations)}")
    else:
        organization = organizations[0]
        expected_same_as = [item["url"] for item in brand["sameAs"]]
        if organization.get("name") != brand["brandName"] or organization.get("@id") != brand["organizationId"]:
            errors.append("Home Organization identity mismatch")
        if organization.get("sameAs") != expected_same_as:
            errors.append("Organization sameAs mismatch")
        forbidden = {"address", "telephone", "email", "foundingDate", "taxID", "legalName"}
        if forbidden & organization.keys():
            errors.append(f"unverified Organization fields: {sorted(forbidden & organization.keys())}")
    for profile in brand["sameAs"]:
        if urlparse(profile["url"]).scheme != "https" or not profile.get("verifiedProfileName"):
            errors.append(f"unverified sameAs entry: {profile}")
    if '<meta property="og:site_name" content="SUZUKA Official"' not in home:
        errors.append("Home og:site_name mismatch")
    if "<title>SUZUKA Official | Original AI Music Project</title>" not in home:
        errors.append("Home title mismatch")
    if "SUZUKA Official · Original AI Music Project" not in home:
        errors.append("Home visible brand descriptor missing")
    if "BRAND-V11:ABOUT-ENTITY:START" not in about or "本サイトのSUZUKAは" not in about:
        errors.append("About entity source missing")
    manifest = json.loads((ROOT / "site.webmanifest").read_text(encoding="utf-8"))
    if manifest.get("name") != brand["brandName"] or manifest.get("short_name") != brand["shortName"]:
        errors.append("manifest brand mismatch")
    brand_profiles = {item["url"] for item in brand["sameAs"]}
    for artist in cms["artists"]:
        path = ROOT / f'artists/{artist["slug"]}/index.html'
        source = path.read_text(encoding="utf-8")
        entity = next((node for node in nodes(path) if node.get("name") == artist["name"] and node.get("@type") in {"Person", "MusicGroup"}), None)
        if not entity or entity.get("@type") != artist["type"]:
            errors.append(f'{artist["slug"]}: artist type mismatch')
        if entity and set(entity.get("sameAs", [])) & brand_profiles:
            errors.append(f'{artist["slug"]}: brand profile incorrectly used as artist sameAs')
        if 'href="../../about/">About SUZUKA' not in source:
            errors.append(f'{artist["slug"]}: About SUZUKA link missing')
    non_home_website = []
    for path in ROOT.glob("**/index.html"):
        if path == ROOT / "index.html":
            continue
        if any(node.get("@type") == "WebSite" for node in nodes(path)):
            non_home_website.append(str(path.relative_to(ROOT)))
    if non_home_website:
        errors.append(f"WebSite outside Home: {non_home_website[:5]}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(json.dumps({
        "status": "PASS", "websiteName": website[0]["name"],
        "alternateNames": len(website[0]["alternateName"]), "sameAs": len(organizations[0]["sameAs"]),
        "artists": len(cms["artists"]), "websiteDuplicates": 0, "organizationDuplicates": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
