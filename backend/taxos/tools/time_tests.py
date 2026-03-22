import pytest
from taxos.tools.time import parse_datetime


@pytest.mark.parametrize(
  "input_value, timezone, expected_iso",
  [
    # UTC input variants
    ("2024-01-01T12:00:00Z     ", "America/New_York", "2024-01-01T07:00:00-05:00"),
    ("2024-01-01T12:00:00-00:00", "America/New_York", "2024-01-01T07:00:00-05:00"),
    ("2024-01-01T12:00:00+00:00", "America/New_York", "2024-01-01T07:00:00-05:00"),
    # Noon in Pacific Time should be 3pm in New York (3 hour difference)
    ("2024-01-01T12:00:00-08:00", "America/New_York", "2024-01-01T15:00:00-05:00"),
    # Noon in UTC +8 should be 11pm the previous day in New York (13 hours difference)
    ("2024-01-01T12:00:00+08:00", "America/New_York", "2023-12-31T23:00:00-05:00"),
    # We assume that the input is in local time if it has no timezone info
    ("2024-01-01T12:00:00      ", "America/New_York", "2024-01-01T12:00:00-05:00"),
    ("2024-01-01T12:00:00      ", "UTC             ", "2024-01-01T12:00:00+00:00"),
  ],
)
def test_parse_datetime(input_value, timezone, expected_iso):
  result = parse_datetime(input_value, timezone)
  assert result.isoformat() == expected_iso, f"Expected {expected_iso}, got {result}"
