#!/usr/bin/env python3
"""Audit Universe 2.0 sections."""
import argparse,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);r=p.parse_args().root
 text=(r/"universe/index.html").read_text();errors=[]
 for x in ("世界年表","アーティスト相関図","作品相関図","世界MAP","ストーリー","キーワード・用語","代表作品・おすすめ順","今後追加予定","BreadcrumbList","assets/main.js"):
  if x not in text:errors.append(f"missing {x}")
 if text.count("creator-universe-node")<7:errors.append("seven artist worlds are required")
 if errors:print("Universe audit failed:\n- "+"\n- ".join(errors),file=sys.stderr);return 1
 print("Universe audit passed: Universe 2.0 and 7 artist worlds.");return 0
if __name__=="__main__":raise SystemExit(main())
