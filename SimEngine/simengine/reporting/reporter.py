"""Reporter — generates analysis from simulation results.

Adapted from MiroFish's ReportAgent pattern: uses ReACT loop with tools.
But instead of querying Twitter/Reddit data, it queries the universal
simulation history.
"""

from __future__ import annotations

from typing import Any

from simengine.core.engine import SimulationResult


REPORT_SYSTEM_PROMPT = """\
You are an expert analyst reviewing the results of a multi-agent simulation.

Based on the simulation data provided, generate a structured report that includes:
1. EXECUTIVE SUMMARY — key findings in 2-3 sentences
2. KEY DYNAMICS — what patterns emerged from agent interactions
3. CRITICAL MOMENTS — turning points or surprising events
4. AGENT ANALYSIS — how different agents behaved and why
5. OUTCOMES — final state, decisions made, deals closed, votes passed
6. INSIGHTS — non-obvious takeaways and recommendations

Write in a clear, professional tone. Support claims with specific examples
from the simulation data.
"""


async def generate_report(
    result: SimulationResult,
    seed_prompt: str,
    llm_client: Any,
) -> str:
    """Generate a narrative report from simulation results."""
    simulation_data = _format_simulation_data(result)

    user_prompt = (
        f"SIMULATION SCENARIO:\n{seed_prompt}\n\n"
        f"SIMULATION DATA:\n{simulation_data}\n\n"
        f"Generate a comprehensive analysis report."
    )

    return await llm_client.chat(
        system=REPORT_SYSTEM_PROMPT,
        user=user_prompt,
        temperature=0.3,
    )


def _format_simulation_data(result: SimulationResult) -> str:
    """Convert SimulationResult into readable text for the LLM."""
    lines = [f"Total rounds: {result.metadata.get('total_rounds', 0)}"]
    lines.append(f"Total actions: {result.metadata.get('total_actions', 0)}")
    lines.append(f"Agents: {result.metadata.get('agent_count', 0)}")
    lines.append("")

    for round_result in result.rounds:
        lines.append(f"--- Round {round_result.round_number} ---")
        for ar in round_result.actions_taken:
            agent = ar.action.agent_id
            kind = ar.action.kind
            payload = ar.action.payload
            if kind == "speak" or kind == "question":
                msg = payload.get("message", "")
                lines.append(f"  [{agent}] {kind}: {msg}")
            elif kind == "propose":
                lines.append(f"  [{agent}] proposes: {payload.get('proposal', payload.get('message', ''))}")
            elif kind == "vote":
                lines.append(f"  [{agent}] votes {payload.get('option', '?')} on {payload.get('proposal_id', '?')}")
            else:
                lines.append(f"  [{agent}] {kind}: {payload}")

        if round_result.events:
            for ev in round_result.events:
                lines.append(f"  EVENT: {ev}")

        if round_result.global_state:
            # Only include key state changes
            decisions = round_result.global_state.get("decisions", [])
            completed = round_result.global_state.get("completed_deals", [])
            if decisions:
                lines.append(f"  Decisions: {decisions}")
            if completed:
                lines.append(f"  Completed deals: {len(completed)}")
        lines.append("")

    # Final state
    lines.append("--- FINAL STATE ---")
    for k, v in result.final_state.items():
        if isinstance(v, list) and len(v) > 5:
            lines.append(f"  {k}: {len(v)} items")
        else:
            lines.append(f"  {k}: {v}")

    return "\n".join(lines)
