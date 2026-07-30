#!/usr/bin/env python3
"""Audit GA4 installation, exclusions, events and SEO URL cleanliness."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

MEASUREMENT_ID = "G-LS3PCRB60D"
EVENTS = (
    "official_mv_click", "youtube_click", "instagram_click", "release_click",
    "search_use", "playlist_click", "weekly_pick_click", "artist_click",
)

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    root=parser.parse_args().root.resolve(); errors=[]; installed=0
    pages=sorted(root.glob("**/index.html"))
    for path in pages:
        relative=path.relative_to(root); text=path.read_text(encoding="utf-8")
        admin=relative.parts[0]=="admin"
        loader=text.count(f"googletagmanager.com/gtag/js?id={MEASUREMENT_ID}")
        config=text.count(f"gtag('config', '{MEASUREMENT_ID}'")
        event_script=len(re.findall(r'assets/analytics\.js',text))
        if admin:
            if loader or config or event_script or MEASUREMENT_ID in text:
                errors.append(f"{relative}: admin must not contain GA4")
            continue
        installed+=1
        if (loader,config,event_script)!=(1,1,1):
            errors.append(f"{relative}: expected one loader/config/event script, found {loader}/{config}/{event_script}")
        head=text.find("<head>"); tag=text.find("<!-- SUZUKA:GA4:START -->")
        if head<0 or tag<0 or tag-head>20:
            errors.append(f"{relative}: Google tag is not immediately after opening head")
        for match in re.findall(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"',text):
            if "google" in match.lower() or "utm_" in match.lower() or MEASUREMENT_ID in match:
                errors.append(f"{relative}: analytics value in canonical")
        for block in re.findall(r'<script type="application/ld\\+json">(.*?)</script>',text,re.DOTALL):
            try: json.loads(block)
            except json.JSONDecodeError as error: errors.append(f"{relative}: invalid JSON-LD: {error}")
            if MEASUREMENT_ID in block or "utm_" in block: errors.append(f"{relative}: analytics value in JSON-LD")
    source=(root/"assets/analytics.js").read_text(encoding="utf-8")
    for event in EVENTS:
        if f'"{event}"' not in source: errors.append(f"assets/analytics.js: missing {event}")
    if "search_term" in source:
        errors.append("assets/analytics.js: raw search terms must not be transmitted")
    sitemap=(root/"sitemap.xml").read_text(encoding="utf-8")
    if MEASUREMENT_ID in sitemap or "utm_" in sitemap: errors.append("sitemap contains analytics data")
    about=(root/"about/index.html").read_text(encoding="utf-8")
    if "Google Analyticsの利用について" not in about: errors.append("About analytics notice missing")
    if errors:
        print("Analytics audit failed:\n- "+"\n- ".join(errors),file=sys.stderr);return 1
    print(f"Analytics audit passed: {installed} public pages, 2 admin pages excluded, {len(EVENTS)} events, no duplicate tags.")
    return 0
if __name__=="__main__": raise SystemExit(main())
