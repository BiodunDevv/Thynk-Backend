from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import Request

from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException

_RATE_BUCKETS: dict[str, deque] = defaultdict(deque)


def enforce_simple_rate_limit(request: Request, key: str, limit: int, minutes: int = 1) -> None:
    now = datetime.now(timezone.utc)
    bucket = _RATE_BUCKETS[key]
    window_start = now - timedelta(minutes=minutes)
    while bucket and bucket[0] < window_start:
        bucket.popleft()
    if len(bucket) >= limit:
        raise AppException(
            status_code=429,
            message="Too many requests. Please try again later.",
            error_code=ErrorCodes.RATE_LIMIT_EXCEEDED,
            details={"request_id": getattr(request.state, "request_id", "")},
        )
    bucket.append(now)
