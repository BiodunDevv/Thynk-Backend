# Thynk Backend

Production-ready FastAPI backend for **Thynk**, an AI-powered prompt generation platform powering a hosted Next.js web application and progressive web app.

## Stack

- Python / FastAPI
- MongoDB with Beanie
- JWT auth
- Brevo email
- Device push notification support
- Azure OpenAI prompt generation
- Paystack-first payments with Stripe-ready abstraction
- Docker / Docker Compose
- Pytest, Ruff, Black

## Run locally

1. Copy `.env.example` to `.env`
2. Start MongoDB with Docker Compose or point `.env` to your hosted MongoDB instance
3. Install dependencies
4. Run `uvicorn app.main:app --reload`

Local backend URL:

```text
http://127.0.0.1:8000
```

### Auto-reload dev server

For local development with automatic restart when files change, run:

```bash
python3 dev_server.py
```

This watches the `app/` folder and reloads the FastAPI server automatically.

## Local frontend env

If your Next.js PWA frontend needs a local env file, use the example in:

- [.env.web.example](/Users/mac/Desktop/Thynk%20FullStack/Thynk-backend/.env.web.example)

Suggested local frontend values:

```env
NEXT_PUBLIC_APP_NAME=Thynk
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_V1_PREFIX=/api/v1
NEXT_PUBLIC_SITE_URL=http://127.0.0.1:3000
```

That matches the local backend server output:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000
```

and the backend CORS settings now allow the common local Next.js origins on `127.0.0.1:3000`, `localhost:3000`, `127.0.0.1:3001`, and `localhost:3001`.

## Hosting posture

This backend is now set up for a hosted web deployment behind a Next.js frontend / PWA:

- CORS is environment-driven through `ALLOWED_ORIGINS`
- the API exposes `/healthz` and `/readyz` for hosting providers
- Docker runs the app as a non-root user
- `uvicorn` is started with proxy-header support for reverse proxies

## Python version

The backend targets **Python 3.11**. The current local interpreter used for validation is:

- `Python 3.11.0`

## Deploying on Azure

This repository is now cleaned up for Azure-first hosting. The same Dockerfile works cleanly for:

- Azure App Service for Containers
- Azure Container Apps
- Azure Web App with Docker

Recommended Azure shape:

1. Push this repository to GitHub or your source control
2. Deploy the Docker image to Azure App Service or Azure Container Apps
3. Set the health check path to:

```text
/healthz
```

4. Configure these production environment variables in Azure:

```text
APP_NAME
APP_ENV=production
APP_DEBUG=false
API_V1_PREFIX=/api/v1
MONGODB_URI
MONGODB_DB_NAME
JWT_SECRET_KEY
JWT_REFRESH_SECRET_KEY
BREVO_API_KEY
BREVO_SENDER_EMAIL
BREVO_SENDER_NAME
AI_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_DEPLOYMENT_NAME
AZURE_OPENAI_MODEL_NAME
AZURE_OPENAI_API_VERSION
AZURE_OPENAI_MAX_TOKENS
PAYSTACK_SECRET_KEY
PAYSTACK_PUBLIC_KEY
PAYSTACK_WEBHOOK_SECRET
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
FRONTEND_URL
ALLOWED_ORIGINS
SUPPORT_EMAIL
SUPER_ADMIN_EMAIL
SUPER_ADMIN_PASSWORD
SUPER_ADMIN_NAME
```

5. Point your Next.js frontend domains into `ALLOWED_ORIGINS`
6. Point your public API domain, for example `api.thynk.app`, to Azure
7. Register payment webhooks using the final public API URLs

Use these health endpoints:

- `/healthz`
- `/readyz`

## Docker

Run `docker compose up --build`

## API Documentation

After starting the server, open:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

To test protected endpoints:

1. Register or login.
2. Copy the `access_token`.
3. Click `Authorize` in Swagger.
4. Enter `Bearer <access_token>`.
5. Run protected requests.

For Super Admin endpoints, use the seeded super admin account from environment variables.

## Seed commands

- `python -m app.scripts.seed_database`
- `python -m app.scripts.create_super_admin`

## Tests

Run `pytest`

## Payment webhooks

Use provider tools to forward webhook events to:

- `POST /api/v1/payments/webhook/paystack`
- `POST /api/v1/payments/webhook/stripe`

## Notes

- Branding uses **Thynk** everywhere.
- Azure OpenAI is the active AI provider for V1.
- Paystack is live-ready first; Stripe is scaffolded.
- Support attachments are modeled but not yet backed by file storage.
- The backend is intended to serve a hosted Next.js frontend and PWA, not a mobile-only client.
- `.dockerignore` excludes local-only files and test/cache artifacts from hosted builds.
# Thynk-Backend
