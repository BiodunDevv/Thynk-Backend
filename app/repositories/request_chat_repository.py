from app.models.request_chat import RequestChat
from app.repositories.base import BaseRepository


class RequestChatRepository(BaseRepository[RequestChat]):
    def __init__(self) -> None:
        super().__init__(RequestChat)
