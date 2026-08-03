#!/usr/bin/env python3
"""Prepare, but never submit, an IndexNow key file and production-only payload."""
from __future__ import annotations
import argparse, json, re, xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

BASE="https://www.suzukaofficial.com/"
NS={"s":"http://www.sitemaps.org/schemas/sitemap/0.9"}

def main()->None:
    parser=argparse.ArgumentParser(); parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); parser.add_argument("--key",required=True); parser.add_argument("--write",action="store_true"); args=parser.parse_args()
    root=args.root.resolve(); key=args.key
    if not re.fullmatch(r"[A-Za-z0-9-]{8,128}",key): raise SystemExit("IndexNow key must be 8-128 letters, numbers or hyphens")
    urls=[node.text or "" for node in ET.parse(root/"sitemap.xml").getroot().findall("s:url/s:loc",NS)]
    for url in urls:
        parsed=urlparse(url)
        if parsed.scheme!="https" or parsed.netloc!="www.suzukaofficial.com" or not url.startswith(BASE): raise SystemExit(f"Non-production URL rejected: {url}")
    payload={"host":"www.suzukaofficial.com","key":key,"keyLocation":f"{BASE}{key}.txt","urlList":urls}
    if args.write:
        (root/f"{key}.txt").write_text(key+"\n",encoding="utf-8")
        output=root/"docs/search/indexnow-payload.json"; output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"preparedUrls":len(urls),"keyLocation":payload["keyLocation"],"submitted":False},ensure_ascii=False))
if __name__=="__main__": main()
