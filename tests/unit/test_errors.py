from job_hunt_agent.errors import describe_failure, hint_for, short_reason

CREDITS_MESSAGE = (
    "This request requires more credits, or fewer max_tokens. You requested up to "
    "64000 tokens, but can only afford 551."
)


class FakeAPIError(Exception):
    """Looks like the openai SDK's APIStatusError: has status_code and body."""

    def __init__(self, status_code, body):
        super().__init__(f"Error code: {status_code} - {body}")
        self.status_code = status_code
        self.body = body


def credits_error():
    body = {"error": {"message": CREDITS_MESSAGE, "code": 402}, "user_id": "user_1"}
    return FakeAPIError(402, body)


def test_short_reason_uses_only_the_api_message():
    assert short_reason(credits_error()) == CREDITS_MESSAGE + " (HTTP 402)"


def test_short_reason_finds_message_in_text_when_there_is_no_body():
    error = RuntimeError("Error code: 400 - {'error': {'message': 'x/y is not a valid model ID', 'code': 400}}")
    assert short_reason(error) == "x/y is not a valid model ID"


def test_short_reason_looks_through_wrapped_errors():
    try:
        try:
            raise credits_error()
        except FakeAPIError as inner:
            raise RuntimeError("wrapper") from inner
    except RuntimeError as outer:
        assert hint_for(outer).startswith("Add credits")


def test_short_reason_for_plain_error_is_type_and_first_line():
    assert short_reason(RuntimeError("boom\nmore")) == "RuntimeError: boom"


def test_hint_for_credits():
    assert "openrouter.ai/settings/credits" in hint_for(credits_error())
    assert "MAX_OUTPUT_TOKENS" in hint_for(credits_error())


def test_hint_for_bad_model_and_bad_key():
    assert "OPENROUTER_MODEL" in hint_for(FakeAPIError(400, {}))
    assert "OPENROUTER_API_KEY" in hint_for(FakeAPIError(401, {}))


def test_hint_for_server_error_and_guardrail_and_default():
    assert "Try again later" in hint_for(FakeAPIError(503, {}))
    assert "more capable" in hint_for(Exception("Task failed guardrail validation after 2 retries."))
    assert "--debug" in hint_for(RuntimeError("boom"))


def test_describe_failure_is_two_lines_with_step_and_hint():
    message = describe_failure(credits_error(), [], "key-123")
    first, second = message.splitlines()
    assert first == f"Error: Step 1/3 (Research) failed: {CREDITS_MESSAGE} (HTTP 402). No files were written."
    assert second.startswith("Hint: Add credits")


def test_describe_failure_hides_api_key():
    error = FakeAPIError(401, {"error": {"message": "bad key sk-secret-123"}})
    assert "sk-secret-123" not in describe_failure(error, [], "sk-secret-123")
