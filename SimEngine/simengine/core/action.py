"""Actions — the universal vocabulary of agent behavior.

MiroFish hardcodes actions as platform-specific enums (CREATE_POST, LIKE, REPOST).
SimEngine makes actions declarative: each Environment defines what actions are
possible, and agents choose from that set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Action:
    """A single action an agent wants to perform.

    Unlike MiroFish's ActionType enum, this is a generic container.
    The Environment validates and executes it.
    """

    kind: str  # e.g. "speak", "vote", "propose_deal", "object", "pass"
    agent_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    # payload carries action-specific data:
    #   speak  -> {"message": "I disagree with the valuation"}
    #   vote   -> {"option": "approve", "reason": "..."}
    #   propose_deal -> {"terms": {...}, "target_agent": "cfo_acme"}


@dataclass
class ActionResult:
    """What happened after the action was executed by the Environment."""

    action: Action
    success: bool
    outcome: dict[str, Any] = field(default_factory=dict)
    # outcome examples:
    #   speak  -> {"heard_by": ["agent_2", "agent_3"], "reactions": [...]}
    #   vote   -> {"recorded": True, "current_tally": {"approve": 3, "reject": 1}}
    visible_to: list[str] = field(default_factory=list)
    # which agents can see this result (for information asymmetry)
