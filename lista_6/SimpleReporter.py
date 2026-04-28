import statistics
from TimeSeries import TimeSeries


class SimpleReporter:
    def analyze(self, series: TimeSeries) -> list:
        values = [x for x in series.measurement if x is not None]
        if not values:
            return [
                f"Info: {series.name_of_indicator} at {series.code_of_station} has no data"
            ]
        mean = statistics.mean(values)
        return [
            f"Info: {series.name_of_indicator} at {series.code_of_station} "
            f"has mean = {mean:.2f} {series.unit_of_measurement}"
        ]