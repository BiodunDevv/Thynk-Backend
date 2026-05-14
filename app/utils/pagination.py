from math import ceil

from app.core.response import PaginatedMeta


def build_pagination_meta(page: int, limit: int, total: int) -> PaginatedMeta:
    total_pages = max(1, ceil(total / limit)) if limit else 1
    return PaginatedMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
