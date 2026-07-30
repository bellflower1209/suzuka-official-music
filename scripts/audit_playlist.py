#!/usr/bin/env python3
"""Audit playlist data, pages and structured data."""
import argparse,json,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);r=p.parse_args().root;errors=[]
 data=json.loads((r/"assets/data/playlists.json").read_text())["playlists"]
 if len(data)!=12: errors.append(f"expected 12 playlists, found {len(data)}")
 for x in data:
  path=r/f"playlists/{x['slug']}/index.html"
  if not path.is_file(): errors.append(f"missing {path.relative_to(r)}");continue
  text=path.read_text()
  for marker in ("CollectionPage","ItemList","BreadcrumbList","assets/main.js","検索"):
   if marker not in text: errors.append(f"{x['slug']}: missing {marker}")
  if "autoplay=1" in text: errors.append(f"{x['slug']}: autoplay enabled")
 if errors: print("Playlist audit failed:\n- "+"\n- ".join(errors),file=sys.stderr);return 1
 print(f"Playlist audit passed: {len(data)} playlists.");return 0
if __name__=="__main__":raise SystemExit(main())
