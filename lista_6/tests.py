import unittest
from datetime import date

from Station import Station
from TimeSeries import TimeSeries
from SeriesValidator import MeanValidator, AnomalyValidator, MissingDataValidator
from SimpleReporter import SimpleReporter


def make_series(values: list, name="PM10", station="TestStation", unit="ug/m3"):
    dates = [date(2024, 1, i + 1) for i in range(len(values))]
    return TimeSeries(
        name_of_indicator=name,
        code_of_station=station,
        averaging_time="24g",
        list_of_dates=dates,
        measurement=values,
        unit_of_measurement=unit,
    )

class TestStation(unittest.TestCase):

    def setUp(self):
        self.s1 = Station("DsSniezka", "Śnieżka", "ul. Główna 1",
                          "tlo", date(2010, 1, 1), date(2023, 12, 31))
        self.s2 = Station("DsSniezka", "Inna nazwa", "ul. Boczna 2",
                          "miejska", date(2015, 6, 1), date(2022, 1, 1))
        self.s3 = Station("DsBialka", "Białka", "ul. Polna 5",
                          "tlo", date(2012, 3, 15), date(2024, 1, 1))

    def test_eq_same_code(self):
        self.assertEqual(self.s1, self.s2)

    def test_eq_different_code(self):
        self.assertNotEqual(self.s1, self.s3)

    def test_eq_non_station(self):
        self.assertNotEqual(self.s1, "DsSniezka")



class TestTimeSeriesProperties(unittest.TestCase):

    def test_median_odd(self):
        ts = make_series([10.0, 20.0, 30.0])
        self.assertAlmostEqual(ts.median, 20.0)


    def test_median_with_none(self):
        ts = make_series([None, 10.0, None, 30.0])
        self.assertAlmostEqual(ts.median, 20.0)

    def test_median_empty(self):
        ts = make_series([])
        self.assertIsNone(ts.median)

    def test_range_returns_max_min(self):
        ts = make_series([5.0, 15.0, 3.0, 10.0])
        self.assertEqual(ts.range, (15.0, 3.0))

    def test_range_empty(self):
        ts = make_series([])
        self.assertIsNone(ts.range)



class TestTimeSeriesGetitem(unittest.TestCase):

    def setUp(self):
        self.ts = make_series([1.0, 2.0, 3.0, 4.0, 5.0])


    def test_getitem_slice(self):
        result = self.ts[1:3]
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][1], 2.0)
        self.assertEqual(result[1][1], 3.0)


    def test_getitem_wrong_type(self):
        with self.assertRaises(TypeError):
            _ = self.ts["klucz"]


class TestMeanValidator(unittest.TestCase):

    def test_mean_exceeds_threshold(self):
        ts = make_series([50.0, 60.0, 70.0])
        validator = MeanValidator(threshold=40.0)
        result = validator.analyze(ts)
        self.assertEqual(len(result), 1)
        self.assertIn("mean", result[0])

    def test_mean_below_threshold(self):
        ts = make_series([10.0, 15.0, 20.0])
        validator = MeanValidator(threshold=50.0)
        result = validator.analyze(ts)
        self.assertEqual(result, [])

    def test_mean_empty_series(self):
        ts = make_series([])
        validator = MeanValidator(threshold=10.0)
        self.assertEqual(validator.analyze(ts), [])


class TestAnomalyValidator(unittest.TestCase):

    def test_detects_anomalies(self):
        ts = make_series([10.0, 100.0, 5.0, 200.0])
        validator = AnomalyValidator(max_value=50.0)
        result = validator.analyze(ts)
        self.assertEqual(len(result), 2)

    def test_no_anomalies(self):
        ts = make_series([10.0, 20.0, 30.0])
        validator = AnomalyValidator(max_value=100.0)
        self.assertEqual(validator.analyze(ts), [])

    def test_ignores_none(self):
        ts = make_series([None, 200.0, None])
        validator = AnomalyValidator(max_value=50.0)
        result = validator.analyze(ts)
        self.assertEqual(len(result), 1)


class TestMissingDataValidator(unittest.TestCase):

    def test_high_missing_rate(self):
        ts = make_series([None, None, None, 1.0])
        validator = MissingDataValidator(max_missing_pct=50.0)
        result = validator.analyze(ts)
        self.assertEqual(len(result), 1)
        self.assertIn("missing", result[0])

    def test_low_missing_rate(self):
        ts = make_series([1.0, 2.0, None, 4.0])
        validator = MissingDataValidator(max_missing_pct=50.0)
        self.assertEqual(validator.analyze(ts), [])

    def test_empty_series(self):
        ts = make_series([])
        validator = MissingDataValidator()
        self.assertEqual(validator.analyze(ts), [])

class TestSimpleReporter(unittest.TestCase):

    def test_returns_info_with_mean(self):
        ts = make_series([10.0, 20.0, 30.0])
        reporter = SimpleReporter()
        result = reporter.analyze(ts)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].startswith("Info:"))
        self.assertIn("mean", result[0])

    def test_info_contains_station_and_param(self):
        ts = make_series([5.0], name="SO2", station="WrWybrzeze")
        reporter = SimpleReporter()
        result = reporter.analyze(ts)
        self.assertIn("SO2", result[0])
        self.assertIn("WrWybrzeze", result[0])

    def test_empty_series_message(self):
        ts = make_series([])
        reporter = SimpleReporter()
        result = reporter.analyze(ts)
        self.assertEqual(len(result), 1)
        self.assertIn("no data", result[0])



class TestDuckTypingPolymorphism(unittest.TestCase):

    def test_all_analyzers_callable_without_isinstance(self):

        ts = make_series([5.0, 150.0, None, 80.0], name="NO2", station="KrAlKras")

        analyzers = [
            MeanValidator(threshold=40.0),
            AnomalyValidator(max_value=100.0),
            MissingDataValidator(max_missing_pct=10.0),
            SimpleReporter(),
        ]

        all_results = []
        for analyzer in analyzers:
            messages = analyzer.analyze(ts)
            all_results.extend(messages)

        self.assertGreater(len(all_results), 0)

    def test_simple_reporter_is_not_series_validator(self):
        from SeriesValidator import SeriesValidator
        reporter = SimpleReporter()
        self.assertNotIsInstance(reporter, SeriesValidator)

    def test_duck_typing_same_interface(self):
        ts = make_series([10.0])
        analyzers = [
            MeanValidator(threshold=5.0),
            AnomalyValidator(max_value=5.0),
            SimpleReporter(),
        ]
        for analyzer in analyzers:
            result = analyzer.analyze(ts)
            self.assertIsInstance(result, list)



if __name__ == "__main__":
    print("=" * 60)
    print("DEMONSTRACJA – duck typing (polimorfizm strukturalny)")
    print("=" * 60)

    sample = make_series(
        [5.0, 150.0, None, 80.0, 200.0],
        name="NO2",
        station="KrAlKras",
        unit="ug/m3",
    )

    analyzers = [
        MeanValidator(threshold=40.0),
        AnomalyValidator(max_value=100.0),
        MissingDataValidator(max_missing_pct=10.0),
        SimpleReporter(),
    ]

    for analyzer in analyzers:
        messages = analyzer.analyze(sample)
        for msg in messages:
            print(msg)

    print("\n" + "=" * 60)
    print("TESTY JEDNOSTKOWE")
    print("=" * 60)
    unittest.main(verbosity=2)