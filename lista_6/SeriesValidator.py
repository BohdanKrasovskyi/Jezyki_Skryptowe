import statistics
from abc import ABC, abstractmethod
from TimeSeries import TimeSeries


class SeriesValidator(ABC):

    @abstractmethod
    def analyze(self, series: TimeSeries) -> list:
        pass


class MeanValidator(SeriesValidator):

    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    def analyze(self, series: TimeSeries) -> list:
        values: list[float] = [x for x in series.measurement if x is not None]
        if not values:
            return []
        mean: float = statistics.mean(values)
        if mean > self.threshold:
            return [
                f"Warning: {series.name_of_indicator} at {series.code_of_station} "
                f"has mean = {mean:.2f} {series.unit_of_measurement} > threshold {self.threshold}"
            ]
        return []


class AnomalyValidator(SeriesValidator):

    def __init__(self, max_value: float) -> None:
        self.max_value = max_value

    def analyze(self, series: TimeSeries) -> list:
        anomalies: list[str] = []
        for date, value in zip(series.list_of_dates, series.measurement):
            if value is not None and value > self.max_value:
                anomalies.append(
                    f"Anomaly: {series.name_of_indicator} at {series.code_of_station} "
                    f"on {date} = {value:.2f} {series.unit_of_measurement} > max {self.max_value}"
                )
        return anomalies


class MissingDataValidator(SeriesValidator):
    def __init__(self, max_missing_pct: float = 10.0) -> None:
        self.max_missing_pct = max_missing_pct

    def analyze(self, series: TimeSeries) -> list:
        total: int = len(series.measurement)
        if total == 0:
            return []
        missing: int = sum(1 for x in series.measurement if x is None)
        pct: float = missing / total * 100
        if pct > self.max_missing_pct:
            return [
                f"Warning: {series.name_of_indicator} at {series.code_of_station} "
                f"has {pct:.1f}% missing data (limit: {self.max_missing_pct}%)"
            ]
        return []


class OutlierDetector(SeriesValidator):
    def __init__(self, k: float = 3.0) -> None:
        self.k = k

    def analyze(self, series: TimeSeries) -> list:
        values: list[float] = [x for x in series.measurement if x is not None]
        if len(values) < 2:
            return []
        mean: float = statistics.mean(values)
        std: float = statistics.stdev(values)
        if std == 0:
            return []
        anomalies: list[str] = []
        for date, value in zip(series.list_of_dates, series.measurement):
            if value is not None and abs(value - mean) > self.k * std:
                anomalies.append(
                    f"Outlier: {series.name_of_indicator} at {series.code_of_station} "
                    f"on {date} = {value:.2f} {series.unit_of_measurement} "
                    f"(>{self.k} std from mean {mean:.2f})"
                )
        return anomalies


class ZeroSpikeDetector(SeriesValidator):
    def __init__(self, consecutive: int = 3) -> None:
        self.consecutive = consecutive

    def analyze(self, series: TimeSeries) -> list:
        anomalies: list[str] = []
        count: int = 0
        spike_start: int | None = None
        for i, value in enumerate(series.measurement):
            if value is None or value == 0:
                if count == 0:
                    spike_start = i
                count += 1
                if count == self.consecutive:
                    anomalies.append(
                        f"ZeroSpike: {series.name_of_indicator} at {series.code_of_station} "
                        f"has {self.consecutive} consecutive zero/None values "
                        f"starting at index {spike_start}"
                    )
            else:
                count = 0
                spike_start = None
        return anomalies


class ThresholdDetector(SeriesValidator):
    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    def analyze(self, series: TimeSeries) -> list:
        anomalies: list[str] = []
        for date, value in zip(series.list_of_dates, series.measurement):
            if value is not None and value > self.threshold:
                anomalies.append(
                    f"Threshold exceeded: {series.name_of_indicator} at {series.code_of_station} "
                    f"on {date} = {value:.2f} {series.unit_of_measurement} > {self.threshold}"
                )
        return anomalies