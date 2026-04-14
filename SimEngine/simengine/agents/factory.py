"""Agent Factory — creates agents from entities + environment context.

MiroFish's OasisProfileGenerator creates Twitter/Reddit users.
SimEngine's factory creates agents appropriate for ANY environment.
"""

from __future__ import annotations

from typing import Any

from simengine.core.agent import Agent, AgentProfile, AgentMemory
from simengine.knowledge.entity import Entity, KnowledgeBase

PERSONA_SYSTEM_PROMPT = """\
You are creating a persona for a simulation agent.

Given an entity (person, organization, role) and the simulation context,
generate a detailed persona that includes:
- How they think and make decisions
- Their goals, motivations, and fears
- Their communication style
- Their knowledge and blind spots
- Their biases and tendencies

The persona should be specific enough to drive realistic behavior in the simulation.
Output as a single paragraph of text, written in second person ("You are...").
"""


async def create_agents_from_knowledge(
    kb: KnowledgeBase,
    environment_type: str,
    seed_prompt: str,
    llm_client: Any,
    agent_filter: list[str] | None = None,
) -> list[Agent]:
    """Generate agents from a KnowledgeBase.

    Args:
        kb: Extracted knowledge with entities and relationships
        environment_type: What kind of simulation ("boardroom", "marketplace", etc.)
        seed_prompt: The scenario description
        llm_client: LLM for persona generation
        agent_filter: Entity types to convert to agents (e.g. ["person", "company"])
                      If None, uses all entities.
    """
    agents = []
    for entity in kb.entities.values():
        if agent_filter and entity.entity_type not in agent_filter:
            continue

        related = kb.get_related(entity.entity_id)
        relationships = {
            other.entity_id: rel.relation_type
            for rel, other in related
        }

        persona = await _generate_persona(
            entity, environment_type, seed_prompt, related, llm_client
        )

        profile = AgentProfile(
            agent_id=entity.entity_id,
            name=entity.name,
            role=entity.attributes.get("role", entity.entity_type),
            persona=persona,
            goals=entity.attributes.get("goals", []),
            traits=entity.attributes,
            relationships=relationships,
        )

        agents.append(Agent(profile=profile, memory=AgentMemory()))

    return agents


async def _generate_persona(
    entity: Entity,
    environment_type: str,
    seed_prompt: str,
    related: list[tuple[Any, Entity]],
    llm_client: Any,
) -> str:
    """Use LLM to generate a detailed persona for an entity."""
    relationships_text = "\n".join(
        f"- {rel.relation_type} -> {other.name}" for rel, other in related
    )

    user_prompt = (
        f"Entity: {entity.name} ({entity.entity_type})\n"
        f"Summary: {entity.summary}\n"
        f"Attributes: {entity.attributes}\n"
        f"Relationships:\n{relationships_text}\n\n"
        f"Simulation type: {environment_type}\n"
        f"Scenario: {seed_prompt}\n\n"
        f"Generate this entity's persona for the simulation."
    )

    return await llm_client.chat(system=PERSONA_SYSTEM_PROMPT, user=user_prompt)
