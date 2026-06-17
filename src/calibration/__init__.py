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

# Phase 1 #2 — LLM self-calibration (Kadavath 2022)
from calibration.self_calibration import (
    SELF_CAL_PROMPT_TEMPLATE,
    SelfCalibrationResult,
    build_prompt as build_self_cal_prompt,
    parse_response as parse_self_cal_response,
    apply_decision_gate,
)

# Phase 1 #3 — Structured Reflexion (Shinn 2023)
from calibration.reflexion import (
    Reflexion,
    from_brier_result,
    to_json as reflexion_to_json,
    from_json as reflexion_from_json,
    append_jsonl as append_reflexion_jsonl,
    load_jsonl as load_reflexion_jsonl,
    build_forward_context,
)

# Phase 1 #4 — Information staleness (O'Hara 1995)
from calibration.staleness import (
    DEFAULT_HALF_LIFE_SECONDS,
    StalenessResult,
    staleness,
    weighted_mean,
)

# Phase 1 #5 — Confidence-shrunk Kelly (Kelly 1956 + Guo 2017)
from calibration.kelly import (
    KellyResult,
    kelly_fraction,
    confidence_shrunk_kelly,
)

# Phase 1 #6 — PR-gated self-modification (Sakana 2025)
from calibration.self_modification import (
    MergeProposal,
    MergeDecision,
    MergeStatus,
    evaluate as evaluate_merge_proposal,
)

__all__ = [
    # #1 ECE + temperature scaling
    "expected_calibration_error",
    "ReliabilityBin",
    "fit_temperature",
    "apply_temperature",
    "nll_loss",
    "reliability_diagram_data",
    # #2 self-calibration
    "SELF_CAL_PROMPT_TEMPLATE",
    "SelfCalibrationResult",
    "build_self_cal_prompt",
    "parse_self_cal_response",
    "apply_decision_gate",
    # #3 reflexion
    "Reflexion",
    "from_brier_result",
    "reflexion_to_json",
    "reflexion_from_json",
    "append_reflexion_jsonl",
    "load_reflexion_jsonl",
    "build_forward_context",
    # #4 staleness
    "DEFAULT_HALF_LIFE_SECONDS",
    "StalenessResult",
    "staleness",
    "weighted_mean",
    # #5 kelly
    "KellyResult",
    "kelly_fraction",
    "confidence_shrunk_kelly",
    # #6 self-modification
    "MergeProposal",
    "MergeDecision",
    "MergeStatus",
    "evaluate_merge_proposal",
]

__version__ = "0.1.0"
