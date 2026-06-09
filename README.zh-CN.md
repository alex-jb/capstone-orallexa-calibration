# Capstone — Orallexa Calibration(2026 暑期)

[English](README.md) | **中文**

**学生:** 季晓宇(Alex Ji)
**项目:** 叶史瓦大学(Yeshiva University)CS 硕士
**指导老师:** Michael Yang 教授(Capstone in Computer Science I)
**时间线:** 2026-06-02 → 2026-08-31(13 周)
**最后更新:** 2026-06-09(第 2 周)

## 一句话论点

> 一个校准纪律严格的 AI 交易 agent(Orallexa),在小额真金(\$300-\$5k)从 paper trading 推进到生产部署后,能在两类异构资产 —— 预测市场(Polymarket)与股票微观结构(SpaceX 商业航天板块)—— 上同时取得可量化的 Brier 分数优势。

## 为什么这是 research 而不是 side project

1. **数据本身就 falsifiable**:每个预测都在事件结算前 timestamp 到公开 GitHub。事后 cherry-pick 在物理上不可能。
2. **Brier 分数是成功度量**:1950 年提出的概率校准量化指标(Brier 1950)。改善与否完全可以从公开 log 审计。
3. **真金强制函数**:纯 paper 跑 ML 容易过度乐观。agent 硬编码规则 —— 真金不会在 live paper P&L 跟 backtest 偏离时部署;paper-validate 至少 2 周 **并且** walk-forward 闸门(mean OOS Sharpe > 0.5 跨 4 个滑动窗口)必须通过。
4. **负面结果也可发表**:即使 Brier 没改善,把"是哪个校准假设挂了"的 post-mortem 写出来本身就是贡献。**第 2 周已经产出 4 篇 postmortem** —— 它们是 capstone 的早期实证内容,不是挫折。

## 三个具体 deliverables

| 编号 | Deliverable | 当前状态(2026-06-09) | 暑期目标 |
|---|---|---|---|
| D1 | 公开 SpaceX 股票研究 feed | 28 天 live(自 2026-05-12)https://alex-jb.github.io/spacex-ipo-tracker | 90 天 timestamped 预测,事后 Brier 打分对照实际股票走势 |
| D2 | Polymarket 校准论文 | **Backtest 已被推翻**(in-sample +60.9% 在 OOS 不复现)。Walk-forward 闸门 verdict FAIL(mean OOS Sharpe -3.08)。真金暂停。Paper 继续记录。 | 4-8 周 live paper vs 真金 \$300 cohort —— 仅在 walkforward 闸门通过后启动 —— 双轨 P&L 对比 + 最终论文 |
| D3 | 开源 agent 框架 | Orallexa v0.2 已发布 https://github.com/alex-jb/orallexa-ai-trading-agent。**2026-06 已 ship 3 个相邻 OSS 校准工具**(council-diff、council-diff-py、memory-wall-tracker、postmortems 合集) | 版本化 v1.0 release + 可复现 README + 至少 1 个外部用户真的跑起来 |

## 第 1-2 周进展与实证发现(2026-06-02 → 2026-06-09)

前两周产出了 **4 项 calibration 级别的负面发现**。每一项都以独立 postmortem 形式记录,带日期、根因、代码级修复尝试、资金影响。全部公开在 https://github.com/alex-jb/alex-brain/tree/main/postmortems,镜像在 vibexforge.com/postmortems。

### F1 — Walk-forward 闸门 verdict: FAIL(2026-06-08)
- Backtest 报告 +$5,950 / 60.9% 胜率 / 128 笔 / 过去 30 天
- Walk-forward 验证(滑动 train/test 窗口):mean OOS Sharpe **-3.08**,最差窗口 Sharpe **-4.23**,mean 胜率 **31.6%**(OOS 比 in-sample 掉 29.3 个百分点)
- **根因**: 隐形的 `--use-atr-stops` CLI flag 在 eval 时传了,在 production cron 没传。"漂亮"的 backtest 测的是从未在生产里跑过的代码路径。教科书级 look-ahead bias。
- **方法论贡献**: walk-forward 闸门(`scripts/walkforward.py`)现在是任何真金部署前的硬性闸门。Mean OOS Sharpe 必须跨 4 个滚动窗口超过 0.5。当前 FAIL。无真金交易。

### F2 — Paper P&L 推翻"Brier 单一成功度量"假设(2026-05-27)
- 14 天 paper 组合模拟器: **-$1,015 / -10.16% / 25.6% 胜率 / 39 笔交易中 26 笔触发止损**
- 同期 Brier 分数是健康的 0.196(远低于 0.25 抛硬币基线)
- **方法论贡献**: Brier(概率校准)和 Sharpe(方向边际)度量的是正交维度。一个系统可以通过 Brier 闸门同时亏钱。这在 capstone 文献综述里被记为"校准诚实 agent 论文中一个 underspecified 的失败模式"(Brier 1950 度量的是对的事;它不是度量*唯一*的事)。

### F3 — Ensemble 通胀: 5 personas ≠ 5 voters(2026-06-05)
- 5-persona LLM 辩论 ensemble(Bull / Bear / Judge / Critic / Auditor)在单一 ticker 上反复返回 5/5 BUY consensus
- 实测:同一 Claude 模型 + 共享 RAG 上下文下,personas 间偏差相关性 ≈ 0.6,不是 0
- **方法论贡献**: ship 了 shrinkage 层(`ensemble_shrinkage.py`,λ=0.4 实测调参),把 5/5 ensemble 共识朝先验拉回。另加 `sports_brier` n<30 verdict guard —— 在低于 30 个结算样本时拒绝发布概率 verdict。
- 这个发现推广到任何"多 persona 共享 model + 共享 context"的 LLM ensemble —— 不止限于交易场景。

