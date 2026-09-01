"""Pure sequence-level validation for canonical candles."""

from datetime import timedelta

from ..models import Candle, Timeframe
from .models import AnomalySeverity, ValidationAnomaly, ValidationReport, ValidationStatus
from .record import RecordValidator


_TIMEFRAME_DELTAS = {
    Timeframe.M1: timedelta(minutes=1),
    Timeframe.M5: timedelta(minutes=5),
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.H4: timedelta(hours=4),
    Timeframe.D1: timedelta(days=1),
}


class SequenceValidator:
    """Validate continuity, ordering, and duplicate identity without repairing data."""

    def __init__(self, record_validator: RecordValidator | None = None) -> None:
        self._record_validator = record_validator or RecordValidator()

    def validate(self, candles: list[Candle] | tuple[Candle, ...]) -> ValidationReport:
        anomalies: list[ValidationAnomaly] = []
        invalid_records = 0
        duplicate_count = 0
        gap_count = 0
        out_of_order_count = 0
        seen: set[tuple[str, str, str, object]] = set()

        for index, candle in enumerate(candles):
            record_anomalies = self._record_validator.validate(candle, index=index)
            errors = tuple(a for a in record_anomalies if a.severity == AnomalySeverity.ERROR)
            if errors:
                invalid_records += 1
                anomalies.extend(record_anomalies)
            else:
                anomalies.extend(record_anomalies)

            identity = (
                candle.instrument.exchange,
                candle.instrument.symbol,
                candle.timeframe.value,
                candle.open_time,
            )
            if identity in seen:
                duplicate_count += 1
                anomalies.append(
                    ValidationAnomaly(
                        code="DUPLICATE_CANDLE",
                        severity=AnomalySeverity.ERROR,
                        message="Candle identity has already appeared in the sequence.",
                        index=index,
                    )
                )
                invalid_records += 1
            else:
                seen.add(identity)

            if index == 0:
                continue

            previous = candles[index - 1]
            if candle.open_time < previous.open_time:
                out_of_order_count += 1
                anomalies.append(
                    ValidationAnomaly(
                        code="OUT_OF_ORDER",
                        severity=AnomalySeverity.ERROR,
                        message="Candle open time is earlier than the preceding candle.",
                        index=index,
                    )
                )
                invalid_records += 1
                continue

            expected = previous.open_time + _TIMEFRAME_DELTAS[previous.timeframe]
            if candle.open_time != expected:
                gap_count += 1
                anomalies.append(
                    ValidationAnomaly(
                        code="MISSING_INTERVAL",
                        severity=AnomalySeverity.WARNING,
                        message="Candle sequence is not continuous at this boundary.",
                        index=index,
                        context={
                            "expected_open_time": expected.isoformat(),
                            "actual_open_time": candle.open_time.isoformat(),
                        },
                    )
                )

        status = ValidationStatus.FAIL if any(
            a.severity == AnomalySeverity.ERROR for a in anomalies
        ) else ValidationStatus.WARNING if anomalies else ValidationStatus.PASS

        return ValidationReport(
            status=status,
            records_checked=len(candles),
            valid_records=len(candles) - invalid_records,
            invalid_records=invalid_records,
            duplicate_count=duplicate_count,
            gap_count=gap_count,
            out_of_order_count=out_of_order_count,
            anomalies=tuple(anomalies),
        )
