# Annotated Bibliography

**Capstone:** From Paper to Production — Calibration Discipline in a Solo-Operated AI Trading Agent (Orallexa)
**Student:** Xiaoyu (Alex) Ji · MS Computer Science, Yeshiva University
**Course:** COM-6000-CP1 · Week 3 deliverable · 2026-06-16

*Scope: this bibliography supports a capstone that tests whether a multi-source AI agent can hold a measurable Brier-score advantage over a market-implied baseline when moved from backtest to live, small-capital trading. Sources are grouped into three themes — (A) calibration and forecasting discipline, (B) markets, prediction markets, and risk control, and (C) AI agents and self-improvement.*

---

## A. Calibration & Forecasting Discipline

**Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review*, 78(1), 1–3.**
The foundational paper defining the Brier score — the mean squared error between a probabilistic forecast and the binary outcome it predicts. It establishes that forecasts should be scored on *calibration*, not just direction. This capstone uses the Brier score as its single headline metric: every resolved prediction contributes a `(p − o)²` term, and the deliverable quantity is `Brier_agent − Brier_baseline` over rolling 30-day windows. Brier's 75-year-old, fully public formulation is precisely what makes the project auditable — anyone can recompute the score from the timestamped logs.

**Tetlock, P. E. (2005). *Expert Political Judgment: How Good Is It? How Can We Know?* Princeton University Press.**
A landmark longitudinal study showing that most expert forecasters are poorly calibrated, and that disciplined, score-tracked forecasting outperforms confident narrative. Tetlock's methodology — pre-commit to a probability, then score it after resolution — is the model for this capstone's *pre-registration discipline*: predictions are timestamped on GitHub before events resolve, eliminating hindsight bias. It frames the project's core claim that calibration must be *measured over time*, not asserted from a backtest.

**Tetlock, P. E., & Gardner, D. (2015). *Superforecasting: The Art and Science of Prediction.* Crown.**
The accessible successor to Tetlock (2005), distilling the Good Judgment Project's findings into operational habits: think in explicit probabilities, update incrementally, and keep score honestly. The capstone's daily-retro loop operationalizes "update incrementally," and its public Brier ledger operationalizes "keep score honestly." This source justifies the project's emphasis on *process over outcome* — a single profitable trade proves nothing; a tracked Brier delta across hundreds of decisions does.

**Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of modern neural networks. *ICML*.**
Shows that modern deep networks are systematically *over-confident* and introduces Expected Calibration Error (ECE) plus temperature scaling as a fix. This is directly relevant because the agent extracts probabilities from a large language model, which inherits the same over-confidence pathology. The paper motivates the capstone's decision to treat raw model probabilities as *uncalibrated signals* that must be checked against a market baseline rather than trusted at face value, and supplies ECE as a secondary diagnostic alongside the Brier score.

**Kadavath, S., et al. (2022). Language models (mostly) know what they know. *arXiv:2207.05221*.**
An empirical study (Anthropic) finding that large language models can produce reasonably calibrated self-assessments of correctness under the right prompting, but degrade out of distribution. This is the closest prior work to the capstone's signal-generation layer: it both supports using an LLM as a probability extractor and warns that calibration is fragile in novel, adversarial settings — exactly the "wild" the capstone tests. It directly informs the hypothesis that LLM calibration claims may *not* survive live markets.

---

## B. Markets, Prediction Markets & Risk

**Hanson, R. (2003). Combinatorial information market design. *Information Systems Frontiers*, 5(1), 107–119.**
Provides the theoretical basis for treating prediction markets as efficient information aggregators whose prices approximate true event probabilities. This justifies the capstone's use of the Polymarket implied midpoint as the *Brier baseline* the agent must beat: if markets already aggregate information efficiently, any consistent Brier improvement is meaningful alpha rather than noise. It also grounds the choice of binary prediction markets as one of the two clean test surfaces.

**O'Hara, M. (1995). *Market Microstructure Theory.* Blackwell.**
The standard text on how information asymmetry, order flow, and liquidity shape price formation. It explains why alpha decays faster in heavily-traded mega-caps than in thinner, less-covered names — the rationale for the capstone selecting small-cap pure-play tickers (RKLB, ASTS, LUNR, etc.) as the equity test surface. Microstructure theory also frames the project's concern with *information staleness and latency* as real degradation channels for a live agent versus a backtest.

**Kelly, J. L. (1956). A new interpretation of information rate. *Bell System Technical Journal*, 35(4), 917–926.**
Introduces the Kelly criterion: the bet-sizing rule that maximizes long-run growth given an edge and its probability. The capstone uses calibrated probabilities to drive Kelly-fraction position sizing, making calibration *economically* consequential — a mis-calibrated probability directly mis-sizes capital. This paper connects the project's measurement layer (Brier) to its action layer (position size), and motivates the hard caps (fractional Kelly, $300 exposure limit) that keep the live system safe.

**Wilder, J. W. (1978). *New Concepts in Technical Trading Systems.* Trend Research.**
The origin of Average True Range (ATR), the volatility measure used in the capstone's hard-coded risk controls. The agent sets stop-loss floors that scale with 14-day ATR (minimum 2%, cap 15%), so positions in volatile names get wider stops. While the project is calibration-first rather than technical-analysis-driven, ATR supplies a principled, volatility-aware risk floor, and is cited to document the provenance of that control.

---

## C. AI Agents & Self-Improvement

**Shinn, N., Cassano, F., Berman, E., Gopinath, A., Narasimhan, K., & Yao, S. (2023). Reflexion: Language agents with verbal reinforcement learning. *NeurIPS 2023*.** [arXiv:2303.11366]
Introduces "Reflexion," in which an agent verbally reflects on failures and feeds those reflections back into future attempts as in-context learning. This is the methodology behind the capstone's daily-retro loop: each losing decision is logged to a reflection file that is injected into the next day's prompt context. The paper supports the design choice to improve the agent through structured self-critique rather than weight updates — appropriate for a solo, low-cost operation.

**Sakana AI (2025). The Darwin-Gödel Machine: Self-modifying agents through open-ended search.** [https://sakana.ai/dgm]
Describes agents that iteratively rewrite their own code/prompts under an open-ended search process. It inspires the capstone's highest layer of self-improvement — evolving agent prompts via *PR-gated* changes — but with a deliberate modification: a mandatory human-in-the-loop merge gate replaces unconstrained self-editing. This source is included partly as a *boundary* reference: it marks the capability the project intentionally constrains for safety, anchoring the discussion of why the agent is structurally incapable of autonomous, unreviewed change.

---

*Citation style: APA-flavored author–date. Full BibTeX records in `proposal/references.bib`.*
