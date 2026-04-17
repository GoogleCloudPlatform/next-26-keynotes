# Demo: Marathon Planner Before/After

Demonstrates the value of multi-agent collaboration by comparing two deployments:

| Variant | Sub-Agents | What Happens |
|---------|-----------|--------------|
| **Solo** | None (evaluator only) | Evaluator catches gaps, re-planning loop |
| **Full Team** | Traffic + Community + Economic | Plan passes evaluation on first try |

Both services run the **same code and image** — the only difference is which agent env vars are set.

## Architecture

```
demo/
  scenarios.py            # Named scenarios (prompts, agent configs, expected behavior)
  test_endpoints.py       # E2E test client for both endpoints
  deploy/
    main.tf               # Terraform: solo + full Cloud Run services
    variables.tf           # Terraform variables
    terraform.tfvars       # Real values (gitignored)
    terraform.tfvars.example
```

Each demo variant has a dedicated **web UI** (built separately) that connects to its Cloud Run endpoint via A2A JSON-RPC.

## Setup

### 1. Deploy the demo services

```bash
cd demo/deploy
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your real values
terraform init
terraform apply
```

Note the output URLs:

```
solo_url = "https://marathon-planner-solo-xxxxx-uc.a.run.app"
full_url = "https://marathon-planner-full-xxxxx-uc.a.run.app"
```

### 2. Verify both services are healthy

```bash
# Quick health check (agent cards only)
uv run python -m demo.test_endpoints --health-only

# Full E2E test (sends demo prompt to both endpoints)
uv run python -m demo.test_endpoints

# Test one variant at a time
uv run python -m demo.test_endpoints --solo
uv run python -m demo.test_endpoints --full
```

## Endpoints for UI Integration

Both services expose the same A2A JSON-RPC interface:

**Agent Card** (GET):

```
GET {service_url}/.well-known/agent.json
```

**Send Message** (POST):

```json
POST {service_url}
Content-Type: application/json

{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "unique-id",
    "params": {
        "message": {
            "messageId": "msg-id",
            "role": "user",
            "parts": [{"kind": "text", "text": "Plan a marathon in..."}]
        }
    }
}
```

The demo prompt is defined in `demo/scenarios.py` — UIs should import from there or use the same prompt text.

## Demo Flow

### Act 1: Solo Mode (The Problem)

1. Open the **solo UI** (connected to `marathon-planner-solo`)
2. **Talking point**: "The agent generates a plan on its own, but watch what happens when we evaluate it..."
3. The evaluator scores low (~0.5-0.7) and flags missing traffic analysis, community impact, and economic projections
4. The agent tries to revise, but without specialist knowledge it produces generic content
5. **Talking point**: "It takes 2-3 iterations and the plan still lacks depth. The agent is doing everything itself."

### Act 2: Full Team (The Solution)

1. Open the **full team UI** (connected to `marathon-planner-full`)
2. **Talking point**: "Same prompt, same evaluator, but now the agent can delegate to specialists..."
3. Watch the agent delegate to Traffic, Community, and Economic planners via A2A
4. Each specialist returns expert analysis (road closures, cheer zones, revenue projections)
5. The combined plan passes evaluation on the first try (score >= 0.85)
6. **Talking point**: "Multi-agent collaboration — each agent does what it's best at. The plan passes on the first try."

### Key Talking Points

- **Same code, different config**: Both services run the exact same image. The only difference is which env vars are set.
- **A2A protocol**: Agents communicate via the Agent-to-Agent protocol — no hardcoded integrations.
- **Evaluator as quality gate**: The evaluator agent uses Vertex AI Eval with 7 custom metrics to score plans objectively.
- **Iterative improvement**: In solo mode, the re-planning loop shows how the evaluator drives quality even without specialists.

## Troubleshooting

**Services not starting?**

```bash
gcloud run services list --project=YOUR_PROJECT_ID --region=us-central1
gcloud run services logs marathon-planner-solo --project=YOUR_PROJECT_ID --region=us-central1
```

**Timeout errors?**
Agent orchestration can take 2-3 minutes in full-team mode. The Cloud Run timeout is set to 600s.

**Evaluator always passes/fails?**
Check that `EVALUATOR_AGENT_RESOURCE_NAME` is set correctly in both services. The solo service should NOT have traffic/community/economic env vars.

## Cleanup

```bash
cd demo/deploy
terraform destroy
```
