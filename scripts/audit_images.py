#!/usr/bin/env python3
"""Audit public image markup, files and the Google image sitemap."""
from __future__ import annotations
import argparse, re, sys, xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from PIL import Image

BASE="https://www.suzukaofficial.com/"
NS={"s":"http://www.sitemaps.org/schemas/sitemap/0.9","i":"http://www.google.com/schemas/sitemap-image/1.1"}

class Parser(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.images=[]; self.canonical=""
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if tag=="img": self.images.append(values)
        if tag=="link" and "canonical" in (values.get("rel") or "").split(): self.canonical=values.get("href") or ""

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); root=ap.parse_args().root.resolve()
    errors=[]; checked=0; local_files=set()
    for path in sorted(root.glob("**/index.html")):
        rel=path.relative_to(root)
        if rel.parts[0]=="admin": continue
        parser=Parser(); parser.feed(path.read_text(encoding="utf-8"))
        for image in parser.images:
            checked+=1; src=image.get("src") or ""
            if not (image.get("alt") or "").strip(): errors.append(f"{rel}: image alt missing: {src}")
            if not image.get("width") or not image.get("height"): errors.append(f"{rel}: image dimensions missing: {src}")
            if not src: continue
            absolute=urljoin(parser.canonical,src); parsed=urlparse(absolute)
            if parsed.netloc==urlparse(BASE).netloc and parsed.path.startswith(urlparse(BASE).path):
                local=root/parsed.path[len(urlparse(BASE).path):].lstrip("/"); local_files.add(local)
                if not local.is_file(): errors.append(f"{rel}: image missing: {src}")
    for path in sorted(local_files):
        if not path.is_file(): continue
        if path.stat().st_size>5*1024*1024: errors.append(f"{path.relative_to(root)}: image exceeds 5 MiB")
        try:
            with Image.open(path) as image:
                if image.width<1 or image.height<1: errors.append(f"{path.relative_to(root)}: invalid dimensions")
        except Exception as error: errors.append(f"{path.relative_to(root)}: unreadable image: {error}")
    sitemap=ET.parse(root/"image-sitemap.xml").getroot(); sitemap_images=sitemap.findall(".//i:loc",NS)
    if not sitemap_images: errors.append("image-sitemap.xml contains no images")
    if errors: print("Image audit failed:\n- "+"\n- ".join(errors),file=sys.stderr); return 1
    print(f"Image audit passed: {checked} HTML image references, {len(local_files)} local files, {len(sitemap_images)} sitemap entries.")
    return 0
if __name__=="__main__": raise SystemExit(main())
