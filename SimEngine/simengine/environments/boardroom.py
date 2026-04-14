"""Boardroom Environment — structured discussion with proposals and votes.

Use cases:
- BoardSim: digital board of directors evaluating strategy
- DealRoom: B2B negotiation between buyer and seller teams
- PolicyLab: committee debating a new regulation

Interaction model:
  Rounds = agenda items or discussion phases.
  Agents can: speak, propose, support, object, vote, pass.
  Global state tracks: current topic, proposals on table, vote tallies.
"""

from __future__ import annotations

from typing import Any

from simengine.core.action import Action, ActionResult
from simengine.core.agent import Agent
from simengine.core.environment import Environment, RoundResult


class BoardroomEnvironment(Environment):
    """A meeting room where agents discuss topics and make decisions."""

    ACTIONS = ["speak", "propose", "support", "object", "vote", "question", "pass"]

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(name="boardroom", config=config or {})
        self.global_state = {
            "agenda": self.config.get("agenda", ["General discussion"]),
            "current_topic_index": 0,
            "proposals": [],  # {"id", "author", "text", "supporters", "objectors"}
            "votes": {},  # proposal_id -> {"approve": [], "reject": [], "abstain": []}
            "discussion_log": [],
            "decisions": [],
        }

    def available_actions(self, agent: Agent) -> list[str]:
        actions = list(self.ACTIONS)
        # Can only vote if there's an active proposal
        if not self.global_state["proposals"]:
            actions.remove("vote")
        return actions

    async def execute_action(self, action: Action) -> ActionResult:
        handler = {
            "speak": self._handle_speak,
            "propose": self._handle_propose,
            "support": self._handle_support,
            "object": self._handle_object,
            "vote": self._handle_vote,
            "question": self._handle_question,
            "pass": self._handle_pass,
        }.get(action.kind, self._handle_pass)

        return await handler(action)

    def get_context_for_agent(self, agent: Agent) -> str:
        state = self.global_state
        agenda = state["agenda"]
        topic_idx = state["current_topic_index"]
        current_topic = agenda[topic_idx] if topic_idx < len(agenda) else "Open discussion"

        # Recent discussion (last 15 entries)
        recent = state["discussion_log"][-15:]
        discussion_text = "\n".join(recent) if recent else "(No discussion yet)"

        # Active proposals
        proposals_text = ""
        if state["proposals"]:
            lines = []
            for p in state["proposals"]:
                supporters = ", ".join(p["supporters"]) or "none"
                objectors = ", ".join(p["objectors"]) or "none"
                lines.append(f"  - [{p['id']}] by {p['author']}: {p['text']}")
                lines.append(f"    Supporters: {supporters} | Objectors: {objectors}")
            proposals_text = "\n".join(lines)
        else:
            proposals_text = "  (none)"

        # Participants
        participants = ", ".join(
            f"{a.profile.name} ({a.profile.role})" for a in self.agents.values()
        )

        return (
            f"MEETING — Round {self.round_number}\n"
            f"Topic: {current_topic}\n"
            f"Participants: {participants}\n\n"
            f"RECENT DISCUSSION:\n{discussion_text}\n\n"
            f"ACTIVE PROPOSALS:\n{proposals_text}\n\n"
            f"You are {agent.profile.name} ({agent.profile.role}). "
            f"What do you contribute to this discussion?"
        )

    async def on_round_end(self, round_result: RoundResult) -> None:
        # Advance topic if enough rounds on current one
        rounds_per_topic = self.config.get("rounds_per_topic", 3)
        if self.round_number % rounds_per_topic == 0:
            idx = self.global_state["current_topic_index"]
            if idx < len(self.global_state["agenda"]) - 1:
                self.global_state["current_topic_index"] = idx + 1
                topic = self.global_state["agenda"][idx + 1]
                round_result.events.append(f"Topic changed to: {topic}")

    # --- Action handlers ---

    async def _handle_speak(self, action: Action) -> ActionResult:
        msg = action.payload.get("message", "...")
        entry = f"{action.agent_id}: {msg}"
        self.global_state["discussion_log"].append(entry)
        return ActionResult(action=action, success=True, outcome={"entry": entry})

    async def _handle_propose(self, action: Action) -> ActionResult:
        proposal_text = action.payload.get("proposal", action.payload.get("message", ""))
        proposal_id = f"P{len(self.global_state['proposals']) + 1}"
        proposal = {
            "id": proposal_id,
            "author": action.agent_id,
            "text": proposal_text,
            "supporters": [action.agent_id],
            "objectors": [],
        }
        self.global_state["proposals"].append(proposal)
        self.global_state["votes"][proposal_id] = {"approve": [], "reject": [], "abstain": []}
        entry = f"{action.agent_id} PROPOSES [{proposal_id}]: {proposal_text}"
        self.global_state["discussion_log"].append(entry)
        return ActionResult(action=action, success=True, outcome={"proposal_id": proposal_id})

    async def _handle_support(self, action: Action) -> ActionResult:
        pid = action.payload.get("proposal_id", "")
        for p in self.global_state["proposals"]:
            if p["id"] == pid:
                if action.agent_id not in p["supporters"]:
                    p["supporters"].append(action.agent_id)
                entry = f"{action.agent_id} SUPPORTS {pid}"
                self.global_state["discussion_log"].append(entry)
                return ActionResult(action=action, success=True, outcome={"supported": pid})
        return ActionResult(action=action, success=False, outcome={"error": f"Proposal {pid} not found"})

    async def _handle_object(self, action: Action) -> ActionResult:
        pid = action.payload.get("proposal_id", "")
        reason = action.payload.get("reason", "")
        for p in self.global_state["proposals"]:
            if p["id"] == pid:
                if action.agent_id not in p["objectors"]:
                    p["objectors"].append(action.agent_id)
                entry = f"{action.agent_id} OBJECTS to {pid}: {reason}"
                self.global_state["discussion_log"].append(entry)
                return ActionResult(action=action, success=True, outcome={"objected": pid})
        return ActionResult(action=action, success=False, outcome={"error": f"Proposal {pid} not found"})

    async def _handle_vote(self, action: Action) -> ActionResult:
        pid = action.payload.get("proposal_id", "")
        option = action.payload.get("option", "abstain")  # approve / reject / abstain
        if pid in self.global_state["votes"]:
            tally = self.global_state["votes"][pid]
            if option in tally:
                tally[option].append(action.agent_id)
            entry = f"{action.agent_id} VOTES {option} on {pid}"
            self.global_state["discussion_log"].append(entry)
            return ActionResult(action=action, success=True, outcome={"vote": option, "tally": dict(tally)})
        return ActionResult(action=action, success=False, outcome={"error": f"No vote for {pid}"})

    async def _handle_question(self, action: Action) -> ActionResult:
        msg = action.payload.get("message", "...")
        target = action.payload.get("target", "all")
        entry = f"{action.agent_id} ASKS {target}: {msg}"
        self.global_state["discussion_log"].append(entry)
        return ActionResult(action=action, success=True, outcome={"entry": entry})

    async def _handle_pass(self, action: Action) -> ActionResult:
        return ActionResult(action=action, success=True, outcome={"skipped": True})