### F4 — 规则执行测试: SPCX IPO 6/12 SKIP(2026-06-09)
- Robinhood IPO Access 批了 SPCX 4 股 × $162 max($648 上限)2026-06-12
- 5-persona ensemble 返回 BUY 共识。SpaceX-IPO-Tracker 公开 feed 已发 28 天正面 thesis
- Walk-forward verdict 仍然 FAIL
- **硬规则被执行了**: 不动真金。Capstone 把"在公开记录里发布带推理的 SKIP 决定"当作校准纪律测试,而不是 F1/F2/F3 那种研究发现。

## 2026-06 期间产出的相邻 OSS 贡献

这些不是额外的 deliverables;它们是从 capstone 工作里 spin out 的校准工具 —— 通过公开版本化、MIT 许可、并在最终论文中可引用,获得益处。

- **[council-diff](https://github.com/alex-jb/council-diff)**(TypeScript, MIT)—— 5-voice AI 议会辩论库,带 Brier 审计模块。把 trading-stack 辩论层泛化到 founder / engineer / investor / career / product / quant 多个 domain。
- **[council-diff-py](https://github.com/alex-jb/council-diff-py)**(Python, MIT)—— council-diff 的 Python 移植,同样 Brier 审计数学,persistence-agnostic。`pip install council-diff`。
- **[memory-wall-tracker](https://github.com/alex-jb/memory-wall-tracker)**(Python, MIT)—— Brier-audited 的 Druckenmiller Q1 2026 AI inference memory basket(AVGO/INTC/ARM/MU/STX/WDC)日研报。跨资产校准测试床: 预测市场 verdict(Polymarket)vs 股票微观结构 verdict(本 basket),在同一个 Brier 计分板下对比。
- **[Postmortems 合集](https://github.com/alex-jb/alex-brain/tree/main/postmortems)** —— 4 篇 calibration-honest 负面结果,带 `resolve_by` 日期发布。最终论文中将其引用为 13 周窗口里的实证贡献。

## 仓库结构

```
proposal/         一页正式 proposal + 文献引用
weekly-reports/   每周 Brier 审计聚合(Sunday cron)
figures/          生成的图表(Brier 时间序列、paper-vs-real P&L、walk-forward verdict)
data-snapshots/   匿名化的预测日志(只读,append-only)
references/       引用论文 PDF(licensing 允许的)
scripts/          Cracked Score Phase 2 POC + weekly Brier 自动生成
```

## 状态板(2026-06-09)

- ✅ 每日 Brier 审计 cron live(数据在 `weekly-reports/`)
- ✅ 公开 SpaceX picks feed live(2026-06-09 已 28 天)
- ✅ Polymarket decide pipeline live(`polymarket_decide.py`)
- ✅ Walk-forward 验证框架已 ship(`scripts/walkforward.py`)
- ✅ Ensemble shrinkage 层已 ship(`ensemble_shrinkage.py`,λ=0.4)
- ✅ 4 篇 postmortem 已发布,带日期 `resolve_by`(上述 F1/F2/F3/F4)
- ✅ 相邻 OSS 校准工具已 ship(council-diff / council-diff-py / memory-wall-tracker)
- 🛑 真金部署 **被阻断** 在 walk-forward 闸门(当前 FAIL)。重审 2026-06-23。
- ⚪ 指导老师签字待定 — Michael Yang 教授(首次会议安排中)
- ⚪ 最终论文 draft(目标:2026-08-15)

## 关联仓库

- [orallexa-ai-trading-agent](https://github.com/alex-jb/orallexa-ai-trading-agent) — 交易 agent 本体(markets/ 目录)
- [spacex-ipo-tracker](https://github.com/alex-jb/spacex-ipo-tracker) — 公开每日研究 feed(deliverable D1)
- [solo-founder-os](https://github.com/alex-jb/solo-founder-os) — 支撑 agent 基础设施(成本审计、评估 harness)
- [council-diff](https://github.com/alex-jb/council-diff) + [council-diff-py](https://github.com/alex-jb/council-diff-py) —— 泛化版 5-voice 辩论库,带 Brier 审计
- [memory-wall-tracker](https://github.com/alex-jb/memory-wall-tracker) —— Brier-audited 股票研究 feed
- [alex-brain/postmortems](https://github.com/alex-jb/alex-brain/tree/main/postmortems) —— 校准诚实 failure 日志

## 诚实声明

- 单人项目,无团队。capstone 只 optimize 一个人在 13 周内能可信交付并审计的范围。
- 小额资金(\$300-\$5k)。在这个规模下 agent 不会产生 publishable 的经济发现 —— 能发表的是**方法论**和 **Brier 校准 delta**。
- 不做 GPU 训练。agent 只在 foundation model(Claude Sonnet 4.6 + GPT)输出之上做合成,不 fine-tune。贡献在合成层 + 校准反馈回路,不在模型架构。
- **第 2 周更新**: 校准 delta 本身目前是一个负面结果。贡献在于把四层不同失败(look-ahead bias、Brier vs Sharpe 正交性、ensemble 通胀、规则执行纪律)各自如何挂掉的方法论记录下来。最终论文将报告这些作为实证发现 —— 无论 walk-forward 闸门在 2026-08-31 前是否通过。

## 引用(暂定)

```
Ji, X. (2026). Orallexa Calibration: A Brier-audited multi-agent trading
research framework. MS Capstone, Yeshiva University.
公开审计日志: github.com/alex-jb/alex-brain/postmortems
```
