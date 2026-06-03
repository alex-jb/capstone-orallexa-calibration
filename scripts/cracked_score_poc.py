#!/usr/bin/env python3
"""cracked_score_poc.py — Cracked Score Phase 2 prototype.

Validates the scoring engine OFFLINE before the live waitlist crosses 200.
Given a GitHub handle, fetches public profile + recent repos and computes a
0-100 score across the 12 axes promised on /cracked landing.

Run on a few known-good handles (your own + 2-3 friends) and eyeball the
output. If the relative ordering matches your intuition, the scoring engine
is ready to wire up to /cracked when waitlist threshold hits.

Usage:
    python3 cracked_score_poc.py alex-jb
    python3 cracked_score_poc.py karpathy
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

GH_TOKEN = os.environ.get("GITHUB_TOKEN")
USER_AGENT = "vibex-cracked-score-poc/1.0"


def gh(path: str, params: dict | None = None) -> dict | list | None:
    url = f"https://api.github.com{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
    if GH_TOKEN:
        headers["Authorization"] = f"Bearer {GH_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        print(f"[gh] {path} failed: {e}", file=sys.stderr)
        return None


def days_ago(iso: str) -> int:
    return (datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))).days


def axes(handle: str) -> dict[str, dict]:
    """Compute 12 axes for a GitHub user. Each returns {raw, normalized 0-100}."""
    user = gh(f"/users/{handle}")
    if not user:
        return {}
    repos = gh(f"/users/{handle}/repos", {"sort": "updated", "per_page": 100, "type": "owner"}) or []
    repos = [r for r in repos if not r.get("fork")]

    now = datetime.now(timezone.utc)
    recent_repos = [r for r in repos if days_ago(r["pushed_at"]) <= 90]
    stars_total = sum(r.get("stargazers_count", 0) for r in repos)
    forks_total = sum(r.get("forks_count", 0) for r in repos)
    langs = {r.get("language") for r in repos if r.get("language")}
    public_repos = user.get("public_repos", 0)
    followers = user.get("followers", 0)

    # Velocity: % of repos pushed in last 90 days
    velocity_pct = (len(recent_repos) / public_repos * 100) if public_repos else 0
    # Depth: max stars on any single repo (caps signal of "cracked-ness")
    top_repo_stars = max((r.get("stargazers_count", 0) for r in repos), default=0)
    # Breadth: distinct languages with ≥3 repos
    lang_breadth = sum(1 for l in langs if sum(1 for r in repos if r.get("language") == l) >= 3)
    # README discipline: % of repos with description
    described = sum(1 for r in repos if (r.get("description") or "").strip())
    desc_pct = (described / public_repos * 100) if public_repos else 0
    # Account age × public-repos (older + active = signal)
    account_days = days_ago(user.get("created_at", "2020-01-01T00:00:00Z"))
    age_score = min(account_days / 30, 100)  # 100 = 8+ years on GH
    # OSS contribution (proxy: stars received total)
    oss_signal = min(stars_total, 5000) / 5000 * 100
    # Social signal: log-scale follower count (1k=33, 10k=66, 100k=100)
    # Linear caps too early — gaearon (90k) and karpathy (195k) both saturate
    # at 100 with the old min(x,1000)/1000 formula. Log10 spreads them out.
    import math
    follower_signal = (math.log10(max(followers, 1)) / 5) * 100 if followers else 0
    # Fork → star ratio (high = code people copy + iterate on, not just star)
    fork_ratio = (forks_total / stars_total * 100) if stars_total else 0
    # Signal/noise: avg stars per repo
    avg_stars = (stars_total / public_repos) if public_repos else 0
    sig_noise = min(avg_stars / 20, 1) * 100  # 100 = avg 20+ stars/repo

    def clamp(v: float) -> int:
        return max(0, min(100, int(round(v))))

    return {
        "velocity":          {"raw": f"{velocity_pct:.0f}% repos pushed 90d",     "score": clamp(velocity_pct)},
        "depth":             {"raw": f"top repo {top_repo_stars} stars",          "score": clamp(top_repo_stars / 20)},
        "breadth":           {"raw": f"{lang_breadth} langs ≥3 repos",            "score": clamp(lang_breadth * 15)},
        "oss":               {"raw": f"{stars_total} total stars received",       "score": clamp(oss_signal)},
        "discipline":        {"raw": f"{desc_pct:.0f}% repos with desc",          "score": clamp(desc_pct)},
        "tenure":            {"raw": f"{account_days // 365}y on GitHub",         "score": clamp(age_score)},
        "social":            {"raw": f"{followers} followers",                    "score": clamp(follower_signal)},
        "iteration":         {"raw": f"fork:star ratio {fork_ratio:.1f}%",        "score": clamp(fork_ratio * 2)},
        "signal_to_noise":   {"raw": f"avg {avg_stars:.1f} stars/repo",           "score": clamp(sig_noise)},
        "recent_activity":   {"raw": f"{len(recent_repos)} repos active 90d",     "score": clamp(len(recent_repos) * 5)},
        "language_focus":    {"raw": f"primary: {user.get('blog') or '?'}",       "score": clamp(len(langs) * 10)},
        "writing":           {"raw": f"bio: {bool(user.get('bio'))}",             "score": 50 if user.get("bio") else 20},
    }


def overall(scored: dict[str, dict]) -> int:
    return int(round(sum(a["score"] for a in scored.values()) / len(scored))) if scored else 0


def main():
    if len(sys.argv) < 2:
        print("usage: cracked_score_poc.py <github_handle>")
        sys.exit(1)
    handle = sys.argv[1].lstrip("@")
    print(f"\n🧠 Cracked Score POC — @{handle}\n")
    scored = axes(handle)
    if not scored:
        print(f"user @{handle} not found or rate limited")
        return
    for axis, data in scored.items():
        bar = "█" * (data["score"] // 5)
        print(f"  {axis:<18} {data['score']:>3}  {bar:<20}  ({data['raw']})")
    print(f"\n  {'='*60}")
    print(f"  OVERALL CRACKED SCORE: {overall(scored)} / 100\n")


if __name__ == "__main__":
    main()
