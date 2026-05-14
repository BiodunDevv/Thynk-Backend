from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self) -> None:
        super().__init__(Payment)

    async def get_by_reference(self, reference: str) -> Payment | None:
        return await Payment.find_one(Payment.provider_reference == reference)
