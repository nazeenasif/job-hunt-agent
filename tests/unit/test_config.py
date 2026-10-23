import pytest

from job_hunt_agent import config
from job_hunt_agent.config import SetupError, full_model_name, load_settings


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    """Stop a real .env file from leaking into the tests."""
    monkeypatch.setattr(config, "load_dotenv", lambda *args: None)


def test_loads_both_values(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key-123")
    monkeypatch.setenv("OPENROUTER_MODEL", "x/y")
    settings = load_settings()
    assert settings.api_key == "key-123"
    assert settings.model == "x/y"


def test_adds_openrouter_prefix():
    assert full_model_name("x/y") == "openrouter/x/y"


def test_does_not_double_prefix():
    assert full_model_name("openrouter/x/y") == "openrouter/x/y"


def test_missing_key_names_variable(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_MODEL", "x/y")
    with pytest.raises(SetupError) as error:
        load_settings()
    assert "OPENROUTER_API_KEY" in str(error.value)
    assert ".env.example" in str(error.value)


def test_blank_key_counts_as_missing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "   ")
    monkeypatch.setenv("OPENROUTER_MODEL", "x/y")
    with pytest.raises(SetupError):
        load_settings()


def test_missing_model_names_variable_and_hides_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-secret-123")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    with pytest.raises(SetupError) as error:
        load_settings()
    assert "OPENROUTER_MODEL" in str(error.value)
    assert "sk-secret-123" not in str(error.value)


def test_max_output_tokens_defaults_to_4000(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key-123")
    monkeypatch.setenv("OPENROUTER_MODEL", "x/y")
    monkeypatch.delenv("MAX_OUTPUT_TOKENS", raising=False)
    assert load_settings().max_output_tokens == 4000


def test_max_output_tokens_can_be_set(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key-123")
    monkeypatch.setenv("OPENROUTER_MODEL", "x/y")
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", "1500")
    assert load_settings().max_output_tokens == 1500


@pytest.mark.parametrize("bad_value", ["abc", "0", "-5", "2.5"])
def test_invalid_max_output_tokens_is_rejected(monkeypatch, bad_value):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key-123")
    monkeypatch.setenv("OPENROUTER_MODEL", "x/y")
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", bad_value)
    with pytest.raises(SetupError) as error:
        load_settings()
    assert "MAX_OUTPUT_TOKENS" in str(error.value)
