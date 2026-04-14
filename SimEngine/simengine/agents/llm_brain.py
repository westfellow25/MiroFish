"""LLM Brain — the default decision-making engine for agents.

Each round, the agent's brain receives:
- Who am I (profile + persona)
- What do I remember (memory)
- What can I do (available actions)
- What's happening (environment context)

And outputs: one Action.
"""

from __future__ import annotations

import json
from typing import Any

from simengine.core.action import Action
from simengine.core.agent import AgentProfile, AgentMemory

DECISION_SYSTEM_PROMPT = """\
You are roleplaying as a participant in a simulation.
Stay in character at all times. Your decisions should reflect your persona,
goals, and what you've observed so far.

Given the current situation, choose ONE action from the available actions
and provide your response as JSON:
{
  "action": "<action_kind>",
  "payload": { ... },
  "reasoning": "brief internal thought about why you chose this"
}

The payload depends on the action:
- "speak" -> {"message": "what you say"}
- "vote" -> {"option": "approve/reject/abstain", "reason": "why"}
- "propose" -> {"proposal": "description of your proposal"}
- "pass" -> {}
- Other actions will have their own payload structure described in context.
"""


class LLMBrain:
    """Default agent brain powered by an LLM."""

    def __init__(self, llm_client: Any, temperature: float = 0.7):
        self.llm_client = llm_client
        self.temperature = temperature

    async def decide(
        self,
        profile: AgentProfile,
        memory: AgentMemory,
        available_actions: list[str],
        context: str,
    ) -> Action:
        user_prompt = (
            f"YOUR IDENTITY:\n{profile.persona}\n\n"
            f"YOUR ROLE: {profile.role}\n"
            f"YOUR GOALS: {', '.join(profile.goals) if profile.goals else 'Act according to your persona'}\n\n"
            f"YOUR MEMORY OF RECENT EVENTS:\n{memory.summary()}\n\n"
            f"CURRENT SITUATION:\n{context}\n\n"
            f"AVAILABLE ACTIONS: {', '.join(available_actions)}\n\n"
            f"What do you do? Respond with JSON."
        )

        response = await self.llm_client.chat_json(
            system=DECISION_SYSTEM_PROMPT,
            user=user_prompt,
            temperature=self.temperature,
        )

        return Action(
            kind=response.get("action", "pass"),
            agent_id=profile.agent_id,
            payload=response.get("payload", {}),
        )
