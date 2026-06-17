#!/usr/bin/env python3
"""staleness_audit.py — staleness-weighted Brier audit (Phase 1 #4).

Sibling to ece_audit.py. Same data source (brier_audit.load_decisions /
brier_for_decision), but applies the staleness module's exponential
decay to weight each decision's contribution by the age of the input
signals at the moment the decision was made.

The capstone hypothesis: predictions made from stale data carry less
information than predictions made from fresh data, so the same nominal
Brier hides a meaningful gap. Two systems with identical raw Brier can
differ materially in *staleness-weighted* Brier — and the staleness-
weighted version is the one that maps to live decision quality.

Output: data-snapshots/staleness-YYYY-MM-DD.json

This is **measurement-only** during Phase 1. Live trading behavior is
not modified. Stale-weighted ECE produces an additional reporting channel.

Run manually:
    python3 scripts/staleness_audit.py [--lookahead 1] [--n-bins 10]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ORALLEXA_SCRIPTS = Path.home() / ".orallexa" / "markets" / "scripts"

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(ORALLEXA_SCRIPTS))

try:
    import brier_audit  # type: ignore
except ImportError as e:
    print(f"[staleness] could not import brier_audit from {ORALLEXA_SCRIPTS}: {e}",
          file=sys.stderr)
    sys.exit(1)

import math

from calibration.staleness import DEFAULT_HALF_LIFE_SECONDS


def freshness_weight_for_decision(decision: dict) -> float:
    """Compute a single freshness weight in [0, 1] for one decision.

    A decision can cite multiple source ages (polymarket midpoint = 5 min ago,
    news sentiment = 3h ago, etc). Each source contributes a decay weight; the
    decision's freshness is the geometric mean of those weights.

    Uses the closed-form 2 ** (-age / half_life) directly to avoid the
    staleness() wrapper's wall-clock dependency (we want the weight as of
    the decision moment, which is encoded by age_seconds, not now()).
    """
    sources = decision.get("source_ages_seconds") or {}
    if not sources:
        return 1.0
    weights = []
    for source, age in sources.items():
        if source not in DEFAULT_HALF_LIFE_SECONDS:
            continue
        try:
            age_f = float(age)
        except (TypeError, ValueError):
            continue
        half_life = DEFAULT_HALF_LIFE_SECONDS[source]
        decay = math.pow(2.0, -age_f / half_life)
        weights.append(decay)
    if not weights:
        return 1.0
    log_sum = sum(math.log(max(w, 1e-12)) for w in weights)
    return math.exp(log_sum / len(weights))


def load_resolved_with_freshness(lookahead_days: int = 1) -> list[dict]:
    decisions = brier_audit.load_decisions()
    rows: list[dict] = []
    for d in decisions:
        try:
            r = brier_audit.brier_for_decision(d, lookahead_days=lookahead_days)
        except Exception:
            continue
        if r is None:
            continue
        freshness = freshness_weight_for_decision(d)
        rows.append({**r, "decision": d, "freshness": freshness})
    return rows


def weighted_brier(rows: list[dict]) -> dict:
    if not rows:
        return {"mean_brier_raw": 0.0, "mean_brier_weighted": 0.0, "weight_sum": 0.0, "n": 0}
    total_w = sum(r["freshness"] for r in rows)
    if total_w <= 0:
        return {"mean_brier_raw": 0.0, "mean_brier_weighted": 0.0, "weight_sum": 0.0, "n": len(rows)}
    weighted = sum(r["brier"] * r["freshness"] for r in rows) / total_w
    raw = sum(r["brier"] for r in rows) / len(rows)
    return {
        "mean_brier_raw": raw,
        "mean_brier_weighted": weighted,
        "delta_weighted_minus_raw": weighted - raw,
        "weight_sum": total_w,
        "n": len(rows),
    }


def freshness_bin_table(rows: list[dict], n_bins: int = 5) -> list[dict]:
    if not rows:
        return []
    bins: list[list[dict]] = [[] for _ in range(n_bins)]
    for r in rows:
        idx = min(int(r["freshness"] * n_bins), n_bins - 1)
        bins[idx].append(r)
    table = []
    for i, group in enumerate(bins):
        if not group:
            continue
        avg_fresh = statistics.fmean(g["freshness"] for g in group)
        avg_brier = statistics.fmean(g["brier"] for g in group)
        table.append({
            "freshness_bin_lo": i / n_bins,
            "freshness_bin_hi": (i + 1) / n_bins,
            "n": len(group),
            "avg_freshness": avg_fresh,
            "avg_brier": avg_brier,
        })
    return table


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookahead", type=int, default=1)
    parser.add_argument("--n-bins", type=int, default=5)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    print(f"[staleness] loading resolved predictions (lookahead={args.lookahead}d)…")
    rows = load_resolved_with_freshness(args.lookahead)
    if not rows:
        print("[staleness] no resolved decisions found")
        return 0

    summary = weighted_brier(rows)
    table = freshness_bin_table(rows, args.n_bins)
    payload = {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lookahead_days": args.lookahead,
        "summary": summary,
        "freshness_bins": table,
    }

    out_path = Path(args.out) if args.out else REPO / "data-snapshots" / f"staleness-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))

    print(f"[staleness] n={summary['n']}, raw Brier={summary['mean_brier_raw']:.4f}, "
          f"freshness-weighted Brier={summary['mean_brier_weighted']:.4f}, "
          f"delta={summary['delta_weighted_minus_raw']:+.4f}")
    for bin_row in table:
        print(f"  fresh[{bin_row['freshness_bin_lo']:.1f}-{bin_row['freshness_bin_hi']:.1f}] "
              f"n={bin_row['n']:3d} avg_fresh={bin_row['avg_freshness']:.2f} avg_brier={bin_row['avg_brier']:.3f}")
    print(f"[staleness] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
