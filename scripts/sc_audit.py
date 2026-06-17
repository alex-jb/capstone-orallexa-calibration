#!/usr/bin/env python3
"""sc_audit.py — Self-Calibration audit (Phase 1 #2, Kadavath 2022).

For every recent BUY/SELL decision in decision_log.json, fire a
second-order Claude API call asking "how confident are you in that
confidence?". Parse the JSON response, aggregate the second-order
confidence distribution, and write a calibration-style report alongside
brier_audit and ece_audit.

Usage
-----
    # Dry-run (no API calls, just prints prompts)
    python3 scripts/sc_audit.py --dry-run

    # Live audit on yesterday's decisions
    ANTHROPIC_API_KEY=sk-ant-... python3 scripts/sc_audit.py

    # Or with a key file
    python3 scripts/sc_audit.py --key-file ~/.config/anthropic_key

    # Specific lookback window
    python3 scripts/sc_audit.py --hours-back 48 --max-decisions 30

Output
------
- data-snapshots/sc-YYYY-MM-DD.json
- data-snapshots/sc-YYYY-MM-DD.md

What you read in the report
---------------------------
- n decisions audited (BUY/SELL only; WAIT is skipped)
- average second-order confidence
- demote rate (fraction that would be demoted to WAIT under the gate)
- distribution of primary_doubt strings (cluster the cause categories)
- per-ticker breakdown (which tickers tend to produce low-confidence forecasts)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

ORALLEXA_SCRIPTS = Path.home() / ".orallexa" / "markets" / "scripts"
sys.path.insert(0, str(ORALLEXA_SCRIPTS))

from calibration import (  # noqa: E402
    SelfCalibrationResult,
    apply_decision_gate,
    build_self_cal_prompt,
    parse_self_cal_response,
)

try:
    import brier_audit  # noqa: E402
except ImportError as e:
    print(f"[sc] could not import brier_audit: {e}", file=sys.stderr)
    sys.exit(2)


OUT_DIR = REPO_ROOT / "data-snapshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


DEFAULT_MODEL = "claude-haiku-4-5-20251001"  # cheap+fast for batch audit


def load_recent_directional_decisions(
    hours_back: int = 24, max_n: int = 50
) -> list[dict]:
    """Pull recent BUY/SELL decisions (skip WAIT — they have no claim to audit)."""
    decisions = brier_audit.load_decisions()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours_back)
    out = []
    for d in decisions:
        if d.get("decision") not in ("BUY", "SELL"):
            continue
        ts = d.get("timestamp", "")
        if not ts:
            continue
        try:
            d_ts = datetime.fromisoformat(ts)
            if d_ts.tzinfo is None:
                d_ts = d_ts.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if d_ts < cutoff:
            continue
        out.append(d)
    # newest first
    out.sort(key=lambda d: d["timestamp"], reverse=True)
    return out[:max_n]


def _forecast_p(d: dict) -> float:
    """Extract the directional forecast probability for the chosen side."""
    probs = d.get("probabilities", {})
    if d["decision"] == "BUY":
        return float(probs.get("up", 0.5))
    return float(probs.get("down", 0.5))


def read_api_key(key_file: str | None) -> str | None:
    """Prefer env var, fall back to a key file."""
    env = os.environ.get("ANTHROPIC_API_KEY")
    if env:
        return env.strip()
    if key_file:
        p = Path(key_file).expanduser()
        if p.exists():
            return p.read_text().strip()
    default = Path.home() / ".config" / "anthropic_key"
    if default.exists():
        return default.read_text().strip()
    return None


def call_claude(prompt: str, model: str, api_key: str) -> str:
    """Single Claude API call. Returns the raw text response."""
    try:
        from anthropic import Anthropic
    except ImportError:
        raise RuntimeError(
            "anthropic SDK not installed. `pip install anthropic` first."
        )
    client = Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    if not resp.content:
        return ""
    block = resp.content[0]
    return getattr(block, "text", "") or ""


def audit_one(
    d: dict,
    *,
    threshold: float,
    model: str,
    api_key: str | None,
    dry_run: bool,
) -> dict:
    """Audit one decision. Returns a record dict suitable for the report."""
    ticker = d["ticker"]
    decision = d["decision"]
    forecast_p = _forecast_p(d)
    if not 0 < forecast_p < 1:
        return {
            "ticker": ticker, "timestamp": d["timestamp"],
            "decision": decision, "forecast_p": forecast_p,
            "status": "skip_bad_probability",
        }
    prompt = build_self_cal_prompt(ticker, decision, forecast_p)
    if dry_run:
        return {
            "ticker": ticker, "timestamp": d["timestamp"],
            "decision": decision, "forecast_p": forecast_p,
            "status": "dry_run", "prompt_preview": prompt[:140],
        }
    if not api_key:
        return {
            "ticker": ticker, "timestamp": d["timestamp"],
            "decision": decision, "forecast_p": forecast_p,
            "status": "missing_api_key",
        }
    try:
        raw = call_claude(prompt, model=model, api_key=api_key)
    except Exception as e:
        return {
            "ticker": ticker, "timestamp": d["timestamp"],
            "decision": decision, "forecast_p": forecast_p,
            "status": "api_error", "error": str(e)[:200],
        }
    try:
        sc = parse_self_cal_response(raw, threshold=threshold)
    except ValueError as e:
        return {
            "ticker": ticker, "timestamp": d["timestamp"],
            "decision": decision, "forecast_p": forecast_p,
            "status": "parse_error", "error": str(e)[:200],
            "raw_preview": raw[:200],
        }
    final_decision = apply_decision_gate(decision, sc)
    return {
        "ticker": ticker, "timestamp": d["timestamp"],
        "decision": decision, "forecast_p": forecast_p,
        "status": "ok",
        "second_order_confidence": sc.second_order_confidence,
        "primary_doubt": sc.primary_doubt,
        "would_size_full_kelly": sc.would_size_full_kelly,
        "passes_threshold": sc.passes_threshold,
        "threshold": sc.threshold,
        "gated_decision": final_decision,
        "demoted": final_decision != decision,
    }


def aggregate(records: list[dict]) -> dict:
    ok = [r for r in records if r["status"] == "ok"]
    if not ok:
        return {
            "n_total": len(records),
            "n_ok": 0,
            "message": "no successfully audited decisions",
        }
    soc = [r["second_order_confidence"] for r in ok]
    demoted = [r for r in ok if r["demoted"]]
    per_ticker: dict[str, list[float]] = {}
    for r in ok:
        per_ticker.setdefault(r["ticker"], []).append(r["second_order_confidence"])
    doubts: dict[str, int] = {}
    for r in ok:
        d = (r["primary_doubt"] or "").strip().lower()[:60]
        if d and d != "none":
            doubts[d] = doubts.get(d, 0) + 1
    return {
        "n_total": len(records),
        "n_ok": len(ok),
        "avg_second_order_confidence": sum(soc) / len(soc),
        "min_second_order_confidence": min(soc),
        "max_second_order_confidence": max(soc),
        "demote_rate": len(demoted) / len(ok),
        "per_ticker_avg_soc": {
            k: sum(v) / len(v) for k, v in per_ticker.items()
        },
        "top_doubt_clusters": sorted(
            doubts.items(), key=lambda kv: -kv[1]
        )[:10],
    }


def render_markdown(stats: dict, records: list[dict], threshold: float) -> str:
    lines = [
        "# Self-Calibration audit",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Decisions probed: **{stats['n_total']}**",
        f"- Successfully audited: **{stats['n_ok']}**",
        f"- Threshold (demote ↓): `{threshold:.2f}`",
        "",
    ]
    if stats["n_ok"] == 0:
        lines += ["No successfully audited decisions.", ""]
        return "\n".join(lines)
    lines += [
        f"- Avg second-order confidence: **`{stats['avg_second_order_confidence']:.3f}`**",
        f"- Range: `{stats['min_second_order_confidence']:.3f}` – `{stats['max_second_order_confidence']:.3f}`",
        f"- **Demote rate: `{stats['demote_rate']:.1%}`** (fraction of BUY/SELL → WAIT under the gate)",
        "",
        "## Per-ticker average second-order confidence",
        "",
        "| Ticker | Avg SOC |",
        "| --- | ---: |",
    ]
    for ticker, soc in sorted(
        stats["per_ticker_avg_soc"].items(), key=lambda kv: kv[1]
    ):
        lines.append(f"| {ticker} | `{soc:.3f}` |")
    lines += [
        "",
        "## Top primary-doubt clusters",
        "",
    ]
    if stats["top_doubt_clusters"]:
        for doubt, count in stats["top_doubt_clusters"]:
            lines.append(f"- {count}× — *{doubt}*")
    else:
        lines.append("- (none reported above 'none')")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours-back", type=int, default=24)
    ap.add_argument("--max-decisions", type=int, default=50)
    ap.add_argument("--threshold", type=float, default=0.60)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument(
        "--key-file", default=None,
        help="Path to a file containing ANTHROPIC_API_KEY (default: env var, "
        "then ~/.config/anthropic_key).",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Don't call the API; print prompt previews instead.",
    )
    ap.add_argument("--rate-limit-ms", type=int, default=250,
        help="Sleep between API calls to avoid 429s.")
    args = ap.parse_args()

    decisions = load_recent_directional_decisions(
        hours_back=args.hours_back, max_n=args.max_decisions
    )
    print(f"[sc] found {len(decisions)} BUY/SELL decisions in the last "
          f"{args.hours_back}h")
    if not decisions:
        print("[sc] nothing to audit. Exiting.")
        return 0

    api_key = None if args.dry_run else read_api_key(args.key_file)
    if not args.dry_run and not api_key:
        print(
            "[sc] no API key found (env ANTHROPIC_API_KEY, --key-file, or "
            "~/.config/anthropic_key). Run with --dry-run for a no-API preview.",
            file=sys.stderr,
        )
        return 3

    records = []
    for i, d in enumerate(decisions, 1):
        rec = audit_one(
            d,
            threshold=args.threshold,
            model=args.model,
            api_key=api_key,
            dry_run=args.dry_run,
        )
        records.append(rec)
        flag = "✓" if rec["status"] == "ok" else f"!{rec['status']}"
        print(f"[sc] {i:3d}/{len(decisions)} {rec['ticker']:5s} "
              f"{rec['decision']:4s} p={rec['forecast_p']:.3f}  {flag}")
        if not args.dry_run and rec["status"] == "ok":
            time.sleep(args.rate_limit_ms / 1000.0)

    stats = aggregate(records)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_path = OUT_DIR / f"sc-{today}.json"
    md_path = OUT_DIR / f"sc-{today}.md"
    json_path.write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(),
         "threshold": args.threshold, "model": args.model,
         "stats": stats, "records": records},
        indent=2,
    ))
    md_path.write_text(render_markdown(stats, records, args.threshold))
    print()
    print(f"[sc] wrote {json_path}")
    print(f"[sc] wrote {md_path}")
    if stats["n_ok"] > 0:
        print()
        print(f"  Avg SOC:      {stats['avg_second_order_confidence']:.3f}")
        print(f"  Demote rate:  {stats['demote_rate']:.1%}")
        if stats["top_doubt_clusters"]:
            print(f"  Top doubt:    {stats['top_doubt_clusters'][0][0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
