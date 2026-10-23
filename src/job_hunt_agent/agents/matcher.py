"""Matcher agent: compares the resume to the job requirements."""

from crewai import LLM, Agent


def make_matcher(llm: LLM) -> Agent:
    """Create the agent whose only job is to match the resume against the job."""
    return Agent(
        role="Resume Matcher",
        goal=(
            "Compare the resume to the job requirements honestly, quoting proof "
            "word-for-word from the resume."
        ),
        backstory=(
            "You are a fair, skeptical hiring manager. You only count a skill as "
            "matched when you can point to the exact resume line that shows it."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )
