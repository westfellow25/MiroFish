"""Smoke test — runs a full simulation with a mock brain (no LLM required).

This proves the engine actually works end-to-end.
Run: python -m tests.smoke_boardroom
"""

from __future__ import annotations

import asyncio
import random

from simengine.core.agent import Agent, AgentProfile, AgentMemory
from simengine.core.action import Action
from simengine.core.engine import SimulationEngine
from simengine.environments.boardroom import BoardroomEnvironment


class MockBrain:
    """Deterministic brain for testing — picks actions based on role."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.proposal_counter = 0

    async def decide(self, profile, memory, available_actions, context):
        # CEO proposes things, others speak/vote
        if "ceo" in profile.role.lower() and "propose" in available_actions and self.proposal_counter < 2:
            self.proposal_counter += 1
            return Action(
                kind="propose",
                agent_id=profile.agent_id,
                payload={"proposal": f"[Mock] Proposal #{self.proposal_counter} from {profile.name}"},
            )

        if "vote" in available_actions and self.rng.random() < 0.3:
            # Vote on the latest proposal (agents can see it in context)
            return Action(
                kind="vote",
                agent_id=profile.agent_id,
                payload={
                    "proposal_id": f"P{self.proposal_counter}",
                    "option": self.rng.choice(["approve", "reject", "abstain"]),
                    "reason": "(mock reasoning)",
                },
            )

        # Default: speak
        return Action(
            kind="speak",
            agent_id=profile.agent_id,
            payload={"message": f"[Mock] {profile.name} comments on topic (round state)."},
        )


def make_agents() -> list[Agent]:
    brain = MockBrain()
    profiles = [
        AgentProfile(agent_id="ceo_1", name="Sarah", role="CEO", persona="Visionary"),
        AgentProfile(agent_id="cfo_1", name="James", role="CFO", persona="Conservative"),
        AgentProfile(agent_id="inv_1", name="Mike", role="Investor", persona="Aggressive"),
    ]
    return [Agent(profile=p, memory=AgentMemory(), brain=brain) for p in profiles]


async def main():
    print("SMOKE TEST — Boardroom with mock brain")
    print("=" * 60)

    env = BoardroomEnvironment(config={
        "agenda": ["Discuss Q4 strategy", "Vote on pivot"],
        "max_rounds": 5,
        "rounds_per_topic": 3,
    })
    agents = make_agents()
    engine = SimulationEngine()

    result = await engine.run(env, agents)

    print(f"\nCompleted {len(result.rounds)} rounds")
    print(f"Total actions: {result.metadata['total_actions']}")
    print(f"Final proposals: {len(result.final_state.get('proposals', []))}")
    print(f"Discussion entries: {len(result.final_state.get('discussion_log', []))}")

    print("\n--- DISCUSSION LOG ---")
    for entry in result.final_state.get("discussion_log", []):
        print(f"  {entry}")

    print("\n--- VOTE TALLIES ---")
    for pid, tally in result.final_state.get("votes", {}).items():
        print(f"  {pid}: {tally}")

    # Sanity assertions
    assert len(result.rounds) == 5, f"Expected 5 rounds, got {len(result.rounds)}"
    assert result.metadata["total_actions"] > 0, "No actions were taken"
    assert len(result.final_state.get("proposals", [])) > 0, "No proposals made"

    print("\n\u2705 SMOKE TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())
