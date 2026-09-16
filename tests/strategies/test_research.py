import pytest

from trading_system.strategies.research import fit_and_freeze


class DummyStrategy:
    name = "dummy"

    def __init__(self, data):
        self.data = data

    @classmethod
    def fit(cls, training_data):
        return cls(tuple(training_data))

    def freeze(self):
        return self

    def generate_signal(self, context):
        raise NotImplementedError


def test_fit_and_freeze_uses_training_data_only() -> None:
    strategy = fit_and_freeze(DummyStrategy, (1, 2, 3))
    assert strategy.data == (1, 2, 3)


def test_fit_and_freeze_rejects_empty_training_data() -> None:
    with pytest.raises(ValueError, match="training_data"):
        fit_and_freeze(DummyStrategy, ())
