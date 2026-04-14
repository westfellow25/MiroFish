"""CLI entry point — run a simulation from a YAML config.

Usage:
    python -m simengine.run configs/examples/boardsim_strategy.yaml
    python -m simengine.run configs/examples/dealroom_saas.yaml
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from simengine.core.config import SimulationConfig
from simengine.core.engine import SimulationEngine
from simengine.core.agent import Agent, AgentProfile, AgentMemory
from simengine.agents.llm_brain import LLMBrain
from simengine.environments.boardroom import BoardroomEnvironment
from simengine.environments.marketplace import MarketplaceEnvironment
from simengine.reporting.reporter import generate_report
from simengine.utils.llm_client import LLMClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("simengine")

ENVIRONMENT_REGISTRY: dict[str, type] = {
    "boardroom": BoardroomEnvironment,
    "marketplace": MarketplaceEnvironment,
}


async def main(config_path: str) -> None:
    config = SimulationConfig.from_yaml(config_path)
    logger.info("Loaded config: %s", config.name)

    # Init LLM
    llm = LLMClient(
        api_key=os.environ.get("LLM_API_KEY", ""),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
        model=config.llm.get("model", os.environ.get("LLM_MODEL", "gpt-4o")),
    )

    # Create environment
    env_cls = ENVIRONMENT_REGISTRY.get(config.environment.type)
    if not env_cls:
        logger.error("Unknown environment type: %s", config.environment.type)
        logger.info("Available: %s", list(ENVIRONMENT_REGISTRY.keys()))
        sys.exit(1)

    env = env_cls(config={
        "max_rounds": config.environment.max_rounds,
        **config.environment.params,
    })

    # Create agents
    brain = LLMBrain(llm_client=llm, temperature=config.llm.get("temperature", 0.7))
    agents = []
    for ac in config.agents:
        profile = AgentProfile(
            agent_id=ac.agent_id,
            name=ac.name,
            role=ac.role,
            persona=ac.persona,
            goals=ac.goals,
            traits=ac.traits,
            relationships=ac.relationships,
        )
        agents.append(Agent(profile=profile, memory=AgentMemory(), brain=brain))

    # Run
    engine = SimulationEngine(llm_client=llm)

    async def on_round(round_result):
        actions_summary = []
        for ar in round_result.actions_taken:
            msg = ar.action.payload.get("message", ar.action.payload.get("proposal", ""))
            preview = msg[:80] + "..." if len(msg) > 80 else msg
            actions_summary.append(f"  {ar.action.agent_id} [{ar.action.kind}]: {preview}")
        print(f"\n=== Round {round_result.round_number} ===")
        print("\n".join(actions_summary))

    engine.on_round(on_round)
    result = await engine.run(env, agents)

    # Report
    print("\n" + "=" * 60)
    print("GENERATING REPORT...")
    print("=" * 60 + "\n")

    report = await generate_report(result, config.seed_prompt, llm)
    print(report)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m simengine.run <config.yaml>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
