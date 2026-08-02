#!/usr/bin/env python3
"""Regenerate twice in isolation and require byte-identical outputs."""
from __future__ import annotations
import argparse, hashlib, os, shutil, subprocess, sys, tempfile
from pathlib import Path

def digest(root:Path)->str:
    value=hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and ".DS_Store" not in p.parts):
        value.update(path.relative_to(root).as_posix().encode()); value.update(path.read_bytes())
    return value.hexdigest()

def file_digests(root:Path)->dict[str,str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and ".DS_Store" not in p.parts)
    }

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); source=ap.parse_args().root.resolve()
    with tempfile.TemporaryDirectory(prefix="suzuka-sync-audit-") as tmp:
        root=Path(tmp)/"site"; shutil.copytree(source,root,ignore=shutil.ignore_patterns(".git",".DS_Store","__pycache__"))
        env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"}
        command=[sys.executable,str(root/"scripts/build_explore_catalog.py"),"--root",str(root)]
        subprocess.run(command,cwd=root,env=env,check=True,stdout=subprocess.DEVNULL)
        first=digest(root)
        first_files=file_digests(root)
        subprocess.run(command,cwd=root,env=env,check=True,stdout=subprocess.DEVNULL)
        second=digest(root)
        second_files=file_digests(root)
    if first!=second:
        changed=sorted(path for path in set(first_files)|set(second_files) if first_files.get(path)!=second_files.get(path))
        print(f"Sync audit failed: {first} != {second}; changed: {', '.join(changed)}",file=sys.stderr)
        return 1
    print(f"Sync audit passed: second generation produced no differences ({second}).")
    return 0
if __name__=="__main__": raise SystemExit(main())
