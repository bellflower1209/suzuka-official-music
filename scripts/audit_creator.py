#!/usr/bin/env python3
"""Audit Creator CMS, generated catalog and deterministic recommendations."""
import argparse, json, sys
from pathlib import Path

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); root=p.parse_args().root
    errors=[]
    cms=json.loads((root/"assets/data/creator-cms.json").read_text())
    catalog=json.loads((root/"assets/data/releases-catalog.json").read_text())
    rec=json.loads((root/"assets/data/recommendations.json").read_text())["recommendations"]
    if cms.get("schemaVersion")!="3.1": errors.append("schemaVersion must be 3.1")
    for key in ("artists","releases","upcoming","news","taxonomy","featureDefinitions","playlistDefinitions","wiki","universe","community"):
        if key not in cms: errors.append(f"CMS missing {key}")
    for name, records in (("artist",cms["artists"]),("release",cms["releases"])):
        slugs=[x.get("slug") for x in records]
        if len(slugs)!=len(set(slugs)): errors.append(f"duplicate {name} slug")
    if len(catalog["releases"])!=len(cms["releases"]): errors.append("catalog/release count mismatch")
    for item in catalog["releases"]:
        groups=rec.get(item["slug"],{})
        for key in ("sameArtist","sameGenre","sameTheme","popular","recent","aiRecommended"):
            if key not in groups: errors.append(f"{item['slug']}: recommendation group {key} missing")
        if item["slug"] in sum(groups.values(),[]): errors.append(f"{item['slug']}: self recommendation")
    if "Math.random" in (root/"scripts/build_creator_platform.py").read_text(): errors.append("Math.random is forbidden")
    for path in ("admin/index.html","admin/dashboard/index.html","assets/creator-admin.js","assets/creator-dashboard.js"):
        if not (root/path).is_file(): errors.append(f"missing {path}")
    if errors: print("Creator audit failed:\n- "+"\n- ".join(errors),file=sys.stderr); return 1
    print(f"Creator audit passed: {len(cms['releases'])} releases, {len(cms['artists'])} artists, deterministic recommendations.")
    return 0
if __name__=="__main__": raise SystemExit(main())
