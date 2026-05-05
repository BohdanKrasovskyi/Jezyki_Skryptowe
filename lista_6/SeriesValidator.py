import statistics
from abc import ABC, abstractmethod
from TimeSeries import TimeSeries


class SeriesValidator(ABC):

    @abstractmethod
    def analyze(self, series: TimeSeries) -> list:
        pass


class MeanValidator(SeriesValidator):

    def __init__(self, threshold: float):
        self.threshold = threshold

    def analyze(self, series: TimeSeries) -> list:
        values = [x for x in series.measurement if x is not None]
        if not values:
            return []
        mean = statistics.mean(values)
        if mean > self.threshold:
            return [
                f"Warning: {series.name_of_indicator} at {series.code_of_station} "
                f"has mean = {mean:.2f} {series.unit_of_measurement} > threshold {self.threshold}"
            ]
        return []


class AnomalyValidator(SeriesValidator):

    def __init__(self, max_value: float):
        self.max_value = max_value

    def analyze(self, series: TimeSeries) -> list:
        anomalies = []
        for date, value in zip(series.list_of_dates, series.measurement):
            if value is not None and value > self.max_value:
                anomalies.append(
                    f"Anomaly: {series.name_of_indicator} at {series.code_of_station} "
                    f"on {date} = {value:.2f} {series.unit_of_measurement} > max {self.max_value}"
                )
        return anomalies


class MissingDataValidator(SeriesValidator):
    def __init__(self, max_missing_pct: float = 10.0):
        self.max_missing_pct = max_missing_pct

    def analyze(self, series: TimeSeries) -> list:
        total = len(series.measurement)
        if total == 0:
            return []
        missing = sum(1 for x in series.measurement if x is None)
        pct = missing / total * 100
        if pct > self.max_missing_pct:
            return [
                f"Warning: {series.name_of_indicator} at {series.code_of_station} "
                f"has {pct:.1f}% missing data (limit: {self.max_missing_pct}%)"
            ]
        return []