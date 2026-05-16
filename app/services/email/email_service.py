from app.core.config import get_settings
from app.services.email.brevo_client import BrevoClient
from app.services.email.renderer import render_template


class EmailService:
    def __init__(self) -> None:
        self.client = BrevoClient()
        settings = get_settings()
        self.sender = {"email": settings.brevo_sender_email, "name": settings.brevo_sender_name}

    async def _send(self, to_email: str, to_name: str, subject: str, html_template: str, text_template: str, **context):
        payload = {
            "sender": self.sender,
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "htmlContent": render_template(f"html/{html_template}", context),
            "textContent": render_template(f"text/{text_template}", context),
        }
        return await self.client.send_email(payload)

    async def send_verification_code(self, email: str, name: str, code: str) -> dict:
        return await self._send(email, name, "Verify your Thynk account", "verify_account.html", "verify_account.txt", name=name, code=code)

    async def send_password_reset_code(self, email: str, name: str, code: str) -> dict:
        return await self._send(email, name, "Reset your Thynk password", "password_reset.html", "password_reset.txt", name=name, code=code)

    async def send_welcome_email(self, email: str, name: str) -> dict:
        return await self._send(email, name, "Welcome to Thynk", "welcome.html", "welcome.txt", name=name)

    async def send_subscription_success(self, email: str, name: str, plan: str) -> dict:
        return await self._send(email, name, "Your Thynk subscription is active", "subscription_success.html", "subscription_success.txt", name=name, plan=plan)

    async def send_payment_completion(self, email: str, name: str, plan: str, manage_url: str) -> dict:
        return await self._send(
            email,
            name,
            "Your Thynk payment was received",
            "payment_completion.html",
            "payment_completion.txt",
            name=name,
            plan=plan,
            manage_url=manage_url,
        )

    async def send_payment_failed(self, email: str, name: str) -> dict:
        return await self._send(email, name, "Payment issue on Thynk", "payment_failed.html", "payment_failed.txt", name=name)

    async def send_coupon_applied(self, email: str, name: str, coupon_code: str) -> dict:
        return await self._send(email, name, "Coupon applied on Thynk", "coupon_applied.html", "coupon_applied.txt", name=name, coupon_code=coupon_code)

    async def send_support_ticket_created(self, email: str, name: str, ticket_number: str) -> dict:
        return await self._send(email, name, "Your Thynk support ticket was created", "support_ticket_created.html", "support_ticket_created.txt", name=name, ticket_number=ticket_number)

    async def send_support_ticket_reply(self, email: str, name: str, ticket_number: str, reply_preview: str) -> dict:
        return await self._send(email, name, "Support replied to your Thynk ticket", "support_ticket_reply.html", "support_ticket_reply.txt", name=name, ticket_number=ticket_number, reply_preview=reply_preview)

    async def send_support_ticket_resolved(self, email: str, name: str, ticket_number: str) -> dict:
        return await self._send(email, name, "Your Thynk ticket was resolved", "support_ticket_resolved.html", "support_ticket_resolved.txt", name=name, ticket_number=ticket_number)

    async def send_support_ticket_closed(self, email: str, name: str, ticket_number: str) -> dict:
        return await self._send(email, name, "Your Thynk ticket was closed", "support_ticket_closed.html", "support_ticket_closed.txt", name=name, ticket_number=ticket_number)

    async def send_admin_support_notification(self, admin_email: str, ticket_number: str, subject: str) -> dict:
        return await self._send(admin_email, "Admin", "New Thynk support activity", "admin_support_notification.html", "admin_support_notification.txt", ticket_number=ticket_number, subject=subject)
