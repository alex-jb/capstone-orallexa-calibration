#!/usr/bin/env python3
"""ece_audit.py — nightly Expected Calibration Error audit for Orallexa.

Sibling to brier_audit.py (lives in ~/.orallexa/markets/scripts/) — same
data source (decision_log.json), same outcome-resolution logic (close-vs-
entry at lookahead_days), but reports:

    - ECE (10-bin Expected Calibration Error)
    - Reliability diagram bins (printed as a table)
    - Optimal temperature T* fit on a chronological held-out fold
    - ECE after temperature scaling
    - Brier delta (raw vs temperature-scaled)

Output: capstone-orallexa-calibration/data-snapshots/ece-YYYY-MM-DD.json

This is **measurement-only** during Phase 1 (Weeks 4-6 of capstone).
Live trading behavior is NOT modified. Temperature scaling produces an
additional calibrated probability channel for ECE reporting; the raw
channel continues to drive BUY/WAIT/SELL decisions until Week 7+.

Run manually:
    python3 scripts/ece_audit.py [--lookahead 1] [--n-bins 10]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

# Reuse brier_audit's outcome-resolution logic.
ORALLEXA_SCRIPTS = Path.home() / ".orallexa" / "markets" / "scripts"
sys.path.insert(0, str(ORALLEXA_SCRIPTS))

import numpy as np

from calibration import (
    expected_calibration_error,
    fit_temperature,
    apply_temperature,
    reliability_diagram_data,
)

# Import the existing brier_audit module to reuse outcome resolution.
try:
    import brier_audit
except ImportError as e:
    print(f"[ece] could not import brier_audit from {ORALLEXA_SCRIPTS}: {e}",
          file=sys.stderr)
    print("[ece] If running on a fresh machine, ensure the orallexa markets "
          "scripts are installed at ~/.orallexa/markets/scripts/.",
          file=sys.stderr)
    sys.exit(2)


OUT_DIR = REPO_ROOT / "data-snapshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_resolved_predictions(lookahead_days: int = 1) -> list[dict]:
    """Walk decision_log, resolve every BUY/SELL decision old enough to have
    a price-action outcome, return (forecast_p, actual, ticker, timestamp) rows.
    """
    decisions = brier_audit.load_decisions()
    today = datetime.now(timezone.utc).date()
    out = []
    for d in decisions:
        ts = d.get("timestamp", "")
        if not ts:
            continue
        try:
            d_date = datetime.fromisoformat(ts).date()
        except ValueError:
            continue
        # Need at least lookahead_days + 2 calendar days to be safe (weekends).
        if (today - d_date).days < lookahead_days + 2:
            continue
        r = brier_audit.brier_for_decision(d, lookahead_days=lookahead_days)
        if r is None:
            continue
        out.append(r)
    return out


def chronological_split(rows: list[dict], val_fraction: float = 0.25):
    """Split rows chronologically into train, val.

    Temperature must be fit on a *held-out* set to avoid leakage. We split
    by timestamp so the validation fold is strictly the newest decisions.
    """
    rows_sorted = sorted(rows, key=lambda r: r["timestamp"])
    n_val = max(10, int(len(rows_sorted) * val_fraction))
    if n_val >= len(rows_sorted):
        return rows_sorted, []
    train = rows_sorted[:-n_val]
    val = rows_sorted[-n_val:]
    return train, val


def _arrays(rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    p = np.array([r["forecast_p"] for r in rows], dtype=float)
    y = np.array([r["actual"] for r in rows], dtype=float)
    return p, y


def report(rows: list[dict], n_bins: int = 10, val_fraction: float = 0.25) -> dict:
    if len(rows) < 30:
        return {
            "status": "insufficient_data",
            "n": len(rows),
            "message": f"need ≥30 resolved predictions, have {len(rows)}",
        }

    p_all, y_all = _arrays(rows)
    ece_raw = expected_calibration_error(p_all, y_all, n_bins=n_bins)
    brier_raw = float(((p_all - y_all) ** 2).mean())

    diag = reliability_diagram_data(p_all, y_all, n_bins=n_bins)

    # Temperature scaling on a chronological train/val split.
    train, val = chronological_split(rows, val_fraction=val_fraction)
    if len(train) < 10 or len(val) < 10:
        temperature_block = {
            "status": "insufficient_split",
            "train_n": len(train),
            "val_n": len(val),
        }
    else:
        p_train, y_train = _arrays(train)
        p_val, y_val = _arrays(val)
        t_star = fit_temperature(p_train, y_train)
        p_val_calibrated = apply_temperature(p_val, t_star)
        p_all_calibrated = apply_temperature(p_all, t_star)
        ece_val_raw = expected_calibration_error(p_val, y_val, n_bins=n_bins)
        ece_val_cal = expected_calibration_error(
            p_val_calibrated, y_val, n_bins=n_bins
        )
        brier_all_cal = float(((p_all_calibrated - y_all) ** 2).mean())
        temperature_block = {
            "status": "fitted",
            "t_star": t_star,
            "train_n": len(train),
            "val_n": len(val),
            "val_ece_raw": ece_val_raw,
            "val_ece_calibrated": ece_val_cal,
            "val_ece_improvement": ece_val_raw - ece_val_cal,
            "brier_all_calibrated": brier_all_cal,
            "brier_all_improvement": brier_raw - brier_all_cal,
        }

    return {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n": len(rows),
        "n_bins": n_bins,
        "ece_raw": ece_raw,
        "brier_raw": brier_raw,
        "bins": [
            {
                "lo": b.lo,
                "hi": b.hi,
                "count": b.count,
                "avg_confidence": b.avg_confidence,
                "avg_accuracy": b.avg_accuracy,
                "gap": b.gap,
            }
            for b in diag.bins
        ],
        "temperature": temperature_block,
    }


def render_markdown(rep: dict) -> str:
    if rep["status"] != "ok":
        return f"# ECE audit — {rep['status']}\n\n{rep.get('message', '')}\n"

    lines = [
        "# Expected Calibration Error audit",
        "",
        f"- Generated: {rep['generated_at']}",
        f"- Resolved predictions: **{rep['n']}**",
        f"- Bins: {rep['n_bins']}",
        f"- **ECE (raw):** `{rep['ece_raw']:.4f}`",
        f"- **Brier (raw):** `{rep['brier_raw']:.4f}`",
        "",
        "## Reliability bins",
        "",
        "| Bin | n | Avg confidence | Avg accuracy | Gap |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for b in rep["bins"]:
        if b["count"] == 0:
            lines.append(
                f"| {b['lo']:.2f}–{b['hi']:.2f} | 0 | — | — | — |"
            )
            continue
        lines.append(
            f"| {b['lo']:.2f}–{b['hi']:.2f} | {b['count']} | "
            f"{b['avg_confidence']:.3f} | {b['avg_accuracy']:.3f} | "
            f"{b['gap']:+.3f} |"
        )
    lines.append("")

    t = rep["temperature"]
    if t["status"] == "fitted":
        t_star = t["t_star"]
        if t_star > 1.05:
            interp = "over-confident → soften"
        elif t_star < 0.95:
            interp = "under-confident → sharpen"
        else:
            interp = "roughly calibrated"
        lines += [
            "## Temperature scaling",
            "",
            f"- Train n: {t['train_n']}  ·  Val n: {t['val_n']}",
            f"- **T\\***: `{t_star:.3f}` ({interp})",
            f"- Val ECE (raw):       `{t['val_ece_raw']:.4f}`",
            f"- Val ECE (calibrated): `{t['val_ece_calibrated']:.4f}`",
            f"- Val ECE improvement: **`{t['val_ece_improvement']:+.4f}`**",
            f"- Brier all (calibrated): `{t['brier_all_calibrated']:.4f}`",
            f"- Brier improvement: **`{t['brier_all_improvement']:+.4f}`**",
            "",
        ]
    else:
        lines += [
            "## Temperature scaling",
            "",
            f"- Status: `{t['status']}`",
            "",
        ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookahead", type=int, default=1)
    ap.add_argument("--n-bins", type=int, default=10)
    ap.add_argument(
        "--val-fraction", type=float, default=0.25,
        help="Fraction of newest decisions used as held-out fold for temperature fit.",
    )
    args = ap.parse_args()

    print(f"[ece] loading resolved predictions (lookahead={args.lookahead}d)…")
    rows = load_resolved_predictions(args.lookahead)
    print(f"[ece] resolved n = {len(rows)}")

    rep = report(rows, n_bins=args.n_bins, val_fraction=args.val_fraction)

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_path = OUT_DIR / f"ece-{today_str}.json"
    md_path = OUT_DIR / f"ece-{today_str}.md"
    json_path.write_text(json.dumps(rep, indent=2))
    md_path.write_text(render_markdown(rep))
    print(f"[ece] wrote {json_path}")
    print(f"[ece] wrote {md_path}")

    if rep["status"] == "ok":
        print()
        print(f"  ECE (raw):       {rep['ece_raw']:.4f}")
        print(f"  Brier (raw):     {rep['brier_raw']:.4f}")
        t = rep["temperature"]
        if t["status"] == "fitted":
            print(f"  T* (held-out):   {t['t_star']:.3f}")
            print(f"  ECE improvement: {t['val_ece_improvement']:+.4f}")
            print(f"  Brier improv.:   {t['brier_all_improvement']:+.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
