import datetime
import statistics
from datetime import date
from uuid import UUID
from typing import List

class TimeSeries:
    def __init__(self, name_of_indicator : str, code_of_station : str, averaging_time : str,
                list_of_dates : List[date], measurement : List[float | None],
                unit_of_measurement : str) -> None:
        self.name_of_indicator = name_of_indicator
        self.code_of_station = code_of_station
        self.averaging_time = averaging_time
        self.list_of_dates = list_of_dates
        self.measurement = measurement
        self.unit_of_measurement = unit_of_measurement

    @property
    def median(self) -> float | None:
        if not self.list_of_dates:
            return None
        measurement_clear = [x for x in self.measurement if x != None]
        measurement_clear.sort()
        if not measurement_clear:
            return None
        return statistics.median(measurement_clear)

    @property
    def range(self) -> tuple[float, float] | None:
        if not self.list_of_dates:
            return None
        measurement_clear = [x for x in self.measurement if x != None]
        if not measurement_clear:
            return None
        return max(measurement_clear), min(measurement_clear)

    def __getitem__(self, val) -> tuple[date, float | None] | List[tuple[date, float | None]]:
        if isinstance(val, slice):
            start, stop, step = val.start, val.stop, val.step
            if step is None:
                step = 1
            if start is None:
                start = 0
            if stop is None:
                stop = len(self.list_of_dates)
            ret = []
            for i in range(start, stop, step):
                ret.append((self.list_of_dates[i], self.measurement[i]))
            return ret
        if isinstance(val, int):
            return self.list_of_dates[val], self.measurement[val],
        if isinstance(val, datetime.date):
            ret = []
            for i in range(0, len(self.list_of_dates)):
                if self.list_of_dates[i] == val:
                    ret.append((self.list_of_dates[i], self.measurement[i]))
            if not ret:
                raise KeyError
            return ret
        raise TypeError