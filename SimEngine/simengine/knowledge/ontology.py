"""Ontology extraction — from raw text to structured entities.

Adapted from MiroFish's ontology_generator.py but made domain-agnostic.
MiroFish's prompt forced 10 social-media entity types.
SimEngine lets the LLM discover entity types from the seed data,
or you can provide a domain schema.
"""

from __future__ import annotations

import json
from typing import Any

from simengine.knowledge.entity import Entity, KnowledgeBase, Relationship

EXTRACTION_SYSTEM_PROMPT = """\
You are an expert at extracting structured knowledge from unstructured text.

Given the input text and an optional domain hint, extract:
1. ENTITIES — people, organizations, products, concepts, policies, etc.
2. RELATIONSHIPS — how entities are connected.

Output valid JSON:
{
  "entities": [
    {"id": "e1", "name": "...", "type": "...", "summary": "...", "attributes": {...}}
  ],
  "relationships": [
    {"source": "e1", "target": "e2", "type": "...", "description": "..."}
  ]
}

Rules:
- Extract ALL meaningful entities, not just people
- Relationship types should be verbs: "works_for", "competes_with", "regulates"
- Attributes should capture quantitative and qualitative properties
- Be thorough but precise
"""


async def extract_knowledge(
    text: str,
    llm_client: Any,
    domain_hint: str = "",
) -> KnowledgeBase:
    """Extract entities and relationships from seed text using LLM."""
    user_prompt = f"Domain: {domain_hint}\n\nText:\n{text}" if domain_hint else text

    response = await llm_client.chat_json(
        system=EXTRACTION_SYSTEM_PROMPT,
        user=user_prompt,
    )

    return _parse_knowledge(response)


def _parse_knowledge(data: dict[str, Any]) -> KnowledgeBase:
    """Parse LLM JSON output into a KnowledgeBase."""
    kb = KnowledgeBase()

    for e in data.get("entities", []):
        kb.add_entity(Entity(
            entity_id=str(e["id"]),
            name=e["name"],
            entity_type=e.get("type", "unknown"),
            summary=e.get("summary", ""),
            attributes=e.get("attributes", {}),
        ))

    for r in data.get("relationships", []):
        kb.add_relationship(Relationship(
            source_id=str(r["source"]),
            target_id=str(r["target"]),
            relation_type=r.get("type", "related_to"),
            description=r.get("description", ""),
        ))

    return kb
