import datetime
import pytest

from lista_6.TimeSeries import TimeSeries
from lista_6.SeriesValidator import (
    OutlierDetector, ZeroSpikeDetector, ThresholdDetector,
    MeanValidator, AnomalyValidator, MissingDataValidator,
)
from lista_6.SimpleReporter import SimpleReporter


def make_ts(measurements: list, indicator: str = "SO2", station: str = "StationX") -> TimeSeries:
    dates = [datetime.date(2026, 1, i + 1) for i in range(len(measurements))]
    return TimeSeries(indicator, station, "24g", dates, measurements, "ug/m3")



def test_outlier_detector_flags_outlier():
    ts = make_ts([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1000.0])
    result = OutlierDetector(k=2.0).analyze(ts)
    assert len(result) > 0


def test_outlier_detector_no_flag_within_bounds():
    ts = make_ts([10.0, 11.0, 12.0, 10.5, 11.5])
    result = OutlierDetector(k=2.0).analyze(ts)
    assert result == []


def test_outlier_detector_ignores_none():
    ts = make_ts([1.0, None, 1.0, 1.0, 1.0, 1.0, 1000.0])
    result = OutlierDetector(k=2.0).analyze(ts)
    assert len(result) > 0


def test_outlier_detector_single_value_returns_empty():
    ts = make_ts([42.0])
    result = OutlierDetector(k=2.0).analyze(ts)
    assert result == []


def test_outlier_detector_all_none_returns_empty():
    ts = make_ts([None, None, None])
    result = OutlierDetector(k=2.0).analyze(ts)
    assert result == []


def test_outlier_detector_uniform_values_no_std():
    # std == 0, so nothing should be flagged
    ts = make_ts([5.0, 5.0, 5.0, 5.0])
    result = OutlierDetector(k=1.0).analyze(ts)
    assert result == []


def test_outlier_detector_message_contains_indicator_and_station():
    ts = make_ts([1.0, 1.0, 1.0, 1.0, 1.0, 1000.0], indicator="PM10", station="ABC")
    result = OutlierDetector(k=1.0).analyze(ts)
    assert any("PM10" in msg and "ABC" in msg for msg in result)


def test_outlier_detector_high_k_no_flag():
    ts = make_ts([1.0, 1.0, 1.0, 1.0, 1.0, 1000.0])
    result = OutlierDetector(k=100.0).analyze(ts)
    assert result == []


def test_outlier_detector_flags_multiple_outliers():
    ts = make_ts([5.0, 5.0, 5.0, 5.0, 5.0, 1000.0, 2000.0])
    result = OutlierDetector(k=2.0).analyze(ts)
    assert len(result) == 2


# ZeroSpikeDetector

def test_zero_spike_detector_three_zeros():
    ts = make_ts([5.0, 0.0, 0.0, 0.0, 3.0])
    result = ZeroSpikeDetector().analyze(ts)
    assert len(result) > 0


def test_zero_spike_detector_three_nones():
    ts = make_ts([5.0, None, None, None, 3.0])
    result = ZeroSpikeDetector().analyze(ts)
    assert len(result) > 0


def test_zero_spike_detector_mixed_zero_none():
    ts = make_ts([5.0, 0.0, None, 0.0, 3.0])
    result = ZeroSpikeDetector().analyze(ts)
    assert len(result) > 0


def test_zero_spike_detector_no_spike():
    ts = make_ts([5.0, 0.0, 0.0, 3.0])
    result = ZeroSpikeDetector().analyze(ts)
    assert result == []


def test_zero_spike_detector_exactly_threshold():
    ts = make_ts([1.0, 0.0, 0.0, 0.0])
    result = ZeroSpikeDetector(consecutive=3).analyze(ts)
    assert len(result) > 0


def test_zero_spike_detector_custom_consecutive_4():
    ts = make_ts([1.0, 0.0, 0.0, 0.0, 1.0])
    result = ZeroSpikeDetector(consecutive=4).analyze(ts)
    assert result == []


def test_zero_spike_detector_all_zeros():
    ts = make_ts([0.0, 0.0, 0.0, 0.0, 0.0])
    result = ZeroSpikeDetector(consecutive=3).analyze(ts)
    assert len(result) > 0


def test_zero_spike_detector_empty_series():
    ts = make_ts([])
    result = ZeroSpikeDetector().analyze(ts)
    assert result == []


