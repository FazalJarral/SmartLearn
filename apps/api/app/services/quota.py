from datetime import UTC, datetime, timedelta


def next_utc_midnight(now: datetime | None = None) -> datetime:
    current = now.astimezone(UTC) if now else datetime.now(UTC)
    tomorrow = current.date() + timedelta(days=1)
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=UTC)


def remaining_uploads(accepted_today: int, daily_limit: int) -> int:
    return max(daily_limit - accepted_today, 0)
