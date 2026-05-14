import re


def normalize_email(email: str) -> str:
    return email.strip().lower()


def sanitize_template_content(content: str) -> str:
    content = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[redacted-email]", content)
    content = re.sub(r"\+?\d[\d\-\s]{6,}\d", "[redacted-phone]", content)
    return content
