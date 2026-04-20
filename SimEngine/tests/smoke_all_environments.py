"""Smoke test — validates ALL environments work end-to-end with mock brain.

Run: python -m tests.smoke_all_environments
"""

from __future__ import annotations

import asyncio
import random

from simengine.core.agent import Agent, AgentProfile, AgentMemory
from simengine.core.action import Action
from simengine.core.engine import SimulationEngine
from simengine.environments.boardroom import BoardroomEnvironment
from simengine.environments.marketplace import MarketplaceEnvironment
from simengine.environments.negotiation import NegotiationEnvironment
from simengine.environments.organization import OrganizationEnvironment


class MockBrain:
    """Picks actions cycling through the available list with small variation."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.counter = 0

    async def decide(self, profile, memory, available_actions, context):
        self.counter += 1

        # Pick a deterministic-ish action based on counter
        if not available_actions:
            return Action(kind="pass", agent_id=profile.agent_id)

        # Prefer "productive" actions over pass
        productive = [a for a in available_actions if a != "pass"]
        choices = productive or available_actions
        kind = choices[self.counter % len(choices)]

        # Payload tailored per action kind (with realistic defaults)
        payload: dict = {}
        if kind in ("speak", "question", "announce", "ask_info", "share_info", "request_help", "report_issue"):
            payload = {"message": f"[Mock] {profile.name} says something ({kind})."}
        elif kind == "propose":
            payload = {"proposal": f"[Mock] Proposal by {profile.name}"}
        elif kind == "support":
            payload = {"proposal_id": "P1"}
        elif kind == "object":
            payload = {"proposal_id": "P1", "reason": "too risky"}
        elif kind == "vote":
            payload = {
                "proposal_id": "P1",
                "option": self.rng.choice(["approve", "reject", "abstain"]),
                "reason": "(mock)",
            }
        elif kind == "pitch":
            payload = {"product": "Mock product", "message": "Pitch text"}
        elif kind == "make_offer":
            payload = {"target": "other_agent", "product": "Mock product", "terms": {"price": 100}}
        elif kind == "counter_offer":
            payload = {"deal_id": "D1", "terms": {"price": 90}}
        elif kind == "accept":
            payload = {"deal_id": "D1"}
        elif kind == "reject":
            payload = {"deal_id": "D1", "reason": "too expensive"}
        elif kind == "offer":
            payload = {"terms": {"price": 100, "delivery": "2 weeks"}}
        elif kind == "concede":
            payload = {"concession": "flexible on timeline"}
        elif kind == "walk_away":
            payload = {"reason": "unacceptable terms"}
        elif kind == "assign_task":
            payload = {"assignee": "other_agent", "description": "Do the thing"}
        elif kind == "escalate":
            payload = {"target": "boss", "message": "blocker issue"}
        elif kind == "deliver":
            payload = {"task_id": "T1"}
        elif kind == "socialize":
            payload = {"target": "other_agent", "message": "coffee?"}

        return Action(kind=kind, agent_id=profile.agent_id, payload=payload)


def make_agents(n: int = 3, roles: list[str] | None = None) -> list[Agent]:
    brain = MockBrain()
    roles = roles or ["CEO", "CFO", "Member"]
    return [
        Agent(
            profile=AgentProfile(
                agent_id=f"agent_{i}",
                name=f"Agent{i}",
                role=roles[i % len(roles)],
                persona=f"Mock persona {i}",
            ),
            memory=AgentMemory(),
            brain=brain,
        )
        for i in range(n)
    ]


async def run_environment(name: str, env, agents):
    print(f"\n{'=' * 60}")
    print(f"Testing: {name}")
    print("=" * 60)
    engine = SimulationEngine()
    result = await engine.run(env, agents)
    print(f"  rounds: {len(result.rounds)}")
    print(f"  total actions: {result.metadata['total_actions']}")
    assert len(result.rounds) > 0
    assert result.metadata["total_actions"] > 0
    print(f"  OK")
    return result


async def main():
    # Boardroom
    await run_environment(
        "BoardroomEnvironment",
        BoardroomEnvironment(config={"agenda": ["Topic A"], "max_rounds": 3}),
        make_agents(3, ["CEO", "CFO", "Investor"]),
    )

    # Marketplace
    await run_environment(
        "MarketplaceEnvironment",
        MarketplaceEnvironment(config={"market_context": "Mock market", "max_rounds": 3}),
        make_agents(3, ["Seller", "Buyer", "Buyer"]),
    )

    # Negotiation (2 agents only)
    await run_environment(
        "NegotiationEnvironment",
        NegotiationEnvironment(config={"subject": "contract", "max_rounds": 4}),
        make_agents(2, ["Seller", "Buyer"]),
    )

    # Organization
    await run_environment(
        "OrganizationEnvironment",
        OrganizationEnvironment(config={"company_context": "Mock Inc", "max_rounds": 3}),
        make_agents(3, ["Manager", "IC", "IC"]),
    )

    print(f"\n\u2705 ALL ENVIRONMENTS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
