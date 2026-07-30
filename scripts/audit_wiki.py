#!/usr/bin/env python3
"""Audit generated SUZUKA Wiki."""
import argparse,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);r=p.parse_args().root;errors=[]
 pages=[r/"wiki/index.html",*sorted((r/"wiki").glob("*/index.html"))]
 if len(pages)!=7:errors.append(f"expected 7 wiki pages, found {len(pages)}")
 surface="".join(x.read_text() for x in pages)
 for x in ("アーティスト","作品","用語","ジャンル","公開年表","AIアーティスト","五十音","アルファベット","検索","BreadcrumbList"):
  if x not in surface:errors.append(f"missing {x}")
 if errors:print("Wiki audit failed:\n- "+"\n- ".join(errors),file=sys.stderr);return 1
 print(f"Wiki audit passed: {len(pages)} pages.");return 0
if __name__=="__main__":raise SystemExit(main())
