from pathlib import Path

import pytest

from trading_system.backtest.dataset_loader import load_candle_dataset


def test_missing_dataset_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_candle_dataset(tmp_path / "missing.parquet")
