# Capstone Project Plan + Gantt Chart — Week 4 Deliverable

**Student:** Xiaoyu (Alex) Ji · COM 6000-CP1 · MS CS, Yeshiva University
**Advisor:** Prof. Michael Yang
**Submitted:** 2026-06-17 (early — Week 3.5)
**Course deadline:** 2026-06-23 (Week 4)

---

## 1. Working title (revised from Week 1-2 proposal)

**Calibration Discipline as the Audit Primitive for Spatial Pre-Trade Compliance in Live Trading**

(The Week 1-2 thesis — *"From Paper to Production: Calibration Discipline in a Solo-Operated AI Trading Agent"* — is preserved as the **Phase 1 core**. The extension proposed in the advisor amendment email of 2026-06-17 adds a measurement-first **Phase 2 spatial enforcement layer** that plugs into the validated Phase 1 backend without contaminating the Week 4-6 paper-trading validation window.)

---

## 2. Hypothesis and falsifiable predictions

**H1 (core, unchanged).** A multi-source AI agent can hold a measurable Brier-score advantage over a market-implied baseline when deployed live with small real capital ($300-$5k), across two heterogeneous asset classes — *iff* live paper P&L tracks backtest for ≥14 days before any real money.

**H2 (added).** A calibrated probability channel produced by Guo et al. 2017 temperature scaling reduces Expected Calibration Error by ≥50% on a chronological held-out fold without degrading the agent's rank-ordering (since temperature is monotone).

**H3 (added).** A Kadavath et al. 2022 second-order self-calibration gate, fired before staking capital, demotes BUY/SELL → WAIT at a rate that itself becomes calibration evidence: if the LLM's own second-order confidence is well-calibrated, demote-rate at threshold 0.6 should correlate negatively with the resulting Brier of any decision that survives the gate.

---

## 3. Empirical strategy

Two test surfaces:

- **Polymarket binary events.** Baseline: market midpoint at the time of forecast. Brier surface is dense and resolves in days.
- **SpaceX-sector equities.** Eight pure-play tickers (RKLB, ASTS, LUNR, BKSY, PL, RDW, LMT, LIN). Baseline: buy-and-hold basket.

Per-prediction Brier `(p − o)²`. Deliverable quantity: `Brier_agent − Brier_baseline` over rolling 30-day windows.

Public pre-registration: every prediction timestamped on `github.com/alex-jb/spacex-ipo-tracker` before it resolves → no cherry-picking.

