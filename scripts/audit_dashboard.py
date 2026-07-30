#!/usr/bin/env python3
"""Audit the Creator Dashboard coverage."""
import argparse,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);r=p.parse_args().root
 text=(r/"admin/dashboard/index.html").read_text(); js=(r/"assets/creator-dashboard.js").read_text(); errors=[]
 labels=("公開作品","Upcoming","公開予定","MV不足","News不足","Gallery不足","Wiki不足","Universe不足","画像不足","SEO不足","JSON-LD不足","Search Console登録候補","YouTube未設定","Instagram未設定","公開日時未設定","おすすめ未設定")
 for x in labels:
  if x not in text: errors.append(f"missing {x}")
 if 'noindex, nofollow' not in text: errors.append("dashboard must be noindex")
 if "creator-cms.json" not in js or "recommendations.json" not in js: errors.append("dashboard is not source-backed")
 if errors: print("Dashboard audit failed:\n- "+"\n- ".join(errors),file=sys.stderr);return 1
 print(f"Dashboard audit passed: {len(labels)} checks.");return 0
if __name__=="__main__":raise SystemExit(main())
