"""Turn an AI-step failure into a short message the user can act on.

API errors from OpenRouter arrive as long JSON blobs. We pull out just the
human-readable message and add a one-line hint. The full details are shown only
with --debug.
"""

import re

STEP_NAMES = ["Research", "Matching", "Writing"]

# One-line hints for the HTTP status codes OpenRouter commonly returns.
HINTS_BY_STATUS = {
    400: "Check that OPENROUTER_MODEL in .env is a chat model ID from https://openrouter.ai/models.",
    401: "Check that OPENROUTER_API_KEY in .env is correct and still active.",
    402: (
        "Add credits at https://openrouter.ai/settings/credits, switch to a cheaper model, "
        "or lower MAX_OUTPUT_TOKENS in .env."
    ),
    403: "Your key is not allowed to use this model. Try another OPENROUTER_MODEL.",
    404: "Check that OPENROUTER_MODEL in .env is a valid model ID from https://openrouter.ai/models.",
    408: "The request timed out. Try again.",
    429: "You are being rate-limited. Wait a minute and try again.",
}
SERVER_ERROR_HINT = "OpenRouter or the model provider had a problem. Try again later."
GUARDRAIL_HINT = "The model's answer kept failing our checks. Try a more capable OPENROUTER_MODEL."
DEFAULT_HINT = "Run again with --debug to see the full error."

# Finds 'message': '...' (or "message": "...") inside an error's text.
MESSAGE_IN_TEXT = re.compile(r"""['"]message['"]:\s*['"](.+?)['"](?:,|\})""")


def find_status_code(error: BaseException) -> int | None:
    """Return the HTTP status code of an API error, looking through wrapped errors too."""
    current: BaseException | None = error
    while current is not None:
        status = getattr(current, "status_code", None)
        if isinstance(status, int):
            return status
        current = current.__cause__ or current.__context__
    return None


def find_api_message(error: BaseException) -> str | None:
    """Return the human-readable message from an API error, or None if there isn't one."""
    body = getattr(error, "body", None)
    if isinstance(body, dict):
        inner = body.get("error", body)
        if isinstance(inner, dict) and isinstance(inner.get("message"), str):
            return inner["message"]

    match = MESSAGE_IN_TEXT.search(str(error))
    if match:
        return match.group(1)
    return None


def short_reason(error: BaseException) -> str:
    """One readable line explaining what went wrong."""
    status = find_status_code(error)
    message = find_api_message(error)
    if message and status:
        return f"{message} (HTTP {status})"
    if message:
        return message

    lines = str(error).strip().splitlines()
    first_line = lines[0] if lines else "no details"
    return f"{type(error).__name__}: {first_line}"


def hint_for(error: BaseException) -> str:
    """A one-line suggestion for how to fix the error."""
    status = find_status_code(error)
    if status in HINTS_BY_STATUS:
        return HINTS_BY_STATUS[status]
    if status is not None and status >= 500:
        return SERVER_ERROR_HINT
    if "guardrail validation" in str(error):
        return GUARDRAIL_HINT
    return DEFAULT_HINT


def describe_failure(error: BaseException, finished_steps: list[str], api_key: str) -> str:
    """Build the two-line "Step N/3 (...) failed" message, never showing the API key."""
    step_number = min(len(finished_steps) + 1, len(STEP_NAMES))
    step_name = STEP_NAMES[step_number - 1]

    message = (
        f"Error: Step {step_number}/3 ({step_name}) failed: {short_reason(error)}. "
        "No files were written.\n"
        f"Hint: {hint_for(error)}"
    )
    return message.replace(api_key, "***")
