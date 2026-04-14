"""Configuration loading from YAML files.

SimEngine is configured declaratively: you describe WHAT to simulate,
not HOW to wire the code. One YAML file = one simulation scenario.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AgentConfig:
    """Agent definition from config file."""

    agent_id: str
    name: str
    role: str
    persona: str
    goals: list[str] = field(default_factory=list)
    traits: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, str] = field(default_factory=dict)


@dataclass
class EnvironmentConfig:
    """Environment definition from config file."""

    type: str  # "boardroom", "marketplace", "negotiation", etc.
    name: str
    max_rounds: int = 10
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationConfig:
    """Complete simulation scenario."""

    name: str
    description: str
    environment: EnvironmentConfig
    agents: list[AgentConfig]
    seed_prompt: str = ""  # the "what if" question
    llm: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> SimulationConfig:
        with open(path) as f:
            data = yaml.safe_load(f)

        env_data = data["environment"]
        environment = EnvironmentConfig(
            type=env_data["type"],
            name=env_data.get("name", env_data["type"]),
            max_rounds=env_data.get("max_rounds", 10),
            params=env_data.get("params", {}),
        )

        agents = [
            AgentConfig(
                agent_id=a.get("id", f"agent_{i}"),
                name=a["name"],
                role=a["role"],
                persona=a.get("persona", ""),
                goals=a.get("goals", []),
                traits=a.get("traits", {}),
                relationships=a.get("relationships", {}),
            )
            for i, a in enumerate(data["agents"])
        ]

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            environment=environment,
            agents=agents,
            seed_prompt=data.get("seed_prompt", ""),
            llm=data.get("llm", {}),
        )
