# Changelog

Capstone thesis: *Calibration Discipline as the Audit Primitive for Spatial Pre-Trade Compliance in Live Trading.*
Repository tracks the 6-module Phase 1 calibration core + Week-by-week empirical artifacts. Dates are NY local.

---

## 2026-06-17 — Phase 1 #3-#6 wire-up + launchd cron + week-4 plan

### Added

- **`scripts/reflexion_retro.py`** — nightly retro loop wire-up (Phase 1 #3). Reads the day's worst-Brier decisions via `brier_audit`, generates rule-based Reflexion entries (`--use-anthropic` available for Claude generation), appends to `data-snapshots/reflexion_log.jsonl`. Uses existing `calibration.reflexion.append_jsonl`.
- **`scripts/staleness_audit.py`** — staleness-weighted Brier audit (Phase 1 #4). Sibling to `ece_audit.py`. Weights each resolved decision by geometric-mean exponential decay across cited source ages (polymarket_midpoint=5min, news=6h, etc). Outputs `data-snapshots/staleness-YYYY-MM-DD.json` with raw vs freshness-weighted Brier delta + 5-bin freshness histogram.
- **`scripts/kelly_audit.py`** — confidence-shrunk Kelly sizing audit (Phase 1 #5). Loads latest ECE snapshot, applies `confidence_shrunk_kelly` to last N forecasts, reports raw vs shrunk-and-capped bankroll exposure + percent reduction from calibration discipline. Measurement-only; does not modify live paper-trading sizing.
- **`scripts/dgm_proposal_demo.py`** — first synthetic Darwin-Gödel self-modification proposal (Phase 1 #6). Generates 3 synthetic `MergeProposal` (one APPROVE-worthy, one below-Brier-threshold, one missing human approval), runs each through the merge gate. Smoke-tested 2026-06-17: 1 APPROVE + 1 BLOCK_NO_BRIER_GAIN + 1 BLOCK_NO_HUMAN_APPROVAL. First artifact for the constrained-D-G thesis claim.
- **`cron/` directory** with 4 launchd plists + install README — `com.alexji.capstone.{reflexion-retro,staleness-audit,kelly-audit,dgm-proposal-demo}.plist` scheduled 23:00 / 23:15 / 23:30 daily + Sundays 22:00 respectively.
- **`proposal/week-4-project-plan-and-gantt.{md,pdf}`** — 184-line Week 4 project plan (Phase 1 calibration core weeks 4-6 + Phase 2 spatial enforcement weeks 7-10, August 12 defendable claim rests on Phase 1).

### Notes

- All four wire-up scripts import the existing `src/calibration/` modules cleanly. None duplicate logic from the modules — the scripts are pure plumbing that exercises the existing API surface.
- The `dgm_proposal_demo.py` exit code 0 even when proposals are blocked. Blocking is the *intended* outcome of the discipline, not a failure mode.

---

## Earlier — Phase 1 #1 + #2 + Week 1-3 prototype

### Added (chronologically)

- **`src/calibration/ece.py`** — Binned Expected Calibration Error (Guo 2017). `ReliabilityBin` dataclass. Phase 1 #1.
- **`src/calibration/temperature.py`** — NLL loss + temperature fit (scipy bounded Brent) + `apply_temperature`. Phase 1 #1.
- **`src/calibration/reliability.py`** — `ReliabilityDiagramData` dataclass for matplotlib plotting.
- **`src/calibration/self_calibration.py`** — Kadavath 2022 second-order self-calibration prompt template + `parse_response` + `apply_decision_gate`. Phase 1 #2.
- **`src/calibration/reflexion.py`** — Reflexion dataclass (cause ≤200, lesson ≤240, forward_prompt ≤240), JSONL append/load, `build_forward_context`.
- **`src/calibration/staleness.py`** — exponential decay with per-source half-life dictionary (8 sources).
- **`src/calibration/kelly.py`** — Kelly fraction + confidence-shrunk Kelly with max_fraction cap (default 0.25 = quarter Kelly).
- **`src/calibration/self_modification.py`** — `MergeProposal` + `MergeDecision` + `MergeStatus` enum. `evaluate()` requires Brier delta ≥ 0.005 AND human_approved AND held_out_n ≥ 30.
- **`scripts/ece_audit.py`** — live ECE audit. 2026-06-17 result on n=279: ECE 0.0459, T* = 5.474 (severe overconfidence detected).
- **`scripts/sc_audit.py`** — live Claude Haiku 4.5 second-order audit. 2026-06-17 result on n=8 last 24h BUY/SELL: avg SOC 0.338, demote rate 100%.
- **`scripts/weekly_brier_report.py`** — Sunday weekly Brier summary.
- **`tests/test_calibration.py`** + **`tests/test_phase1_upgrades.py`** — 64 unit tests covering all 6 calibration modules.

---

## Backlog / next milestones

- Phase 1 #4 cron first fire (waits for 23:15 NY local 2026-06-17).
- Phase 1 #5 paper-trading harness wiring (not yet; lives in `~/.orallexa/markets/scripts/`).
- Phase 1 #6 first non-synthetic proposal from Reflexion-clustered lessons.
- August 12 capstone defense materials freeze.
- ICAIF 2027 paper draft (target submission ~2026-09-15).
- Phase 4 EU AI Act + ECOA evaluation study design (lives in sibling repo `embodied-compliance-council/docs/phase-4-eu-ai-act-evaluation-design.md`).
