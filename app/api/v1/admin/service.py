from app.api.v1.admin.schemas import AdminOverviewResponse
from app.models.request_chat import RequestChat
from app.models.subscription import Subscription
from app.models.support_ticket import SupportTicket
from app.models.user import User


async def get_dashboard_overview() -> AdminOverviewResponse:
    total_users = await User.find_all().count()
    active_users = await User.find(User.is_active == True).count()
    verified_users = await User.find(User.is_verified == True).count()
    paying_users = await Subscription.find(Subscription.status == "active").count()
    total_prompts_generated = sum(user.prompt_generation_count for user in await User.find_all().to_list())
    open_support_tickets = await SupportTicket.find(SupportTicket.status == "open").count()
    reported_request_chats = await RequestChat.find(RequestChat.is_reported == True).count()
    return AdminOverviewResponse(
        total_users=total_users,
        active_users=active_users,
        verified_users=verified_users,
        paying_users=paying_users,
        total_prompts_generated=total_prompts_generated,
        open_support_tickets=open_support_tickets,
        reported_request_chats=reported_request_chats,
    )
