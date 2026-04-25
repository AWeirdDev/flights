from datetime import date
from weekend_scraper.weekends import next_n_weekends

def test_next_n_weekends():
    # Today is Friday 2026-04-24
    today = date(2026, 4, 24)
    n = 3
    expected = [
        (date(2026, 4, 24), date(2026, 4, 26)),
        (date(2026, 5, 1), date(2026, 5, 3)),
        (date(2026, 5, 8), date(2026, 5, 10))
    ]
    assert next_n_weekends(today, n) == expected

def test_next_n_weekends_not_friday():
    # Today is Monday 2026-04-20
    today = date(2026, 4, 20)
    n = 1
    expected = [
        (date(2026, 4, 24), date(2026, 4, 26))
    ]
    assert next_n_weekends(today, n) == expected

def test_next_n_weekends_saturday():
    # Today is Saturday 2026-04-25
    today = date(2026, 4, 25)
    n = 1
    expected = [
        (date(2026, 5, 1), date(2026, 5, 3))
    ]
    assert next_n_weekends(today, n) == expected
