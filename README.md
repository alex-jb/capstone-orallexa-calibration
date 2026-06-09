# Capstone — Orallexa Calibration (Summer 2026)

**English** | [中文](README.zh-CN.md)

**Student:** Xiaoyu (Alex) Ji
**Program:** MS Computer Science, Yeshiva University
**Advisor:** Prof. Michael Yang (Capstone in Computer Science I)
**Timeline:** 2026-06-02 → 2026-08-31 (13 weeks)
**Last updated:** 2026-06-09 (Week 2)

## One-line thesis

> A calibration-disciplined AI trading agent (Orallexa) can produce measurable Brier-score improvement over a market-implied baseline when scaled from paper to real capital at small sizes ($300-$5k), tested concurrently on prediction markets (Polymarket) and equity microstructure (SpaceX commercial-space sector).

## Why this is research, not a side project

1. **Falsifiability built into the data**: every prediction is timestamped on GitHub before the event resolves. No ex-post cherry-picking is possible.
2. **Brier score is the success metric**: a 50-year-old quantitative calibration measure (Brier 1950). Improvements are auditable from public logs.
3. **Real-money forcing function**: paper-only ML is famously over-optimistic. The agent has a hardcoded rule that real capital does not deploy until live paper P&L tracks backtest for ≥2 weeks **AND** a walk-forward gate (mean OOS Sharpe > 0.5 across 4 sliding windows) passes.
4. **Negative results are publishable**: if Brier score does not improve, the post-mortem of *which* calibration assumption broke is the contribution. **Week 2 has already produced 4 such postmortems** — they are the early empirical content of the capstone, not a setback.

## Three concrete deliverables

