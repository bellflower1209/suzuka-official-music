#!/usr/bin/env python3
"""Ensure recommendation fallbacks are never presented as measured popularity."""
import argparse, json, sys
from pathlib import Path

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    root=parser.parse_args().root.resolve(); errors=[]
    source=json.loads((root/"assets/data/ranking-source.json").read_text(encoding="utf-8"))["releases"]
    rankings=json.loads((root/"assets/data/rankings.json").read_text(encoding="utf-8"))["rankings"]
    if not any("mvViews" in value for value in source.values()) and rankings["mv"]["label"]=="MV再生数順":
        errors.append("MV ranking must not claim view-count order without registered views")
    if not any("popularity" in value for value in source.values()) and rankings["popular"]["label"]=="人気作品TOP10":
        errors.append("popular ranking must be labeled as recommendation without registered metrics")
    if "実再生数未登録" not in rankings["mv"].get("fallback", ""):
        errors.append("MV fallback disclosure missing")
    if errors:
        print("Ranking audit failed:\n- "+"\n- ".join(errors),file=sys.stderr); return 1
    print(f"Ranking audit passed: {len(rankings)} lists, recommendation fallbacks clearly labeled.")
    return 0
if __name__=="__main__": raise SystemExit(main())
