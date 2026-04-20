"""CLI entry point — run a simulation from a YAML config.

Usage:
    python -m simengine configs/examples/boardsim_strategy.yaml
    python -m simengine configs/examples/dealroom_saas.yaml
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
from simengine.environments.negotiation import NegotiationEnvironment
from simengine.environments.organization import OrganizationEnvironment
from simengine.reporting.reporter import generate_report
from simengine.utils.llm_client import LLMClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("simengine")

ENVIRONMENT_REGISTRY: dict[str, type] = {
    "boardroom": BoardroomEnvironment,
    "marketplace": MarketplaceEnvironment,
    "negotiation": NegotiationEnvironment,
    "organization": OrganizationEnvironment,
}


# ANSI colors — fall back to no color if not a TTY
_TTY = sys.stdout.isatty()


def _c(code: str) -> str:
    return code if _TTY else ""


BOLD = _c("\033[1m")
DIM = _c("\033[2m")
RESET = _c("\033[0m")
CYAN = _c("\033[36m")
GREEN = _c("\033[32m")
YELLOW = _c("\033[33m")
MAGENTA = _c("\033[35m")
BLUE = _c("\033[34m")


ACTION_COLOR = {
    "speak": CYAN,
    "question": CYAN,
    "propose": MAGENTA,
    "support": GREEN,
    "vote": YELLOW,
    "object": YELLOW,
    "offer": MAGENTA,
    "make_offer": MAGENTA,
    "counter_offer": MAGENTA,
    "accept": GREEN,
    "reject": YELLOW,
    "pitch": CYAN,
    "announce": BLUE,
    "pass": DIM,
}


def _preview(payload: dict, width: int = 90) -> str:
    for key in ("message", "proposal", "terms", "reason", "description"):
        if key in payload:
            val = payload[key]
            s = str(val)
            return s[:width] + ("..." if len(s) > width else "")
    return str(payload)[:width]


def _format_action(ar) -> str:
    kind = ar.action.kind
    agent = ar.action.agent_id
    color = ACTION_COLOR.get(kind, "")
    preview = _preview(ar.action.payload)
    return f"  {BOLD}{agent}{RESET} {color}[{kind}]{RESET} {preview}"


async def main(config_path: str) -> None:
    config = SimulationConfig.from_yaml(config_path)
    print(f"\n{BOLD}{BLUE}Scenario:{RESET} {config.name}")
    print(f"{DIM}{config.description}{RESET}\n")

    # Init LLM
    api_key = os.environ.get("LLM_API_KEY", "")
    if not api_key:
        print(f"{YELLOW}WARNING: LLM_API_KEY not set — agents will fail to respond.{RESET}")
        print(f"{DIM}Set LLM_API_KEY and optionally LLM_BASE_URL and LLM_MODEL.{RESET}\n")

    llm = LLMClient(
        api_key=api_key,
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

    print(f"{BOLD}Agents:{RESET}")
    for a in agents:
        print(f"  - {a.profile.name} ({a.profile.role})")
    print()

    # Run
    engine = SimulationEngine(llm_client=llm)

    async def on_round(round_result):
        header = f"{BOLD}Round {round_result.round_number}{RESET}"
        if round_result.events:
            header += f" {DIM}— {'; '.join(round_result.events)}{RESET}"
        print(f"\n{'─' * 60}")
        print(header)
        print("─" * 60)
        for ar in round_result.actions_taken:
            print(_format_action(ar))

    engine.on_round(on_round)
    result = await engine.run(env, agents)

    # Report
    print(f"\n{'═' * 60}")
    print(f"{BOLD}{BLUE}GENERATING REPORT…{RESET}")
    print(f"{'═' * 60}\n")

    report = await generate_report(result, config.seed_prompt, llm)
    print(report)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m simengine <config.yaml>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
