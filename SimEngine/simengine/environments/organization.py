"""Organization Environment — hierarchical workplace dynamics.

Use cases:
- TalentEcho: test reorg before reorg
- Simulating how a "toxic employee" affects a team
- Predicting friction points in a newly merged company

Interaction model:
  Agents occupy roles in a hierarchy. They can: assign_task, request_help,
  escalate, deliver, report_issue, socialize.
  Global state tracks: open tasks, morale, information flows.
"""

from __future__ import annotations

from typing import Any

from simengine.core.action import Action, ActionResult
from simengine.core.agent import Agent
from simengine.core.environment import Environment


class OrganizationEnvironment(Environment):
    """A workplace with hierarchy, tasks, and morale."""

    ACTIONS = [
        "assign_task", "request_help", "escalate",
        "deliver", "report_issue", "socialize", "pass",
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(name="organization", config=config or {})
        self.global_state = {
            "company_context": self.config.get("company_context", ""),
            "open_tasks": [],  # {"id", "assignee", "assigner", "description", "status", "round_created"}
            "completed_tasks": [],
            "escalations": [],
            "issues_reported": [],
            "morale": {},  # agent_id -> 0-100
            "interaction_log": [],
        }
        # Init morale per agent (agents added later via add_agent)

    def add_agent(self, agent: Agent) -> None:
        super().add_agent(agent)
        # default morale
        if agent.id not in self.global_state["morale"]:
            self.global_state["morale"][agent.id] = 70

    def available_actions(self, agent: Agent) -> list[str]:
        actions = list(self.ACTIONS)
        # Can only "deliver" if agent has open tasks assigned to them
        has_tasks = any(t["assignee"] == agent.id for t in self.global_state["open_tasks"])
        if not has_tasks and "deliver" in actions:
            actions.remove("deliver")
        return actions

    async def execute_action(self, action: Action) -> ActionResult:
        handler = {
            "assign_task": self._handle_assign_task,
            "request_help": self._handle_request_help,
            "escalate": self._handle_escalate,
            "deliver": self._handle_deliver,
            "report_issue": self._handle_report_issue,
            "socialize": self._handle_socialize,
            "pass": self._handle_pass,
        }.get(action.kind, self._handle_pass)
        return await handler(action)

    def get_context_for_agent(self, agent: Agent) -> str:
        state = self.global_state
        my_tasks = [t for t in state["open_tasks"] if t["assignee"] == agent.id]
        assigned_by_me = [t for t in state["open_tasks"] if t["assigner"] == agent.id]

        tasks_text = ""
        if my_tasks:
            tasks_text += "Your open tasks:\n" + "\n".join(
                f"  - [{t['id']}] from {t['assigner']}: {t['description']}" for t in my_tasks
            ) + "\n"
        if assigned_by_me:
            tasks_text += "Tasks you assigned to others:\n" + "\n".join(
                f"  - [{t['id']}] to {t['assignee']}: {t['description']} (status: {t['status']})"
                for t in assigned_by_me
            ) + "\n"
        if not tasks_text:
            tasks_text = "No open tasks\n"

        recent_log = state["interaction_log"][-12:]
        log_text = "\n".join(recent_log) if recent_log else "(no recent activity)"

        my_morale = state["morale"].get(agent.id, 70)
        relationships = agent.profile.relationships
        rel_text = ", ".join(f"{k}: {v}" for k, v in relationships.items()) if relationships else "(none recorded)"

        return (
            f"WORKPLACE — Round {self.round_number}\n"
            f"Company: {state['company_context']}\n"
            f"You are {agent.profile.name} ({agent.profile.role})\n"
            f"Your morale: {my_morale}/100\n"
            f"Your relationships: {rel_text}\n\n"
            f"{tasks_text}\n"
            f"RECENT ACTIVITY:\n{log_text}\n\n"
            f"What do you do?"
        )

    async def _handle_assign_task(self, action: Action) -> ActionResult:
        assignee = action.payload.get("assignee", "")
        description = action.payload.get("description", "")
        task_id = f"T{len(self.global_state['open_tasks']) + len(self.global_state['completed_tasks']) + 1}"
        task = {
            "id": task_id,
            "assigner": action.agent_id,
            "assignee": assignee,
            "description": description,
            "status": "open",
            "round_created": self.round_number,
        }
        self.global_state["open_tasks"].append(task)
        entry = f"{action.agent_id} ASSIGNS {task_id} to {assignee}: {description}"
        self.global_state["interaction_log"].append(entry)
        return ActionResult(
            action=action, success=True, outcome={"task_id": task_id},
            visible_to=[action.agent_id, assignee],
        )

    async def _handle_request_help(self, action: Action) -> ActionResult:
        target = action.payload.get("target", "")
        topic = action.payload.get("message", "")
        entry = f"{action.agent_id} asks {target} for help: {topic}"
        self.global_state["interaction_log"].append(entry)
        return ActionResult(action=action, success=True, outcome={"asked_help_from": target})

    async def _handle_escalate(self, action: Action) -> ActionResult:
        issue = action.payload.get("message", "")
        target = action.payload.get("target", "manager")
        self.global_state["escalations"].append({
            "from": action.agent_id, "to": target, "issue": issue, "round": self.round_number,
        })
        entry = f"{action.agent_id} ESCALATES to {target}: {issue}"
        self.global_state["interaction_log"].append(entry)
        return ActionResult(action=action, success=True, outcome={"escalated": issue})

    async def _handle_deliver(self, action: Action) -> ActionResult:
        task_id = action.payload.get("task_id", "")
        for task in self.global_state["open_tasks"]:
            if task["id"] == task_id and task["assignee"] == action.agent_id:
                task["status"] = "delivered"
                self.global_state["open_tasks"].remove(task)
                self.global_state["completed_tasks"].append(task)
                entry = f"{action.agent_id} DELIVERS {task_id}"
                self.global_state["interaction_log"].append(entry)
                # Small morale boost for completing a task
                self.global_state["morale"][action.agent_id] = min(
                    100, self.global_state["morale"].get(action.agent_id, 70) + 2
                )
                return ActionResult(action=action, success=True, outcome={"delivered": task_id})
        return ActionResult(action=action, success=False, outcome={"error": "task not found"})

    async def _handle_report_issue(self, action: Action) -> ActionResult:
        issue = action.payload.get("message", "")
        self.global_state["issues_reported"].append({
            "from": action.agent_id, "issue": issue, "round": self.round_number,
        })
        entry = f"{action.agent_id} REPORTS: {issue}"
        self.global_state["interaction_log"].append(entry)
        # Reporting drops morale slightly
        self.global_state["morale"][action.agent_id] = max(
            0, self.global_state["morale"].get(action.agent_id, 70) - 3
        )
        return ActionResult(action=action, success=True, outcome={"issue": issue})

    async def _handle_socialize(self, action: Action) -> ActionResult:
        target = action.payload.get("target", "")
        msg = action.payload.get("message", "")
        entry = f"{action.agent_id} chats with {target}: {msg}"
        self.global_state["interaction_log"].append(entry)
        # Socializing lifts morale for both
        self.global_state["morale"][action.agent_id] = min(
            100, self.global_state["morale"].get(action.agent_id, 70) + 1
        )
        if target in self.global_state["morale"]:
            self.global_state["morale"][target] = min(
                100, self.global_state["morale"][target] + 1
            )
        return ActionResult(action=action, success=True, outcome={"socialized_with": target})

    async def _handle_pass(self, action: Action) -> ActionResult:
        return ActionResult(action=action, success=True, outcome={"skipped": True})
