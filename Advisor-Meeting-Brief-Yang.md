# Advisor Meeting Brief — Prof. Michael Yang
**Capstone:** Orallexa — *From Paper to Production: Calibration Discipline in a Solo-Operated AI Trading Agent*
**Student:** Xiaoyu (Alex) Ji · MS CS, Yeshiva University · COM-6000-CP1
**Date:** 2026-06-16 (Week 3) · *EN = read aloud · 中文 = self-prep*

> **One-line frame for the whole meeting:** the project's pre-registered falsification gate did its job — it caught a backtest that didn't reproduce out-of-sample, so real money was correctly held. *That honest result is exactly what this capstone was built to produce.*

---

# PART 1 — Proposal recap (Week 2, to re-anchor him)

**Problem.** Most AI-trading work reports calibration metrics (Brier, ECE) on *closed backtests* where the answer key is known. What's rarely tested is whether those calibration claims survive the *wild* — live, adversarial markets with staleness, latency, and other agents on the same signal.

**Research question.** Can a single-developer AI agent hold a measurable Brier-score advantage over a market-implied baseline when deployed live with small real capital ($300–$5k), across two heterogeneous asset classes?

**Hypothesis.** A multi-source pipeline (Claude probability extraction + technical indicators + Brier-feedback loop) will cut Brier by ≥0.05 vs a market baseline over a 90-day live window — *if and only if* live paper P&L tracks backtest for ≥14 days before any real money. (The "iff" is the falsification criterion.)

**Methodology.**
- **Two test surfaces:** Polymarket binary events (baseline = market midpoint) · SpaceX-sector equities, 8 pure-play tickers (baseline = buy-and-hold basket).
- **Metric:** per prediction, Brier component `(p − o)²`; deliverable quantity = `Brier_agent − Brier_baseline` over rolling 30-day windows.
- **Public pre-registration:** every prediction timestamped on GitHub before it resolves → no cherry-picking.
- **Hard risk controls:** 3-loss kill switch · $300 cap · no leverage · ATR-scaled stop floor (2%–15%) · sector exposure ≤30%.

**Outcomes are publishable regardless of sign:** positive (Brier beats baseline → methods paper) · null (Brier ≈ baseline → honest case study) · negative (post-mortem of *which* calibration assumption broke).

---

# PART 2 — Week 3 progress + what to say

## 1. Opening — where we are
**EN:** "Quick progress check-in. We're in Week 3. Proposal done; just finished this week's deliverable — an annotated bibliography across calibration, prediction markets, and agent self-improvement. The agent's run live the whole time, producing daily Brier-scored predictions. I have one important early result that's exactly what the methodology was built to catch."

**中文:** Week 3 汇报。提案完成、本周注释参考文献刚交。agent 一直 live 跑、每天 Brier 打分。有个重要早期发现想讲——正是方法论要抓的。

## 2. The key finding — lead with this
**EN:** "My proposal had an 'if and only if' clause: no real money unless live paper tracks the backtest. Two weeks in, it didn't. A walk-forward out-of-sample test came back with a negative mean OOS Sharpe — the backtest claims did **not** reproduce on held-out data. So per my own pre-registered rule, I **held** the $300 deployment planned for late June. The gate worked. That's a falsifiable result in the project's favor, not a failure."

**中文:** 提案的 "iff":paper 不 track backtest 就不投真钱。两周后没 track——walk-forward 样本外 mean OOS Sharpe 为负,backtest 没复现。按自己 pre-register 的规则,我**暂缓**了 6 月底 $300 实盘。闸起作用了——对项目有利的 falsifiable 结果,不是失败。

🔑 *"if and only if" gate · walk-forward · OOS Sharpe negative · held real money*

## 3. What I'm doing about it
**EN:** "I traced it to entry timing, not sizing. I backtested an ATR-based stop on a 30-day, n=128 window: baseline lost money at a 22.7% win rate; adding 1.5× ATR stops swung it to 60.9% — about a $6,800 improvement, significant at p < 0.005. It's in production now. I will **not** revisit real money until live paper reproduces that for ≥2 weeks. Measurement first, capital second."

**中文:** 定位到是 entry timing 不是 sizing。ATR 止损回测 n=128:baseline 亏、22.7% win;加 1.5×ATR → 60.9%、约 +$6,800、p<0.005。已上生产。live paper 不复现两周,绝不碰真钱。

🔑 *n=128 · 22.7% → 60.9% · +$6,800 · p<0.005*

## 4. On schedule
**EN:** "On pace with the course: Week 1 interest statement, Week 2 proposal, Week 3 annotated bibliography — done. Next is the project plan and Gantt chart from my 12-week deliverable list. Every prediction is still timestamped publicly before it resolves."

**中文:** 进度按表:Week1-3 都完成,下周甘特图。预测仍全程公开 timestamp。

## 5. The ask
**EN:** "Two things I'd value. First, a methods gut-check: given the OOS reproduction problem, does my plan — fix entry rules, re-validate on paper, only then revisit small real capital — read as rigorous, or would you push the design elsewhere? Second, any paper on out-of-sample validation or forecast calibration you'd point me to, I'd read it this week. [If pending:] And whenever you're comfortable, I'd love to formalize your advisor signature for capstone credit."

**中文:** ① 方法 gut-check:修 entry → paper 重验 → 才碰小额真钱,够严谨吗?② 推 OOS validation / 校准的 paper。[未签] 方便时正式签字算学分。

---

## Demo order
| When | Pull up |
|---|---|
| §1 | Annotated bibliography (this week's deliverable) |
| §2 | Walk-forward verdict + latest weekly Brier report |
| §3 | ATR-stops validation (n=128, +$6.8k swing) |
| §4 | https://alex-jb.github.io/spacex-ipo-tracker — public timestamped picks |

## Anticipated pushback → answer
- **"So it's not working?"** → "The *trading edge* isn't proven yet — but the *methodology* is working exactly as designed. The point was to test whether backtest calibration survives live and to not risk capital on an unproven claim. Catching that early is the contribution."
- **"Will you have a result by August?"** → "Yes, any sign. Positive → methods paper; null → honest case study; negative → documented post-mortem. All publishable; none depend on returns."
- **"Is this just wrapping GPT?"** → "No. The LLM is one signal. The agent composes LLM + technical indicators + market-implied prices into Kelly-fractional sizing via a Brier-feedback loop. The contribution is the composition + calibration layer."

## Words: avoid → use
trading bot → **calibration-disciplined agent** · make money → **measure live Brier vs backtest** · it failed → **the falsification gate triggered** · side project → **production system**

## Nervous-fallback one-liner
> "My pre-registered gate caught a backtest that didn't reproduce out-of-sample, so I correctly held real capital. That honest negative *is* the kind of result this capstone was built to produce."
