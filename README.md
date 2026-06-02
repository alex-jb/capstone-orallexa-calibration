# Capstone — Orallexa Calibration (Summer 2026)

**Student:** Xiaoyu (Alex) Ji
**Program:** MS Computer Science, Yeshiva University
**Advisor:** TBD (request pending)
**Timeline:** 2026-06-02 → 2026-08-31 (13 weeks)

## One-line thesis

> A calibration-disciplined AI trading agent (Orallexa) can produce measurable Brier-score improvement over a market-implied baseline when scaled from paper to real capital at small sizes ($300-$5k), tested concurrently on prediction markets (Polymarket) and equity microstructure (SpaceX commercial-space sector).

## Why this is research, not a side project

1. **Falsifiability built into the data**: every prediction is timestamped on GitHub before the event resolves. No ex-post cherry-picking is possible.
2. **Brier score is the success metric**: a 50-year-old quantitative calibration measure (Brier 1950). Improvements are auditable from public logs.
3. **Real-money forcing function**: paper-only ML is famously over-optimistic. The agent has a hardcoded rule that real capital does not deploy until live paper P&L tracks backtest for ≥2 weeks.
4. **Negative results are publishable**: if Brier score does not improve, the post-mortem of *which* calibration assumption broke is the contribution.

## Three concrete deliverables

| ID | Deliverable | Current state | Summer-end target |
|---|---|---|---|
| D1 | Public SpaceX equity research feed | Live since 2026-05-12 at https://alex-jb.github.io/spacex-ipo-tracker | 90 days of timestamped picks scored Brier vs realized stock moves |
| D2 | Polymarket calibration paper | 14 days paper-validate in progress; backtest +60.9% win rate with ATR stops (n=128) | 4-8 weeks live paper-vs-real $300 cohort with side-by-side P&L delta + final paper |
| D3 | Open-source agent framework | Orallexa v0.2 published at https://github.com/alex-jb/orallexa-ai-trading-agent | Versioned v1.0 release + reproducible README + 1 external user actually runs it |

## Repository structure

```
proposal/         1-page formal proposal + bibliography
weekly-reports/   Brier-audit weekly aggregations (Sunday cron)
figures/          Generated plots (Brier-over-time, paper-vs-real P&L)
data-snapshots/   Anonymized prediction logs (read-only, append-only)
references/       PDF copies of cited papers (where licensing permits)
```

## Status board

- ✅ Daily Brier audit cron live (data in `weekly-reports/`)
- ✅ Public SpaceX picks feed live (50 days as of 2026-06-02 baseline)
- ✅ Polymarket decide pipeline live (`polymarket_decide.py`)
- ⚪ Real-money deployment pending paper validation (target: 2026-06-20)
- ⚪ Advisor signature pending (meeting scheduled 2026-06-02)
- ⚪ Final paper draft (target: 2026-08-15)

## Related repositories

- [orallexa-ai-trading-agent](https://github.com/alex-jb/orallexa-ai-trading-agent) — the trading agent itself (markets/ dir)
- [spacex-ipo-tracker](https://github.com/alex-jb/spacex-ipo-tracker) — public daily research feed (deliverable D1)
- [solo-founder-os](https://github.com/alex-jb/solo-founder-os) — supporting agent infrastructure (cost audit, evaluation harness)

## Honest caveats

- Single founder, no team. The capstone optimizes for what one person can credibly ship and audit in 13 weeks.
- Small capital ($300-$5k). The agent will not generate publishable economic findings at that size; what is publishable is the **methodology** and the **Brier calibration delta**.
- No GPU training. The agent composes outputs from foundation models (Claude Sonnet 4.6 + GPT) rather than fine-tuning. The contribution is in the composition layer + calibration feedback loop, not in model architecture.
