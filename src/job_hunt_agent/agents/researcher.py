"""Researcher agent: reads the job posting and pulls out what it asks for."""

from crewai import LLM, Agent


def make_researcher(llm: LLM) -> Agent:
    """Create the agent whose only job is to analyze the job posting."""
    return Agent(
        role="Job Posting Researcher",
        goal="Extract exactly what the job posting asks for, and nothing it does not say.",
        backstory=(
            "You are a careful recruiter who reads job ads closely. You report only "
            "what the posting actually states, and you clearly mark anything you "
            "had to infer."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )
