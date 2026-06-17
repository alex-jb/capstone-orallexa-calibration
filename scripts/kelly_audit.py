#!/usr/bin/env python3
"""kelly_audit.py — confidence-shrunk Kelly sizing audit (Phase 1 #5).

Reads the most-recent ECE result from data-snapshots/ece-YYYY-MM-DD.json
and applies confidence_shrunk_kelly to a synthetic set of forecasts. The
output answers two questions:

1. How much would the agent have bet on each recent forecast under raw
   Kelly vs confidence-shrunk Kelly?
2. What is the total bankroll exposure reduction the calibration discipline
   would have produced?

The script is **measurement-only** during Phase 1. Position sizing in the
live paper-trading harness (lives in ~/.orallexa/markets/scripts) is not
modified by running this. The output is a journal artifact for the
capstone thesis defending the claim that calibration discipline + Kelly
shrinkage is a deployable risk-sizing control.

Output: data-snapshots/kelly-YYYY-MM-DD.json

Run manually:
    python3 scripts/kelly_audit.py [--win-loss-ratio 1.5] [--max-fraction 0.25]
"""
from __future__ import annotations

import argparse
import json
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
    print(f"[kelly] could not import brier_audit from {ORALLEXA_SCRIPTS}: {e}",
          file=sys.stderr)
    sys.exit(1)

from calibration.kelly import kelly_fraction, confidence_shrunk_kelly


def load_latest_ece() -> dict | None:
    snapshots = sorted((REPO / "data-snapshots").glob("ece-*.json"))
    if not snapshots:
        return None
    return json.loads(snapshots[-1].read_text())


def load_recent_forecasts(lookahead_days: int = 1, top_n: int = 30) -> list[dict]:
    decisions = brier_audit.load_decisions()
    rows: list[dict] = []
    for d in decisions:
        try:
            r = brier_audit.brier_for_decision(d, lookahead_days=lookahead_days)
        except Exception:
            continue
        if r is None:
            continue
        p = r.get("forecast_p", r.get("p"))
        if p is None:
            continue
        rows.append({"ticker": d.get("ticker", "?"), "decision": d.get("decision", "?"),
                     "p": float(p), "brier": float(r["brier"])})
    return rows[-top_n:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookahead", type=int, default=1)
    parser.add_argument("--top-n", type=int, default=30,
                        help="apply Kelly sizing to last N forecasts")
    parser.add_argument("--win-loss-ratio", type=float, default=1.5,
                        help="b = payoff per dollar lost; default 1.5")
    parser.add_argument("--max-fraction", type=float, default=0.25,
                        help="quarter Kelly cap (default 0.25)")
    parser.add_argument("--ece-max", type=float, default=0.25,
                        help="ECE shrinkage saturation (default 0.25)")
    args = parser.parse_args()

    ece_payload = load_latest_ece()
    if not ece_payload:
        print("[kelly] no ECE snapshot found in data-snapshots/ — run scripts/ece_audit.py first",
              file=sys.stderr)
        return 2
    current_ece = float(ece_payload.get("ece_raw", ece_payload.get("ece", 0.10)))

    rows = load_recent_forecasts(args.lookahead, args.top_n)
    if not rows:
        print("[kelly] no recent forecasts to size")
        return 0

    audit_rows = []
    raw_total = 0.0
    shrunk_total = 0.0
    for row in rows:
        result = confidence_shrunk_kelly(
            p_win=row["p"],
            win_loss_ratio=args.win_loss_ratio,
            ece=current_ece,
            ece_max=args.ece_max,
            max_fraction=args.max_fraction,
        )
        audit_rows.append({
            "ticker": row["ticker"],
            "decision": row["decision"],
            "forecast_p": row["p"],
            "raw_kelly": result.raw_kelly,
            "shrunk_kelly": result.shrunk_kelly,
            "capped_kelly": result.capped_kelly,
            "shrinkage_factor": result.shrinkage_factor,
        })
        raw_total += max(result.raw_kelly, 0)
        shrunk_total += max(result.capped_kelly, 0)

    summary = {
        "ece_input": current_ece,
        "win_loss_ratio": args.win_loss_ratio,
        "max_fraction_cap": args.max_fraction,
        "ece_max": args.ece_max,
        "n_forecasts": len(rows),
        "raw_total_exposure": raw_total,
        "shrunk_total_exposure": shrunk_total,
        "exposure_reduction_pct": (
            100.0 * (raw_total - shrunk_total) / raw_total if raw_total > 0 else 0.0
        ),
    }

    payload = {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "audit_rows": audit_rows,
    }

    out_path = REPO / "data-snapshots" / f"kelly-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))

    print(f"[kelly] n={summary['n_forecasts']} forecasts, ECE input={current_ece:.4f}")
    print(f"[kelly] raw Kelly total exposure = {raw_total*100:.1f}% bankroll")
    print(f"[kelly] confidence-shrunk + capped total exposure = {shrunk_total*100:.1f}% bankroll")
    print(f"[kelly] exposure reduction from calibration discipline = "
          f"{summary['exposure_reduction_pct']:.1f}%")
    print(f"[kelly] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
