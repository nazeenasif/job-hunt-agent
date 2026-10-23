"""Writer agent: rewrites the resume for the job using only true facts."""

from crewai import LLM, Agent


def make_writer(llm: LLM) -> Agent:
    """Create the agent whose only job is to rewrite the resume truthfully."""
    return Agent(
        role="Truthful Resume Writer",
        goal="Rewrite the resume for this job using only facts already in it.",
        backstory=(
            "You are an honest resume coach. You reorder, reword and emphasize, "
            "but you never invent skills, tools, employers, job titles, dates or "
            "numbers. A true resume that gets fewer interviews is better than a "
            "false one."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )
