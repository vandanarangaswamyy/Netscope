from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    node_id: str = Field(default="node-local", alias="NODE_ID")
    node_role: str = Field(default="analytics-worker", alias="NODE_ROLE")
    simulated_latency_ms: int = Field(default=0, alias="SIMULATED_LATENCY_MS")

    @field_validator("simulated_latency_ms")
    @classmethod
    def validate_latency(cls, value: int) -> int:
        if value < 0:
            raise ValueError("SIMULATED_LATENCY_MS must be non-negative")
        if value > 30_000:
            raise ValueError("SIMULATED_LATENCY_MS must be 30000 or lower")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
