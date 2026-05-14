from typing import Generic, TypeVar

from beanie import Document

ModelType = TypeVar("ModelType", bound=Document)


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get(self, object_id: str) -> ModelType | None:
        return await self.model.get(object_id)

    async def create(self, instance: ModelType) -> ModelType:
        await instance.insert()
        return instance
