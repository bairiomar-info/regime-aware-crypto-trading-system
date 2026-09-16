from pathlib import Path

import pytest

from trading_system.backtest.dataset_loader import load_candle_dataset


def test_missing_dataset_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_candle_dataset(tmp_path / "missing.parquet")


def test_empty_dataset_is_rejected(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    import pyarrow as pa
    import pyarrow.parquet as parquet

    target = tmp_path / "empty.parquet"
    parquet.write_table(pa.table({"open_time": pa.array([], type=pa.timestamp("us"))}), target)

    with pytest.raises(ValueError, match="must not be empty"):
        load_candle_dataset(target)
