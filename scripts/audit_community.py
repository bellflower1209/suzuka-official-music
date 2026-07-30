#!/usr/bin/env python3
"""Audit privacy-safe static community implementation."""
import argparse,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);r=p.parse_args().root
 text=(r/"community/index.html").read_text();js=(r/"assets/creator-platform.js").read_text();errors=[]
 for x in ("人気投票","アンケート","おすすめ曲","月間ランキング","コメント募集","イベント","端末","WebPage","BreadcrumbList","assets/main.js"):
  if x not in text:errors.append(f"missing {x}")
 if "localStorage" not in js:errors.append("localStorage persistence missing")
 if "fetch(" in js:errors.append("community must not send user input externally")
 if errors:print("Community audit failed:\n- "+"\n- ".join(errors),file=sys.stderr);return 1
 print("Community audit passed: local-only voting, survey, recommendations and comments.");return 0
if __name__=="__main__":raise SystemExit(main())
