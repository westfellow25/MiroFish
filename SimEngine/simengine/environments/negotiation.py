"""Negotiation Environment — 1-on-1 structured bargaining.

Use cases:
- Salary negotiation simulation
- Vendor contract talks
- M&A term-sheet discussions
- Hostage negotiation training

Interaction model:
  Exactly two parties take turns. Each turn: offer, concede, walk_away, accept.
  Global state tracks: current bid, best alternative, deal terms.
"""

from __future__ import annotations

from typing import Any

from simengine.core.action import Action, ActionResult
from simengine.core.agent import Agent
from simengine.core.environment import Environment, RoundResult


class NegotiationEnvironment(Environment):
    """Two parties taking turns until deal, walkaway, or stalemate."""

    ACTIONS = ["offer", "concede", "ask_info", "share_info", "accept", "walk_away", "pass"]

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(name="negotiation", config=config or {})
        self.global_state = {
            "subject": self.config.get("subject", "an agreement"),
            "current_offers": {},  # agent_id -> {"terms": {...}, "round": N}
            "last_mover": None,
            "deal_closed": None,  # {"by": id, "terms": {...}, "round": N}
            "walk_away_by": None,
            "transcript": [],
        }

    def available_actions(self, agent: Agent) -> list[str]:
        # Deal closed or broken down -> no actions
        if self.global_state["deal_closed"] or self.global_state["walk_away_by"]:
            return ["pass"]

        actions = list(self.ACTIONS)
        # Can only accept if counterparty made an offer
        counterpart_offer = self._get_counterpart_offer(agent.id)
        if counterpart_offer is None:
            if "accept" in actions:
                actions.remove("accept")
        return actions

    async def execute_action(self, action: Action) -> ActionResult:
        handler = {
            "offer": self._handle_offer,
            "concede": self._handle_concede,
            "ask_info": self._handle_ask_info,
            "share_info": self._handle_share_info,
            "accept": self._handle_accept,
            "walk_away": self._handle_walk_away,
            "pass": self._handle_pass,
        }.get(action.kind, self._handle_pass)
        return await handler(action)

    def get_context_for_agent(self, agent: Agent) -> str:
        state = self.global_state
        counterpart = self._get_counterpart(agent.id)
        counterpart_name = self.agents[counterpart].profile.name if counterpart else "counterparty"

        my_offer = state["current_offers"].get(agent.id)
        their_offer = state["current_offers"].get(counterpart)

        offers_text = ""
        if my_offer:
            offers_text += f"Your last offer: {my_offer['terms']} (round {my_offer['round']})\n"
        else:
            offers_text += "You haven't made an offer yet\n"

        if their_offer:
            offers_text += f"Their last offer: {their_offer['terms']} (round {their_offer['round']})\n"
        else:
            offers_text += f"{counterpart_name} hasn't made an offer yet\n"

        transcript = state["transcript"][-10:]
        transcript_text = "\n".join(transcript) if transcript else "(nothing said yet)"

        return (
            f"NEGOTIATION — Round {self.round_number}\n"
            f"Subject: {state['subject']}\n"
            f"You are {agent.profile.name} ({agent.profile.role})\n"
            f"Counterparty: {counterpart_name}\n\n"
            f"CURRENT OFFERS:\n{offers_text}\n"
            f"RECENT TRANSCRIPT:\n{transcript_text}\n\n"
            f"What's your move?"
        )

    def is_finished(self) -> bool:
        if self.global_state["deal_closed"] or self.global_state["walk_away_by"]:
            return True
        return super().is_finished()

    def _get_counterpart(self, agent_id: str) -> str | None:
        others = [aid for aid in self.agents if aid != agent_id]
        return others[0] if others else None

    def _get_counterpart_offer(self, agent_id: str) -> dict | None:
        counterpart = self._get_counterpart(agent_id)
        if not counterpart:
            return None
        return self.global_state["current_offers"].get(counterpart)

    async def _handle_offer(self, action: Action) -> ActionResult:
        terms = action.payload.get("terms", {})
        self.global_state["current_offers"][action.agent_id] = {
            "terms": terms,
            "round": self.round_number,
        }
        self.global_state["last_mover"] = action.agent_id
        entry = f"{action.agent_id} OFFERS: {terms}"
        self.global_state["transcript"].append(entry)
        return ActionResult(action=action, success=True, outcome={"offered": terms})

    async def _handle_concede(self, action: Action) -> ActionResult:
        concession = action.payload.get("concession", "")
        entry = f"{action.agent_id} CONCEDES: {concession}"
        self.global_state["transcript"].append(entry)
        return ActionResult(action=action, success=True, outcome={"concession": concession})

    async def _handle_ask_info(self, action: Action) -> ActionResult:
        question = action.payload.get("message", "")
        entry = f"{action.agent_id} asks: {question}"
        self.global_state["transcript"].append(entry)
        return ActionResult(action=action, success=True, outcome={"asked": question})

    async def _handle_share_info(self, action: Action) -> ActionResult:
        info = action.payload.get("message", "")
        entry = f"{action.agent_id} shares: {info}"
        self.global_state["transcript"].append(entry)
        return ActionResult(action=action, success=True, outcome={"shared": info})

    async def _handle_accept(self, action: Action) -> ActionResult:
        counterpart = self._get_counterpart(action.agent_id)
        their_offer = self.global_state["current_offers"].get(counterpart) if counterpart else None
        if not their_offer:
            return ActionResult(action=action, success=False, outcome={"error": "no offer to accept"})
        self.global_state["deal_closed"] = {
            "by": action.agent_id,
            "terms": their_offer["terms"],
            "round": self.round_number,
        }
        entry = f"{action.agent_id} ACCEPTS: {their_offer['terms']} — DEAL CLOSED"
        self.global_state["transcript"].append(entry)
        return ActionResult(action=action, success=True, outcome={"closed": their_offer["terms"]})

    async def _handle_walk_away(self, action: Action) -> ActionResult:
        reason = action.payload.get("reason", "")
        self.global_state["walk_away_by"] = action.agent_id
        entry = f"{action.agent_id} WALKS AWAY: {reason}"
        self.global_state["transcript"].append(entry)
        return ActionResult(action=action, success=True, outcome={"walked_away": reason})

    async def _handle_pass(self, action: Action) -> ActionResult:
        return ActionResult(action=action, success=True, outcome={"skipped": True})
