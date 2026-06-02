#!/usr/bin/env python3
"""weekly_brier_report.py — aggregate daily Brier audits into a Sunday weekly report.

Source: alex-brain/research/brier-audit/YYYY-MM-DD.json (7 most recent)
Output: capstone-orallexa-calibration/weekly-reports/YYYY-MM-DD-week-N.md

What goes in the report:
  - 7-day Brier average vs prior-week average (delta)
  - Tickers with most calibration improvement / regression this week
  - "Verdict" trend (🟢 strong / 🟡 mild / 🔴 worse than baseline)
  - Capstone milestone callout: week N of 13

Run weekly Sunday 21:00 NY via launchd, or manually:
    python3 scripts/weekly_brier_report.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = Path.home()
BRIER_DIR = HOME / "Desktop" / "Interview-Prep" / "Projects" / "alex-brain" / "research" / "brier-audit"
REPO_ROOT = HOME / "Desktop" / "capstone-orallexa-calibration"
OUT_DIR = REPO_ROOT / "weekly-reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CAPSTONE_START = datetime(2026, 6, 2, tzinfo=timezone.utc)


def load_json_safe(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def collect_days(end_date: datetime, n: int) -> list[dict]:
    """Walk backwards n days from end_date, load whatever Brier JSON exists."""
    out = []
    for offset in range(n):
        d = end_date - timedelta(days=offset)
        path = BRIER_DIR / f"{d.strftime('%Y-%m-%d')}.json"
        data = load_json_safe(path)
        if data:
            out.append(data)
    return list(reversed(out))


def avg(numbers: list[float]) -> float:
    return sum(numbers) / len(numbers) if numbers else 0.0


def verdict_from_brier(b: float) -> str:
    if b < 0.18:
        return "🟢 Strong edge"
    if b < 0.22:
        return "🟢 Edge"
    if b < 0.245:
        return "🟡 Mild edge"
    if b < 0.255:
        return "⚪ Roughly coin-flip baseline"
    return "🔴 Worse than baseline"


def render(this_week: list[dict], last_week: list[dict], week_n: int, end_date: datetime) -> str:
    if not this_week:
        return f"# Week {week_n} — no Brier data\n\nNo audit data found for the week ending {end_date.strftime('%Y-%m-%d')}.\n"

    this_briers = [d["overall_brier"] for d in this_week]
    last_briers = [d["overall_brier"] for d in last_week]

    this_avg = avg(this_briers)
    last_avg = avg(last_briers) if last_briers else None
    delta = (this_avg - last_avg) if last_avg is not None else None

    total_resolved = sum(d.get("n_resolved", 0) for d in this_week)

    # Per-ticker aggregation across the 7 days
    ticker_briers: dict[str, list[float]] = {}
    ticker_n: dict[str, int] = {}
    for day in this_week:
        for ticker, stats in (day.get("per_ticker") or {}).items():
            ticker_briers.setdefault(ticker, []).append(stats["brier"])
            ticker_n[ticker] = ticker_n.get(ticker, 0) + stats["n"]

    ticker_avg = sorted(
        ((t, avg(bs), ticker_n[t]) for t, bs in ticker_briers.items() if ticker_n[t] >= 3),
        key=lambda x: x[1],
    )

    lines = []
    lines.append(f"# Weekly Brier report — Week {week_n} of 13")
    lines.append("")
    lines.append(f"**Week ending:** {end_date.strftime('%Y-%m-%d')}")
    lines.append(f"**Capstone day:** {(end_date - CAPSTONE_START).days + 1}")
    lines.append(f"**Daily audits included:** {len(this_week)}")
    lines.append(f"**Total resolved decisions:** {total_resolved}")
    lines.append("")
    lines.append("## Headline metric")
    lines.append("")
    lines.append(f"| | Brier average | Verdict |")
    lines.append("|---|---:|---|")
    lines.append(f"| **This week** | **{this_avg:.4f}** | {verdict_from_brier(this_avg)} |")
    if last_avg is not None:
        arrow = "↗ regressed" if delta > 0.005 else "↘ improved" if delta < -0.005 else "→ flat"
        lines.append(f"| Last week | {last_avg:.4f} | (delta {delta:+.4f}) {arrow} |")
    lines.append(f"| 0.25 coin-flip baseline | 0.2500 | uninformative reference |")
    lines.append(f"| 0.13 FiveThirtyEight election | 0.1300 | strong calibration reference |")
    lines.append("")

    if ticker_avg:
        lines.append("## Per-ticker calibration (≥3 decisions this week, sorted best → worst)")
        lines.append("")
        lines.append("| Ticker | N | Brier | vs coin-flip |")
        lines.append("|---|---:|---:|---:|")
        for ticker, b, n in ticker_avg[:20]:
            delta_baseline = b - 0.25
            sign = "✅" if delta_baseline < -0.02 else ("⚠️" if delta_baseline > 0.02 else "·")
            lines.append(f"| {ticker} | {n} | {b:.4f} | {delta_baseline:+.4f} {sign} |")
        lines.append("")

    lines.append("## Capstone status note")
    lines.append("")
    if week_n <= 2:
        lines.append("- Phase 1: paper-validation. No real money deployed.")
    elif week_n <= 4:
        lines.append("- Phase 2: first real-money deployment window. $20-$50 max position size.")
    elif week_n <= 8:
        lines.append("- Phase 3: scale assessment. If Brier holds at < 0.22, scale to $1k.")
    elif week_n <= 10:
        lines.append("- Phase 4: methodology paper drafting in parallel with live audit.")
    else:
        lines.append("- Phase 5: final paper revision + defense prep.")
    lines.append("")
    lines.append(f"Generated by `weekly_brier_report.py` on {datetime.now(timezone.utc).isoformat()}.")
    return "\n".join(lines)


def main():
    end_date = datetime.now(timezone.utc)
    if len(sys.argv) > 1:
        end_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone.utc)

    week_n = max(1, ((end_date - CAPSTONE_START).days // 7) + 1)
    this_week = collect_days(end_date, 7)
    last_week_end = end_date - timedelta(days=7)
    last_week = collect_days(last_week_end, 7)

    report = render(this_week, last_week, week_n, end_date)
    out_path = OUT_DIR / f"{end_date.strftime('%Y-%m-%d')}-week-{week_n}.md"
    out_path.write_text(report)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
