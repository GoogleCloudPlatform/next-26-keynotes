# Agent Template

Reusable template for creating new ADK agents with A2A protocol, ADK Skills, Memory Bank, and structured output.

## Usage

1. Copy this directory to create a new agent:
   ```bash
   cp -r src/_agent_template src/my_new_agent
   ```

2. Search-replace the following placeholders in all files:

   | Placeholder | Example | Description |
   |-------------|---------|-------------|
   | `{{AGENT_MODULE}}` | `docking_agent` | Python module name (snake_case) |
   | `{{AGENT_DISPLAY_NAME}}` | `Docking Agent` | Human-readable name |
   | `{{AGENT_PREFIX}}` | `DOCKING` | Uppercase prefix for env vars |
   | `{{EXECUTOR_CLASS}}` | `DockingAgentExecutor` | AgentExecutor subclass name |
   | `{{CARD_FUNC}}` | `create_docking_agent_card` | Agent card factory function |
   | `{{MEMORY_FUNC}}` | `create_docking_memory_topics` | Memory topics factory function |
   | `{{DEPLOY_FUNC}}` | `deploy_docking_agent` | Deploy script entry function |
   | `{{VALIDATION_FIELD}}` | `assigned_bay` | Primary field to validate in JSON response |
   | `{{ARTIFACT_NAME}}` | `docking_assignment` | Artifact name for A2A response |
   | `{{PORT}}` | `8001` | Local server port number |
   | `{{SKILL_NAME}}` | `analyze-data` | Kebab-case skill directory name |

3. Quick search-replace with sed:
   ```bash
   cd src/my_new_agent
   find . -type f \( -name '*.py' -o -name '*.md' \) -exec sed -i '' \
     -e 's/{{AGENT_MODULE}}/my_new_agent/g' \
     -e 's/{{AGENT_DISPLAY_NAME}}/My New Agent/g' \
     -e 's/{{AGENT_PREFIX}}/MY_NEW/g' \
     -e 's/{{EXECUTOR_CLASS}}/MyNewAgentExecutor/g' \
     -e 's/{{CARD_FUNC}}/create_my_new_agent_card/g' \
     -e 's/{{MEMORY_FUNC}}/create_my_new_memory_topics/g' \
     -e 's/{{DEPLOY_FUNC}}/deploy_my_new_agent/g' \
     -e 's/{{VALIDATION_FIELD}}/result/g' \
     -e 's/{{ARTIFACT_NAME}}/my_new_result/g' \
     -e 's/{{PORT}}/8010/g' \
     -e 's/{{SKILL_NAME}}/example-skill/g' \
     {} +
   ```

4. Fill in the `TODO` sections:
   - `agent/config.py` — Agent identity, model, output schema
   - `agent/prompts.py` — Agent instruction prompt
   - `agent/schemas.py` — Pydantic models for structured output
   - `agent/tools.py` — FunctionTool implementations
   - `skills/{{SKILL_NAME}}/SKILL.md` — Skill procedure steps
   - `skills/{{SKILL_NAME}}/references/` — Reference data
   - `skills/{{SKILL_NAME}}/scripts/` — Executable scripts
   - `runtime/agent_card.py` — Agent card with skills and examples
   - `services/memory_manager.py` — Custom memory topic definitions

## Directory Structure

```
my_new_agent/
├── __init__.py                    # Package exports (lazy imports)
├── agent/                         # Agent definition
│   ├── __init__.py                # Re-exports root_agent, config
│   ├── agent.py                   # LlmAgent wiring (config + skills + tools)
│   ├── config.py                  # Agent identity, model, schema
│   ├── prompts.py                 # Instruction prompt
│   ├── schemas.py                 # Pydantic output models
│   └── tools.py                   # FunctionTools for computation
├── skills/                        # ADK Skills (procedural knowledge)
│   └── example-skill/
│       ├── SKILL.md               # Step-by-step instructions
│       ├── references/            # Reference data for the LLM
│       │   └── guide.md
│       └── scripts/               # Executable scripts
│           └── validate.py
├── runtime/                       # Deployment & serving
│   ├── __init__.py
│   ├── agent_card.py              # A2A AgentCard for discovery
│   ├── agent_executor.py          # A2A executor with sessions
│   ├── deploy.py                  # Deploy to Agent Engine
│   ├── local_server.py            # Local A2A server for testing
│   └── test_client.py             # Test client for local server
└── services/                      # Infrastructure services
    ├── __init__.py
    ├── memory_manager.py          # Memory Bank with custom topics
    └── session_manager.py         # Session lifecycle with TTL cache
```

## File Guide

| File | What to do |
|------|-----------|
| `agent/config.py` | Set agent name, model, output schema |
| `agent/prompts.py` | Write the agent's instruction prompt, mention available skills |
| `agent/schemas.py` | Define Pydantic output models |
| `agent/tools.py` | Implement FunctionTools for computation the LLM can't do |
| `agent/agent.py` | Usually unchanged — wires config + skills + tools |
| `skills/*/SKILL.md` | Write step-by-step skill procedures (YAML frontmatter + steps) |
| `skills/*/references/` | Add reference data files the skill reads |
| `skills/*/scripts/` | Add scripts the skill executes |
| `runtime/agent_card.py` | Describe agent capabilities for A2A discovery |
| `runtime/agent_executor.py` | Usually unchanged — handles A2A protocol |
| `runtime/deploy.py` | Update display name and topic descriptions |
| `runtime/local_server.py` | Usually unchanged — starts local A2A server |
| `runtime/test_client.py` | Add test cases for your agent |
| `services/memory_manager.py` | Define custom memory topics (3-5 per agent) |
| `services/session_manager.py` | Usually unchanged — generic session management |

## Agent Ports

| Port | Agent |
|------|-------|
| 8001 | Event Planner Agent |
| 8002 | Community Planner Agent |
| 8003 | Traffic Planner Agent |
| 8004 | Economic Planner Agent |
| 8005 | Evaluator Agent |
| 8084 | Marathon Planner Agent (orchestrator) |

## After Creating Your Agent

1. Add your agent's schemas to `src/schemas.py` re-export hub
2. Add test file in `tests/test_my_new_agent.py`
3. Add deploy/run/test commands to `CLAUDE.md`
4. If orchestrated, add tool entry to `src/planner_agent/core/tools.py`
