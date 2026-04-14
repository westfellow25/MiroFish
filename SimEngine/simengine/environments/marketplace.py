"""Marketplace Environment — B2B deal-making simulation.

Use cases:
- MarketClone: test product-market fit before launch
- DealRoom: multi-party negotiation
- ChainBreaker: supply chain stress test

Interaction model:
  Agents represent companies/buyers/sellers.
  They can: pitch, request_info, make_offer, counter_offer, accept, reject, pass.
  Global state tracks: active deals, market signals, completed transactions.
"""

from __future__ import annotations

from typing import Any

from simengine.core.action import Action, ActionResult
from simengine.core.agent import Agent
from simengine.core.environment import Environment, RoundResult


class MarketplaceEnvironment(Environment):
    """A B2B marketplace where agents negotiate deals."""

    ACTIONS = [
        "pitch", "request_info", "make_offer",
        "counter_offer", "accept", "reject",
        "announce", "pass",
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(name="marketplace", config=config or {})
        self.global_state = {
            "market_context": self.config.get("market_context", ""),
            "active_deals": [],  # {"id", "seller", "buyer", "product", "offers": [...]}
            "completed_deals": [],
            "rejected_deals": [],
            "announcements": [],
            "activity_log": [],
        }

    def available_actions(self, agent: Agent) -> list[str]:
        actions = list(self.ACTIONS)
        # Can only counter/accept/reject if involved in an active deal
        agent_deals = [
            d for d in self.global_state["active_deals"]
            if d["seller"] == agent.id or d["buyer"] == agent.id
        ]
        if not agent_deals:
            for a in ("counter_offer", "accept", "reject"):
                if a in actions:
                    actions.remove(a)
        return actions

    async def execute_action(self, action: Action) -> ActionResult:
        handler = {
            "pitch": self._handle_pitch,
            "request_info": self._handle_request_info,
            "make_offer": self._handle_make_offer,
            "counter_offer": self._handle_counter_offer,
            "accept": self._handle_accept,
            "reject": self._handle_reject,
            "announce": self._handle_announce,
            "pass": self._handle_pass,
        }.get(action.kind, self._handle_pass)

        return await handler(action)

    def get_context_for_agent(self, agent: Agent) -> str:
        state = self.global_state
        market_ctx = state["market_context"]

        # This agent's active deals
        my_deals = [
            d for d in state["active_deals"]
            if d["seller"] == agent.id or d["buyer"] == agent.id
        ]
        deals_text = ""
        if my_deals:
            lines = []
            for d in my_deals:
                other = d["buyer"] if d["seller"] == agent.id else d["seller"]
                last_offer = d["offers"][-1] if d["offers"] else "no offers yet"
                lines.append(f"  Deal {d['id']} with {other}: {d['product']} — {last_offer}")
            deals_text = "\n".join(lines)
        else:
            deals_text = "  (no active deals)"

        # Public announcements and recent activity
        recent = state["activity_log"][-10:]
        activity_text = "\n".join(recent) if recent else "(quiet market)"

        participants = ", ".join(
            f"{a.profile.name} ({a.profile.role})" for a in self.agents.values()
        )

        return (
            f"MARKETPLACE — Round {self.round_number}\n"
            f"Market: {market_ctx}\n"
            f"Players: {participants}\n\n"
            f"YOUR ACTIVE DEALS:\n{deals_text}\n\n"
            f"MARKET ACTIVITY:\n{activity_text}\n\n"
            f"You are {agent.profile.name} ({agent.profile.role}). "
            f"What's your next move?"
        )

    # --- Handlers ---

    async def _handle_pitch(self, action: Action) -> ActionResult:
        msg = action.payload.get("message", "")
        product = action.payload.get("product", "")
        entry = f"{action.agent_id} PITCHES: {product} — {msg}"
        self.global_state["activity_log"].append(entry)
        return ActionResult(action=action, success=True, outcome={"pitched": product})

    async def _handle_request_info(self, action: Action) -> ActionResult:
        target = action.payload.get("target", "")
        question = action.payload.get("message", "")
        entry = f"{action.agent_id} asks {target}: {question}"
        self.global_state["activity_log"].append(entry)
        return ActionResult(action=action, success=True, outcome={"asked": target})

    async def _handle_make_offer(self, action: Action) -> ActionResult:
        target = action.payload.get("target", "")
        product = action.payload.get("product", "")
        terms = action.payload.get("terms", {})
        deal_id = f"D{len(self.global_state['active_deals']) + 1}"
        deal = {
            "id": deal_id,
            "seller": action.agent_id,
            "buyer": target,
            "product": product,
            "offers": [{"from": action.agent_id, "terms": terms}],
        }
        self.global_state["active_deals"].append(deal)
        entry = f"{action.agent_id} OFFERS {product} to {target}: {terms}"
        self.global_state["activity_log"].append(entry)
        return ActionResult(
            action=action, success=True, outcome={"deal_id": deal_id},
            visible_to=[action.agent_id, target],
        )

    async def _handle_counter_offer(self, action: Action) -> ActionResult:
        deal_id = action.payload.get("deal_id", "")
        terms = action.payload.get("terms", {})
        for deal in self.global_state["active_deals"]:
            if deal["id"] == deal_id:
                deal["offers"].append({"from": action.agent_id, "terms": terms})
                entry = f"{action.agent_id} COUNTERS on {deal_id}: {terms}"
                self.global_state["activity_log"].append(entry)
                return ActionResult(
                    action=action, success=True, outcome={"deal_id": deal_id},
                    visible_to=[deal["seller"], deal["buyer"]],
                )
        return ActionResult(action=action, success=False, outcome={"error": "deal not found"})

    async def _handle_accept(self, action: Action) -> ActionResult:
        deal_id = action.payload.get("deal_id", "")
        for deal in self.global_state["active_deals"]:
            if deal["id"] == deal_id:
                self.global_state["active_deals"].remove(deal)
                self.global_state["completed_deals"].append(deal)
                entry = f"DEAL CLOSED: {deal_id} — {deal['product']} ({deal['seller']} -> {deal['buyer']})"
                self.global_state["activity_log"].append(entry)
                return ActionResult(action=action, success=True, outcome={"closed": deal_id})
        return ActionResult(action=action, success=False, outcome={"error": "deal not found"})

    async def _handle_reject(self, action: Action) -> ActionResult:
        deal_id = action.payload.get("deal_id", "")
        reason = action.payload.get("reason", "")
        for deal in self.global_state["active_deals"]:
            if deal["id"] == deal_id:
                self.global_state["active_deals"].remove(deal)
                deal["rejection_reason"] = reason
                self.global_state["rejected_deals"].append(deal)
                entry = f"DEAL REJECTED: {deal_id} by {action.agent_id}: {reason}"
                self.global_state["activity_log"].append(entry)
                return ActionResult(action=action, success=True, outcome={"rejected": deal_id})
        return ActionResult(action=action, success=False, outcome={"error": "deal not found"})

    async def _handle_announce(self, action: Action) -> ActionResult:
        msg = action.payload.get("message", "")
        entry = f"{action.agent_id} ANNOUNCES: {msg}"
        self.global_state["announcements"].append(entry)
        self.global_state["activity_log"].append(entry)
        return ActionResult(action=action, success=True, outcome={"announced": msg})

    async def _handle_pass(self, action: Action) -> ActionResult:
        return ActionResult(action=action, success=True, outcome={"skipped": True})
