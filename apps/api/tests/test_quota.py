from datetime import UTC, datetime

from app.services.quota import next_utc_midnight, remaining_uploads


def test_remaining_uploads_never_negative():
    assert remaining_uploads(10, 5) == 0


def test_next_utc_midnight():
    assert next_utc_midnight(datetime(2026, 9, 3, 23, 1, tzinfo=UTC)).isoformat() == "2026-09-04T00:00:00+00:00"
