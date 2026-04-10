"""Simulation Controller Agent definition.

Exports root_agent for use by the executor and local server.
"""

import logging

# Set the package-level log level to DEBUG
logging.getLogger(__package__).setLevel(logging.DEBUG)

from .agent import root_agent, app


__all__ = ["root_agent", "app"]
