from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parents[2] / "emails"

env = Environment(
    loader=FileSystemLoader(str(BASE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(template_name: str, context: dict) -> str:
    return env.get_template(template_name).render(**context)
