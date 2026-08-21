import tempfile
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, overridable via ETL_* environment variables or a .env file."""

    model_config = SettingsConfigDict(env_prefix="ETL_", env_file=".env", extra="ignore")

    app_dir: Path = Path(__file__).resolve().parent.parent
    # Serverless platforms (e.g. Vercel) only allow writes under the system temp dir; using it
    # everywhere keeps local dev and serverless deploys consistent. Override via ETL_UPLOAD_DIR /
    # ETL_OUTPUT_DIR for a persistent path on a traditional host.
    upload_dir: Path = Path(tempfile.gettempdir()) / "veryon-etl" / "uploads"
    output_dir: Path = Path(tempfile.gettempdir()) / "veryon-etl" / "output"
    templates_dir: Path = app_dir / "templates"
    # Flat JSON file backing the saved/reusable formula library (MVP: no DB yet).
    formulas_file: Path = Path(tempfile.gettempdir()) / "veryon-etl" / "saved_formulas.json"

    # openpyxl only reads the modern .xlsx format, so legacy .xls is intentionally unsupported.
    allowed_upload_extensions: tuple[str, ...] = (".xlsx",)
    max_upload_size_bytes: int = 10 * 1024 * 1024
    sample_row_count: int = 20
    # Cap for the raw whole-sheet grid preview used by the constant-value cell picker.
    raw_grid_row_count: int = 200

    # 8080/8081 = veryon-sheet-sorter's actual Lovable/Vite dev port (falls back to 8081+ if
    # 8080 is busy), 5173 = Vite default, 3000/3001 = other common TanStack Start ports.
    # Override/extend via ETL_ALLOWED_ORIGINS (JSON array string), e.g. for preview deployments.
    allowed_origins: list[str] = [
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:8082",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Deployed frontend origin, read from FRONTEND_URL directly (no ETL_ prefix) so it matches
    # the env var name set in the Vercel project settings. Merged into CORS on top of the local
    # dev origins above instead of hardcoding the production URL in source.
    frontend_url: str | None = Field(
        default="https://veryon-sheet-sorter.vercel.app", validation_alias="FRONTEND_URL"
    )

    @property
    def cors_allowed_origins(self) -> list[str]:
        origins = list(self.allowed_origins)
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
        return origins

    def ensure_directories(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
