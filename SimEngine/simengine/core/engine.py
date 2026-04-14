"""SimulationEngine — the top-level orchestrator.

Connects all pieces: seed data -> knowledge graph -> agents -> environment -> report.
This replaces MiroFish's Flask API + subprocess pipeline with a clean programmatic API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from simengine.core.agent import Agent
from simengine.core.environment import Environment, RoundResult

logger = logging.getLogger("simengine")


@dataclass
class SimulationResult:
    """Everything that came out of a simulation run."""

    rounds: list[RoundResult] = field(default_factory=list)
    agents: list[Agent] = field(default_factory=list)
    final_state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class SimulationEngine:
    """Main entry point for running simulations.

    Usage:
        engine = SimulationEngine()

        # 1. Build knowledge from seed data
        entities = await engine.extract_entities(seed_files)

        # 2. Generate agents from entities
        agents = await engine.create_agents(entities, environment_type="boardroom")

        # 3. Create environment and run
        env = BoardroomEnvironment(config={...})
        result = await engine.run(env, agents)

        # 4. Generate report
        report = await engine.generate_report(result)
    """

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client
        self._on_round_callback: Any = None

    def on_round(self, callback: Any) -> None:
        """Register a callback for real-time round updates."""
        self._on_round_callback = callback

    async def run(
        self,
        environment: Environment,
        agents: list[Agent],
        max_rounds: int | None = None,
    ) -> SimulationResult:
        """Run a full simulation."""
        if max_rounds is not None:
            environment.config["max_rounds"] = max_rounds

        environment.add_agents(agents)

        logger.info(
            "Starting simulation: %s with %d agents, max %d rounds",
            environment.name,
            len(agents),
            environment.config.get("max_rounds", 10),
        )

        result = SimulationResult(agents=agents)

        while not environment.is_finished():
            round_result = await environment.run_round()
            result.rounds.append(round_result)

            logger.info(
                "Round %d: %d actions",
                round_result.round_number,
                len(round_result.actions_taken),
            )

            if self._on_round_callback:
                await self._on_round_callback(round_result)

        result.final_state = dict(environment.global_state)
        result.metadata = {
            "environment": environment.name,
            "total_rounds": len(result.rounds),
            "total_actions": sum(len(r.actions_taken) for r in result.rounds),
            "agent_count": len(agents),
        }

        logger.info("Simulation complete: %s", result.metadata)
        return result
