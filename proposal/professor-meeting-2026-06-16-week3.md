# Advisor Meeting — Prof. Michael Yang (Week 3 check-in)

**Date:** 2026-06-16 · **Capstone:** Orallexa Calibration (From Paper to Production)
**Format:** read EN aloud; 中文 for self-prep. This is a *progress* meeting, not the first pitch.
**Headline to land:** *the falsification gate worked — and that is the result, not a setback.*

---

## 1. Opening — where we are
**EN:**
> Hi Professor — quick progress check-in. We're in Week 3 of the capstone. I've completed the proposal, and just finished this week's deliverable — an annotated bibliography across calibration, prediction markets, and agent self-improvement. The agent's been running live the whole time, producing daily Brier-scored predictions. I have one important early result I want to walk you through, because it's exactly the kind of thing the methodology was built to catch.

**中文:** Week 3 进度汇报。提案完成、本周注释参考文献刚交。agent 一直在 live 跑、每天产出 Brier 打分的预测。有一个重要的早期发现想跟您讲——它正是这套方法论设计出来要抓的东西。

---

## 2. The key finding (lead with this — it's your strongest card)
**EN:**
> My proposal had an "if and only if" clause: no real money deploys unless live paper-trading tracks the backtest. Two weeks in, it didn't. I ran a walk-forward out-of-sample test and the mean OOS Sharpe came back negative — the backtest claims did **not** reproduce on held-out data. So per my own pre-registered rule, I **held** the $300 real-money deployment that was planned for late June. The gate did its job. That's a falsifiable result in the project's favor, not a failure.

**中文:** 提案里有个 "if and only if":paper 不 track backtest 就不投真钱。两周后,它没 track——walk-forward 样本外测试,mean OOS Sharpe 是负的,backtest 的 claim **没有**在留出数据上复现。所以按我自己 pre-register 的规则,我**暂缓**了 6 月底计划的 $300 实盘。这道闸起作用了——这是个对项目有利的 falsifiable 结果,不是失败。

**🔑 Memorize:** *"if and only if" gate / walk-forward / OOS Sharpe negative / held real money*

---

## 3. What I'm doing about it (shows engineering + rigor)
**EN:**
> I traced it to entry timing, not sizing. I backtested an ATR-based stop-loss rule on a 30-day, n=128 window: baseline lost money at a 22.7% win rate; adding 1.5× ATR stops swung it to a 60.9% win rate — about a $6,800 improvement, significant at p < 0.005. That's now ported into production. The discipline is: I will **not** reconsider real money until the live paper P&L reproduces that for at least two weeks. Measurement first, capital second.

**中文:** 我定位到是 entry timing,不是 sizing。ATR 止损规则在 30 天 n=128 窗口回测:baseline 亏钱、win rate 22.7%;加 1.5×ATR 止损 → win rate 60.9%,约 +$6,800,p<0.005 显著。已 port 到生产。纪律是:live paper 不复现这个、连续两周,我**不**重新考虑真钱。先测量,后资金。

**🔑 Numbers:** n=128 / 22.7% → 60.9% / +$6,800 / p<0.005

---

## 4. Deliverables on track (show the schedule)
**EN:**
> On the course schedule I'm on pace: Week 1 interest statement, Week 2 proposal, Week 3 annotated bibliography — done. Next week is the project plan and Gantt chart, which I'll build from the proposal's 12-week deliverable list. Every prediction is still timestamped publicly on GitHub before it resolves, so the whole record is auditable.

**中文:** 课程进度按表走:Week1 兴趣陈述、Week2 提案、Week3 注释参考文献都完成。下周项目计划+甘特图。所有预测仍然在 GitHub 上结算前 timestamp,全程可审计。

---

## 5. The ask
**EN:**
> Two things I'd value from you. First, a methods gut-check: given the OOS reproduction problem, does my plan — fix entry rules, re-validate on paper, only then revisit small real capital — sound rigorous to you, or would you push the design somewhere else? Second, if you have a paper or two on out-of-sample validation or forecast calibration you'd point me to, I'd read them this week.
> [If signature still pending:] And whenever you're comfortable, I'd love to formalize the advisor signature so this counts for capstone credit.

**中文:** 想要您两样:① 方法 gut-check——面对 OOS 不复现,我的计划(修 entry rule → paper 重验 → 才考虑小额真钱)够严谨吗,还是您会往别处推?② 有没有 OOS validation / 预测校准的 paper 推给我,我这周读。[若还没签字] 您方便时,想正式拿到导师签字算学分。

---

## Demo order (cheat sheet)
| When | Pull up |
|---|---|
| After §1 | 📄 `ANNOTATED-BIBLIOGRAPHY.md` (this week's deliverable) |
| After §2 | 💻 walk-forward verdict / latest `weekly-reports/` Brier table |
| After §3 | 💻 ATR-stops validation note (n=128, +$6.8k swing) |
| After §4 | 💻 https://alex-jb.github.io/spacex-ipo-tracker — public timestamped picks |

---

## Anticipated pushback + answers
**Q: "So it's not working?"**
> "The *trading* edge isn't proven yet — but the *methodology* is working exactly as designed. The whole point was to measure whether backtest calibration survives live, and to not deploy capital on an unproven claim. Catching that early, before risking money, is the contribution."

**Q: "Will you have a result by August?"**
> "Yes, regardless of outcome. Positive: Brier beats baseline → methods paper. Null: Brier ≈ baseline → honest case study. Negative: a documented post-mortem of which calibration assumption broke. All three are publishable; none depend on making money."

**Q: "Is this just wrapping GPT?"**
> "No — the LLM is one signal source. The agent composes LLM probabilities + technical indicators + market-implied prices into Kelly-fractional sizing through a Brier-feedback loop. The contribution is the composition + calibration layer, not the model."

---

## Words: avoid → use
trading bot → **calibration-disciplined agent** · make money → **measure live Brier vs backtest** · it failed → **the falsification gate triggered** · side project → **production system**

## Nervous-fallback one-liner
> "My pre-registered gate caught a backtest that didn't reproduce out-of-sample, so I correctly held real capital. That honest negative *is* the kind of result this capstone was built to produce."
