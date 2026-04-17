import asyncio
import time
from httpx import AsyncClient
from dotenv import load_dotenv

load_dotenv()

from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace.span import Span
from google.adk.telemetry.setup import maybe_set_otel_providers, OTelHooks

# Set up in-memory OpenTelemetry exporter before the ADK app starts
exporter = InMemorySpanExporter()
maybe_set_otel_providers([OTelHooks(span_processors=[SimpleSpanProcessor(exporter)])])

from src.planner_agent.main import app

async def run_test() -> None:
    prompt = "Plan a marathon for 50,000 participants in Las Vegas. It has to go by the Mandalay Bay Resort and spend half of its time in residential communities. We are doing it on April 26, 2026."
    
    print(f"Starting performance test with prompt: \n'{prompt}'\n")
    
    start_time = time.time()
    first_byte_time = None
    
    # We will POST to the A2A route directly
    from httpx import ASGITransport
    
    # JSON-RPC 2.0 conforming request for a2a server
    request_body = {
        "jsonrpc": "2.0",
        "method": "message/stream",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"text": prompt}],
                "messageId": "test-id-12345"
            }
        },
        "id": 1
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with client.stream(
            "POST", "/", json=request_body, headers={"Accept": "text/event-stream"}
        ) as response:
            async for line in response.aiter_lines():
                if not first_byte_time and line.strip():
                    first_byte_time = time.time()
                    ttfb = first_byte_time - start_time
                    print(f"✅ Time To First Byte (TTFB): {ttfb:.3f}s")
                # Keep yielding to consume the full SSE stream so open telemetry spans close
                
    total_time = time.time() - start_time
    print(f"✅ Total Execution Time: {total_time:.3f}s")
    
    print("\n" + "="*50)
    print("📊 OPENTELEMETRY TRACE ANALYSIS")
    print("="*50 + "\n")
    
    # Allow async span processors a moment to flush
    await asyncio.sleep(2)
    spans = exporter.get_finished_spans()
    
    # Analyze Models
    print("🧠 MODEL CALL LATENCY")
    model_count = 0
    for span in sorted(spans, key=lambda s: s.start_time):
        if "gen_ai.request.model" in span.attributes and "token" not in span.name.lower():
            model_count += 1
            duration = (span.end_time - span.start_time) / 1e9
            model = span.attributes["gen_ai.request.model"]
            print(f"  - Call {model_count} ({model}): {duration:.3f}s")
    
    # Analyze Tools
    print("\n🛠️ TOOL EXECUTION LATENCY")
    for span in sorted(spans, key=lambda s: s.start_time):
        if "gen_ai.tool.name" in span.attributes:
            duration = (span.end_time - span.start_time) / 1e9
            tool_name = span.attributes["gen_ai.tool.name"]
            print(f"  - Tool '{tool_name}': {duration:.3f}s")
            
    # Analyze Agents and Token Usage
    print("\n🤖 AGENT LATENCY & TOKEN USAGE")
    agent_stats = {}
    for span in sorted(spans, key=lambda s: s.start_time):
        attrs = span.attributes or {}
        if "gen_ai.agent.name" in attrs:
            agent_name = attrs["gen_ai.agent.name"]
            
            if agent_name not in agent_stats:
                agent_stats[agent_name] = {
                    "start_time": span.start_time, 
                    "end_time": span.end_time, 
                    "usage": {}
                }
                
            # Expand the time window to encompass all spans for this agent
            current_start = agent_stats[agent_name]["start_time"]
            current_end = agent_stats[agent_name]["end_time"]
            
            s_time = int(span.start_time) if span.start_time else current_start
            e_time = int(span.end_time) if span.end_time else current_end
            
            agent_stats[agent_name]["start_time"] = min(current_start, s_time)
            agent_stats[agent_name]["end_time"] = max(current_end, e_time)
            
            # Aggregate tokens from model calls inside this agent
            for k, v in attrs.items():
                if k.startswith("gen_ai.usage."):
                    metric_name = k.replace("gen_ai.usage.", "")
                    agent_stats[agent_name]["usage"][metric_name] = agent_stats[agent_name]["usage"].get(metric_name, 0) + v
                
    for agent, stats in agent_stats.items():
        dur_s = (stats["end_time"] - stats["start_time"]) / 1e9
        print(f"  - Agent '{agent}':")
        print(f"      Time Spent: {dur_s:.3f}s")
        for metric, val in stats["usage"].items():
            print(f"      {metric}: {val:,}")
        
    print("\n✅ Performance Test Completed Successfully.")

if __name__ == "__main__":
    asyncio.run(run_test())
