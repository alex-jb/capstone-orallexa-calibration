# Formal Capstone Proposal — Summer 2026

**Title:** From Paper to Production: Calibration Discipline in a Solo-Operated AI Trading Agent

**Student:** Xiaoyu (Alex) Ji · MS CS · Yeshiva University
**Proposed advisor:** [TBD — pending faculty signature]
**Submission date:** 2026-06-02

---

## 1. Problem statement

Most academic work on AI-driven trading evaluates models on backtests over historical data. The literature reports calibration metrics (Brier score, log-loss, expected calibration error) on closed datasets where the answer key is known. **What is rarely measured is whether these calibration claims survive the wild** — adversarial real-time markets where information staleness, latency, and other agents trading the same signal degrade predictive quality.

This capstone asks: *can a single-developer AI trading agent maintain measurable Brier-score improvement over a market-implied baseline when deployed in production with real capital at small sizes ($300-$5k), across two heterogeneous asset classes?*

## 2. Hypothesis

A multi-source agent pipeline — Claude Sonnet 4.6 probability extraction + technical indicators (ATR-based volatility floors) + Brier-feedback loops — will achieve a Brier score reduction of ≥0.05 versus a market-implied baseline (e.g. Polymarket midpoint, S&P 500 sector benchmark) over a 90-day live evaluation window, *if and only if* the agent's paper P&L tracks backtest P&L for at least 14 days prior to real-money deployment.

The "if and only if" clause encodes the methodological discipline: backtest-paper divergence is the falsification criterion. If backtest claims do not reproduce in live paper, no real money is deployed.

## 3. Methodology

### 3.1 Two test surfaces

| Surface | Asset class | Signal source | Brier baseline |
|---|---|---|---|
| Polymarket | Binary prediction markets | LLM probability + persistence filter + 10pp mispricing gate | Polymarket implied midpoint |
| SpaceX equity sector | 8 pure-play tickers (RKLB, ASTS, LUNR, BKSY, PL, RDW, LMT, LIN) | LLM directional + sentiment + ATR stops | Buy-and-hold SPCE basket |

### 3.2 Calibration measurement

For each prediction *p* over outcome *o ∈ {0, 1}*, the Brier score component is *(p − o)²*. The agent's daily Brier is averaged across resolved decisions; the baseline's Brier is computed identically on the same decision space. **The deliverable metric is `Brier_agent − Brier_baseline`** over rolling 30-day windows.

### 3.3 Public pre-registration

Every prediction is timestamped on a public GitHub repository ([spacex-ipo-tracker](https://github.com/alex-jb/spacex-ipo-tracker)) before the event resolves. This eliminates the cherry-picking attack vector that contaminates retail quant blogs.

### 3.4 Risk controls (hard-coded)

- **3-loss kill switch**: 3 consecutive losing trades pauses live execution
- **$300 cap on Polymarket**: total real-money exposure
- **No leverage**: spot-only on equity, no derivatives
- **ATR stop-loss floor**: minimum 2%, cap 15%, scales with 14-day Average True Range
- **Sector exposure cap**: no single sector >30% of bankroll

## 4. Deliverables (12 weeks)

1. **Weeks 1-2**: Complete paper-validation phase. Daily Brier weekly reports.
2. **Weeks 3-4**: Deploy first real-money position ($20-$50 size) on highest-confidence Polymarket signal. Begin live Brier audit.
3. **Weeks 5-8**: If paper tracks backtest, scale to $1k. Add second asset surface (equity) with same calibration discipline.
4. **Weeks 9-10**: Methodology paper draft. Open-source v1.0 release.
5. **Weeks 11-12**: Final paper revision. Defense + portfolio documentation.

## 5. Expected outcomes (success + failure)

- **Positive result**: Brier improvement ≥0.05 across both surfaces → methodology paper publishable at student venues (ICML student workshop, NeurIPS spotlights).
- **Null result**: Brier improvement <0.05 but Brier ≤ market baseline → methodology paper still publishable as "honest negative" case study.
- **Negative result**: Brier > market baseline → post-mortem paper on *which* calibration assumption failed (instructive for future agent research).

## 6. Required resources

- **Computational**: existing personal MacBook + Anthropic API budget (~$50/month, self-funded)
- **Data**: free APIs (yfinance, polymarket gamma-api, GitHub stars-history, HN Algolia, Reddit JSON)
- **Capital at risk**: $300 (self-funded, hard-capped)
- **Advisor time**: estimated 1-2 hours per week for paper discussion + methodology critique

## 7. Why this works at a student budget

Foundation model APIs (Claude/GPT) make the marginal cost of probability extraction near-zero. The research bottleneck is no longer compute or data — it is **calibration discipline**: rigorous tracking of whether claimed accuracy survives production. That is a 1-person problem.

## 8. Related work (selected)

See `references/references.bib`.

Key prior work: Brier (1950) for the calibration metric foundation; Tetlock (2005) for expert calibration methodology; Hanson (2003) for prediction-market theory; Shinn et al. (2023) for Reflexion-style agent self-improvement loops; Sakana AI (2025) for Darwin-Gödel Machine self-modifying agents.

---

**Signature line for advisor:**

I, ______________________, agree to serve as faculty advisor for this capstone for Summer 2026, including weekly 1-hour discussion meetings and final paper review.

Date: ___________
