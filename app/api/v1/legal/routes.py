from fastapi import APIRouter

from app.api.v1.legal.schemas import LegalDocumentResponse
from app.api.v1.legal.service import get_legal_document
from app.core.response import SuccessResponse

router = APIRouter(prefix="/legal", tags=["Legal"])


@router.get("/terms", response_model=SuccessResponse[LegalDocumentResponse], summary="Get terms and conditions", description="Returns the Terms and Conditions document for the Thynk web application and PWA.")
async def terms():
    return SuccessResponse(message="Terms fetched successfully.", data=get_legal_document("terms"))


@router.get("/privacy", response_model=SuccessResponse[LegalDocumentResponse], summary="Get privacy policy", description="Returns the Privacy Policy document for the Thynk web application and PWA.")
async def privacy():
    return SuccessResponse(message="Privacy policy fetched successfully.", data=get_legal_document("privacy"))


@router.get("/refund-policy", response_model=SuccessResponse[LegalDocumentResponse], summary="Get refund policy", description="Returns the Refund Policy document for the Thynk web application and PWA.")
async def refund_policy():
    return SuccessResponse(message="Refund policy fetched successfully.", data=get_legal_document("refund-policy"))
