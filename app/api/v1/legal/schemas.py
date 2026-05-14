from pydantic import BaseModel


class LegalDocumentResponse(BaseModel):
    slug: str
    title: str
    content: str
