from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.exceptions import AppException
from app.core.logging import configure_logging
from app.core.request_id import RequestIDMiddleware
from app.core.response import ErrorDetail, ErrorResponse

settings = get_settings()
configure_logging()

tags_metadata = [
    {"name": "Auth", "description": "Authentication endpoints for registration, login, email verification, password reset, token refresh, and logout."},
    {"name": "Users", "description": "User account management endpoints."},
    {"name": "Profile", "description": "Profile endpoints for the logged-in user."},
    {"name": "Prompt Generation", "description": "Endpoints for generating AI-enhanced prompts and enforcing usage rules."},
    {"name": "Request Chats", "description": "Endpoints for storing and managing user AI request conversations."},
    {"name": "Prompt Templates", "description": "Endpoints for browsing reusable prompt templates."},
    {"name": "Saved Prompts", "description": "Endpoints for listing and organizing saved prompts."},
    {"name": "Subscriptions", "description": "Endpoints for subscription state and plan access."},
    {"name": "Payments", "description": "Endpoints for initializing, verifying, and receiving payment webhooks."},
    {"name": "Coupons", "description": "Endpoints for validating coupons."},
    {"name": "Notifications", "description": "Endpoints for device push token registration and notification history."},
    {"name": "Support", "description": "Endpoints for support tickets and replies."},
    {"name": "Legal", "description": "Endpoints for legal documents shown in the Thynk web application and PWA."},
    {"name": "Admin Dashboard", "description": "Super Admin dashboard metrics."},
    {"name": "Admin Request Chats", "description": "Super Admin request chat review and template conversion operations."},
    {"name": "Admin Templates", "description": "Super Admin prompt template management."},
    {"name": "Admin Coupons", "description": "Super Admin coupon management."},
    {"name": "Admin Payments", "description": "Super Admin payment review."},
    {"name": "Admin Support", "description": "Super Admin support desk operations."},
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Thynk Backend API",
    description="Complete API documentation for Thynk's hosted backend, powering the Next.js web application and progressive web app experience including authentication, AI prompt generation, subscriptions, payments, coupons, support, notifications, request chats, templates, and admin operations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "deepLinking": False,
    },
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["System"], summary="Root health check", description="Simple root health endpoint for platform routing and deployment checks.")
async def health_check():
    return {
        "name": settings.app_name,
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@app.get("/healthz", tags=["System"], summary="Liveness probe", description="Lightweight liveness endpoint for load balancers, container health checks, and hosting platforms.")
async def liveness_check():
    return {"status": "ok"}


@app.get("/readyz", tags=["System"], summary="Readiness probe", description="Readiness endpoint for hosting platforms to verify the API process is ready to serve traffic.")
async def readiness_check():
    return {"status": "ready"}


def error_payload(request: Request, status_code: int, message: str, code: str, details: dict | None = None, field_errors: list[dict] | None = None):
    return ErrorResponse(
        message=message,
        error=ErrorDetail(
            code=code,
            status_code=status_code,
            details=details or {},
            field_errors=field_errors or [],
            request_id=getattr(request.state, "request_id", "unknown"),
        ),
    ).model_dump(mode="json")


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content=error_payload(request, exc.status_code, exc.message, exc.error_code, exc.details, exc.field_errors))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    field_errors = [{"field": ".".join(str(item) for item in error["loc"][1:]), "message": error["msg"]} for error in exc.errors()]
    return JSONResponse(status_code=422, content=error_payload(request, 422, "Validation failed. Please check your input.", "VALIDATION_ERROR", field_errors=field_errors))


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content=error_payload(request, 500, "Internal server error.", "INTERNAL_SERVER_ERROR", details={"exception": str(exc) if settings.app_debug else {}}))
