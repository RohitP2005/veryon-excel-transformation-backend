"""File-backed store of user-added custom templates (MVP: flat JSON file, no DB yet).

Kept separate from the built-in templates in app/templates/*.json, which stay read-only and
bundled with the app - this store is where templates users upload through the UI get persisted.
"""
import json
from pathlib import Path

from app.core.config import settings
from app.schemas.template import TemplateDetail


class CustomTemplateStore:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._write([])

    def _read(self) -> list[TemplateDetail]:
        raw = self._file_path.read_text(encoding="utf-8").strip()
        return [TemplateDetail(**item) for item in (json.loads(raw) if raw else [])]

    def _write(self, templates: list[TemplateDetail]) -> None:
        payload = json.dumps([t.model_dump() for t in templates], indent=2)
        self._file_path.write_text(payload, encoding="utf-8")

    def list(self) -> list[TemplateDetail]:
        return self._read()

    def get(self, template_id: str) -> TemplateDetail | None:
        return next((t for t in self._read() if t.id == template_id), None)

    def create(self, template: TemplateDetail) -> TemplateDetail:
        templates = self._read()
        templates.append(template)
        self._write(templates)
        return template


custom_template_store = CustomTemplateStore(settings.custom_templates_file)