def test_zero_spike_detector_message_contains_station():
    ts = make_ts([5.0, 0.0, 0.0, 0.0, 3.0], station="ZZZ")
    result = ZeroSpikeDetector().analyze(ts)
    assert any("ZZZ" in msg for msg in result)



def test_threshold_detector_flags_exceeded():
    ts = make_ts([1.0, 2.0, 50.0, 1.5])
    result = ThresholdDetector(threshold=10.0).analyze(ts)
    assert len(result) > 0


def test_threshold_detector_no_flag_below():
    ts = make_ts([1.0, 2.0, 5.0, 1.5])
    result = ThresholdDetector(threshold=10.0).analyze(ts)
    assert result == []


def test_threshold_detector_ignores_none():
    ts = make_ts([None, None, 5.0])
    result = ThresholdDetector(threshold=3.0).analyze(ts)
    assert len(result) > 0


def test_threshold_detector_exact_threshold_not_flagged():
    ts = make_ts([10.0])
    result = ThresholdDetector(threshold=10.0).analyze(ts)
    assert result == []


def test_threshold_detector_flags_multiple():
    ts = make_ts([100.0, 200.0, 1.0])
    result = ThresholdDetector(threshold=50.0).analyze(ts)
    assert len(result) == 2


def test_threshold_detector_all_none_returns_empty():
    ts = make_ts([None, None, None])
    result = ThresholdDetector(threshold=0.0).analyze(ts)
    assert result == []


def test_threshold_detector_message_contains_value():
    ts = make_ts([99.9])
    result = ThresholdDetector(threshold=10.0).analyze(ts)
    assert any("99.90" in msg for msg in result)




def test_mean_validator_flags_high_mean():
    ts = make_ts([20.0, 30.0, 25.0])
    result = MeanValidator(threshold=10.0).analyze(ts)
    assert len(result) > 0


def test_mean_validator_no_flag_low_mean():
    ts = make_ts([1.0, 2.0, 3.0])
    result = MeanValidator(threshold=100.0).analyze(ts)
    assert result == []


def test_mean_validator_ignores_none():
    ts = make_ts([None, 20.0, None, 30.0])
    result = MeanValidator(threshold=10.0).analyze(ts)
    assert len(result) > 0


def test_mean_validator_all_none_returns_empty():
    ts = make_ts([None, None])
    result = MeanValidator(threshold=5.0).analyze(ts)
    assert result == []


def test_mean_validator_message_contains_mean():
    ts = make_ts([10.0, 20.0])
    result = MeanValidator(threshold=5.0).analyze(ts)
    assert any("15.00" in msg for msg in result)


def test_mean_validator_exact_threshold_not_flagged():
    ts = make_ts([10.0])
    result = MeanValidator(threshold=10.0).analyze(ts)
    assert result == []


# ---------------------------------------------------------------------------
# AnomalyValidator
# ---------------------------------------------------------------------------

def test_anomaly_validator_flags_above_max():
    ts = make_ts([1.0, 5.0, 200.0])
    result = AnomalyValidator(max_value=100.0).analyze(ts)
    assert len(result) > 0


def test_anomaly_validator_no_flag_below_max():
    ts = make_ts([1.0, 5.0, 50.0])
    result = AnomalyValidator(max_value=100.0).analyze(ts)
    assert result == []


def test_anomaly_validator_ignores_none():
    ts = make_ts([None, 200.0, None])
    result = AnomalyValidator(max_value=100.0).analyze(ts)
    assert len(result) > 0


def test_anomaly_validator_exact_max_not_flagged():
    ts = make_ts([100.0])
    result = AnomalyValidator(max_value=100.0).analyze(ts)
    assert result == []


def test_anomaly_validator_flags_multiple():
    ts = make_ts([500.0, 600.0, 5.0])
    result = AnomalyValidator(max_value=100.0).analyze(ts)
    assert len(result) == 2


def test_anomaly_validator_message_contains_date():
    ts = make_ts([999.0])
    result = AnomalyValidator(max_value=10.0).analyze(ts)
    assert any("2026-01-01" in msg for msg in result)


# ---------------------------------------------------------------------------
# MissingDataValidator
# ---------------------------------------------------------------------------

def test_missing_data_validator_flags_too_many_missing():
    ts = make_ts([None, None, None, None, 1.0])  # 80% missing
    result = MissingDataValidator(max_missing_pct=10.0).analyze(ts)
    assert len(result) > 0


