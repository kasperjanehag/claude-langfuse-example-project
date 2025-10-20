"""
Agent SDK - An example system demonstrating eval-driven development for receipt inspection.
"""

__version__ = "0.1.0"

from agent_sdk.agents.receipt_inspection import ReceiptInspectionAgent
from agent_sdk.utils.config import Config

__all__ = ["ReceiptInspectionAgent", "Config"]
