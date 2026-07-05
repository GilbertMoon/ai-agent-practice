from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "agentops-final-project"
    environment: str = "local"
    log_level: str = "INFO"

    enable_rag: bool = True
    enable_memory: bool = True
    enable_evaluation: bool = True
    enable_trace_log: bool = True

    docs_dir: str = "final_project/sample_docs"
    log_dir: str = "final_project/logs"
    output_dir: str = "final_project/outputs"
    report_dir: str = "final_project/reports"

    gemini_api_key: str = ""
    gemini_model_name: str = "gemini-flash-lite-latest"

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent

    def _resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.base_dir / path

    @property
    def agent_log_path(self) -> Path:
        return self._resolve_path(self.log_dir) / "agent_trace.jsonl"

    @property
    def evaluation_path(self) -> Path:
        return self._resolve_path(self.output_dir) / "evaluation.csv"

    @property
    def backlog_path(self) -> Path:
        return self._resolve_path(self.report_dir) / "improvement_backlog.md"

    @property
    def latest_report_path(self) -> Path:
        return self._resolve_path(self.report_dir) / "latest_report.md"

    def to_public_dict(self) -> dict[str, str | bool]:
        return {
            "service_name": self.service_name,
            "environment": self.environment,
            "log_level": self.log_level,
            "enable_rag": self.enable_rag,
            "enable_memory": self.enable_memory,
            "enable_evaluation": self.enable_evaluation,
            "enable_trace_log": self.enable_trace_log,
            "docs_dir": str(self._resolve_path(self.docs_dir)),
            "log_dir": str(self._resolve_path(self.log_dir)),
            "output_dir": str(self._resolve_path(self.output_dir)),
            "report_dir": str(self._resolve_path(self.report_dir)),
            "gemini_model_name": self.gemini_model_name,
        }


settings = Settings()