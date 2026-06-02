# Professor Meeting — Talking Points (中英对照)

**Date:** 2026-06-02
**Context:** First meeting with Paradigms professor (Spring 2026 semester) about Summer 2026 capstone. Professor already knows Orallexa from Alex's final presentation last semester.
**Format:** Read English aloud. Chinese is for self-prep / nervous-fallback.

---

## 1. Opening — refresh his memory

**EN:**
> Hi Professor — I'm Alex Ji from your Paradigms class last semester. I presented my final project on Orallexa, the AI trading agent. I want to take that work and formalize it as my summer capstone, and I'd love your input — and ideally your sponsorship.

**中文:**
> 老师好,我是上学期 Paradigms 课的 Alex Ji。我 final presentation 讲的就是 Orallexa,那个 AI trading agent。这个暑假我想把那个工作正式做成 capstone,想听您的意见,最好您能做我的指导老师。

---

## 2. Evidence of progress — pull up your inbox

**EN:**
> Since the final presentation, I've been running the agent continuously for about a month. Every morning at 9 AM, it scans markets, writes a structured brief, and emails me a calibrated probability estimate on specific binary events and equity moves. I have 30 days of those emails — I can show you a few right now if you'd like to see what the agent actually produces.

**中文:**
> 从期末展示之后,这个 agent 已经连续跑了快一个月了。每天早上 9 点它扫描市场、写一份结构化简报、给我邮箱发一个带 calibrated probability 的预测。我现在 inbox 里有 30 天的邮件,如果您想看现在就能给您看 agent 实际产出长什么样。

**🔑 Action:** Open your inbox here. Show 3-5 daily brief emails. **Physical receipts > slides.**

---

## 3. Capstone deliverable #1 — Polymarket

**EN:**
> For the capstone, I want to take Orallexa from advisory mode into a production system with two concrete deliverables that can make small amounts of real money while staying academically falsifiable.
>
> The first is Polymarket. The agent already runs a daily pipeline that flags binary events where its estimate diverges from the market by more than 10 percentage points for at least 7 days. I've backtested this — over a 30-day window, adding a 1.5× ATR stop-loss rule lifted simulated returns from negative 10% to positive 60.9% win rate at n equals 128 trades. The capstone goal is to deploy $300 of real capital starting in late June and measure whether the live Brier score tracks the backtest claim.

**中文:**
> Capstone 想做的是:把 Orallexa 从"咨询模式"推进到"生产系统",两个具体 deliverable,可以用小额真实资金,但学术上仍然 falsifiable。
>
> 第一个是 Polymarket。agent 已经每天跑一个 pipeline,识别那些"我的估计和市场价格差 10 个百分点以上、并且持续 7 天"的二元事件。我已经 backtest 过 —— 30 天窗口加 1.5× ATR 止损规则,win rate 从负 10% 提升到正 60.9%,n=128 笔交易。capstone 目标是 6 月底投 $300 真金,测 live Brier 分数能不能 track backtest 的 claim。

**🔑 Memorize these numbers:** 30 days / 10pp / 7 days / 60.9% / n=128 / $300

---

## 4. Capstone deliverable #2 — SpaceX equity

**EN:**
> The second is the SpaceX commercial-space sector. I've been publishing daily research picks on 8 pure-play tickers — Rocket Lab, AST SpaceMobile, Intuitive Machines, BlackSky, Planet Labs, Redwire, Lockheed, Linde — at a public GitHub Pages site since May 12th. Every prediction is timestamped before it resolves. By summer's end I will have 90 days of pre-registered picks scored against realized stock moves. That's stricter falsifiability than most retail quant work.

**中文:**
> 第二个是 SpaceX 商业航天板块。从 5 月 12 号开始我在公开的 GitHub Pages 上每天发 8 个 pure-play tickers 的研究 —— RKLB / ASTS / LUNR / BKSY / PL / RDW / LMT / LIN。每个预测都在事件结算前 timestamp。到暑假结束我会有 90 天的 pre-registered 预测,对照实际股票表现打分。这比大多数 retail quant 写博客严格得多。

**🔑 Academic keyword:** `pre-registered` — this is the hook that signals research seriousness.

---

## 5. What I want to add this summer

**EN:**
> What I'd like to add this summer to make the agent more accurate: a sentiment-ingestion pipeline tied to FOMC and SpaceX-launch news, a second calibration backstop using Kalshi prediction markets cross-checked against Polymarket, and a screen-recording observability layer so I can actually audit what the agent was reasoning about when it made each call.

