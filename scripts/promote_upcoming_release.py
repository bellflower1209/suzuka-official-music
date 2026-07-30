#!/usr/bin/env python3
"""Promote one verified YouTube premiere from upcoming to published CMS data."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--slug",required=True);p.add_argument("--cover",required=True)
    p.add_argument("--description",required=True);p.add_argument("--genres",nargs="+",required=True)
    p.add_argument("--moods",nargs="+",required=True);p.add_argument("--themes",nargs="+",required=True)
    p.add_argument("--duration",type=int,default=0);p.add_argument("--weight",type=int,default=2)
    a=p.parse_args(); path=a.root/"assets/data/creator-cms.json"; cms=json.loads(path.read_text())
    upcoming=next((x for x in cms["upcoming"] if x["slug"]==a.slug),None)
    if not upcoming: raise SystemExit(f"Upcoming release not found: {a.slug}")
    artist=next(x for x in cms["artists"] if x["slug"]==upcoming["artistSlug"])
    released_at=upcoming["scheduledAt"]; title=upcoming["title"]
    record={
        "id":a.slug,"slug":a.slug,"title":title,"displayTitle":title,"artist":upcoming["artist"],
        "artistSlug":upcoming["artistSlug"],"artistSlugs":[upcoming["artistSlug"]],"artistType":artist["type"],
        "releaseDate":released_at[:10],"releaseYear":int(released_at[:4]),"releaseType":"single",
        "genres":a.genres,"moods":a.moods,"themes":a.themes,"language":"ja",
        "coverImage":a.cover,"coverAlt":f'{upcoming["artist"]}「{title}」公式YouTubeサムネイル',
        "releaseUrl":f"releases/{a.slug}/","youtubeUrl":upcoming["youtubeUrl"],
        "newsUrl":f"news/{a.slug}-release/","duration":a.duration,"status":"published","featured":True,
        "recommendationWeight":a.weight,"relatedReleases":[],"searchKeywords":list(dict.fromkeys(
            artist.get("searchKeywords",[])+a.genres+a.themes+[upcoming["artist"],title])),
        "aiArtistType":"fictional AI artist","description":a.description,
        "tags":list(dict.fromkeys(a.genres+a.themes+a.moods)),"lyrics":"","introduction":a.description,
        "publishedAt":released_at,"instagramUrl":"","shortsUrl":"","galleryImages":[a.cover],
        "productionNote":a.description,"seo":{"title":f"{title}｜{upcoming['artist']}｜SUZUKA Official Music",
        "description":a.description+" SUZUKAの架空のAIアーティスト作品です。","jsonLdEnabled":True},
    }
    cms["releases"].append(record)
    cms["upcoming"]=[x for x in cms["upcoming"] if x["slug"]!=a.slug]
    cms["news"].append({"slug":f"{a.slug}-release","title":f'{upcoming["artist"]}「{title}」公開',
        "artistSlug":upcoming["artistSlug"],"releaseSlug":a.slug,"publishedAt":released_at,
        "description":a.description,"image":a.cover,"status":"published"})
    path.write_text(json.dumps(cms,ensure_ascii=False,indent=2)+"\n")
    print(f"Promoted {a.slug}: {len(cms['releases'])} published / {len(cms['upcoming'])} upcoming")
if __name__=="__main__": main()
