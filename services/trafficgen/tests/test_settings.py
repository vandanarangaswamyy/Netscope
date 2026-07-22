import pytest
from pydantic import ValidationError

from trafficgen.settings import Settings


def test_settings_accepts_low_default_rate():
    settings = Settings(REQUESTS_PER_SECOND=2.5)

    assert settings.requests_per_second == 2.5


def test_settings_rejects_zero_rate():
    with pytest.raises(ValidationError, match="REQUESTS_PER_SECOND must be greater than zero"):
        Settings(REQUESTS_PER_SECOND=0)


def test_settings_rejects_excessive_rate():
    with pytest.raises(ValidationError, match="REQUESTS_PER_SECOND must be 100 or lower"):
        Settings(REQUESTS_PER_SECOND=101)


def test_settings_rejects_invalid_slo():
    with pytest.raises(ValidationError, match="SLO_LATENCY_MS must be greater than zero"):
        Settings(SLO_LATENCY_MS=0)
