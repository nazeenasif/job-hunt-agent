"""Data passed between the agents and the checks.

These are the "plain data" the constitution asks for: each agent returns one of
these, and the next agent (or our own checks) reads it.
"""

from typing import Literal

from pydantic import BaseModel, Field


class JobAnalysis(BaseModel):
    """What the job posting asks for (output of the Researcher)."""

    title: str = Field(description='Job title, or "Not stated"')
    seniority: str = Field(
        description='Seniority level, "Not stated", or a guess ending in " (inferred)"'
    )
    must_have_skills: list[str] = Field(
        description="5-8 required skills; fewer only if the posting states fewer"
    )
    nice_to_have_skills: list[str] = Field(description="Optional / preferred skills")
    responsibilities: list[str] = Field(description="Main duties of the job")
    ats_keywords: list[str] = Field(
        description="Keywords and phrases from the posting that ATS software looks for"
    )


class MatchItem(BaseModel):
    """One requirement matched to a line of the resume."""

    requirement: str = Field(description="A must-have skill from the job analysis")
    proof_line: str = Field(description="A line copied word-for-word from the resume")
    note: str = Field(
        default="",
        description="For weak matches: one line explaining the connection",
    )


class MatchReport(BaseModel):
    """How the resume compares to the job (output of the Matcher)."""

    strong_matches: list[MatchItem]
    weak_matches: list[MatchItem]
    gaps: list[str] = Field(description="Must-have skills with no proof in the resume")
    top_improvements: list[str] = Field(description="Exactly 3 truthful improvements")


class UnverifiedItem(BaseModel):
    """Something in the tailored resume that was not found in the original."""

    text: str
    kind: Literal["number", "skill", "name"]
