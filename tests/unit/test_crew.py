from job_hunt_agent.config import Settings
from job_hunt_agent.crew import make_llm


def test_make_llm_uses_max_output_tokens():
    llm = make_llm(Settings(api_key="key-123", model="x/y", max_output_tokens=1234))
    assert llm.max_tokens == 1234
