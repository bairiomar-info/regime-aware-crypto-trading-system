"""Pure validation of individual canonical candles."""

from .models import AnomalySeverity, ValidationAnomaly
from ..models import Candle


class RecordValidator:
    """Validate canonical Candle objects without mutating or repairing them."""

    def validate(self, candle: Candle, *, index: int | None = None) -> tuple[ValidationAnomaly, ...]:
        """Return anomalies found in a candle.

        Construction of ``Candle`` already enforces its structural invariants.
        This validator exists as the explicit pipeline boundary and records
        research-policy checks that are not appropriate for the domain model.
        """
        anomalies: list[ValidationAnomaly] = []

        if not candle.is_closed:
            anomalies.append(
                ValidationAnomaly(
                    code="FORMING_CANDLE",
                    severity=AnomalySeverity.WARNING,
                    message="Candle is not finalized.",
                    index=index,
                )
            )

        return tuple(anomalies)
