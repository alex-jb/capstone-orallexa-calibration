"""Information staleness tagging and decay weighting — Phase 1 #4.

References
----------
O'Hara, M. (1995). *Market Microstructure Theory*. Blackwell.
Sections on information asymmetry, order flow, and price formation
in heterogeneously-staled signals.

Why this exists
---------------
Polymarket midpoints from 5 minutes ago vs 5 hours ago have very
different reliability. SEC EDGAR filings two seconds old vs two weeks
old. Same with technical indicators: an RSI computed from a stale tape
is a noisy estimate of the live RSI. The Brier audit treats every
prediction equally; this module weights *signals into* the prediction
by their age, applying exponential decay with a per-source half-life.

Half-life conventions used in the capstone:
- Polymarket midpoint: 5 minutes
- Equity price quote (real-time IEX): 30 seconds
- Equity end-of-day close: 24 hours
- SEC EDGAR 13F holdings: 14 days
- News headline sentiment: 6 hours
- Technical indicators (RSI, MACD, ATR): 1 hour (intraday) / 1 day (swing)

These defaults are sensible but expected to be tuned per ticker as
the agent's daily-retro loop refines them.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


SourceType = Literal[
    "polymarket_midpoint",
    "equity_realtime",
    "equity_eod_close",
    "sec_13f",
    "news_sentiment",
    "technical_intraday",
    "technical_swing",
    "llm_belief",
]


DEFAULT_HALF_LIFE_SECONDS: dict[str, float] = {
    "polymarket_midpoint": 300.0,         # 5 min
    "equity_realtime": 30.0,              # 30 sec
    "equity_eod_close": 86_400.0,         # 24 hours
    "sec_13f": 14 * 86_400.0,             # 14 days
    "news_sentiment": 6 * 3_600.0,        # 6 hours
    "technical_intraday": 3_600.0,        # 1 hour
    "technical_swing": 86_400.0,          # 1 day
    "llm_belief": 86_400.0,               # 1 day (model knowledge cutoff drift)
}


@dataclass(frozen=True)
class StalenessResult:
    age_seconds: float
    half_life_seconds: float
    decay_weight: float                   # in [0, 1]; 1 = fresh, 0.5 = one half-life old, 0 = stale beyond cutoff
    is_fresh: bool                        # decay_weight ≥ 0.5
    is_acceptable: bool                   # decay_weight ≥ acceptable_threshold


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc(ts: datetime | str) -> datetime:
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def staleness(
    source: SourceType | str,
    signal_timestamp: datetime | str,
    *,
    half_life_seconds: float | None = None,
    acceptable_threshold: float = 0.25,
    now: datetime | None = None,
) -> StalenessResult:
    """Compute exponential-decay staleness weight for one signal.

    decay_weight = 2 ** (-age / half_life)

    Parameters
    ----------
    source : SourceType — picks the default half-life if half_life_seconds is None
    signal_timestamp : when the signal was observed (UTC)
    half_life_seconds : override the default
    acceptable_threshold : decay_weight below this is "too stale to trust"
        default 0.25 = two half-lives old (~6 dB attenuation)
    now : inject for testability; defaults to UTC now

    Returns
    -------
    StalenessResult
    """
    if half_life_seconds is None:
        half_life_seconds = DEFAULT_HALF_LIFE_SECONDS.get(source)
        if half_life_seconds is None:
            raise ValueError(
                f"Unknown source '{source}' and no half_life_seconds override; "
                f"known sources: {sorted(DEFAULT_HALF_LIFE_SECONDS.keys())}"
            )
    if half_life_seconds <= 0:
        raise ValueError(f"half_life_seconds must be > 0, got {half_life_seconds}")
    if not 0 < acceptable_threshold < 1:
        raise ValueError(
            f"acceptable_threshold must be in (0, 1), got {acceptable_threshold}"
        )

    ts = _to_utc(signal_timestamp)
    n = _to_utc(now) if now is not None else _utc_now()
    age = (n - ts).total_seconds()
    if age < 0:
        # Future-dated signal (clock skew). Treat as fresh but flag.
        age = 0.0
    decay = math.pow(2.0, -age / half_life_seconds)
    return StalenessResult(
        age_seconds=age,
        half_life_seconds=half_life_seconds,
        decay_weight=decay,
        is_fresh=decay >= 0.5,
        is_acceptable=decay >= acceptable_threshold,
    )


def weighted_mean(
    values: list[float],
    weights: list[float],
) -> float:
    """Weighted mean used to combine staleness-weighted signals.

    Returns 0.0 if all weights are zero (caller should treat as "no signal").
    """
    if len(values) != len(weights):
        raise ValueError(
            f"length mismatch: {len(values)} values vs {len(weights)} weights"
        )
    if not values:
        return 0.0
    total_weight = sum(weights)
    if total_weight <= 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights)) / total_weight
