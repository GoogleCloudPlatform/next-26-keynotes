# Dockerfile for Planner Agent on Cloud Run
#
# Builds an A2A server that orchestrates agents using Gemini 3 Flash Preview.
#
# Usage:
#   docker build -t planner-agent -f src/planner_agent/Dockerfile .
#   docker run -p 8080:8080 planner-agent

FROM python:3.11-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy project files (README.md required by hatchling build)
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen --no-dev

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_GENAI_USE_VERTEXAI=true

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/.well-known/agent.json || exit 1

# Run the application using uvicorn with the ASGI app
# Use --no-sync to skip dependency resolution (already done in build)
CMD ["uv", "run", "--no-sync", "uvicorn", "src.planner_agent.main:app", "--host", "0.0.0.0", "--port", "8080"]
