from app.models.template_conversion import TemplateConversion
from app.repositories.base import BaseRepository


class TemplateConversionRepository(BaseRepository[TemplateConversion]):
    def __init__(self) -> None:
        super().__init__(TemplateConversion)
