"""PR-gated self-modification — Phase 1 #6 — Brier-improvement merge rule.

Reference
---------
Sakana AI (2025). *The Darwin-Gödel Machine: Self-modifying agents through
open-ended search.* https://sakana.ai/dgm

Why this exists
---------------
The Darwin-Gödel Machine describes agents that iteratively rewrite their
own code/prompts under an open-ended search process. That is *exactly*
the capstone's daily-retro loop, but with one deliberate constraint:
the capstone refuses to let the agent merge its own self-edits without
a human-in-the-loop gate AND a measurable Brier improvement on a
held-out fold.

This module encodes that gate as a callable contract:

    merge_decision(proposal) -> MergeDecision

Where `proposal` describes a proposed change (prompt edit, indicator
threshold tweak, voice roster update) and the result is one of:

- APPROVE: held-out Brier improves by ≥ min_improvement AND human
  approval flag set
- BLOCK_NO_BRIER_GAIN: held-out Brier does not improve enough
- BLOCK_NO_HUMAN_APPROVAL: human approval flag not set
- BLOCK_INSUFFICIENT_DATA: too few held-out predictions to claim
  improvement (default n < 30)

This is the structural difference between the capstone and the
Darwin-Gödel paper: the capstone agent is *structurally incapable*
of autonomous, unreviewed change. The gate is the moat.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class MergeStatus(str, Enum):
    APPROVE = "approve"
    BLOCK_NO_BRIER_GAIN = "block_no_brier_gain"
    BLOCK_NO_HUMAN_APPROVAL = "block_no_human_approval"
    BLOCK_INSUFFICIENT_DATA = "block_insufficient_data"


ChangeKind = Literal[
    "prompt_edit",
    "indicator_threshold",
    "voice_roster",
    "risk_control",
    "tool_schema",
]


@dataclass(frozen=True)
class MergeProposal:
    """A proposed self-modification."""

    proposal_id: str                            # short identifier (e.g. "2026-06-17-prompt-edit-a1")
    kind: ChangeKind
    description: str                            # ≤ 240 chars; one-line rationale
    baseline_brier: float                       # current production held-out Brier
    candidate_brier: float                      # proposed-change held-out Brier
    held_out_n: int                             # number of predictions in the held-out fold
    human_approved: bool                        # set externally by Alex


@dataclass(frozen=True)
class MergeDecision:
    status: MergeStatus
    proposal_id: str
    brier_delta: float                          # baseline - candidate (positive = improvement)
    reason: str                                 # plain English summary for the audit log


def evaluate(
    proposal: MergeProposal,
    *,
    min_improvement: float = 0.005,
    min_held_out_n: int = 30,
) -> MergeDecision:
    """Evaluate a self-modification proposal against the merge gate.

    Defaults:
    - min_improvement = 0.005 (half a Brier point on a 4-decimal scale)
    - min_held_out_n = 30 (Brier is noisy on smaller samples)

    Both defaults are intentionally tighter than the Sakana paper's
    open-ended search — the capstone constrains the search space and
    insists on statistical room to actually detect the gain.
    """
    if not 0 < min_improvement < 1:
        raise ValueError(
            f"min_improvement must be in (0, 1), got {min_improvement}"
        )
    if min_held_out_n < 1:
        raise ValueError(f"min_held_out_n must be ≥ 1, got {min_held_out_n}")

    delta = proposal.baseline_brier - proposal.candidate_brier

    if proposal.held_out_n < min_held_out_n:
        return MergeDecision(
            status=MergeStatus.BLOCK_INSUFFICIENT_DATA,
            proposal_id=proposal.proposal_id,
            brier_delta=delta,
            reason=(
                f"Held-out fold too small ({proposal.held_out_n} < "
                f"{min_held_out_n}); cannot claim improvement"
            ),
        )

    if delta < min_improvement:
        return MergeDecision(
            status=MergeStatus.BLOCK_NO_BRIER_GAIN,
            proposal_id=proposal.proposal_id,
            brier_delta=delta,
            reason=(
                f"Brier improvement {delta:+.4f} below threshold "
                f"{min_improvement:+.4f}"
            ),
        )

    if not proposal.human_approved:
        return MergeDecision(
            status=MergeStatus.BLOCK_NO_HUMAN_APPROVAL,
            proposal_id=proposal.proposal_id,
            brier_delta=delta,
            reason=(
                f"Brier improvement {delta:+.4f} sufficient but human "
                "approval flag not set; proposal awaits HITL review"
            ),
        )

    return MergeDecision(
        status=MergeStatus.APPROVE,
        proposal_id=proposal.proposal_id,
        brier_delta=delta,
        reason=(
            f"Brier improvement {delta:+.4f} ≥ {min_improvement:+.4f} "
            "and human approval present"
        ),
    )
