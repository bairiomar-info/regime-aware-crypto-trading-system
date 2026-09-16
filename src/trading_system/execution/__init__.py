"""Execution-layer safety boundaries and broker contracts."""

from .broker import Broker, BrokerFill
from .gate import PreTradeConfig, validate_pre_trade
from .paper import PaperExecutionResult, PaperFill, execute_paper_order
from .service import execute_order

__all__ = [
    "Broker",
    "BrokerFill",
    "PaperExecutionResult",
    "PaperFill",
    "PreTradeConfig",
    "execute_order",
    "execute_paper_order",
    "validate_pre_trade",
]
