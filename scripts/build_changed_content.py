#!/usr/bin/env python3
"""Generate in isolation and apply only byte-level changed SUZUKA files."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


IGNORED_PARTS = {".git", ".indexnow-cache", "__pycache__", ".DS_Store"}


def included(path: Path) -> bool:
    return not any(part in IGNORED_PARTS for part in path.parts)


def copy_source(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(".git", ".indexnow-cache", "__pycache__", ".DS_Store"),
    )


def digest_map(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and included(path.relative_to(root))
    }


def tree_digest(values: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(values.items()):
        digest.update(name.encode("utf-8"))
        digest.update(value.encode("ascii"))
    return digest.hexdigest()


def run_generator(root: Path) -> None:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    subprocess.run(
        [sys.executable, str(root / "scripts/build_explore_catalog.py"), "--root", str(root)],
        cwd=root,
        env=env,
        check=True,
    )


def compare(source: Path, generated: Path) -> tuple[list[str], list[str], str]:
    before, after = digest_map(source), digest_map(generated)
    changed = sorted(name for name, value in after.items() if before.get(name) != value)
    deleted = sorted(name for name in before if name not in after)
    return changed, deleted, tree_digest(after)


def apply_transaction(source: Path, generated: Path, changed: list[str], deleted: list[str]) -> None:
    """Copy the validated staged tree with rollback if a filesystem operation fails."""
    with tempfile.TemporaryDirectory(prefix="suzuka-release-backup-") as tmp:
        backup = Path(tmp)
        existing: set[str] = set()
        for name in [*changed, *deleted]:
            target = source / name
            if target.is_file():
                existing.add(name)
                saved = backup / name
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, saved)
        try:
            for name in changed:
                target = source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                staged = generated / name
                temporary = target.with_name(target.name + ".release-sync-tmp")
                shutil.copy2(staged, temporary)
                os.replace(temporary, target)
            for name in deleted:
                target = source / name
                if target.is_file():
                    target.unlink()
                    try:
                        target.parent.rmdir()
                    except OSError:
                        pass
        except Exception:
            for name in [*changed, *deleted]:
                target = source / name
                if name in existing:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup / name, target)
                elif target.exists():
                    target.unlink()
            raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    with tempfile.TemporaryDirectory(prefix="suzuka-changed-build-") as tmp:
        stage = Path(tmp) / "site"
        copy_source(root, stage)
        run_generator(stage)
        changed, deleted, digest = compare(root, stage)
        result = {
            "status": "dry-run" if args.dry_run else "applied",
            "changedCount": len(changed),
            "deletedCount": len(deleted),
            "changedFiles": changed,
            "deletedFiles": deleted,
            "sha256": digest,
        }
        if not args.dry_run and (changed or deleted):
            apply_transaction(root, stage, changed, deleted)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
