from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, overridable via ETL_* environment variables or a .env file."""

    model_config = SettingsConfigDict(env_prefix="ETL_", env_file=".env", extra="ignore")

    app_dir: Path = Path(__file__).resolve().parent.parent
    upload_dir: Path = app_dir / "uploads"
    output_dir: Path = app_dir / "output"
    templates_dir: Path = app_dir / "templates"

    # openpyxl only reads the modern .xlsx format, so legacy .xls is intentionally unsupported.
    allowed_upload_extensions: tuple[str, ...] = (".xlsx",)
    max_upload_size_bytes: int = 10 * 1024 * 1024
    sample_row_count: int = 20

    # 8080/8081 = veryon-sheet-sorter's actual Lovable/Vite dev port (falls back to 8081+ if
    # 8080 is busy), 5173 = Vite default, 3000/3001 = other common TanStack Start ports.
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

    def ensure_directories(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
