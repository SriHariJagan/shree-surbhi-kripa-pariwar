#!/usr/bin/env python3
"""Sanity-check the generated static site: links, assets, ids, metadata."""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted(ROOT.glob("*.html")) + sorted((ROOT / "hi").glob("*.html"))

attr_re = re.compile(r'(?:src|href)="([^"]+)"')
srcset_re = re.compile(r'srcset="([^"]+)"')
id_re = re.compile(r'\sid="([^"]+)"')
problems: list[str] = []


def check_target(page: Path, raw: str, kind: str) -> None:
    if not raw or raw.startswith(("#", "mailto:", "tel:", "data:", "http:", "https:", "upi:")):
        return
    target = unquote(raw.split("#")[0].split("?")[0])
    if not target:
        return
    path = (page.parent / target).resolve()
    if not path.exists():
        problems.append(f"{page.relative_to(ROOT)}: missing {kind} target {raw}")


for page in PAGES:
    text = page.read_text(encoding="utf-8")
    for raw in attr_re.findall(text):
        check_target(page, raw, "link")
    for srcset in srcset_re.findall(text):
        for part in srcset.split(","):
            url = part.strip().split(" ")[0]
            check_target(page, url, "srcset")

    ids = id_re.findall(text)
    duplicates = [k for k, v in Counter(ids).items() if v > 1]
    if duplicates:
        problems.append(f"{page.relative_to(ROOT)}: duplicate ids {duplicates}")

    if "<title>" not in text or len(re.search(r"<title>(.*?)</title>", text).group(1)) > 75:
        problems.append(f"{page.relative_to(ROOT)}: title missing or too long")
    if 'name="description"' not in text:
        problems.append(f"{page.relative_to(ROOT)}: missing meta description")

print(f"Checked {len(PAGES)} pages.")
if problems:
    print(f"{len(problems)} problem(s):")
    for problem in problems:
        print("  -", problem)
    sys.exit(1)
print("All local links, srcsets and ids resolve.")
