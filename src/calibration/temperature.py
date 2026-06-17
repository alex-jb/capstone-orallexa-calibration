"""Temperature scaling for probability calibration (Guo et al. 2017, §4.2).

Temperature scaling is the simplest post-hoc calibration method: divide
the model's logits by a single scalar T > 0 (one parameter) and re-apply
sigmoid (binary) or softmax (multi-class). T > 1 makes the distribution
*softer* (less confident); T < 1 makes it *sharper* (more confident).
T is fit on a held-out validation set by minimizing negative
log-likelihood.

For our binary direction calls, the workflow is:

    1. Convert each forecast_prob p into a logit: z = logit(p) = log(p / (1 - p))
    2. Find T* that minimizes NLL of (sigmoid(z / T), y) on a held-out fold.
    3. At inference time, compute the calibrated probability as
       sigmoid(logit(p_raw) / T*).

Guo et al. observe that temperature scaling does NOT change the model's
rank-ordering. This is *critical* for the capstone: live trading
decisions (BUY / WAIT / SELL) come from the rank-ordering of the three
classes; temperature scaling only flattens or sharpens the probability
distribution without changing which class wins. So a calibrated
probability channel can be added alongside the raw channel for ECE
reporting *without* changing live trading behavior during the Week 4-6
validation window.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize_scalar


_EPS = 1e-7
"""Small epsilon to avoid log(0) and division by zero."""


def _clip(p: np.ndarray) -> np.ndarray:
    return np.clip(p, _EPS, 1.0 - _EPS)


def _logit(p: np.ndarray) -> np.ndarray:
    p = _clip(p)
    return np.log(p / (1.0 - p))


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def apply_temperature(
    forecast_probs: np.ndarray | list[float],
    temperature: float,
) -> np.ndarray:
    """Apply temperature scaling to a 1-D vector of binary probabilities.

    Returns the calibrated probabilities sigmoid(logit(p) / T).

    Parameters
    ----------
    forecast_probs : array-like
    temperature : float, must be > 0

    Returns
    -------
    np.ndarray of same shape as input

    Raises
    ------
    ValueError if temperature <= 0
    """
    if temperature <= 0:
        raise ValueError(f"temperature must be > 0, got {temperature}")
    p = np.asarray(forecast_probs, dtype=float)
    if p.size == 0:
        return p
    z = _logit(p)
    return _sigmoid(z / temperature)


def nll_loss(
    forecast_probs: np.ndarray | list[float],
    outcomes: np.ndarray | list[float],
) -> float:
    """Average negative log-likelihood for binary classification.

        NLL = -1/n * sum( y * log(p) + (1 - y) * log(1 - p) )

    Higher confidence on correct outcomes lowers the loss. Used as the
    objective for fitting temperature.

    Raises
    ------
    ValueError on mismatched shapes or non-binary outcomes.
    """
    p = np.asarray(forecast_probs, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    if p.shape != y.shape:
        raise ValueError(
            f"shape mismatch: probs {p.shape} vs outcomes {y.shape}"
        )
    if p.size == 0:
        return 0.0
    if not set(np.unique(y).tolist()).issubset({0.0, 1.0}):
        raise ValueError("outcomes must be binary (0 or 1)")
    p = _clip(p)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def fit_temperature(
    forecast_probs: np.ndarray | list[float],
    outcomes: np.ndarray | list[float],
    *,
    bounds: tuple[float, float] = (0.05, 20.0),
) -> float:
    """Find temperature T* minimizing NLL on the supplied (probs, outcomes).

    Uses scipy.optimize.minimize_scalar with bounded Brent's method.
    A wider bounds range admits more aggressive sharpening/softening; the
    default (0.05, 20) covers the realistic range for LLM-derived
    probability streams.

    Parameters
    ----------
    forecast_probs : array-like
    outcomes : array-like of 0/1
    bounds : (lo, hi) for T search

    Returns
    -------
    float
        T* in `bounds`. T* > 1 ⇒ original probs were over-confident.

    Raises
    ------
    ValueError on insufficient data (n < 10) or non-binary outcomes.
    """
    p = np.asarray(forecast_probs, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    if p.shape != y.shape:
        raise ValueError(
            f"shape mismatch: probs {p.shape} vs outcomes {y.shape}"
        )
    if len(p) < 10:
        raise ValueError(
            f"insufficient data to fit temperature (n={len(p)}, need ≥10). "
            "For ICML 2017 Table 2 the smallest dataset has thousands; "
            "in this capstone we relax to 10 because per-ticker folds are tiny."
        )

    z = _logit(p)

    def objective(t: float) -> float:
        if t <= 0:
            return float("inf")
        return nll_loss(_sigmoid(z / t), y)

    result = minimize_scalar(
        objective, bounds=bounds, method="bounded",
        options={"xatol": 1e-4},
    )
    if not result.success:
        raise RuntimeError(f"temperature optimization failed: {result.message}")
    return float(result.x)
