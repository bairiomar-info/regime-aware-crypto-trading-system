from trading_system.strategies import FittableResearchStrategy


class CompatibleStrategy:
    name = "compatible"

    @classmethod
    def fit(cls, training_data):
        return cls()

    def freeze(self):
        return self

    def generate_signal(self, context):
        raise NotImplementedError


def test_fittable_protocol_is_runtime_checkable() -> None:
    assert isinstance(CompatibleStrategy(), FittableResearchStrategy)
