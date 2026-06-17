# src/calibration — Phase 1 #1

Expected Calibration Error + temperature scaling. Reference: Guo et al. (2017), *On Calibration of Modern Neural Networks*, ICML.

## Why this module exists

The capstone (COM 6000-CP1, Prof. Yang) tests whether the Orallexa agent can hold a measurable Brier-score advantage over a market-implied baseline when deployed live. The Week 3 falsification gate triggered (walk-forward OOS Sharpe negative → held the $300 real-money deployment) and surfaced an opportunity: the Brier score is the headline metric, but Brier aggregates *resolution* (does the agent separate events that resolve differently?) and *reliability* (when the agent says 70%, do those events actually resolve true 70% of the time?). Expected Calibration Error isolates the reliability term, and temperature scaling fixes systematic miscalibration without changing rank-ordering or live trading behavior during the Week 4-6 paper-trading validation window.

## Public API

```python
from calibration import (
    expected_calibration_error,
    fit_temperature,
    apply_temperature,
    nll_loss,
    reliability_diagram_data,
)

# 1. Measure ECE (10 equal-width bins, Guo §3.1)
ece = expected_calibration_error(forecast_probs, outcomes, n_bins=10)

# 2. Fit a single-scalar temperature on a held-out fold
T_star = fit_temperature(train_probs, train_outcomes)

# 3. Apply T* at inference time to produce a calibrated probability channel
calibrated_probs = apply_temperature(val_probs, T_star)

# 4. Reliability diagram data ready for matplotlib / plotly
diag = reliability_diagram_data(forecast_probs, outcomes, n_bins=10)
```

## Files

| File | Purpose |
|---|---|
| `ece.py` | ECE estimator (binned) and `ReliabilityBin` dataclass |
| `temperature.py` | NLL loss + temperature fit + apply |
| `reliability.py` | `ReliabilityDiagramData` dataclass for plotting |

## Tests

```
python3 -m pytest tests/test_calibration.py -v
# 19 tests, ~0.3s
```

## Live CLI

```bash
python3 scripts/ece_audit.py
```

Loads `~/.orallexa/markets/decision_log.json`, resolves all decisions whose lookahead window has closed (`brier_audit.brier_for_decision` reused), computes ECE + reliability bins + temperature on a chronological held-out fold, writes JSON + Markdown to `data-snapshots/ece-YYYY-MM-DD.{json,md}`.

## Calibration discipline as the audit primitive

The capstone amendment email (in `docs/capstone-thesis/yang-amendment-email-2026-06-17.md` in the sibling embodied-compliance-council repo) extends the thesis from "calibration discipline in trading" to "calibration as the audit primitive for spatial pre-trade compliance". ECE is the metric that makes a spatial pre-trade approval epistemically meaningful rather than theatrical: a gesture-vote attached to a Brier-and-ECE-scored probability is a probabilistically-attached commitment, not a yes-button.
