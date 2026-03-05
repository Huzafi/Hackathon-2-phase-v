"""Environment configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    database_url: str

    # JWT authentication configuration
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # OpenAI configuration for AI agent
    openai_api_key: str
    openai_model: str = "gpt-4"
    agent_timeout: int = 30  # seconds
    context_window_size: int = 20  # number of messages

    # Kafka configuration for event-driven architecture
    kafka_brokers: str = "localhost:9092"
    kafka_topic_events: str = "task-events"
    kafka_consumer_group: str = "task-service-group"
    kafka_auto_offset_reset: str = "earliest"

    # Dapr configuration for distributed runtime
    dapr_http_endpoint: Optional[str] = None
    dapr_grpc_endpoint: Optional[str] = None
    enable_dapr: bool = False

    # Feature flags
    enable_reminders: bool = True
    enable_recurrence: bool = True
    enable_event_sourcing: bool = True

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
