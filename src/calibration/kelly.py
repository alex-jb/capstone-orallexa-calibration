"""Confidence-shrunk Kelly position sizing — Phase 1 #5.

References
----------
- Kelly, J. L. (1956). *A new interpretation of information rate*.
  Bell System Technical Journal, 35(4), 917-926.
- Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017).
  *On Calibration of Modern Neural Networks*. ICML.

Why this exists
---------------
The capstone uses calibrated probabilities to drive Kelly-fractional
position sizing. A mis-calibrated probability directly mis-sizes
capital — an over-confident 0.80 forecast that should be 0.65 will
allocate too much of the bankroll to the bet. Kelly's classic
formula has no built-in defense against this: it trusts the input.

This module produces a *shrunken* Kelly fraction:

    f_shrunk = f_kelly * (1 - clip(ECE, 0, ECE_max))

where ECE is the recent Expected Calibration Error of the probability
stream, capped at ECE_max (default 0.25). When the agent is poorly
calibrated, position sizes shrink; when calibration is excellent,
shrinkage approaches 0 and the full Kelly fraction is used.

A second guard caps the maximum bet to a fixed fraction of bankroll
(default 0.25 = quarter Kelly even at perfect calibration), matching
the capstone's $300 deployment ceiling and matching practitioner
conventions (full Kelly is too aggressive even with calibrated probs
because variance of returns swamps the long-run growth rate over
small samples).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KellyResult:
    raw_kelly: float
    shrunk_kelly: float
    capped_kelly: float
    shrinkage_factor: float
    ece_clipped: float
    interpretation: str


def kelly_fraction(p_win: float, win_loss_ratio: float) -> float:
    """Raw Kelly fraction for a binary outcome bet.

    f* = (p_win * b - p_loss) / b
       = p_win - (1 - p_win) / b

    where b = payoff_if_win / loss_if_loss (win:loss ratio).

    Parameters
    ----------
    p_win : forecast probability of winning, in (0, 1)
    win_loss_ratio : b > 0; e.g. 1.5 means win $1.50 per $1 lost

    Returns
    -------
    float; can be negative (skip the bet) or > 1 (theoretical, in practice
    capped before sizing)
    """
    if not 0 < p_win < 1:
        raise ValueError(f"p_win must be in (0, 1), got {p_win}")
    if win_loss_ratio <= 0:
        raise ValueError(f"win_loss_ratio must be > 0, got {win_loss_ratio}")
    p_loss = 1.0 - p_win
    return p_win - p_loss / win_loss_ratio


def confidence_shrunk_kelly(
    p_win: float,
    win_loss_ratio: float,
    ece: float,
    *,
    ece_max: float = 0.25,
    max_fraction: float = 0.25,
) -> KellyResult:
    """Compute the Kelly fraction shrunken by recent calibration error.

    f_shrunk = max(0, f_kelly) * (1 - clip(ece, 0, ece_max))
    f_capped = min(f_shrunk, max_fraction)

    Negative Kelly fractions (no edge, or negative edge) → 0 size.

    Parameters
    ----------
    p_win : forecast probability of winning
    win_loss_ratio : b
    ece : recent Expected Calibration Error of the probability stream;
        higher ECE → more aggressive shrinkage
    ece_max : shrinkage saturates here. With ece_max = 0.25, an ECE of
        0.25+ shrinks Kelly to 0.
    max_fraction : hard cap on the fraction of bankroll (default 0.25 =
        quarter Kelly even at perfect calibration)

    Returns
    -------
    KellyResult
    """
    if not 0 <= ece <= 1:
        raise ValueError(f"ece must be in [0, 1], got {ece}")
    if not 0 < ece_max <= 1:
        raise ValueError(f"ece_max must be in (0, 1], got {ece_max}")
    if not 0 < max_fraction <= 1:
        raise ValueError(f"max_fraction must be in (0, 1], got {max_fraction}")

    raw = kelly_fraction(p_win, win_loss_ratio)
    raw_positive = max(0.0, raw)
    ece_clipped = min(ece, ece_max)
    shrinkage_factor = 1.0 - ece_clipped / ece_max  # in [0, 1]
    shrunk = raw_positive * shrinkage_factor
    capped = min(shrunk, max_fraction)

    if raw <= 0:
        interp = "No edge or negative edge — skip"
    elif capped < 0.01:
        interp = "Calibration too poor — size to zero"
    elif capped == max_fraction:
        interp = "Capped at max_fraction"
    else:
        interp = f"Shrunken by {(1 - shrinkage_factor) * 100:.0f}% due to ECE"

    return KellyResult(
        raw_kelly=raw,
        shrunk_kelly=shrunk,
        capped_kelly=capped,
        shrinkage_factor=shrinkage_factor,
        ece_clipped=ece_clipped,
        interpretation=interp,
    )
