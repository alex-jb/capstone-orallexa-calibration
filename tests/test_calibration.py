"""Tests for the calibration module — ECE, temperature scaling, reliability."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calibration import (
    ReliabilityBin,
    apply_temperature,
    expected_calibration_error,
    fit_temperature,
    nll_loss,
    reliability_diagram_data,
)


# ------------------------------------------------------------------ ECE


class TestExpectedCalibrationError:
    def test_perfect_calibration_returns_zero(self) -> None:
        """When forecast_prob == empirical accuracy in every bin, ECE = 0."""
        # Build a dataset where exactly 70% of predictions at p=0.7 resolve true.
        # 100 predictions at 0.7 with 70 successes.
        probs = np.full(100, 0.7)
        outs = np.zeros(100)
        outs[:70] = 1.0
        np.random.default_rng(0).shuffle(outs)
        ece = expected_calibration_error(probs, outs, n_bins=10)
        assert ece == pytest.approx(0.0, abs=1e-9)

    def test_systematic_overconfidence(self) -> None:
        """Forecast 0.9 but resolves true only 50% of the time → ECE = 0.4."""
        probs = np.full(100, 0.9)
        outs = np.zeros(100)
        outs[:50] = 1.0
        ece = expected_calibration_error(probs, outs, n_bins=10)
        assert ece == pytest.approx(0.4, abs=0.01)

    def test_returns_bins_when_requested(self) -> None:
        probs = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        outs = np.array([0, 0, 1, 1, 1])
        ece, bins = expected_calibration_error(
            probs, outs, n_bins=5, return_bins=True
        )
        assert len(bins) == 5
        assert all(isinstance(b, ReliabilityBin) for b in bins)

    def test_empty_input_returns_zero(self) -> None:
        ece = expected_calibration_error([], [])
        assert ece == 0.0

    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="same shape"):
            expected_calibration_error([0.5, 0.7], [1, 0, 1])

    def test_prob_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="lie in"):
            expected_calibration_error([0.5, 1.5], [1, 0])

    def test_non_binary_outcomes_raises(self) -> None:
        with pytest.raises(ValueError, match="binary"):
            expected_calibration_error([0.5, 0.7], [1, 0.5])

    def test_invalid_n_bins_raises(self) -> None:
        with pytest.raises(ValueError, match="n_bins"):
            expected_calibration_error([0.5], [1], n_bins=1)


# ------------------------------------------------------------------ Temperature


class TestTemperatureScaling:
    def test_t_equals_one_is_identity(self) -> None:
        probs = np.array([0.1, 0.5, 0.9])
        out = apply_temperature(probs, temperature=1.0)
        np.testing.assert_allclose(out, probs, atol=1e-9)

    def test_t_greater_than_one_softens(self) -> None:
        """T > 1 pulls probabilities toward 0.5."""
        out = apply_temperature(np.array([0.9]), temperature=2.0)
        assert 0.5 < out[0] < 0.9

    def test_t_less_than_one_sharpens(self) -> None:
        """T < 1 pushes probabilities toward 0/1."""
        out = apply_temperature(np.array([0.6]), temperature=0.5)
        assert out[0] > 0.6

    def test_t_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="> 0"):
            apply_temperature([0.5], temperature=0.0)

    def test_fit_recovers_unity_on_calibrated_data(self) -> None:
        """When data is already calibrated, T* should be ≈ 1."""
        rng = np.random.default_rng(0)
        n = 1000
        probs = rng.uniform(0.1, 0.9, n)
        outcomes = (rng.uniform(0, 1, n) < probs).astype(float)
        t_star = fit_temperature(probs, outcomes)
        assert 0.7 < t_star < 1.5, (
            f"expected T* near 1, got {t_star}"
        )

    def test_fit_recovers_t_above_one_on_overconfident_data(self) -> None:
        """When the model is over-confident, fit_temperature should return T > 1."""
        rng = np.random.default_rng(1)
        n = 2000
        # Generate calibrated true probabilities then sharpen them by T=2.0
        # so the fit should recover ~2.0.
        true_p = rng.uniform(0.1, 0.9, n)
        outcomes = (rng.uniform(0, 1, n) < true_p).astype(float)
        # Reverse-engineer over-confident probs:
        true_logit = np.log(true_p / (1 - true_p))
        overconfident_logit = true_logit * 2.0
        overconfident_p = 1.0 / (1.0 + np.exp(-overconfident_logit))
        t_star = fit_temperature(overconfident_p, outcomes)
        assert 1.5 < t_star < 2.5, (
            f"expected T* near 2.0 (over-confident), got {t_star}"
        )

    def test_fit_insufficient_data_raises(self) -> None:
        with pytest.raises(ValueError, match="insufficient"):
            fit_temperature([0.5] * 5, [1] * 5)

    def test_nll_loss_perfect_prediction_is_low(self) -> None:
        loss = nll_loss([0.99, 0.01], [1.0, 0.0])
        assert loss < 0.02

    def test_nll_loss_inverted_prediction_is_high(self) -> None:
        loss = nll_loss([0.01, 0.99], [1.0, 0.0])
        assert loss > 4.0


# ------------------------------------------------------------------ Reliability


class TestReliabilityDiagram:
    def test_returns_full_dataclass(self) -> None:
        probs = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        outs = np.array([0, 0, 1, 1, 1])
        d = reliability_diagram_data(probs, outs, n_bins=5)
        assert d.n == 5
        assert len(d.bins) == 5
        assert d.bar_centers.shape == (5,)
        assert d.bar_heights.shape == (5,)
        assert d.bar_widths.shape == (5,)
        assert d.diagonal[0].shape == d.diagonal[1].shape

    def test_ece_matches_standalone_function(self) -> None:
        probs = np.array([0.2, 0.4, 0.6, 0.8])
        outs = np.array([0, 1, 0, 1])
        d = reliability_diagram_data(probs, outs, n_bins=10)
        ece_alone = expected_calibration_error(probs, outs, n_bins=10)
        assert d.ece == pytest.approx(ece_alone)
