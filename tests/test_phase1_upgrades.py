"""Tests for Phase 1 upgrades #2-#6.

#2 self_calibration (Kadavath 2022)
#3 reflexion (Shinn 2023)
#4 staleness (O'Hara 1995)
#5 kelly (Kelly 1956 + Guo 2017)
#6 self_modification (Sakana 2025)
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calibration.kelly import KellyResult, confidence_shrunk_kelly, kelly_fraction
from calibration.staleness import (
    DEFAULT_HALF_LIFE_SECONDS,
    staleness,
    weighted_mean,
)
from calibration.reflexion import (
    Reflexion,
    append_jsonl,
    build_forward_context,
    from_brier_result,
    from_json,
    load_jsonl,
    to_json,
)
from calibration.self_calibration import (
    apply_decision_gate,
    build_prompt,
    parse_response,
    SelfCalibrationResult,
)
from calibration.self_modification import (
    MergeDecision,
    MergeProposal,
    MergeStatus,
    evaluate,
)


# ============================================================ #5 Kelly


class TestKelly:
    def test_kelly_positive_edge(self) -> None:
        # 60% to win, 1:1 payoff → 20% Kelly
        assert kelly_fraction(0.6, 1.0) == pytest.approx(0.2)

    def test_kelly_no_edge(self) -> None:
        assert kelly_fraction(0.5, 1.0) == pytest.approx(0.0)

    def test_kelly_negative_edge(self) -> None:
        assert kelly_fraction(0.4, 1.0) < 0

    def test_kelly_extreme_p_raises(self) -> None:
        with pytest.raises(ValueError, match="p_win"):
            kelly_fraction(0.0, 1.0)
        with pytest.raises(ValueError, match="p_win"):
            kelly_fraction(1.0, 1.0)

    def test_shrunk_kelly_perfect_calibration(self) -> None:
        r = confidence_shrunk_kelly(0.6, 1.0, ece=0.0)
        assert r.raw_kelly == pytest.approx(0.2)
        assert r.shrinkage_factor == pytest.approx(1.0)
        assert r.shrunk_kelly == pytest.approx(0.2)
        assert r.capped_kelly == pytest.approx(0.2)
        assert "Capped" not in r.interpretation  # 0.2 < 0.25 default cap

    def test_shrunk_kelly_max_ece_zeroes(self) -> None:
        r = confidence_shrunk_kelly(0.7, 1.0, ece=0.25)
        assert r.shrinkage_factor == pytest.approx(0.0)
        assert r.shrunk_kelly == pytest.approx(0.0)

    def test_shrunk_kelly_partial_ece(self) -> None:
        # ece 0.125 = half of ece_max → shrinkage_factor = 0.5
        r = confidence_shrunk_kelly(0.7, 1.0, ece=0.125)
        assert r.shrinkage_factor == pytest.approx(0.5)
        # raw_kelly = 0.4, shrunk = 0.2
        assert r.shrunk_kelly == pytest.approx(0.2)

    def test_shrunk_kelly_negative_edge_zeroes(self) -> None:
        r = confidence_shrunk_kelly(0.4, 1.0, ece=0.05)
        assert r.shrunk_kelly == 0.0

    def test_shrunk_kelly_caps_at_max_fraction(self) -> None:
        # huge edge + perfect calibration → still capped
        r = confidence_shrunk_kelly(0.9, 2.0, ece=0.0, max_fraction=0.25)
        assert r.capped_kelly == pytest.approx(0.25)
        assert "Capped" in r.interpretation


# ============================================================ #4 Staleness


class TestStaleness:
    def test_fresh_signal_weight_near_one(self) -> None:
        now = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
        ts = now - timedelta(seconds=5)
        r = staleness("polymarket_midpoint", ts, now=now)
        assert r.decay_weight > 0.98
        assert r.is_fresh

    def test_one_half_life_returns_one_half(self) -> None:
        now = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
        # polymarket_midpoint half_life = 300s
        ts = now - timedelta(seconds=300)
        r = staleness("polymarket_midpoint", ts, now=now)
        assert r.decay_weight == pytest.approx(0.5, abs=1e-9)
        assert r.is_fresh  # 0.5 still counts as fresh by convention

    def test_two_half_lives_returns_one_quarter(self) -> None:
        now = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
        ts = now - timedelta(seconds=600)
        r = staleness("polymarket_midpoint", ts, now=now)
        assert r.decay_weight == pytest.approx(0.25, abs=1e-9)
        assert not r.is_fresh

    def test_unknown_source_without_override_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown source"):
            staleness("nonexistent_source", datetime.now(timezone.utc))

    def test_override_half_life(self) -> None:
        now = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
        ts = now - timedelta(seconds=10)
        r = staleness(
            "polymarket_midpoint", ts,
            half_life_seconds=10.0, now=now,
        )
        assert r.decay_weight == pytest.approx(0.5)

    def test_future_signal_clamps_to_zero_age(self) -> None:
        now = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
        ts = now + timedelta(seconds=10)  # clock skew
        r = staleness("polymarket_midpoint", ts, now=now)
        assert r.age_seconds == 0.0
        assert r.decay_weight == pytest.approx(1.0)

    def test_weighted_mean_basic(self) -> None:
        assert weighted_mean([1.0, 2.0], [1.0, 1.0]) == pytest.approx(1.5)

    def test_weighted_mean_zero_weights_returns_zero(self) -> None:
        assert weighted_mean([1.0, 2.0], [0.0, 0.0]) == 0.0

    def test_weighted_mean_shape_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="length mismatch"):
            weighted_mean([1.0], [1.0, 1.0])

    def test_all_default_sources_have_half_lives(self) -> None:
        expected = {
            "polymarket_midpoint", "equity_realtime", "equity_eod_close",
            "sec_13f", "news_sentiment", "technical_intraday",
            "technical_swing", "llm_belief",
        }
        assert set(DEFAULT_HALF_LIFE_SECONDS.keys()) == expected
        assert all(v > 0 for v in DEFAULT_HALF_LIFE_SECONDS.values())


# ============================================================ #3 Reflexion


class TestReflexion:
    def _row(self) -> dict:
        return {
            "ticker": "BKSY", "decision": "BUY",
            "forecast_p": 0.7, "actual": 0.0, "brier": 0.49,
            "timestamp": "2026-06-15T11:31:22",
        }

    def test_from_brier_result_basic(self) -> None:
        r = from_brier_result(
            self._row(),
            cause="Ignored news_sentiment staleness > 6h",
            lesson="Refuse BUY when news_sentiment older than 4 hours",
            forward_prompt="If news sentiment is > 4h old, demote BUY to WAIT.",
            severity="lesson_extracted",
            tags=["staleness", "BKSY"],
        )
        assert r.ticker == "BKSY"
        assert r.forecast_p == 0.7
        assert r.actual == 0.0
        assert r.severity == "lesson_extracted"
        assert r.tags == ["staleness", "BKSY"]

    def test_cause_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="cause too long"):
            from_brier_result(
                self._row(),
                cause="x" * 250,
                lesson="short",
                forward_prompt="short",
            )

    def test_round_trip_json(self) -> None:
        r1 = from_brier_result(self._row(), "c", "l", "fp")
        s = to_json(r1)
        r2 = from_json(s)
        assert r2.ticker == r1.ticker
        assert r2.cause == r1.cause
        assert r2.timestamp == r1.timestamp

    def test_append_and_load_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "subdir" / "refl.jsonl"
            r1 = from_brier_result(self._row(), "c1", "l1", "fp1")
            r2 = from_brier_result(self._row(), "c2", "l2", "fp2")
            append_jsonl(r1, path)
            append_jsonl(r2, path)
            loaded = load_jsonl(path)
            assert len(loaded) == 2
            assert loaded[0].cause == "c1"
            assert loaded[1].cause == "c2"

    def test_load_jsonl_missing_returns_empty(self) -> None:
        assert load_jsonl(Path("/tmp/this_definitely_does_not_exist_42.jsonl")) == []

    def test_build_forward_context_orders_newest_first(self) -> None:
        r_old = Reflexion(
            timestamp="2026-06-10T00:00:00+00:00",
            ticker="X", decision="BUY", forecast_p=0.6, actual=0.0, brier=0.36,
            cause="c1", lesson="l1", forward_prompt="OLD",
        )
        r_new = Reflexion(
            timestamp="2026-06-15T00:00:00+00:00",
            ticker="X", decision="BUY", forecast_p=0.6, actual=0.0, brier=0.36,
            cause="c2", lesson="l2", forward_prompt="NEW",
        )
        ctx = build_forward_context([r_old, r_new], n=14)
        assert ctx.index("NEW") < ctx.index("OLD")

    def test_build_forward_context_empty_returns_empty(self) -> None:
        assert build_forward_context([], n=14) == ""

    def test_invalid_forecast_p_raises(self) -> None:
        with pytest.raises(ValueError, match="forecast_p"):
            Reflexion(
                timestamp="2026-06-15T00:00:00+00:00",
                ticker="X", decision="BUY", forecast_p=1.5,
                actual=0.0, brier=0.36,
                cause="c", lesson="l", forward_prompt="fp",
            )

    def test_invalid_actual_raises(self) -> None:
        with pytest.raises(ValueError, match="actual"):
            Reflexion(
                timestamp="2026-06-15T00:00:00+00:00",
                ticker="X", decision="BUY", forecast_p=0.5,
                actual=0.5, brier=0.0,
                cause="c", lesson="l", forward_prompt="fp",
            )


# ============================================================ #2 Self-calibration


class TestSelfCalibration:
    def test_build_prompt_contains_ticker_and_probability(self) -> None:
        p = build_prompt("BKSY", "BUY", 0.72)
        assert "BKSY" in p
        assert "0.7200" in p
        assert "second-order" in p.lower()

    def test_build_prompt_invalid_decision_raises(self) -> None:
        with pytest.raises(ValueError, match="decision"):
            build_prompt("X", "HOLD", 0.7)

    def test_parse_valid_response(self) -> None:
        r = parse_response(json.dumps({
            "second_order_confidence": 0.75,
            "primary_doubt": "Volume anomaly unexplained",
            "would_size_full_kelly": True,
        }))
        assert r.second_order_confidence == 0.75
        assert r.passes_threshold  # 0.75 > 0.6 default
        assert r.would_size_full_kelly

    def test_parse_strips_markdown_fences(self) -> None:
        text = "```json\n" + json.dumps({
            "second_order_confidence": 0.5,
            "primary_doubt": "regime ambiguous",
            "would_size_full_kelly": False,
        }) + "\n```"
        r = parse_response(text)
        assert not r.passes_threshold  # 0.5 < 0.6

    def test_parse_missing_key_raises(self) -> None:
        with pytest.raises(ValueError, match="missing key"):
            parse_response(json.dumps({"second_order_confidence": 0.5}))

    def test_parse_out_of_range_confidence_raises(self) -> None:
        with pytest.raises(ValueError, match="second_order_confidence"):
            parse_response(json.dumps({
                "second_order_confidence": 1.5,
                "primary_doubt": "",
                "would_size_full_kelly": False,
            }))

    def test_parse_malformed_json_raises(self) -> None:
        with pytest.raises(ValueError, match="parse"):
            parse_response("not json")

    def test_gate_demotes_buy_when_below_threshold(self) -> None:
        result = SelfCalibrationResult(
            second_order_confidence=0.3,
            primary_doubt="",
            would_size_full_kelly=False,
            passes_threshold=False,
            threshold=0.6,
            interpretation="",
        )
        assert apply_decision_gate("BUY", result) == "WAIT"

    def test_gate_passes_buy_when_above_threshold(self) -> None:
        result = SelfCalibrationResult(
            second_order_confidence=0.8,
            primary_doubt="",
            would_size_full_kelly=True,
            passes_threshold=True,
            threshold=0.6,
            interpretation="",
        )
        assert apply_decision_gate("BUY", result) == "BUY"

    def test_gate_wait_stays_wait(self) -> None:
        result = SelfCalibrationResult(
            second_order_confidence=0.9,
            primary_doubt="",
            would_size_full_kelly=True,
            passes_threshold=True,
            threshold=0.6,
            interpretation="",
        )
        assert apply_decision_gate("WAIT", result) == "WAIT"


# ============================================================ #6 Self-modification


class TestSelfModification:
    def _proposal(self, **overrides) -> MergeProposal:
        defaults = dict(
            proposal_id="2026-06-17-test-001",
            kind="prompt_edit",
            description="Add staleness pre-flight to system prompt",
            baseline_brier=0.255,
            candidate_brier=0.245,
            held_out_n=50,
            human_approved=True,
        )
        defaults.update(overrides)
        return MergeProposal(**defaults)

    def test_approve_when_improvement_and_approval(self) -> None:
        d = evaluate(self._proposal())
        assert d.status == MergeStatus.APPROVE
        assert d.brier_delta == pytest.approx(0.010)

    def test_block_when_no_human_approval(self) -> None:
        d = evaluate(self._proposal(human_approved=False))
        assert d.status == MergeStatus.BLOCK_NO_HUMAN_APPROVAL

    def test_block_when_brier_does_not_improve_enough(self) -> None:
        # delta = 0.255 - 0.252 = 0.003 < 0.005 default
        d = evaluate(self._proposal(candidate_brier=0.252))
        assert d.status == MergeStatus.BLOCK_NO_BRIER_GAIN
        assert d.brier_delta == pytest.approx(0.003)

    def test_block_when_held_out_too_small(self) -> None:
        d = evaluate(self._proposal(held_out_n=10))
        assert d.status == MergeStatus.BLOCK_INSUFFICIENT_DATA

    def test_can_tune_thresholds(self) -> None:
        # With stricter min_improvement of 0.015, the default proposal (0.010 delta) should block
        d = evaluate(self._proposal(), min_improvement=0.015)
        assert d.status == MergeStatus.BLOCK_NO_BRIER_GAIN

    def test_brier_delta_negative_when_candidate_worse(self) -> None:
        d = evaluate(self._proposal(candidate_brier=0.270))
        assert d.status == MergeStatus.BLOCK_NO_BRIER_GAIN
        assert d.brier_delta < 0

    def test_invalid_min_improvement_raises(self) -> None:
        with pytest.raises(ValueError, match="min_improvement"):
            evaluate(self._proposal(), min_improvement=0.0)
