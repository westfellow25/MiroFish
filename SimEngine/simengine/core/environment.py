"""Environment — the world where agents interact.

This is the KEY abstraction that replaces OASIS's hardcoded Twitter/Reddit.
MiroFish can only simulate social media. SimEngine can simulate anything.

Each Environment defines:
- What actions are possible (speak, vote, trade, propose, etc.)
- What happens when an action is executed (rules of the world)
- What context agents see (information topology)
- When a round ends and what the global state looks like
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from simengine.core.action import Action, ActionResult
from simengine.core.agent import Agent


@dataclass
class RoundResult:
    """Summary of what happened in one simulation round."""

    round_number: int
    actions_taken: list[ActionResult] = field(default_factory=list)
    global_state: dict[str, Any] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)  # notable events for the log


class Environment(ABC):
    """Abstract simulation environment.

    Subclass this to create new worlds:
    - Boardroom: agents discuss and vote on proposals
    - Marketplace: agents negotiate B2B deals
    - Organization: agents work in a hierarchy
    - City: agents live, commute, consume
    """

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        self.name = name
        self.config = config or {}
        self.agents: dict[str, Agent] = {}
        self.round_number: int = 0
        self.history: list[RoundResult] = []
        self.global_state: dict[str, Any] = {}

    # --- Setup ---

    def add_agent(self, agent: Agent) -> None:
        self.agents[agent.id] = agent

    def add_agents(self, agents: list[Agent]) -> None:
        for agent in agents:
            self.add_agent(agent)

    # --- Core interface (implement these) ---

    @abstractmethod
    def available_actions(self, agent: Agent) -> list[str]:
        """What can this agent do right now?

        May vary per agent (CEO can approve, intern cannot)
        and per state (can't vote if no proposal is on the table).
        """
        ...

    @abstractmethod
    async def execute_action(self, action: Action) -> ActionResult:
        """Apply the action to the world and return what happened.

        This is where the rules of your world live:
        - Boardroom: "speak" adds to discussion, "vote" updates tally
        - Marketplace: "propose_deal" creates offer, "accept" closes deal
        """
        ...

    @abstractmethod
    def get_context_for_agent(self, agent: Agent) -> str:
        """What does this agent currently see/know?

        Controls information asymmetry:
        - Public: everyone sees everything
        - Private: each agent sees only their part
        - Hierarchical: managers see more than reports
        """
        ...

    # --- Optional hooks (override as needed) ---

    async def on_round_start(self, round_number: int) -> None:
        """Inject events, change global state, trigger time-based effects."""
        pass

    async def on_round_end(self, round_result: RoundResult) -> None:
        """Post-round processing: update state, check termination conditions."""
        pass

    def is_finished(self) -> bool:
        """Should the simulation stop? Override for custom termination."""
        max_rounds = self.config.get("max_rounds", 10)
        return self.round_number >= max_rounds

    # --- Simulation loop ---

    async def run_round(self) -> RoundResult:
        """Execute one round of the simulation."""
        self.round_number += 1
        await self.on_round_start(self.round_number)

        round_result = RoundResult(round_number=self.round_number)

        # Determine agent order for this round
        active_agents = self._get_active_agents()

        for agent in active_agents:
            actions = self.available_actions(agent)
            if not actions:
                continue

            context = self.get_context_for_agent(agent)
            action = await agent.act(actions, context)
            result = await self.execute_action(action)
            round_result.actions_taken.append(result)

            # Broadcast result to agents who can see it
            for other in self.agents.values():
                other.observe(result)

        round_result.global_state = dict(self.global_state)
        await self.on_round_end(round_result)
        self.history.append(round_result)
        return round_result

    def _get_active_agents(self) -> list[Agent]:
        """Which agents act this round? Override for custom scheduling."""
        return list(self.agents.values())
