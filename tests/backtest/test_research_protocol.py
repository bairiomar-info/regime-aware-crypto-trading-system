from trading_system.backtest.research_protocol import fit_and_freeze


class DummyStrategy:
    def fit(self, training_data: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(sorted(training_data))

    def freeze(self, fitted: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(fitted)


def test_fit_and_freeze_uses_training_data_only() -> None:
    assert fit_and_freeze(DummyStrategy(), (3, 1, 2)) == (1, 2, 3)
