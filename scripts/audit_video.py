#!/usr/bin/env python3
"""Audit public VideoObjects and the Google video sitemap."""
from __future__ import annotations
import argparse, json, re, sys, xml.etree.ElementTree as ET
from pathlib import Path
from structured_data_dates import ISO_DATETIME_TZ_RE, JSONLD_RE, iter_nodes, types_of, video_id_from_node

NS={"s":"http://www.sitemaps.org/schemas/sitemap/0.9","v":"http://www.google.com/schemas/sitemap-video/1.1"}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); root=ap.parse_args().root.resolve()
    cms=json.loads((root/"assets/data/creator-cms.json").read_text(encoding="utf-8")); evidence=json.loads((root/"assets/data/youtube-publish-dates.json").read_text(encoding="utf-8"))
    upcoming={x["youtubeUrl"].split("=")[-1] for x in cms["upcoming"]}; verified={x["youtubeId"]:x for x in evidence["records"] if x.get("status")=="verified-datetime"}
    errors=[]; count=0
    for path in sorted(root.glob("**/index.html")):
        if path.relative_to(root).parts[0]=="admin": continue
        for block in JSONLD_RE.finditer(path.read_text(encoding="utf-8")):
            for node in iter_nodes(json.loads(block.group(2))):
                if "VideoObject" not in types_of(node): continue
                count+=1; identifier=video_id_from_node(node)
                if identifier in upcoming: errors.append(f"{path.relative_to(root)}: upcoming video exposed")
                if identifier not in verified: errors.append(f"{path.relative_to(root)}: video lacks official evidence {identifier}")
                elif node.get("uploadDate")!=verified[identifier]["verifiedPublishedAt"]: errors.append(f"{path.relative_to(root)}: uploadDate mismatch {identifier}")
                if not ISO_DATETIME_TZ_RE.fullmatch(str(node.get("uploadDate", ""))): errors.append(f"{path.relative_to(root)}: invalid uploadDate")
    tree=ET.parse(root/"video-sitemap.xml").getroot(); videos=tree.findall(".//v:video",NS)
    for video in videos:
        for key in ("thumbnail_loc","title","description","publication_date"):
            if video.find(f"v:{key}",NS) is None: errors.append(f"video-sitemap: missing {key}")
        published=video.findtext("v:publication_date",default="",namespaces=NS)
        if not ISO_DATETIME_TZ_RE.fullmatch(published): errors.append("video-sitemap: invalid publication_date")
    if len(videos)!=count: errors.append(f"video sitemap count {len(videos)} != VideoObject count {count}")
    if errors: print("Video audit failed:\n- "+"\n- ".join(errors),file=sys.stderr); return 1
    print(f"Video audit passed: {count} verified VideoObjects and {len(videos)} video sitemap entries.")
    return 0
if __name__=="__main__": raise SystemExit(main())
