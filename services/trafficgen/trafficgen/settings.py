from functools import lru_cache

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    target_base_url: AnyHttpUrl = Field(default="http://nginx:8080", alias="TARGET_BASE_URL")
    requests_per_second: float = Field(default=2.0, alias="REQUESTS_PER_SECOND")
    request_timeout_seconds: float = Field(default=2.0, alias="REQUEST_TIMEOUT_SECONDS")
    slo_latency_ms: int = Field(default=250, alias="SLO_LATENCY_MS")
    traffic_enabled: bool = Field(default=True, alias="TRAFFIC_ENABLED")

    @field_validator("requests_per_second")
    @classmethod
    def validate_rps(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("REQUESTS_PER_SECOND must be greater than zero")
        if value > 100:
            raise ValueError("REQUESTS_PER_SECOND must be 100 or lower")
        return value

    @field_validator("request_timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("REQUEST_TIMEOUT_SECONDS must be greater than zero")
        if value > 30:
            raise ValueError("REQUEST_TIMEOUT_SECONDS must be 30 or lower")
        return value

    @field_validator("slo_latency_ms")
    @classmethod
    def validate_slo(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("SLO_LATENCY_MS must be greater than zero")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
