from uuid import uuid4


def generate_ticket_number() -> str:
    return f"TKT-{uuid4().hex[:8].upper()}"
