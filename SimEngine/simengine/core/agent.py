"""Agent — an autonomous participant in the simulation.

MiroFish agents are OASIS social-media users with follower_count and karma.
SimEngine agents are domain-agnostic: their profile, goals, and behavior
are defined by the Environment they operate in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from simengine.core.action import Action, ActionResult


@dataclass
class AgentProfile:
    """Everything that defines who the agent is.

    This replaces MiroFish's OasisAgentProfile which was locked to
    Twitter (follower_count, statuses_count) and Reddit (karma).
    """

    agent_id: str
    name: str
    role: str  # "CFO", "journalist", "voter", "competitor_ceo"
    persona: str  # detailed persona prompt for the LLM
    goals: list[str] = field(default_factory=list)
    traits: dict[str, Any] = field(default_factory=dict)
    # traits are domain-specific:
    #   boardroom -> {"risk_tolerance": 0.8, "loyalty": "shareholders"}
    #   marketplace -> {"budget": 500000, "pain_points": ["latency", "cost"]}
    #   negotiation -> {"walk_away_price": 1000000, "style": "aggressive"}
    relationships: dict[str, str] = field(default_factory=dict)
    # agent_id -> relationship type: {"agent_2": "reports_to", "agent_5": "competes_with"}


@dataclass
class AgentMemory:
    """What the agent remembers from the simulation so far."""

    observations: list[ActionResult] = field(default_factory=list)
    internal_state: dict[str, Any] = field(default_factory=dict)
    # internal_state tracks things like:
    #   "mood": "frustrated", "trust_level": {"agent_3": 0.2}

    def add_observation(self, result: ActionResult) -> None:
        self.observations.append(result)

    def recent(self, n: int = 10) -> list[ActionResult]:
        return self.observations[-n:]

    def summary(self) -> str:
        """Condense memory into a text block for the LLM context."""
        lines = []
        for obs in self.recent(20):
            agent = obs.action.agent_id
            kind = obs.action.kind
            payload_summary = obs.action.payload.get("message", str(obs.action.payload))
            lines.append(f"[{agent}] {kind}: {payload_summary}")
        state_str = ", ".join(f"{k}={v}" for k, v in self.internal_state.items())
        if state_str:
            lines.insert(0, f"Your current state: {state_str}")
        return "\n".join(lines)


class AgentBrain(Protocol):
    """How the agent decides what to do next.

    Default implementation uses LLM. But you can swap in rule-based,
    random, or hybrid brains.
    """

    async def decide(
        self,
        profile: AgentProfile,
        memory: AgentMemory,
        available_actions: list[str],
        context: str,
    ) -> Action: ...


@dataclass
class Agent:
    """A simulation participant: profile + memory + brain."""

    profile: AgentProfile
    memory: AgentMemory = field(default_factory=AgentMemory)
    brain: AgentBrain | None = None

    @property
    def id(self) -> str:
        return self.profile.agent_id

    async def act(self, available_actions: list[str], context: str) -> Action:
        if self.brain is None:
            raise RuntimeError(f"Agent {self.id} has no brain assigned")
        return await self.brain.decide(
            self.profile, self.memory, available_actions, context
        )

    def observe(self, result: ActionResult) -> None:
        if result.visible_to and self.id not in result.visible_to:
            return
        self.memory.add_observation(result)
