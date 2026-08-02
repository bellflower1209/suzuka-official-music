#!/usr/bin/env python3
"""Validate Atom feed contents and discovery links."""
from __future__ import annotations
import argparse, re, sys, xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse
from structured_data_dates import ISO_DATETIME_TZ_RE

NS={"a":"http://www.w3.org/2005/Atom"}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); root=ap.parse_args().root.resolve(); errors=[]
    feed=ET.parse(root/"feed.xml").getroot(); entries=feed.findall("a:entry",NS); ids=[]; categories=set()
    for entry in entries:
        identifier=entry.findtext("a:id",default="",namespaces=NS); ids.append(identifier)
        if urlparse(identifier).scheme!="https": errors.append(f"feed non-HTTPS id: {identifier}")
        updated=entry.findtext("a:updated",default="",namespaces=NS)
        if not ISO_DATETIME_TZ_RE.fullmatch(updated): errors.append(f"feed invalid updated: {identifier}")
        category=entry.find("a:category",NS); term=category.get("term","") if category is not None else ""; categories.add(term)
        if term=="upcoming" and not (entry.findtext("a:title",default="",namespaces=NS).startswith("Upcoming｜")): errors.append("upcoming entry not clearly labeled")
    if len(ids)!=len(set(ids)): errors.append("feed duplicate entry IDs")
    if not {"release","news","upcoming"}.issubset(categories): errors.append("feed categories incomplete")
    public=0
    for path in root.glob("**/index.html"):
        rel=path.relative_to(root); text=path.read_text(encoding="utf-8"); links=len(re.findall(r'type="application/atom\+xml"',text))
        if rel.parts[0]=="admin":
            if links: errors.append(f"{rel}: admin feed discovery must be absent")
        else:
            public+=1
            if links!=1: errors.append(f"{rel}: expected one feed discovery link, found {links}")
    if errors: print("Feed audit failed:\n- "+"\n- ".join(errors),file=sys.stderr); return 1
    print(f"Feed audit passed: {len(entries)} entries and discovery on {public} public pages.")
    return 0
if __name__=="__main__": raise SystemExit(main())
