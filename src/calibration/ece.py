"""Expected Calibration Error (ECE) on (forecast_probability, binary_outcome) pairs.

Implements the binned ECE estimator from Guo et al. (2017), §2.3:

    ECE = sum_m=1^M (|B_m| / n) * |acc(B_m) - conf(B_m)|

where bins B_m partition the [0, 1] confidence interval, |B_m| is the
number of predictions falling into bin m, acc(B_m) is the empirical
positive rate in that bin, and conf(B_m) is the average predicted
probability in that bin.

For the capstone's binary direction calls (BUY / SELL), the forecast
probability is the *one-sided* probability that the trade resolves in
the predicted direction (decision == "BUY" → probs["up"], decision ==
"SELL" → probs["down"]). The binary outcome is 1 if price moved in the
predicted direction within the lookahead, else 0. This mirrors
brier_audit.py's existing brier_for_decision() shape so the two
metrics can be computed from the same resolution function without
re-fetching prices.

Sensible defaults:
    - 10 equal-width bins (Guo §3.1). 15 if n > 2000.
    - Predictions with forecast_p in [0.05, 0.95] only (extreme bins
      under-populate in our agent because we use confidence floors).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ReliabilityBin:
    """One bin of a reliability diagram."""

    lo: float
    hi: float
    count: int
    avg_confidence: float
    avg_accuracy: float
    gap: float  # avg_confidence - avg_accuracy (signed)

    def __repr__(self) -> str:
        return (
            f"Bin[{self.lo:.2f}-{self.hi:.2f}] "
            f"n={self.count} conf={self.avg_confidence:.3f} "
            f"acc={self.avg_accuracy:.3f} gap={self.gap:+.3f}"
        )


def expected_calibration_error(
    forecast_probs: np.ndarray | list[float],
    outcomes: np.ndarray | list[float],
    *,
    n_bins: int = 10,
    return_bins: bool = False,
) -> float | tuple[float, list[ReliabilityBin]]:
    """Compute Expected Calibration Error.

    Parameters
    ----------
    forecast_probs : array-like of shape (n,)
        Predicted probabilities in [0, 1].
    outcomes : array-like of shape (n,)
        Binary outcomes (0 or 1).
    n_bins : int, default 10
        Number of equal-width bins. Guo et al. use 10 or 15.
    return_bins : bool
        If True, return (ECE, list of ReliabilityBin) for diagram plotting.

    Returns
    -------
    float or (float, list[ReliabilityBin])
        ECE value in [0, 1]. 0 = perfectly calibrated.

    Raises
    ------
    ValueError
        If inputs have mismatched length, or any forecast_prob is outside [0, 1],
        or any outcome is not in {0, 1}.

    Notes
    -----
    Predictions exactly equal to 1.0 are assigned to the last bin (closed-right
    on the final bin only). All other bins are half-open [lo, hi).
    """
    p = np.asarray(forecast_probs, dtype=float)
    y = np.asarray(outcomes, dtype=float)

    if p.shape != y.shape:
        raise ValueError(
            f"forecast_probs and outcomes must have same shape, got "
            f"{p.shape} vs {y.shape}"
        )
    if p.ndim != 1:
        raise ValueError(f"forecast_probs must be 1-D, got shape {p.shape}")
    if (p < 0).any() or (p > 1).any():
        raise ValueError("forecast_probs must lie in [0, 1]")
    if not set(np.unique(y).tolist()).issubset({0.0, 1.0}):
        raise ValueError("outcomes must be binary (0 or 1)")
    if n_bins < 2:
        raise ValueError(f"n_bins must be >= 2, got {n_bins}")
    if len(p) == 0:
        if return_bins:
            return 0.0, []
        return 0.0

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    n = len(p)
    ece = 0.0
    bins: list[ReliabilityBin] = []

    for m in range(n_bins):
        lo = bin_edges[m]
        hi = bin_edges[m + 1]
        if m == n_bins - 1:
            mask = (p >= lo) & (p <= hi)  # closed-right only on last bin
        else:
            mask = (p >= lo) & (p < hi)
        count = int(mask.sum())
        if count == 0:
            bins.append(
                ReliabilityBin(
                    lo=lo, hi=hi, count=0,
                    avg_confidence=(lo + hi) / 2,
                    avg_accuracy=0.0,
                    gap=0.0,
                )
            )
            continue
        avg_conf = float(p[mask].mean())
        avg_acc = float(y[mask].mean())
        gap = avg_conf - avg_acc
        ece += (count / n) * abs(gap)
        bins.append(
            ReliabilityBin(
                lo=lo, hi=hi, count=count,
                avg_confidence=avg_conf,
                avg_accuracy=avg_acc,
                gap=gap,
            )
        )

    if return_bins:
        return ece, bins
    return ece
