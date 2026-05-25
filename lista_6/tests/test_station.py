import datetime
import pytest
from Station import Station

#ZAD 3a
def test_equality_same_code():
    date = datetime.date(2026, 1, 1)
    s1 = Station("S1", "Białka", "Białka 2/1a",
                 "przemysłowa", date, date)

    s2 = Station("S1", "Bolesławiec", "Bolesławiec 18",
                 "tło", date, date)

    assert s1 == s2

def test_equality_different_code():
    date = datetime.date(2026, 1, 1)
    s1 = Station("S1", "Białka", "Białka 2/1a",
                 "przemysłowa", date, date)

    s2 = Station("S2", "Bolesławiec", "Bolesławiec 18",
                 "tło", date, date)

    assert s1 != s2

def test_equality_with_different_type():
    date = datetime.date(2026, 1, 1)
    s1 = Station("S1", "Białka", "Białka 2/1a",
                 "przemysłowa", date, date)

    code = "S1"

    assert s1 != code