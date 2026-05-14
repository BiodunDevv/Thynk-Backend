from app.models.usage_credit import UsageCredit
from app.repositories.base import BaseRepository


class UsageCreditRepository(BaseRepository[UsageCredit]):
    def __init__(self) -> None:
        super().__init__(UsageCredit)
