import asyncio

from app.core.database import close_db, init_db
from app.seed.seed_admin import seed_super_admin
from app.seed.seed_plans import seed_plans
from app.seed.seed_templates import seed_templates


async def main() -> None:
    await init_db()
    await seed_plans()
    await seed_templates()
    await seed_super_admin()
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
