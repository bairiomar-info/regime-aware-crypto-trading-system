from datetime import datetime, timezone
from decimal import Decimal

from trading_system.compliance.classification import AssetCompliance
from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.risk.models import RiskLimits
from trading_system.risk.pretrade import authorize_order


def order(symbol: str = "BTCUSDT") -> OrderIntent:
    return OrderIntent(symbol, OrderSide.BUY, Decimal("100"), "test")


def asset(symbol: str = "BTCUSDT", interest: str = "0") -> AssetCompliance:
    return AssetCompliance(symbol, Decimal(interest))


def limits() -> RiskLimits:
    return RiskLimits(max_position_weight=Decimal("0.5"), max_portfolio_exposure=Decimal("1"))


def test_pretrade_authorizes_compliant_order_within_risk_limits() -> None:
    result = authorize_order(order(), asset=asset(), target_weight=Decimal("0.4"), current_exposure=Decimal("0.1"), limits=limits())
    assert result.allowed is True
    assert result.reason == "authorized"


def test_pretrade_rejects_forbidden_symbol() -> None:
    result = authorize_order(order(), asset=asset(), target_weight=Decimal("0.1"), current_exposure=Decimal("0"), limits=limits(), forbidden_symbols=frozenset({"BTCUSDT"}))
    assert result.allowed is False
    assert result.reason == "forbidden_symbol"


def test_pretrade_rejects_non_compliant_asset() -> None:
    result = authorize_order(order(), asset=asset(interest="0.0501"), target_weight=Decimal("0.1"), current_exposure=Decimal("0"), limits=limits())
    assert result.allowed is False
    assert "interest-income" in result.reason


def test_pretrade_rejects_gambling_like_asset() -> None:
    result = authorize_order(order(), asset=AssetCompliance("BTCUSDT", Decimal("0"), gambling_like=True), target_weight=Decimal("0.1"), current_exposure=Decimal("0"), limits=limits())
    assert result.allowed is False
    assert result.reason == "asset is classified as gambling-like"


def test_pretrade_rejects_symbol_mismatch() -> None:
    result = authorize_order(order("BTCUSDT"), asset=asset("ETHUSDT"), target_weight=Decimal("0.1"), current_exposure=Decimal("0"), limits=limits())
    assert result.allowed is False
    assert result.reason == "asset_symbol_mismatch"


def test_pretrade_rejects_risk_limit() -> None:
    result = authorize_order(order(), asset=asset(), target_weight=Decimal("0.6"), current_exposure=Decimal("0"), limits=limits())
    assert result.allowed is False
    assert result.reason == "position_weight_limit"
