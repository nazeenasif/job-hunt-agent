"""The three tasks: what each agent is asked to do.

`{job_posting}` and `{resume}` are filled in by CrewAI from the inputs passed
to `crew.kickoff()`.
"""

from typing import Any

from crewai import Agent, Task
from crewai.tasks.task_output import TaskOutput
from pydantic import ValidationError

from job_hunt_agent.checks import check_match_report
from job_hunt_agent.models import JobAnalysis, MatchReport

MATCH_GUARDRAIL_RETRIES = 2

RESEARCH_DESCRIPTION = """Read this job posting and extract what it asks for.

JOB POSTING:
---
{job_posting}
---

Rules:
- Use ONLY what the posting says. Do not add requirements it does not state.
- title: the job title, or "Not stated".
- seniority: the level (e.g. Junior, Mid, Senior, Lead). If the posting does not
  say, write "Not stated", or give your best guess ending in " (inferred)".
- must_have_skills: the 5 to 8 most important REQUIRED skills. If the posting
  states fewer than 5, list only those. Never pad the list.
- nice_to_have_skills: skills marked as preferred, a plus, or bonus.
- responsibilities: the main duties, close to the posting's own words.
- ats_keywords: important keywords and phrases that appear in the posting.
"""

MATCH_DESCRIPTION = """Compare this resume to the job analysis from the previous step.

RESUME:
---
{resume}
---

Put EVERY must-have skill from the job analysis into exactly ONE of these lists:
- strong_matches: the resume clearly shows this skill. Give a proof_line that is
  copied WORD-FOR-WORD from the resume (one line or sentence). Leave note empty.
- weak_matches: the resume shows a related skill or partial experience. Give a
  proof_line copied WORD-FOR-WORD from the resume AND a one-line note explaining
  the connection.
- gaps: there is no resume line you can quote. Just give the skill name.

Then give exactly 3 top_improvements. Each must be honest: reorder, reword or
emphasize something already in the resume, or a real-world action like learning
a skill. Never suggest claiming something that is not true.
- Do NOT write any number, tool, product or company name that is not in the
  resume (skills from the job posting are fine, e.g. "Learn Docker").
- If you suggest adding a detail the candidate might have, use a placeholder
  in square brackets and add "only if true", for example:
  "Add the share of bad rows your checks caught, e.g. [X]%, only if true."
  "Name the [tool] you used for data quality checks, only if true."
"""

WRITE_DESCRIPTION = """Rewrite the resume below for this job, using the job analysis and match
report from the previous steps.

ORIGINAL RESUME:
---
{resume}
---

STRICT RULES (breaking any of these is a failure):
1. Use ONLY facts from the original resume. Do NOT add any skill, tool,
   employer, job title, date or number (metrics, percentages, team sizes,
   years of experience) that is not in the original resume.
   Never compute or state durations or totals (e.g. "three years of
   experience", "5+ years", "over 20 pipelines in total"), even if they could
   be worked out from the dates or other numbers. Only write numbers exactly
   as they appear in the original resume.
2. Keep EVERY job and education entry, each with its employer or school,
   title and dates exactly as written.
3. You MAY reorder sections and bullet points so the most relevant experience
   comes first, reword sentences, and use the job's keywords ONLY where the
   original resume truly supports them.
4. You MAY shorten or drop bullet points and listed skills that are not
   relevant to this job. Never drop a whole job or education entry.
5. End with exactly these two sections, in this order:

## What I changed
- one bullet per change (what you reordered, reworded, emphasized or removed)

## Gaps to work on
- one bullet for every item in the match report's gaps list
  (write "- None found" if there are none)

Return only the Markdown resume. Do not wrap it in a code block.
"""


def remove_code_fence(text: str) -> str:
    """Remove a ``` code block wrapper if the model added one."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()[1:]  # drop the opening ``` or ```json line
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def read_match_report(output: TaskOutput) -> MatchReport:
    """Get the MatchReport from a task output, parsing the raw JSON if needed."""
    if isinstance(output.pydantic, MatchReport):
        return output.pydantic
    return MatchReport.model_validate_json(remove_code_fence(output.raw))


def make_research_task(agent: Agent) -> Task:
    """Step 1: turn the job posting into a JobAnalysis."""
    return Task(
        description=RESEARCH_DESCRIPTION,
        expected_output="A JobAnalysis with title, seniority, skills, responsibilities and ATS keywords.",
        agent=agent,
        output_pydantic=JobAnalysis,
    )


def make_match_task(agent: Agent, research_task: Task, resume: str) -> Task:
    """Step 2: compare the resume to the JobAnalysis and produce a MatchReport.

    A guardrail checks the answer in plain Python. If a proof line is not really
    in the resume (or a rule is broken), the problems are sent back to the agent
    so it can try again.
    """

    def guardrail(output: TaskOutput) -> tuple[bool, Any]:
        """Return (True, output) if the report passes, else (False, what to fix)."""
        try:
            report = read_match_report(output)
        except ValidationError as error:
            return (False, f"Your answer was not a valid MatchReport: {error}")

        analysis = research_task.output.pydantic
        problems = check_match_report(report, analysis, resume)
        if problems:
            return (False, "Fix these problems:\n- " + "\n- ".join(problems))

        output.pydantic = report
        return (True, output)

    return Task(
        description=MATCH_DESCRIPTION,
        expected_output="A MatchReport with strong matches, weak matches, gaps and 3 improvements.",
        agent=agent,
        context=[research_task],
        output_pydantic=MatchReport,
        guardrail=guardrail,
        guardrail_max_retries=MATCH_GUARDRAIL_RETRIES,
    )


def make_write_task(agent: Agent, research_task: Task, match_task: Task) -> Task:
    """Step 3: rewrite the resume, ending with "What I changed" and "Gaps to work on"."""
    return Task(
        description=WRITE_DESCRIPTION,
        expected_output=(
            "The full tailored resume in Markdown, ending with the sections "
            "'## What I changed' and '## Gaps to work on'."
        ),
        agent=agent,
        context=[research_task, match_task],
    )
