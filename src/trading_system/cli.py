from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .data.acquisition.binance import BinanceKlineClient
from .data.acquisition.service import acquire_to_parquet
from .data.models import Instrument, MarketType, Timeframe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trading_system")
    subparsers = parser.add_subparsers(dest="command", required=True)

    acquire = subparsers.add_parser("acquire", help="Acquire historical spot candles")
    acquire.add_argument("--exchange", choices=["binance"], required=True)
    acquire.add_argument("--symbol", required=True, help="Exchange symbol, e.g. BTCUSDT")
    acquire.add_argument("--timeframe", choices=[t.value for t in Timeframe], required=True)
    acquire.add_argument("--start", required=True, help="UTC ISO-8601 datetime")
    acquire.add_argument("--end", required=True, help="UTC ISO-8601 datetime")
    acquire.add_argument("--output", required=True, type=Path)
    acquire.set_defaults(handler=_run_acquire)
    return parser


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("datetime must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("datetime must include a UTC offset")
    return parsed


def _run_acquire(args: argparse.Namespace) -> int:
    start = _parse_utc(args.start)
    end = _parse_utc(args.end)
    if start.utcoffset().total_seconds() != 0 or end.utcoffset().total_seconds() != 0:
        raise SystemExit("--start and --end must use UTC")
    if end <= start:
        raise SystemExit("--end must be after --start")

    symbol = args.symbol.upper()
    if not symbol.endswith("USDT"):
        raise SystemExit("v1 supports USDT-quoted spot instruments only")

    instrument = Instrument(
        symbol=symbol,
        base_asset=symbol[:-4],
        quote_asset="USDT",
        market_type=MarketType.SPOT,
        exchange=args.exchange,
    )
    timeframe = Timeframe(args.timeframe)
    manifest = acquire_to_parquet(
        provider=BinanceKlineClient(),
        instrument=instrument,
        timeframe=timeframe,
        start=start,
        end=end,
        destination=args.output,
    )
    print(manifest.model_dump_json(indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
