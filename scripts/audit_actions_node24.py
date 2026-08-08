#!/usr/bin/env python3
"""Audit every GitHub workflow/local action for the Node.js 24 transition."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_MAJORS = {
    "actions/checkout": 7,
    "actions/setup-node": 7,
    "actions/upload-artifact": 7,
    "actions/download-artifact": 8,
    "actions/cache": 6,
    "actions/cache/restore": 6,
    "actions/cache/save": 6,
    "actions/configure-pages": 6,
    "actions/upload-pages-artifact": 5,
    "actions/deploy-pages": 5,
    "github/codeql-action": 4,
}


def main() -> int:
    workflows = sorted((ROOT / ".github/workflows").glob("*.yml")) + sorted((ROOT / ".github/workflows").glob("*.yaml"))
    local_actions = sorted(path for name in ("action.yml", "action.yaml") for path in ROOT.rglob(name) if ".git" not in path.parts)
    errors, uses = [], []
    for path in workflows + local_actions:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        if re.search(r"using:\s*['\"]?node20\b", text):
            errors.append(f"{relative}: runs.using still uses node20")
        if "ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION" in text:
            errors.append(f"{relative}: forbidden Node 20 escape variable")
        for ref in re.findall(r"\buses:\s*([^\s#]+)", text):
            uses.append((relative, ref))
            name, _, version = ref.partition("@")
            required = REQUIRED_MAJORS.get(name)
            if required is not None:
                match = re.match(r"v(\d+)(?:\D|$)", version)
                if not match or int(match.group(1)) < required:
                    errors.append(f"{relative}: {ref} must be {name}@v{required} or newer")
        for version in re.findall(r"node-version:\s*['\"]?([^\s'\"]+)", text):
            if not re.match(r"24(?:\.|$)", version):
                errors.append(f"{relative}: node-version is {version}, expected 24")
    pages = ROOT / ".github/workflows/pages.yml"
    if not pages.is_file():
        errors.append("missing custom GitHub Pages workflow")
    else:
        text = pages.read_text(encoding="utf-8")
        for marker in ("actions/setup-node@v7", "node-version: 24", "actions/configure-pages@v6", "actions/upload-pages-artifact@v5", "actions/deploy-pages@v5"):
            if marker not in text:
                errors.append(f".github/workflows/pages.yml: missing {marker}")
    if errors:
        print("Node 24 Actions audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(f"Node 24 Actions audit passed: workflows={len(workflows)} localActions={len(local_actions)} uses={len(uses)} node20=0.")
    for relative, ref in uses:
        print(f"- {relative}: {ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