def test_missing_data_validator_no_flag_within_limit():
    ts = make_ts([1.0, 2.0, None, 4.0, 5.0])  # 20% missing
    result = MissingDataValidator(max_missing_pct=50.0).analyze(ts)
    assert result == []


def test_missing_data_validator_empty_series():
    ts = make_ts([])
    result = MissingDataValidator(max_missing_pct=10.0).analyze(ts)
    assert result == []


def test_missing_data_validator_no_missing():
    ts = make_ts([1.0, 2.0, 3.0])
    result = MissingDataValidator(max_missing_pct=10.0).analyze(ts)
    assert result == []


def test_missing_data_validator_all_missing():
    ts = make_ts([None, None, None])
    result = MissingDataValidator(max_missing_pct=10.0).analyze(ts)
    assert len(result) > 0


def test_missing_data_validator_message_contains_percentage():
    ts = make_ts([None, None, 1.0, 1.0])  # 50%
    result = MissingDataValidator(max_missing_pct=10.0).analyze(ts)
    assert any("50.0%" in msg for msg in result)


# ---------------------------------------------------------------------------
# SimpleReporter
# ---------------------------------------------------------------------------

def test_simple_reporter_returns_info_string():
    ts = make_ts([10.0, 20.0, 30.0])
    result = SimpleReporter().analyze(ts)
    assert len(result) == 1
    assert "Info" in result[0]


def test_simple_reporter_no_data():
    ts = make_ts([None, None])
    result = SimpleReporter().analyze(ts)
    assert len(result) == 1
    assert "no data" in result[0].lower()


def test_simple_reporter_mean_in_message():
    ts = make_ts([10.0, 20.0])
    result = SimpleReporter().analyze(ts)
    assert any("15.00" in msg for msg in result)


# ---------------------------------------------------------------------------
# duck-typing helper
# ---------------------------------------------------------------------------

def detect_all_anomalies(analyzers: list, series: TimeSeries) -> list[str]:
    results: list[str] = []
    for analyzer in analyzers:
        messages = analyzer.analyze(series)
        results.extend(messages)
    return results


SAMPLE_TS = make_ts([1.0, 1.1, 0.0, 0.0, 0.0, 200.0, 1.2])


@pytest.mark.parametrize("analyzer", [
    OutlierDetector(k=2.0),
    ZeroSpikeDetector(),
    ThresholdDetector(threshold=10.0),
    MeanValidator(threshold=1.0),
    AnomalyValidator(max_value=10.0),
    MissingDataValidator(max_missing_pct=0.0),
    SimpleReporter(),
])
def test_analyzer_returns_list_of_strings(analyzer):
    result = analyzer.analyze(SAMPLE_TS)
    messages = list(result)
    for msg in messages:
        assert isinstance(msg, str)
        assert len(msg) > 0


@pytest.mark.parametrize("analyzer", [
    OutlierDetector(k=2.0),
    ZeroSpikeDetector(),
    ThresholdDetector(threshold=10.0),
    SimpleReporter(),
])
def test_detect_all_anomalies_returns_list(analyzer):
    result = detect_all_anomalies([analyzer], SAMPLE_TS)
    messages = list(result)
    for msg in messages:
        assert len(msg) > 0


@pytest.mark.parametrize("analyzer,expect_nonempty", [
    (OutlierDetector(k=2.0), True),
    (ZeroSpikeDetector(), True),
    (ThresholdDetector(threshold=10.0), True),
    (SimpleReporter(), True),
])
def test_detect_all_anomalies_triggering_data(analyzer, expect_nonempty):
    result = detect_all_anomalies([analyzer], SAMPLE_TS)
    messages = list(result)
    if expect_nonempty:
        assert len(messages) > 0


def test_detect_all_anomalies_combined_detectors():
    ts = make_ts([1.0, 0.0, 0.0, 0.0, 500.0])
    analyzers = [
        ZeroSpikeDetector(),
        ThresholdDetector(threshold=10.0),
    ]
    result = detect_all_anomalies(analyzers, ts)
    assert len(result) >= 2


def test_detect_all_anomalies_empty_analyzer_list():
    ts = make_ts([1.0, 2.0, 3.0])
    result = detect_all_anomalies([], ts)
    assert result == []