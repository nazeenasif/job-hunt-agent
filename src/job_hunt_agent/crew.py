"""Wire the three agents and tasks into one crew and run it."""

import os
from dataclasses import dataclass

# Your resume must only ever go to the model you chose, so turn off CrewAI's
# anonymous telemetry and its trace collection/sharing. This is done before
# CrewAI is loaded, so it applies from the very start.
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

from crewai import LLM, Crew, Process  # noqa: E402
from crewai.tasks.task_output import TaskOutput  # noqa: E402

from job_hunt_agent.agents.matcher import make_matcher
from job_hunt_agent.agents.researcher import make_researcher
from job_hunt_agent.agents.writer import make_writer
from job_hunt_agent.config import OPENROUTER_BASE_URL, Settings, full_model_name
from job_hunt_agent.models import JobAnalysis, MatchReport
from job_hunt_agent.report import render_job_analysis, render_matches
from job_hunt_agent.tasks import (
    make_match_task,
    make_research_task,
    make_write_task,
    read_match_report,
    remove_code_fence,
)

@dataclass
class CrewResult:
    """Everything the three steps produced."""

    analysis: JobAnalysis
    report: MatchReport
    resume_md: str


def make_llm(settings: Settings) -> LLM:
    """Create the CrewAI LLM that talks to OpenRouter."""
    return LLM(
        model=full_model_name(settings.model),
        base_url=OPENROUTER_BASE_URL,
        api_key=settings.api_key,
        max_tokens=settings.max_output_tokens,
    )


def run_crew(
    settings: Settings, job_posting: str, resume: str, progress: list[str] | None = None
) -> CrewResult:
    """Run Researcher -> Matcher -> Writer in order and return their results.

    Each finished step's name is added to `progress`, so if something fails
    the caller can tell the user which step it was.
    """
    if progress is None:
        progress = []

    def after_research(output: TaskOutput) -> None:
        """Called by CrewAI when step 1 finishes: show the job analysis."""
        print(render_job_analysis(output.pydantic))
        progress.append("Research")
        print("Step 2/3: Matching your resume to the job...")

    def after_matching(output: TaskOutput) -> None:
        """Called by CrewAI when step 2 finishes: show the match report."""
        print(render_matches(read_match_report(output)))
        progress.append("Matching")
        print("Step 3/3: Writing your tailored resume...")

    def after_writing(output: TaskOutput) -> None:
        """Called by CrewAI when step 3 finishes."""
        progress.append("Writing")

    llm = make_llm(settings)
    researcher = make_researcher(llm)
    matcher = make_matcher(llm)
    writer = make_writer(llm)

    research_task = make_research_task(researcher)
    match_task = make_match_task(matcher, research_task, resume)
    write_task = make_write_task(writer, research_task, match_task)

    research_task.callback = after_research
    match_task.callback = after_matching
    write_task.callback = after_writing

    crew = Crew(
        agents=[researcher, matcher, writer],
        tasks=[research_task, match_task, write_task],
        process=Process.sequential,
        verbose=False,
        tracing=False,  # never collect traces or ask to share them
    )

    print("Step 1/3: Researching the job posting...")
    crew.kickoff(inputs={"job_posting": job_posting, "resume": resume})

    return CrewResult(
        analysis=research_task.output.pydantic,
        report=read_match_report(match_task.output),
        resume_md=remove_code_fence(write_task.output.raw) + "\n",
    )
