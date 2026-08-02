#!/usr/bin/env python3
"""Static Core Web Vitals risk audit for generated public templates."""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); root=ap.parse_args().root.resolve(); errors=[]; pages=0
    for path in sorted(root.glob("**/index.html")):
        rel=path.relative_to(root)
        if rel.parts[0]=="admin": continue
        pages+=1; text=path.read_text(encoding="utf-8")
        for tag in re.findall(r"<img\b[^>]*>",text,re.I):
            if not re.search(r"\bwidth=",tag,re.I) or not re.search(r"\bheight=",tag,re.I): errors.append(f"{rel}: image intrinsic size missing")
        if re.search(r"(?:autoplay=1|autoplay:\s*1|<video[^>]+autoplay)",text,re.I): errors.append(f"{rel}: autoplay enabled")
        for script in re.findall(r"<script\b[^>]+src=[^>]+>",text,re.I):
            if "defer" not in script and "async" not in script: errors.append(f"{rel}: render-blocking script")
    css="\n".join(path.read_text(encoding="utf-8") for path in (root/"assets").glob("*.css"))
    if "overflow-x:hidden" not in css.replace(" ",""): errors.append("global horizontal overflow guard missing")
    if errors: print("CWV audit failed:\n- "+"\n- ".join(errors),file=sys.stderr); return 1
    print(f"CWV static audit passed: {pages} public pages; intrinsic image sizes, deferred scripts and no autoplay.")
    return 0
if __name__=="__main__": raise SystemExit(main())
