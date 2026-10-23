"""Load settings from .env.

This module does not import CrewAI, so setup errors show up instantly.
"""

import os
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# The most text the model may write per step. A tailored resume needs about
# 2,000-4,000 tokens. OpenRouter checks this limit against your credit balance,
# so a lower number lets small balances work.
DEFAULT_MAX_OUTPUT_TOKENS = 4000


class SetupError(Exception):
    """A problem the user can fix before any AI work starts (bad file, missing key)."""


@dataclass
class Settings:
    """The values we read from .env."""

    api_key: str
    model: str
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS


def load_settings() -> Settings:
    """Read the settings from .env / the environment.

    OPENROUTER_API_KEY and OPENROUTER_MODEL are required. MAX_OUTPUT_TOKENS is
    optional (default 4000). Raises SetupError if something is missing or
    invalid. The key's value is never shown.
    """
    load_dotenv(find_dotenv(usecwd=True))  # the .env in the folder you run the command from
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_MODEL", "").strip()

    if not api_key:
        raise SetupError(
            "Error: OPENROUTER_API_KEY is not set. "
            "Fix: copy .env.example to .env and add your key."
        )
    if not model:
        raise SetupError(
            "Error: OPENROUTER_MODEL is not set. "
            "Fix: add a model ID to .env (see .env.example)."
        )
    max_output_tokens = read_max_output_tokens()
    return Settings(api_key=api_key, model=model, max_output_tokens=max_output_tokens)


def read_max_output_tokens() -> int:
    """Read the optional MAX_OUTPUT_TOKENS setting, or return the default."""
    value = os.getenv("MAX_OUTPUT_TOKENS", "").strip()
    if not value:
        return DEFAULT_MAX_OUTPUT_TOKENS
    if not value.isdigit() or int(value) == 0:
        raise SetupError(
            f"Error: MAX_OUTPUT_TOKENS must be a whole number above 0 (got '{value}'). "
            f"Fix: set it to a number like {DEFAULT_MAX_OUTPUT_TOKENS} in .env, or remove the line."
        )
    return int(value)


def full_model_name(model: str) -> str:
    """Add the "openrouter/" prefix CrewAI needs, unless it is already there."""
    if model.startswith("openrouter/"):
        return model
    return "openrouter/" + model

