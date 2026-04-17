"""Schemas for the {{AGENT_DISPLAY_NAME}}.

Defines structured output formats used by this agent.
Kept local to simplify Agent Engine deployment (no cross-package imports).
"""

from pydantic import BaseModel, Field


# TODO: Define your Pydantic models for structured output.
# These models define the JSON schema that the LLM must conform to.
#
# Example:
#
# class MyOutputSchema(BaseModel):
#     """Structured output from the agent."""
#
#     status: str = Field(description="Current status")
#     result: str = Field(description="The main result")
#     confidence: float = Field(ge=0, le=1, description="Confidence score")


class MyOutputSchema(BaseModel):
    """TODO: Rename this class and define your output fields."""

    result: str = Field(description="TODO: Define your output fields")
