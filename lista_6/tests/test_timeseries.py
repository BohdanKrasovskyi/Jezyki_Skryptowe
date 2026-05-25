import pytest
import datetime
from TimeSeries import TimeSeries

#ZAD 3B
def test_getitem_integer_index():
    dates = [datetime.date(2024, 9, 16),
             datetime.date(2023, 1, 1),
             datetime.date(2026, 12, 31)]
    measurements = [2.2, None, -1.221]
    ts = TimeSeries("SO2", "DsSniezkaObs",
               "24g", dates, measurements, "ug/m3")
    first = datetime.date(2024, 9, 16), 2.2
    second = datetime.date(2023, 1, 1), None
    third = datetime.date(2026, 12, 31), -1.221

    assert ts[0] == first
    assert ts[1] == second
    assert ts[2] == third
    assert ts[-1] == third

def test_getitem_slice():
    dates = [datetime.date(2024, 9, 16),
             datetime.date(2023, 1, 1),
             datetime.date(2026, 12, 31)]
    measurements = [2.2, None, -1.221]
    ts = TimeSeries("SO2", "DsSniezkaObs",
                    "24g", dates, measurements, "ug/m3")
    first = datetime.date(2024, 9, 16), 2.2
    second = datetime.date(2023, 1, 1), None
    third = datetime.date(2026, 12, 31), -1.221

    assert ts[0:3] == [first, second, third]
    assert ts[1:3] == [second, third]
    assert ts[:2] == [first, second]

def test_getitem_existing_datetime():
    dates = [datetime.date(2026, 1,1)]
    measurements = [2.2]
    ts = TimeSeries("SO2", "DsSniezkaObs",
                    "24g", dates, measurements, "ug/m3")

    assert ts[datetime.date(2026, 1, 1)] == [(datetime.date(2026, 1, 1), 2.2)]

def test_getitem_nonexisting_datetime():
    dates = [datetime.date(2026, 1,1)]
    measurements = [2.2]
    ts = TimeSeries("SO2", "DsSniezkaObs",
                    "24g", dates, measurements, "ug/m3")

    with pytest.raises(KeyError):
        ts[datetime.date(2026, 1, 2)]

#ZAD3c
def test_mean_complete_data():
    measurements = [30.0, 10.0, 20.0]
    dates = [datetime.date(2026, 1, 1)]
    ts = TimeSeries("SO2", "DsSniezkaObs",
                    "24g", dates, measurements, "ug/m3")

    assert ts.mean == 20.0

def test_stddev_complete_data():
    measurements = [30.0, 10.0, 20.0]
    dates = [datetime.date(2026, 1, 1)]
    ts = TimeSeries("SO2", "DsSniezkaObs",
                    "24g", dates, measurements, "ug/m3")

    assert ts.stddev == 10.0

def test_mean_with_none():
    measurements = [5.0, 7.0, None, 12.0, None]
    dates = [datetime.date(2026, 1, 1)]
    ts = TimeSeries("SO2", "DsSniezkaObs",
                    "24g", dates, measurements, "ug/m3")

    assert ts.mean == 8.0

def test_stddev_with_none():
    measurements = [5.0, 7.0, None, 9.0, None]
    dates = [datetime.date(2026, 1, 1)]
    ts = TimeSeries("SO2", "DsSniezkaObs",
                    "24g", dates, measurements, "ug/m3")

    assert ts.stddev == 2.0