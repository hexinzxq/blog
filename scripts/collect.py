#!/usr/bin/env python3
"""每天把 owner 名下仓库最近两周的 commit 抓下来，写成 data/updates.json。

只用标准库，GitHub Actions 里不需要额外安装。
GITHUB_TOKEN 存在时带上去（5000 次/小时），没有也能跑（60 次/小时，够用）。

用法：
    python3 scripts/collect.py
    GH_OWNER=somebody python3 scripts/collect.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
OWNER = os.environ.get("GH_OWNER", "hexinzxq")
WINDOW_DAYS = 14
MAX_ENTRIES = 40
SKIP_REPOS = {"blog"}  # 站点自己的提交，不算「在做什么」

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "updates.json"


def get(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "hexinzxq-blog-collector",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def main() -> int:
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=WINDOW_DAYS)
    since_q = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        repos = get(f"{API}/users/{OWNER}/repos?per_page=100&sort=pushed")
    except urllib.error.HTTPError as exc:
        print(f"列仓库失败：{exc.code} {exc.reason}", file=sys.stderr)
        return 1

    mine = [
        r
        for r in repos
        if not r.get("fork")
        and not r.get("archived")
        and r["name"] not in SKIP_REPOS
        and (r.get("pushed_at") or "") >= since_q
    ]
    mine.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)

    entries: list[dict] = []
    for repo in mine:
        name = repo["name"]
        try:
            commits = get(f"{API}/repos/{OWNER}/{name}/commits?since={since_q}&per_page=30")
        except urllib.error.HTTPError as exc:
            print(f"跳过 {name}：{exc.code}", file=sys.stderr)
            continue

        for c in commits:
            raw = (c.get("commit", {}).get("message") or "").strip()
            first = raw.split("\n", 1)[0].strip()
            if not first or first.startswith("Merge "):
                continue
            entries.append(
                {
                    "repo": name,
                    "message": first[:160],
                    "short": (c.get("sha") or "")[:7],
                    "date": c.get("commit", {}).get("author", {}).get("date") or c.get("commit", {}).get("committer", {}).get("date"),
                    "url": c.get("html_url"),
                }
            )

    entries = [e for e in entries if e["date"]]
    entries.sort(key=lambda e: e["date"], reverse=True)
    entries = entries[:MAX_ENTRIES]

    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_days": WINDOW_DAYS,
        "owner": OWNER,
        "totals": {
            "commits": len(entries),
            "repos": len({e["repo"] for e in entries}),
        },
        "entries": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(entries)} 条提交 / {payload['totals']['repos']} 个仓库 → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