Hard risk controls (binding throughout the live window):
- 3-loss kill switch
- $300 deployment cap (no leverage)
- 14-day ATR-scaled stops (2%–15%)
- Sector exposure ≤ 30%
- **NEW:** confidence-shrunk Kelly (Phase 1 #5) — Kelly fraction × (1 - ECE/0.25), capped at quarter Kelly
- **NEW:** PR-gated self-modification (Phase 1 #6) — no prompt/threshold edit merges to `main` without ≥ 0.005 Brier improvement on a 30+ held-out fold AND a human-approval flag

---

## 4. Six-week Gantt (Phase 1) + four-week extension (Phase 2)

```
WEEK   | dates       | calibration phase 1                | spatial phase 2
-------+-------------+------------------------------------+------------------------------
1 (J2) | 06-02       | proposal interest statement        |
2 (J9) | 06-09       | draft proposal (Brier thesis)      |
3      | 06-16       | annotated bibliography  ───────┐   |
3.5    | 06-17 ●     | ★ Phase 1 #1-#6 modules shipped|   | (capstone amendment email
       |             |   (ECE + temperature + self-cal│   |  sent to advisor)
       |             |    + reflexion + staleness +   │   |
       |             |    Kelly shrink + D-G gate)    │   |
       |             | ★ ece_audit.py LIVE: T* = 5.47 │   |
       |             | ★ sc_audit.py  LIVE: 100% dem  │   |
4      | 06-23       | weekly_brier_report extends    │   |
       |             |  to ECE + SC dashboards        │   |
       |             | reflexion JSONL wired into     │   |
       |             |  nightly brier_audit           │   |
5      | 06-30       | confidence-shrunk Kelly in     │   |
       |             |  paper-trading (not real $)    │   |
       |             | first synthetic D-G self-mod   │   |
       |             |  proposal → first MergeDecision│   |
       |             |  recorded                      │   |
6      | 07-07 ●     | midterm presentation:          │   |
       |             |  ECE before/after, SC demote   │   |
       |             |  rate, Brier delta, Phase 1    │   |
       |             |  results writeup               │   |
       |             |                                ▼   |
7      | 07-14       |                                    | Quest 3S WebXR scene +
       |             |                                    | Three.js podium layout
       |             |                                    | MediaPipe hands setup
8      | 07-21       |                                    | crypto hash chain audit
       |             |                                    | trail (WebCrypto)
       |             |                                    | first gesture-vote loop
9      | 07-28       |                                    | spatial layer integrated
       |             |                                    | with calibrated backend,
       |             |                                    | end-to-end audit export
10 (●) | 08-05       | final presentation + reflection paper
17     | 08-12       | final project write-up due
```

★ = items already done as of 2026-06-17 (this submission).
● = course-marked milestones.

---

## 5. Phase 1 status as of this submission

| # | Upgrade | Source | Module | Tests | Live? |
|---|---|---|---|---|---|
| 1 | ECE + temperature scaling | Guo 2017 (ICML) | `src/calibration/ece.py`, `temperature.py`, `reliability.py` | 19 ✓ | **Yes** (ece_audit.py) |
| 2 | LLM self-calibration | Kadavath 2022 | `src/calibration/self_calibration.py` | 10 ✓ | **Yes** (sc_audit.py) |
| 3 | Structured Reflexion JSON | Shinn 2023 (NeurIPS) | `src/calibration/reflexion.py` | 8 ✓ | Phase 1 wiring Week 4 |
| 4 | Information staleness | O'Hara 1995 | `src/calibration/staleness.py` | 10 ✓ | Phase 1 wiring Week 4 |
| 5 | Confidence-shrunk Kelly | Kelly 1956 + Guo 2017 | `src/calibration/kelly.py` | 9 ✓ | Paper trading Week 5 |
| 6 | PR-gated Darwin-Gödel | Sakana 2025 | `src/calibration/self_modification.py` | 8 ✓ | First synthetic Week 5 |

**Code: 64 unit tests green, 0.3s.**

---

## 6. Two live findings already on the table (Week 3.5)

### Finding F1 — Systematic over-confidence pathology reproduces in production

`scripts/ece_audit.py` on `decision_log.json` (n=279 resolved, lookahead=1 day):

- ECE (raw): `0.0459`
- Brier (raw): `0.2557`
- **Fitted temperature T\* on chronological held-out fold (newest 25%): `5.474`**
- ECE improvement on validation fold: **`+0.0494`** (cuts ECE by roughly half)
- Brier improvement: `+0.0056`

Guo et al. (2017) showed that modern deep networks are systematically over-confident, with calibrated temperatures typically in `[1.5, 3.0]`. Our `T\* = 5.474` indicates a *more severe* over-confidence pathology in LLM-derived trading probabilities than Guo's CNN benchmarks. This is a finding worth defending.

### Finding F2 — LLM second-order self-knowledge would have demoted every recent directional call

`scripts/sc_audit.py` on last 24h BUY/SELL decisions (n=8) calling Claude Haiku 4.5 with the Kadavath-style second-order prompt:

- Average second-order confidence: **`0.338`** (well below the 0.60 demote threshold)
- **Demote rate at threshold 0.60: `100%`**
- Top primary-doubt cluster: *"57% barely exceeds random chance; lacks fresh data and clear regime"*

Kadavath et al. (2022) argued language models *(mostly) know what they know*. F2 reproduces that finding **at the trading-agent level**: the same model family used to *produce* the directional probability, when asked a second-order question, says every recent directional call was too weakly supported to merit conviction. This is the inner loop of the falsification gate.

**F1 + F2 are converging signals** that the raw probability stream is over-stated, and they suggest two independent recalibration channels (temperature scaling + self-calibration gating) that are themselves testable hypotheses for Phase 1.

---

## 7. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 14-day paper validation fails again, ATR fix not enough | Medium | High | iff gate triggers; do not deploy real $ until reproduces. Document and analyze. Honest negative is publishable. |
| Phase 2 spatial layer slips past Week 10 | Medium | Medium | Phase 1 alone is the defensible capstone claim; Phase 2 is "future work" if not done by Aug 12. |
| yfinance throttling delays nightly audits | High | Low | Existing brier_audit has retry logic; ece_audit reuses it. Add caching layer if needed. |
| Claude API cost overruns from sc_audit | Low | Low | Haiku 4.5 batch is cheap (~$0.0005 per audit call); rate-limited; daily cron caps at 50 calls/day = ~$0.025/day |
| Quest 3S hardware not borrowed/purchased by Week 7 | Medium | High (Phase 2) | Phase 2 can be demoed in browser fallback (WebXR + desktop view) without headset for thesis defense |
| Yang declines the scope amendment | Low | Medium | Revert to Phase 1-only thesis (no spatial layer). The 6 calibration upgrades alone constitute a substantial capstone. |

---

## 8. Conference paper plan (out-of-scope for capstone defense, in-scope for combined thesis)

**Target:** ACM ICAIF 2027 (estimated submission deadline 2026-09-15)
**Backup:** IEEE BigData 2026 (December submission)
**Title (working):** *Embodied Calibration: Spatial Pre-Trade Compliance Grounded in a Brier- and ECE-Audited Multi-Source Agent*
**Co-author plan:** Sole-author capstone deliverable; conference paper invites co-authorship from collaborators on the spatial extension.

---

## 9. What I'd value from the advisor in Week 4

1. A gut-check on the scope amendment: does the Phase 1 → Phase 2 framing read as natural sharpening, or scope creep I should pull back from?
2. Recommendations on out-of-sample validation literature beyond Tetlock and Christoffersen for the thesis introduction.
3. A formal advisor signature for capstone credit if pending.
4. Any objection to public-by-default repos (the capstone is in
   `github.com/alex-jb/capstone-orallexa-calibration`, MIT-licensed,
   no real-money trade logs committed) — the public timestamping is
   part of the methodology, but I want to make sure you're comfortable
   with the visibility.

---

## 10. Files in this submission

- `proposal/week-4-project-plan-and-gantt.md` (this document)
- `proposal/proposal.md` and `proposal.pdf` (Week 2 baseline; unchanged)
- `proposal/references.bib` (annotated bibliography source)
- `ANNOTATED-BIBLIOGRAPHY.md` and `Annotated-Bibliography.pdf` (Week 3 deliverable)
- `Advisor-Meeting-Brief-Yang.md` and `.pdf` (Week 3 verbal)
- `src/calibration/` (Phase 1 #1-#6 implementations + tests)
- `scripts/ece_audit.py`, `scripts/sc_audit.py` (live audits)
- `data-snapshots/ece-2026-06-17.{json,md}` (F1 evidence)
- `data-snapshots/sc-2026-06-17.{json,md}` (F2 evidence)
- `weekly-reports/` (Week 1, Week 2 retros)
