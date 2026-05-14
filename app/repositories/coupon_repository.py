from app.models.coupon import Coupon
from app.repositories.base import BaseRepository


class CouponRepository(BaseRepository[Coupon]):
    def __init__(self) -> None:
        super().__init__(Coupon)

    async def get_by_code(self, code: str) -> Coupon | None:
        return await Coupon.find_one(Coupon.code == code.upper())
