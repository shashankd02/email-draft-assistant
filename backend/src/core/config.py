from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "postgresql+psycopg://email_assistant:email_assistant@localhost:5432/email_assistant"
    jwt_secret_key: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    auth_bootstrap_secret: str = "dev-bootstrap-secret"

    # Provider keys (optional in local scaffold)
    openai_api_key: str | None = None
    tavily_api_key: str | None = None
    deepgram_api_key: str | None = None
    openai_stt_model: str = "gpt-4o-mini-transcribe"
    openai_text_model: str = "gpt-4o-mini"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "alloy"
    tavily_max_results: int = 5
    chroma_host: str = "chroma"
    chroma_port: int = 8000
    chroma_tenant: str = "default_tenant"
    chroma_database: str = "default_database"
    langsmith_tracing: bool = False
    langsmith_project: str = "email-assistant"
    langsmith_api_key: str | None = None

    # Runtime controls from spec
    max_retries_per_agent: int = 2
    max_total_retries: int = 5
    hard_timeout_e2e_seconds: int = 30
    quality_threshold: float = 85.0
    eval_core_dataset_path: str = "src/evaluation/datasets/core_prompts.jsonl"
    eval_adversarial_dataset_path: str = "src/evaluation/datasets/adversarial_prompts.jsonl"
    eval_voice_dataset_path: str = "src/evaluation/datasets/voice_prompts.jsonl"
    eval_tone_threshold: float = 85.0
    eval_factuality_threshold: float = 85.0
    eval_clarity_threshold: float = 90.0
    eval_safety_pass_threshold: float = 0.99
    eval_structured_output_threshold: float = 0.98
    eval_fallback_success_threshold: float = 0.95
    draft_rate_limit_requests: int = 30
    draft_rate_limit_window_seconds: int = 60
    retention_drafts_days: int = 90
    retention_transcripts_days: int = 30
    retention_logs_days: int = 90
    retention_scheduler_enabled: bool = True
    retention_scheduler_interval_minutes: int = 60
    strict_provider_mode: bool = True
    alert_p95_latency_ms_threshold: int = 12000
    alert_fallback_rate_threshold: float = 0.2
    alert_provider_error_rate_threshold: float = 0.05
    alert_safety_failure_rate_threshold: float = 0.01


settings = Settings()
