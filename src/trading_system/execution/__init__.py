"""Execution-layer safety boundaries and broker contracts."""

from .broker import Broker, BrokerFill
from .gate import PreTradeConfig, validate_pre_trade
from .service import execute_order

__all__ = ["Broker", "BrokerFill", "PreTradeConfig", "execute_order", "validate_pre_trade"]
