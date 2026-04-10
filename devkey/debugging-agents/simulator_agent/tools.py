import json
import logging
import time
import os
from opentelemetry import trace
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


def log_exceptions(func):
    """Decorator to log exceptions in tools using standard Python logging."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            span = trace.get_current_span()
            trace_prefix = ""
            extra = {}
            if span and span.get_span_context().is_valid:
                ctx = span.get_span_context()
                trace_id = format(ctx.trace_id, "032x")
                span_id = format(ctx.span_id, "016x")
                trace_prefix = f"[trace_id={trace_id} span_id={span_id}] "
                extra["logging.googleapis.com/trace"] = (
                    f"projects/{os.getenv('GCP_PROJECT_ID')}/traces/{trace_id}"
                )
                extra["logging.googleapis.com/spanId"] = span_id

            logger.exception(
                f"{trace_prefix}Exception captured in tool {func.__name__}", extra=extra
            )
            raise e

    return wrapper


_TELEMETRY_STORE = {}


def get_runner_telemetry(sector: str) -> str:
    """Retrieve raw telemetry data for runners.

    Args:
        sector: The sector to fetch data for.
    """
    runners = []

    # 4000 runners = ~368,000 tokens per call.
    # Turn 1 (368K), Turn 2 (736K), Turn 3 (1.1M - BREAKS CONTEXT LIMIT!)
    for i in range(4000):
        runners.append(
            {
                "id": f"{sector}-R-{i}",
                "pos": [40.71 + (i * 0.0001), -74.00 - (i * 0.0001)],
                "hr": 150 + (i % 30),
                "pace": f"0{7 + (i % 3)}:{(i % 60):02d}",
                "core_temp": 98.6 + (i % 4),
                "fluid_intake_ml": 200 + (i % 500),
                "device_status": "synced",
            }
        )

    _TELEMETRY_STORE[sector] = runners

    print(
        f"[💤 DEMO DELAY] Sleeping for 30 seconds to reset Vertex TPM quota after fetching {sector}..."
    )
    time.sleep(30)

    return json.dumps({"sector_id": sector, "raw_data": runners})


def analyze_medical_risk(sector_id: str) -> dict[str, Any]:
    """Analyze medical risk using data previously saved in the telemetry store."""
    data = _TELEMETRY_STORE.get(sector_id)

    if not data:
        return {"status": "error", "message": f"No data found for sector {sector_id}"}

    try:
        high_temp_count = sum(1 for r in data if r.get("core_temp", 0) > 101.0)
        return {
            "status": "success",
            "runners_analyzed": len(data),
            "high_risk_count": high_temp_count,
            "recommendation": (
                "Deploy rapid response carts"
                if high_temp_count > 500
                else "Maintain current posture"
            ),
            "density_warning": len(data) > 4000,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to analyze telemetry: {e}"}


def get_tools() -> list:
    return [
        log_exceptions(get_runner_telemetry),
        log_exceptions(analyze_medical_risk),
    ]
