"""Run the real crew (with a fake model, no network) and make sure it never asks for input.

CrewAI can pause a run to ask "Share this execution trace with CrewAI?". That
would upload the user's resume, so the run must never show it or read stdin.
"""

import builtins
import json
import sys

import crewai_core.user_data
from crewai.llms.base_llm import BaseLLM

from job_hunt_agent import crew
from job_hunt_agent.config import Settings

RESUME = "# Sam Lee\n- Wrote SQL.\n"

ANALYSIS_JSON = json.dumps({
    "title": "Data Engineer",
    "seniority": "Mid",
    "must_have_skills": ["SQL"],
    "nice_to_have_skills": [],
    "responsibilities": ["Build pipelines"],
    "ats_keywords": ["SQL"],
})

REPORT_JSON = json.dumps({
    "strong_matches": [{"requirement": "SQL", "proof_line": "Wrote SQL.", "note": ""}],
    "weak_matches": [],
    "gaps": [],
    "top_improvements": [
        "Move the SQL bullet to the top.",
        "Reword the summary to lead with SQL.",
        "Learn dbt.",
    ],
})

TAILORED_MD = "# Sam Lee\n- Wrote SQL.\n\n## What I changed\n- Nothing.\n\n## Gaps to work on\n- None found\n"


class FakeLLM(BaseLLM):
    """A stand-in model that answers each step with a fixed reply."""

    def call(self, messages, tools=None, callbacks=None, available_functions=None,
             from_task=None, from_agent=None, response_model=None):
        text = messages if isinstance(messages, str) else json.dumps(messages)
        if "Read this job posting" in text:
            answer = ANALYSIS_JSON
        elif "Compare this resume" in text:
            answer = REPORT_JSON
        else:
            answer = TAILORED_MD
        return "Thought: I know the answer.\nFinal Answer: " + answer


class RecordingStdin:
    """Pretends to be an interactive terminal and records every attempt to read it."""

    def __init__(self):
        self.reads = []

    def isatty(self):
        return True

    def readline(self, *args):
        self.reads.append("readline")
        raise RuntimeError("the run tried to wait for input")

    def read(self, *args):
        self.reads.append("read")
        raise RuntimeError("the run tried to wait for input")


def test_full_run_never_waits_for_input(monkeypatch, capsys, tmp_path):
    # CrewAI remembers past answers in a user-data file; a fresh file makes this
    # look like a first run on a new machine, which is when it asks.
    monkeypatch.setattr(
        crewai_core.user_data, "_user_data_file", lambda: tmp_path / ".crewai_user.json"
    )
    # Keep CrewAI's local copy of task outputs in the temp folder, not in AppData.
    monkeypatch.setenv("CREWAI_STORAGE_DIR", str(tmp_path / "crewai_storage"))
    stdin = RecordingStdin()
    input_calls = []

    def fake_input(*args):
        input_calls.append(args)
        raise RuntimeError("the run tried to wait for input")

    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(builtins, "input", fake_input)
    # CREWAI_TESTING hides CrewAI's prompts, which would hide the problem we test for.
    monkeypatch.delenv("CREWAI_TESTING", raising=False)
    monkeypatch.setattr(crew, "make_llm", lambda settings: FakeLLM(model="fake"))

    result = crew.run_crew(Settings(api_key="key-123", model="x/y"), "We need SQL.", RESUME)

    printed = capsys.readouterr().out
    assert result.analysis.title == "Data Engineer"
    assert stdin.reads == []
    assert input_calls == []
    assert "Share this execution trace" not in printed
    assert "Execution Traces" not in printed
