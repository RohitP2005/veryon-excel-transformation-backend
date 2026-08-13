"""Domain-level exceptions raised by the service layer and translated to HTTP responses in main.py."""


class TemplateNotFoundError(Exception):
    def __init__(self, template_id: str):
        super().__init__(f"Template '{template_id}' not found")
        self.template_id = template_id


class UploadNotFoundError(Exception):
    def __init__(self, upload_id: str):
        super().__init__(f"Upload '{upload_id}' not found")
        self.upload_id = upload_id


class JobNotFoundError(Exception):
    def __init__(self, job_id: str):
        super().__init__(f"Generated file '{job_id}' not found")
        self.job_id = job_id


class SavedFormulaNotFoundError(Exception):
    def __init__(self, formula_id: str):
        super().__init__(f"Saved formula '{formula_id}' not found")
        self.formula_id = formula_id


class MappingValidationError(Exception):
    def __init__(self, errors: list[dict[str, str]]):
        super().__init__("Mapping validation failed")
        self.errors = errors


class ETLOperationError(Exception):
    """Raised when an ETL operation cannot be executed (e.g., an invalid formula)."""
