from gameplay.formatting import format_time


def test_format_time_zero() -> None:
    assert format_time(0) == "0:00.000"


def test_format_time_999_ms() -> None:
    assert format_time(999) == "0:00.999"


def test_format_time_one_second() -> None:
    assert format_time(1000) == "0:01.000"


def test_format_time_mixed_minutes_seconds_ms() -> None:
    assert format_time(83456) == "1:23.456"