| ID | Deliverable | Current state (2026-06-09) | Summer-end target |
|---|---|---|---|
| D1 | Public SpaceX equity research feed | 28 days live since 2026-05-12 at https://alex-jb.github.io/spacex-ipo-tracker | 90 days of timestamped picks scored Brier vs realized stock moves |
| D2 | Polymarket calibration paper | **Backtest invalidated** (in-sample +60.9% won't replicate OOS). Walk-forward gate verdict FAIL (mean OOS Sharpe -3.08). Real-money paused. Paper still being recorded. | 4-8 weeks live paper-vs-real $300 cohort — only after walkforward gate passes — with side-by-side P&L delta + final paper |
| D3 | Open-source agent framework | Orallexa v0.2 published at https://github.com/alex-jb/orallexa-ai-trading-agent. **2026-06 shipped 3 adjacent OSS calibration tools** (council-diff, council-diff-py, memory-wall-tracker, postmortems collection). | Versioned v1.0 release + reproducible README + 1 external user actually runs it |

## Week 1-2 progress and empirical findings (2026-06-02 → 2026-06-09)

The first two weeks produced **4 calibration-grade negative findings**. Each is documented as a standalone postmortem with date, root cause, code-level fix attempt, and capital impact. All are public at https://github.com/alex-jb/alex-brain/tree/main/postmortems and mirrored at vibexforge.com/postmortems.

### F1 — Walk-forward gate verdict: FAIL (2026-06-08)
- Backtest reported +$5,950 / 60.9% win rate / 128 trades on the last 30 days.
- Walk-forward validation (sliding train/test windows): mean OOS Sharpe **-3.08**, worst-window Sharpe **-4.23**, mean win rate **31.6%** (-29.3 percentage points OOS vs in-sample).
- **Root cause**: invisible `--use-atr-stops` CLI flag was passed in eval but not in production cron. The "great" backtest measured a code path that never ran in production. The canonical look-ahead bias.
- **Methodology contribution**: walk-forward gate (`scripts/walkforward.py`) is now a hardcoded gate before any real money. Mean OOS Sharpe must exceed 0.5 across 4 rolling windows. Currently FAIL. No real money trades.

### F2 — Paper P&L invalidates the Brier-only success metric (2026-05-27)
- 14-day paper portfolio simulator: **-$1,015 / -10.16% / 25.6% win rate / 26 stops out of 39 trades**.
- The Brier score over the same period was a healthy 0.196 (well below 0.25 coin-flip baseline).
- **Methodology contribution**: Brier (probability calibration) and Sharpe (directional edge) measure orthogonal dimensions. A system can pass the Brier gate while losing money. This is reported in the capstone literature review as an underspecified failure mode in calibration-honest agent papers (Brier 1950 measures the right thing; it does not measure *the only* thing).

### F3 — Ensemble inflation: 5 personas ≠ 5 voters (2026-06-05)
- A 5-persona LLM debate ensemble (Bull / Bear / Judge / Critic / Auditor) was returning 5/5 BUY consensus on individual tickers.
- Empirical bias correlation across personas of the same Claude model with shared RAG context: ≈ 0.6, not 0.
- **Methodology contribution**: shipped a shrinkage layer (`ensemble_shrinkage.py`, λ=0.4 empirically tuned) that demotes 5/5 ensemble agreement toward the prior. Plus a `sports_brier` n<30 verdict guard that refuses to publish a probability verdict on fewer than 30 settled outcomes.
- This generalizes to any multi-persona LLM ensemble where prompts share a model + context — applicable beyond trading.

### F4 — Rule enforcement test: SPCX IPO 6/12 SKIP (2026-06-09)
- Robinhood IPO Access granted 4 shares × $162 max ($648 cap) on SPCX for 2026-06-12.
- 5-persona ensemble returned BUY consensus. SpaceX-IPO-Tracker public feed had been publishing positive thesis for 28 days.
- Walk-forward verdict was still FAIL.
- **The hardcoded rule was enforced**: no real money. The capstone treats "publishing the SKIP decision with reasoning" as a calibration discipline test, not as research finding F1/F2/F3 are.

## Adjacent OSS contributions shipped in 2026-06

These are not additional deliverables; they are calibration tooling spun out of the capstone work that benefit from being publicly versioned, MIT-licensed, and citable in the final paper.

- **[council-diff](https://github.com/alex-jb/council-diff)** (TypeScript, MIT) — 5-voice AI council debate library with a Brier audit module. Generalization of the trading-stack debate layer to founder / engineer / investor / career / product / quant domains.
- **[council-diff-py](https://github.com/alex-jb/council-diff-py)** (Python, MIT) — Python port of council-diff with the same Brier audit math, persistence-agnostic. `pip install council-diff`.
- **[memory-wall-tracker](https://github.com/alex-jb/memory-wall-tracker)** (Python, MIT) — Brier-audited daily research feed on Druckenmiller's Q1 2026 AI inference memory basket (AVGO/INTC/ARM/MU/STX/WDC). Test bed for cross-asset calibration: prediction-market verdicts (Polymarket) vs equity-microstructure verdicts (this basket) under one Brier scoreboard.
- **[Postmortems collection](https://github.com/alex-jb/alex-brain/tree/main/postmortems)** — 4 calibration-honest negative results published with `resolve_by` dates. Cited in the final paper as the empirical contribution from the 13-week window.

## Repository structure

```
proposal/         1-page formal proposal + bibliography
weekly-reports/   Brier-audit weekly aggregations (Sunday cron)
figures/          Generated plots (Brier-over-time, paper-vs-real P&L, walk-forward verdict)
data-snapshots/   Anonymized prediction logs (read-only, append-only)
references/       PDF copies of cited papers (where licensing permits)
scripts/          Cracked Score Phase 2 POC + weekly Brier auto-gen
```

## Status board (2026-06-09)

- ✅ Daily Brier audit cron live (data in `weekly-reports/`)
- ✅ Public SpaceX picks feed live (28 days as of 2026-06-09)
- ✅ Polymarket decide pipeline live (`polymarket_decide.py`)
- ✅ Walk-forward validation framework shipped (`scripts/walkforward.py`)
- ✅ Ensemble shrinkage layer shipped (`ensemble_shrinkage.py`, λ=0.4)
- ✅ 4 postmortems published with dated `resolve_by` (F1/F2/F3/F4 above)
- ✅ Adjacent OSS calibration tools shipped (council-diff / council-diff-py / memory-wall-tracker)
- 🛑 Real-money deployment **BLOCKED** by walk-forward gate (currently FAIL). Re-eval 2026-06-23.
- ⚪ Advisor signature pending — Prof. Michael Yang (first meeting being scheduled)
- ⚪ Final paper draft (target: 2026-08-15)

## Related repositories

- [orallexa-ai-trading-agent](https://github.com/alex-jb/orallexa-ai-trading-agent) — the trading agent itself (markets/ dir)
- [spacex-ipo-tracker](https://github.com/alex-jb/spacex-ipo-tracker) — public daily research feed (deliverable D1)
- [solo-founder-os](https://github.com/alex-jb/solo-founder-os) — supporting agent infrastructure (cost audit, evaluation harness)
- [council-diff](https://github.com/alex-jb/council-diff) + [council-diff-py](https://github.com/alex-jb/council-diff-py) — generalized 5-voice debate library with Brier audit
- [memory-wall-tracker](https://github.com/alex-jb/memory-wall-tracker) — Brier-audited equity research feed
- [alex-brain/postmortems](https://github.com/alex-jb/alex-brain/tree/main/postmortems) — calibration-honest failure log

## Honest caveats

- Single founder, no team. The capstone optimizes for what one person can credibly ship and audit in 13 weeks.
- Small capital ($300-$5k). The agent will not generate publishable economic findings at that size; what is publishable is the **methodology** and the **Brier calibration delta**.
- No GPU training. The agent composes outputs from foundation models (Claude Sonnet 4.6 + GPT) rather than fine-tuning. The contribution is in the composition layer + calibration feedback loop, not in model architecture.
- **Week 2 update**: the calibration delta itself is currently a negative result. The contribution is the documented methodology of how four different layers (look-ahead bias, Brier-vs-Sharpe orthogonality, ensemble inflation, and rule-enforcement discipline) each broke. The final paper will report these as empirical findings whether or not the walk-forward gate passes by 2026-08-31.

## Citation (provisional)

```
Ji, X. (2026). Orallexa Calibration: A Brier-audited multi-agent trading
research framework. MS Capstone, Yeshiva University.
Public audit log: github.com/alex-jb/alex-brain/postmortems
```
