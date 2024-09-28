import pytest
import flights


def test_sum_as_string():
    assert flights.sum_as_string(1, 1) == "2"
