"""Structured Reflexion JSON — Phase 1 #3.

Reference
---------
Shinn, N., Cassano, F., Berman, E., Gopinath, A., Narasimhan, K., & Yao, S.
(2023). *Reflexion: Language agents with verbal reinforcement learning*.
NeurIPS 2023. arXiv:2303.11366.

Why this exists
---------------
The capstone has a daily-retro loop where the agent reads what went
wrong yesterday and adjusts behavior today. In the Week 1-3 prototype
this loop produces *free-form text* that is hard to query and easy to
drift. This module pins it down: every losing decision produces a
strict JSON envelope with three named slots:

    {
      "cause":          one-line root cause hypothesis
      "lesson":         transferable rule extracted from the cause
      "forward_prompt": text to be injected into tomorrow's prompt context
    }

Why three slots, not one big "reflection" blob? Because we want to
*aggregate* lessons over time (cluster by topic, count recurrences)
and we want to *audit* forward_prompts (every line injected into a
production prompt must trace back to a logged reflection). Free-form
text resists both. The JSON schema is the audit primitive.

The injection contract: at the start of each daily prediction run,
the agent loads the last N (default 14) reflection JSON entries,
concatenates `forward_prompt` lines into a "Recent lessons" block,
and prepends that block to its system prompt. Cause and lesson stay
in the audit log but are not re-injected verbatim (they're
post-hoc analysis fodder for the capstone thesis).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


Severity = Literal["info", "warn", "lesson_extracted", "rule_change"]


@dataclass
class Reflexion:
    """One structured reflection entry."""

    timestamp: str                              # ISO-8601 UTC
    ticker: str
    decision: str                               # BUY / SELL / WAIT
    forecast_p: float
    actual: float
    brier: float
    cause: str                                  # ≤ 200 chars; one-line root cause
    lesson: str                                 # ≤ 240 chars; transferable rule
    forward_prompt: str                         # ≤ 240 chars; injected verbatim into next prompt
    severity: Severity = "lesson_extracted"
    tags: list[str] = None                      # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.tags is None:
            object.__setattr__(self, "tags", [])
        for attr, cap in [("cause", 200), ("lesson", 240), ("forward_prompt", 240)]:
            v = getattr(self, attr)
            if len(v) > cap:
                raise ValueError(
                    f"{attr} too long ({len(v)} > {cap}); "
                    "Reflexion slots are intentionally short to force compression"
                )
        if not 0 <= self.forecast_p <= 1:
            raise ValueError(f"forecast_p must be in [0, 1], got {self.forecast_p}")
        if self.actual not in (0.0, 1.0):
            raise ValueError(f"actual must be 0 or 1, got {self.actual}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def from_brier_result(
    brier_row: dict,
    cause: str,
    lesson: str,
    forward_prompt: str,
    *,
    severity: Severity = "lesson_extracted",
    tags: list[str] | None = None,
) -> Reflexion:
    """Build a Reflexion from a brier_audit.brier_for_decision() result.

    The brier_row contract is the same as in scripts/ece_audit.py: a dict
    with keys 'ticker', 'forecast_p', 'actual', 'brier', 'timestamp',
    'decision'.
    """
    return Reflexion(
        timestamp=_now_iso(),
        ticker=brier_row["ticker"],
        decision=brier_row.get("decision", "?"),
        forecast_p=float(brier_row["forecast_p"]),
        actual=float(brier_row["actual"]),
        brier=float(brier_row["brier"]),
        cause=cause,
        lesson=lesson,
        forward_prompt=forward_prompt,
        severity=severity,
        tags=list(tags) if tags else [],
    )


def to_json(r: Reflexion) -> str:
    return json.dumps(asdict(r), ensure_ascii=False, sort_keys=True)


def from_json(s: str) -> Reflexion:
    d = json.loads(s)
    return Reflexion(**d)


def append_jsonl(r: Reflexion, path: Path) -> None:
    """Append one Reflexion as a JSONL line. Creates parent dir if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(to_json(r) + "\n")


def load_jsonl(path: Path) -> list[Reflexion]:
    """Load all Reflexions from a JSONL file. Returns empty list if missing."""
    if not path.exists():
        return []
    out: list[Reflexion] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(from_json(line))
    return out


def build_forward_context(
    reflexions: list[Reflexion],
    *,
    n: int = 14,
    header: str = "Recent lessons (newest first):",
) -> str:
    """Build the prompt-injection block from the most recent N reflections.

    Returns an empty string when there is nothing to inject (no leading
    newlines, no header). Latest reflections are listed first so the
    LLM's recency bias surfaces the most current lessons.
    """
    if not reflexions:
        return ""
    recent = sorted(reflexions, key=lambda r: r.timestamp, reverse=True)[:n]
    if not recent:
        return ""
    bullets = [f"- {r.forward_prompt}" for r in recent if r.forward_prompt.strip()]
    if not bullets:
        return ""
    return header + "\n" + "\n".join(bullets)
