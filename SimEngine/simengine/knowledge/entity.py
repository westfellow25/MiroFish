"""Entity models — the building blocks extracted from seed data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Entity:
    """A person, organization, concept, or thing extracted from seed data."""

    entity_id: str
    name: str
    entity_type: str  # "person", "company", "product", "policy", etc.
    summary: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    # e.g. {"revenue": "500M", "industry": "fintech", "headcount": 200}


@dataclass
class Relationship:
    """A connection between two entities."""

    source_id: str
    target_id: str
    relation_type: str  # "works_for", "competes_with", "regulates", "supplies_to"
    description: str = ""
    weight: float = 1.0


@dataclass
class KnowledgeBase:
    """All entities and relationships from the seed data."""

    entities: dict[str, Entity] = field(default_factory=dict)
    relationships: list[Relationship] = field(default_factory=list)

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.entity_id] = entity

    def add_relationship(self, rel: Relationship) -> None:
        self.relationships.append(rel)

    def get_related(self, entity_id: str) -> list[tuple[Relationship, Entity]]:
        """Get all entities related to a given entity."""
        results = []
        for rel in self.relationships:
            if rel.source_id == entity_id and rel.target_id in self.entities:
                results.append((rel, self.entities[rel.target_id]))
            elif rel.target_id == entity_id and rel.source_id in self.entities:
                results.append((rel, self.entities[rel.source_id]))
        return results

    def summary(self) -> str:
        lines = [f"KnowledgeBase: {len(self.entities)} entities, {len(self.relationships)} relationships"]
        for e in self.entities.values():
            lines.append(f"  [{e.entity_type}] {e.name}: {e.summary[:80]}")
        return "\n".join(lines)