**中文:**
> 暑假想加的几个让 agent 更准的东西:一个 sentiment ingestion pipeline,绑 FOMC 和 SpaceX 发射新闻;第二个 calibration backstop,用 Kalshi 的预测市场和 Polymarket 交叉验证;以及一个屏幕录制的 observability 层,这样我能 audit agent 每次做 call 的时候到底在 reasoning 什么。

**🔑 Three additions:** sentiment / cross-market / observability

---

## 6. The ask (most important)

**EN:**
> I'd like to ask: would you be willing to advise this informally for the summer? I'm not asking for funding. I'm asking for one or two papers per week to read together, and a faculty signature on the final proposal so this can count as my capstone credit. I have a one-page formal proposal I can send you tonight, and the GitHub repo with the daily emails is already live. Can I email you both?

**中文:**
> 我想问:您愿意这个暑假非正式地做我的指导老师吗?我不要 funding。我要的是每周一两篇 papers 一起读,以及在 final proposal 上签字让这个能算我的 capstone 学分。我有一份一页的正式 proposal 今晚可以发给您,GitHub repo 和每日邮件也都已经 live。能给您发邮件吗?

**🔑 The close has three concrete asks:** weekly paper discussion + faculty signature + email follow-up.

---

## Live demo order (cheat sheet)

| When | What to pull up |
|---|---|
| After section 2 | 📱 inbox → 3-5 daily brief emails |
| After section 3 | 💻 [Week 1 Brier report](../weekly-reports/2026-06-02-week-1.md) — show BKSY/PL/RKLB Brier 0.18-0.21 table |
| After section 4 | 💻 https://alex-jb.github.io/spacex-ipo-tracker — show public timestamped picks |
| After section 6 | 📄 [proposal.md](proposal.md) signature line — see if he'll sign on the spot |

---

## Anticipated pushback + ready answers

### Q1: "How much money are you risking?"

**EN:** "$300 hard cap, self-funded. There's a 3-loss kill switch that pauses execution if the agent loses 3 trades in a row. The point is methodology, not return."

**中文:** $300 硬上限,自费。有 3-loss kill switch,连亏 3 笔就停。重点是方法论,不是收益。

### Q2: "What if you lose all of it?"

**EN:** "Then I have a falsifiable negative result. The post-mortem of *which* calibration assumption broke is still publishable. The capstone doesn't depend on positive returns — it depends on honest measurement."

**中文:** 那我就有一个 falsifiable 的负面结果。哪个 calibration 假设挂了的 post-mortem 仍然 publishable。capstone 不依赖正收益,依赖诚实测量。

### Q3: "Is this just wrapping GPT?"

**EN:** "No. The LLM produces probability distributions. The agent's value is in composing distributions across multiple sources — LLM + technical indicators + market-implied prices — and translating them into Kelly-fractional position sizes via a Brier-feedback loop. The LLMs are signal generators. The agent is the composition layer."

**中文:** 不是。LLM 产生概率分布。agent 的价值是把多个来源 —— LLM + 技术指标 + 市场隐含价格 —— 的分布合成,通过 Brier 反馈回路翻译成 Kelly 分数仓位。LLM 是信号生成器,agent 是合成层。

---

## Nervous-fallback one-liner (memorize)

**EN:**
> "I have 30 days of receipts. I have 1056 resolved decisions with a Brier of 0.23, beating the coin-flip baseline. I have a public GitHub repo. I'm not asking for permission to start — I'm asking to formalize what's already running."

**中文:**
> 我有 30 天的物证。我有 1056 个 resolved decisions,Brier 0.23 打败 coin-flip baseline。我有公开 GitHub repo。我不是在求允许开始 —— 我是在求把已经在跑的东西正式化。

---

## Words to avoid (这些词不要说)

| ❌ Avoid | ✅ Use instead |
|---|---|
| "trading bot" | "calibration-disciplined agent" |
| "make money" | "measure live Brier against backtest claim" |
| "side project" | "production system" |
| "vibe coding" | "rapid prototyping with discipline gates" |

---

## After-meeting next steps

If he says yes:
1. Email him within 24 hours: GitHub link + proposal.md + first paper to read
2. Schedule weekly 30-min check-in
3. Sign the proposal during week 2 of capstone

If he says "interesting but…":
1. Ask what specific concern; address it in writing within 48 hours
2. Offer to start informal (no signature) and revisit after 2-week paper validation completes

If he says no:
1. Ask for one specific reference / pointer to another faculty member
2. The capstone runs anyway — the public artifacts already exist
