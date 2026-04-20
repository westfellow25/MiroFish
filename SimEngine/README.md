# SimEngine

**Universal multi-agent simulation engine.**

Inspired by the [MiroFish](https://github.com/666ghj/MiroFish) methodology of swarm intelligence for prediction, but rebuilt as a domain-agnostic engine. Where MiroFish simulates social media (Twitter/Reddit), SimEngine can simulate **any structured interaction**: board meetings, B2B negotiations, supply chains, organizational dynamics, and more.

## Why SimEngine

MiroFish is great at what it does — predicting how public opinion evolves. But its core methodology (seed data → knowledge graph → agent personas → multi-agent simulation → emergent report) is far more general than social media.

SimEngine extracts that core idea and removes the social-media constraint.

## How It Differs from MiroFish

| Aspect | MiroFish | SimEngine |
|---|---|---|
| **Simulation surface** | Twitter + Reddit only | Any Environment subclass |
| **Agent actions** | `CREATE_POST`, `LIKE`, `REPOST` (hardcoded) | Declarative per-environment (`speak`, `vote`, `offer`, `accept`...) |
| **Agent profile** | `follower_count`, `karma`, `bio` | `goals`, `traits`, `relationships`, `persona` |
| **Runtime** | Flask + subprocess + OASIS library | Single async Python process |
| **Configuration** | UI-driven, multi-step flow | One YAML file per scenario |
| **Target user** | Analysts predicting public reactions | Operators, strategists, founders, researchers |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YAML scenario config                     │
│       (agents, environment type, scenario prompt)           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   SimulationEngine                          │
│                   (orchestrator)                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
       ┌─────────┐     ┌─────────┐     ┌─────────┐
       │ Agents  │     │ Environ-│     │Reporter │
       │ (LLM    │◄───►│  ment   │     │ (ReACT  │
       │ brain)  │     │ (rules) │     │ pattern)│
       └─────────┘     └─────────┘     └─────────┘
            │               │               │
            │               │               │
       persona +        actions +       summary of
       memory           global state    simulation
```

### Core abstractions

- **`Environment`** — the world where agents interact. Defines available actions, rules, and visible context. Subclass it to create new worlds.
- **`Agent`** — profile + memory + brain. The brain is any object implementing `decide(profile, memory, actions, context) -> Action`.
- **`Action`** — generic `{kind, agent_id, payload}`. No platform-specific enums.
- **`SimulationEngine`** — runs rounds, collects results, manages lifecycle.

## Available Environments

- **`BoardroomEnvironment`** — structured meetings: speak, propose, support, object, vote.
  Use cases: digital board of directors, committee decisions, policy debates.

- **`MarketplaceEnvironment`** — B2B deal flow: pitch, offer, counter, accept, reject.
  Use cases: sales simulation, supplier negotiations, competitive bidding.

More environments are easy to add — see "Extending" below.

## Quickstart

### Install

```bash
pip install -e .
```

### Run a scenario

```bash
export LLM_API_KEY=sk-...
export LLM_BASE_URL=https://api.openai.com/v1  # or any OpenAI-compatible endpoint
export LLM_MODEL=gpt-4o

python -m simengine configs/examples/boardsim_strategy.yaml
```

### Run smoke test (no LLM required)

```bash
python -m tests.smoke_boardroom
```

This runs a full 5-round boardroom simulation with a mock brain to prove the engine works end-to-end.

## Example Scenarios

### BoardSim — "Should we pivot to AI?"
A SaaS company's board meets to discuss a risky $20M pivot. Five agents (CEO, CFO, Investor, Board Member, VP Customer Success) debate, propose alternatives, and vote.
→ `configs/examples/boardsim_strategy.yaml`

### DealRoom — Enterprise B2B negotiation
A startup pitches its platform to a Fortune 500 buyer with three stakeholders (CTO, CFO, VP Eng), while a competitor tries to undercut the deal.
→ `configs/examples/dealroom_saas.yaml`

## Writing Your Own Scenario

A scenario is a single YAML file:

```yaml
name: "My scenario"
seed_prompt: "What if..."

environment:
  type: boardroom   # or: marketplace
  max_rounds: 10
  params:
    agenda: ["Topic A", "Topic B"]

agents:
  - name: "Alice"
    role: "CEO"
    persona: "Detailed character description..."
    goals: ["Goal 1", "Goal 2"]
    traits:
      risk_tolerance: 0.8
```

Then run:
```bash
python -m simengine path/to/my_scenario.yaml
```

## Extending

### Adding a new environment

1. Subclass `Environment` in `simengine/environments/`
2. Implement three methods:
   - `available_actions(agent)` — what can this agent do now?
   - `execute_action(action)` — apply the action, update state, return result
   - `get_context_for_agent(agent)` — what does this agent see right now?
3. Register it in `simengine/run.py::ENVIRONMENT_REGISTRY`

### Custom agent brains

The default `LLMBrain` uses an LLM for decisions. You can swap in:
- `MockBrain` for testing (see `tests/smoke_boardroom.py`)
- Rule-based brains for deterministic agents
- Hybrid brains combining heuristics + LLM

Just implement the `AgentBrain` protocol:
```python
async def decide(self, profile, memory, available_actions, context) -> Action:
    ...
```

## What's Reused vs New

**Reused concepts from MiroFish:**
- Seed data → structured knowledge extraction
- Entity-driven agent persona generation
- ReACT-style report generation

**Built new for SimEngine:**
- Abstract `Environment` replacing the OASIS Twitter/Reddit coupling
- Generic `Action` system
- Declarative YAML scenario configuration
- Direct async Python runtime (no Flask/subprocess/database)

## Status

This is an **early-stage prototype**. The engine works end-to-end with mock brains (smoke test passes). Full LLM integration requires a compatible API key and has not yet been benchmarked on large scenarios.

## License

TBD.
