"""Loads built-in template definitions from app/templates/*.json into memory at startup."""
import json

from app.core.config import settings
from app.schemas.template import TemplateDetail


class TemplateRegistry:
    def __init__(self, templates_dir) -> None:
        self._templates: dict[str, TemplateDetail] = {}
        for file_path in sorted(templates_dir.glob("*.json")):
            data = json.loads(file_path.read_text(encoding="utf-8"))
            template = TemplateDetail(**data)
            self._templates[template.id] = template

    def list(self) -> list[TemplateDetail]:
        return list(self._templates.values())

    def get(self, template_id: str) -> TemplateDetail | None:
        return self._templates.get(template_id)


template_registry = TemplateRegistry(settings.templates_dir)
