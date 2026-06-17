"""Reliability diagram data (matplotlib-ready).

A reliability diagram plots per-bin (avg_confidence, avg_accuracy) pairs.
A perfectly calibrated model lies on the diagonal y = x.

Returns plotting data (not a plot) so the same module is testable
without a display, and so callers can render with matplotlib, plotly,
or LaTeX/pgfplots — capstone defense will use the diagram in the
midterm presentation slide.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from calibration.ece import ReliabilityBin, expected_calibration_error


@dataclass(frozen=True)
class ReliabilityDiagramData:
    """All numbers needed to draw a reliability diagram + report ECE."""

    bins: list[ReliabilityBin]
    ece: float
    n: int
    bar_centers: np.ndarray  # bin midpoints
    bar_heights: np.ndarray  # avg_accuracy per bin
    bar_widths: np.ndarray   # bin widths (uniform for equal-width binning)
    gap_above: np.ndarray    # signed gap (avg_confidence - avg_accuracy)
    diagonal: tuple[np.ndarray, np.ndarray]  # (x, y) for y = x reference line


def reliability_diagram_data(
    forecast_probs: np.ndarray | list[float],
    outcomes: np.ndarray | list[float],
    *,
    n_bins: int = 10,
) -> ReliabilityDiagramData:
    """Compute the data for a reliability diagram.

    Parameters
    ----------
    forecast_probs : array-like
    outcomes : array-like of 0/1
    n_bins : default 10

    Returns
    -------
    ReliabilityDiagramData

    Usage with matplotlib (capstone Week 6 midterm slide):

        import matplotlib.pyplot as plt
        d = reliability_diagram_data(probs, outcomes, n_bins=10)
        fig, ax = plt.subplots()
        ax.bar(d.bar_centers, d.bar_heights, width=d.bar_widths,
               edgecolor='black', alpha=0.7)
        ax.plot(*d.diagonal, color='red', linestyle='--', label='perfect calibration')
        ax.set_xlabel('Confidence (bin midpoint)')
        ax.set_ylabel('Empirical accuracy')
        ax.set_title(f'Reliability diagram — ECE = {d.ece:.3f}, n = {d.n}')
        ax.legend()
    """
    ece, bins = expected_calibration_error(
        forecast_probs, outcomes, n_bins=n_bins, return_bins=True
    )
    n = int(np.asarray(outcomes).shape[0])
    centers = np.array([(b.lo + b.hi) / 2 for b in bins])
    heights = np.array([b.avg_accuracy for b in bins])
    widths = np.array([b.hi - b.lo for b in bins])
    gaps = np.array([b.gap for b in bins])
    x = np.linspace(0.0, 1.0, 51)
    diagonal = (x, x)
    return ReliabilityDiagramData(
        bins=bins,
        ece=float(ece),
        n=n,
        bar_centers=centers,
        bar_heights=heights,
        bar_widths=widths,
        gap_above=gaps,
        diagonal=diagonal,
    )
