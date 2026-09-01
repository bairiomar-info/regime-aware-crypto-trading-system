from pydantic import BaseModel, ConfigDict, Field


class SystemConfig(BaseModel):
    """Top-level configuration for the trading system."""

    model_config = ConfigDict(extra="forbid")

    name: str = "regime-aware-crypto-trading-system"
    version: str = "0.1.0"

    long_only: bool = True
    spot_only: bool = True
    shariah_compliant: bool = True

    initial_capital: float = Field(default=1000.0, gt=0)
