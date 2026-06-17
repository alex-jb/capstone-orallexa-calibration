"""capstone-orallexa-calibration / calibration — Phase 1 #1.

Expected Calibration Error (ECE) + temperature scaling for the Orallexa
multi-source probability stream.

Reference
---------
Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017).
*On Calibration of Modern Neural Networks*. ICML.
arXiv:1706.04599.

Why this module exists
----------------------
The capstone's Week 3 advisor brief argues for "calibration discipline":
the Brier score is the headline metric (`Brier_agent − Brier_baseline`
over rolling 30-day windows). Brier is a *proper scoring rule* but
aggregates two distinct things — *resolution* (does the agent separate
events that resolve differently?) and *reliability* (when the agent
says 70%, do those events actually resolve true 70% of the time?).

ECE isolates the reliability term. Temperature scaling fixes systematic
miscalibration without changing the model's rank-ordering or resolution.
Both are non-behavioral additions during the Week 4-6 paper-trading
validation window: ECE is purely a measurement; temperature scaling
produces a calibrated probability *channel* alongside the raw channel,
without changing live trading behavior until validation completes.

Capstone deliverable mapping
----------------------------
- Phase 1 (Weeks 4-6): measurement layer.
- Week 4 advisor demo: ECE curve on existing decision_log.
- Week 5: apply temperature scaling to a held-out fold; report ECE
  improvement vs untemperature baseline.
- Week 6 midterm: report the calibrated-channel Brier delta vs baseline.
"""
from __future__ import annotations

from calibration.ece import expected_calibration_error, ReliabilityBin
from calibration.temperature import (
    fit_temperature,
    apply_temperature,
    nll_loss,
)
from calibration.reliability import reliability_diagram_data

__all__ = [
    "expected_calibration_error",
    "ReliabilityBin",
    "fit_temperature",
    "apply_temperature",
    "nll_loss",
    "reliability_diagram_data",
]

__version__ = "0.1.0"
