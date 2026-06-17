"""LLM self-calibration pre-flight check — Phase 1 #2.

Reference
---------
Kadavath, S., Conerly, T., Askell, A., Henighan, T., Drain, D., Perez, E.,
Schiefer, N., Hatfield-Dodds, Z., DasSarma, N., Tran-Johnson, E., Johnston, S.,
El-Showk, S., Jones, A., Elhage, N., Hume, T., Chen, A., Bai, Y., Bowman, S.,
Fort, S., Ganguli, D., Hernandez, D., Jacobson, J., Kernion, J., Kravec, S.,
Lovitt, L., Ndousse, K., Olsson, C., Ringer, S., Amodei, D., Brown, T.,
Clark, J., Joseph, N., Mann, B., McCandlish, S., Olah, C., Kaplan, J. (2022).
*Language models (mostly) know what they know*. arXiv:2207.05221.

Why this exists
---------------
Kadavath et al. show large language models can produce reasonably calibrated
*self-assessments* of correctness when prompted to do so (the "P(IK)" probe,
short for Probability that I Know). The capstone uses an LLM as one of its
probability sources; before staking real capital on a 0.70 BUY forecast,
this module asks the *same* LLM a second-order question:

    "You just said the probability of UP is 0.70. On a scale of 0 to 1,
     how confident are you in that 0.70 estimate?"

If the second-order confidence is below threshold (default 0.60), the
agent demotes the decision from BUY to WAIT. This is the iff-gate's
inner loop: the falsification gate at the *prediction* level mirrors
the OOS-Sharpe gate at the *deployment* level.

The module here defines:

1. The prompt template (single source of truth, easy to audit)
2. A response schema (so the LLM is forced to return JSON we can parse
   without regex)
3. A Python parser + decision rule
4. A no-LLM fallback for unit testing

The actual Claude API call is intentionally NOT in this module — it
lives in scripts/sc_audit.py so the capstone has clean separation
between *logic that is testable without an API key* and *the live
integration*. The thesis defense rests on the logic; the live
integration is a thin shell.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal


SystemPromptInjection = Literal["prepend", "append", "standalone"]


SELF_CAL_PROMPT_TEMPLATE = """You previously emitted the following forecast:

  Ticker: {ticker}
  Decision: {decision}
  Forecast probability the decision resolves correctly: {forecast_p:.4f}

Now answer a second-order question. On a scale of 0.0 to 1.0, how confident
are you that the {forecast_p:.4f} estimate itself is well-calibrated? Consider:

- Was the underlying reasoning grounded in fresh, low-staleness data?
- Was the regime (trending / chopping / event-driven) clearly identifiable?
- Are there any indicators in your reasoning that contradicted each other?
- Would you bet your own money at this confidence level?

Respond ONLY with a JSON object on a single line, no prose, no markdown
fences. Schema:

{{
  "second_order_confidence": <float in [0, 1]>,
  "primary_doubt": "<≤ 120 chars; the single biggest reason to doubt the forecast, or 'none'>",
  "would_size_full_kelly": <true or false>
}}
"""


@dataclass(frozen=True)
class SelfCalibrationResult:
    second_order_confidence: float
    primary_doubt: str
    would_size_full_kelly: bool
    passes_threshold: bool
    threshold: float
    interpretation: str


def build_prompt(ticker: str, decision: str, forecast_p: float) -> str:
    """Render the self-calibration prompt for one prior forecast."""
    if decision not in ("BUY", "SELL", "WAIT"):
        raise ValueError(f"decision must be BUY/SELL/WAIT, got {decision}")
    if not 0 < forecast_p < 1:
        raise ValueError(f"forecast_p must be in (0, 1), got {forecast_p}")
    return SELF_CAL_PROMPT_TEMPLATE.format(
        ticker=ticker, decision=decision, forecast_p=forecast_p,
    )


def parse_response(text: str, *, threshold: float = 0.60) -> SelfCalibrationResult:
    """Parse the LLM's JSON response into a typed result.

    Raises ValueError if the JSON is malformed or missing required fields.

    The threshold is intentionally a parameter so the capstone can
    test multiple thresholds (0.5 / 0.6 / 0.7) and report which one
    produces the best Brier delta. Kadavath et al. use ~0.5 as the
    'I think I know' boundary.
    """
    if not 0 < threshold < 1:
        raise ValueError(f"threshold must be in (0, 1), got {threshold}")
    try:
        # Strip markdown fences if any (some prompts leak them).
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        obj = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError) as e:
        raise ValueError(f"could not parse self-calibration JSON: {e!r}; raw: {text[:120]!r}")

    for key in ("second_order_confidence", "primary_doubt", "would_size_full_kelly"):
        if key not in obj:
            raise ValueError(f"missing key {key!r} in response: {obj}")
    soc = obj["second_order_confidence"]
    if not isinstance(soc, (int, float)) or not 0 <= soc <= 1:
        raise ValueError(f"second_order_confidence must be float in [0, 1], got {soc!r}")

    doubt = str(obj["primary_doubt"])[:120]
    full_kelly = bool(obj["would_size_full_kelly"])
    passes = soc >= threshold

    if not passes:
        interp = f"Below threshold ({soc:.2f} < {threshold}) — demote to WAIT"
    elif full_kelly:
        interp = f"High confidence ({soc:.2f}) and full Kelly accepted"
    else:
        interp = f"Pass threshold ({soc:.2f}) but quarter-Kelly only (model self-flagged)"

    return SelfCalibrationResult(
        second_order_confidence=float(soc),
        primary_doubt=doubt,
        would_size_full_kelly=full_kelly,
        passes_threshold=passes,
        threshold=threshold,
        interpretation=interp,
    )


def apply_decision_gate(
    primary_decision: str,
    self_cal: SelfCalibrationResult,
) -> str:
    """Demote BUY/SELL to WAIT when self-calibration fails the threshold."""
    if primary_decision not in ("BUY", "SELL", "WAIT"):
        raise ValueError(f"primary_decision must be BUY/SELL/WAIT, got {primary_decision}")
    if primary_decision == "WAIT":
        return "WAIT"
    if not self_cal.passes_threshold:
        return "WAIT"
    return primary_decision
