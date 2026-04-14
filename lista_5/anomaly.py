import logging
from dataclasses import dataclass
from typing import Optional

SPIKE_THRESHOLDS: dict[str, float] = {
    "PM10":  500.0,
    "PM2.5": 200.0,
    "SO2":   500.0,
    "NO2":   400.0,
    "NO":    600.0,
    "NOX":   600.0,
    "O3":    300.0,
    "CO":    30_000.0,
    "C6H6":  50.0,
}

DEFAULT_DELTA_THRESHOLD = 200.0
DEFAULT_MAX_ZERO_STREAK = 5

@dataclass
class Measurement:
    time: str
    value: Optional[float]
    station: str
    quantity: str

@dataclass
class Anomaly:
    measurement: Measurement
    reason: str

def detect_anomalies(measurements: list[Measurement],delta_threshold: float = DEFAULT_DELTA_THRESHOLD,max_zero_streak: int = DEFAULT_MAX_ZERO_STREAK) -> list[Anomaly]:
    if not measurements:
        logging.warning("detect_anomalies called with an empty measurement list.")
        return []

    quantity = measurements[0].quantity.upper()
    spike_limit: Optional[float] = SPIKE_THRESHOLDS.get(quantity)

    anomalies: list[Anomaly] = []
    prev_valid: Optional[float] = None
    zero_streak = 0

    for m in measurements:
        val = m.value
        if val is None or val < 0 or val == 0.0:
            zero_streak += 1
            if zero_streak == max_zero_streak + 1:
                anomalies.append(Anomaly(
                    m,
                    f"Zero/None/negative streak exceeded {max_zero_streak} consecutive bad values – possible sensor failure"
                ))
            continue

        zero_streak = 0

        if prev_valid is not None:
            delta = abs(val - prev_valid)
            if delta > delta_threshold:
                anomalies.append(Anomaly(
                    m,
                    f"Sudden jump: |{val:.2f} - {prev_valid:.2f}| = {delta:.2f} > threshold {delta_threshold}"
                ))

        if spike_limit is not None and val > spike_limit:
            anomalies.append(Anomaly(
                m,
                f"Spike above alarm threshold: {val:.2f} > {spike_limit} ({quantity})"
            ))

        prev_valid = val

    return anomalies