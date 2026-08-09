from fastapi import APIRouter

from app.core.exceptions import TemplateNotFoundError
from app.models.template_registry import template_registry
from app.schemas.template import TemplateDetail, TemplateSummary

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[TemplateSummary])
def list_templates() -> list[TemplateSummary]:
    return [
        TemplateSummary(id=t.id, name=t.name, description=t.description, sheet_name=t.sheet_name)
        for t in template_registry.list()
    ]


@router.get("/{template_id}", response_model=TemplateDetail)
def get_template(template_id: str) -> TemplateDetail:
    template = template_registry.get(template_id)
    if template is None:
        raise TemplateNotFoundError(template_id)
    return template
