from app.models.support_ticket import SupportTicket
from app.repositories.base import BaseRepository


class SupportRepository(BaseRepository[SupportTicket]):
    def __init__(self) -> None:
        super().__init__(SupportTicket)
