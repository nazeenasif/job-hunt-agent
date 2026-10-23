"""Turn results into the Markdown text we save and print."""

from job_hunt_agent.models import JobAnalysis, MatchItem, MatchReport, UnverifiedItem


def bullet_list(items: list[str]) -> str:
    """Turn a list into Markdown bullets, or "- None" if it is empty."""
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)


def render_job_analysis(analysis: JobAnalysis) -> str:
    """The "Job Analysis" section of the match report."""
    return (
        "## Job Analysis\n"
        f"- **Title**: {analysis.title}\n"
        f"- **Seniority**: {analysis.seniority}\n\n"
        f"### Must-have skills\n{bullet_list(analysis.must_have_skills)}\n\n"
        f"### Nice-to-have skills\n{bullet_list(analysis.nice_to_have_skills)}\n\n"
        f"### Responsibilities\n{bullet_list(analysis.responsibilities)}\n\n"
        f"### ATS keywords\n{bullet_list(analysis.ats_keywords)}\n"
    )


def match_line(item: MatchItem) -> str:
    """One match as text: requirement, quoted proof, and the note if there is one."""
    line = f'**{item.requirement}** — "{item.proof_line}"'
    if item.note:
        line += f" — {item.note}"
    return line


def render_matches(report: MatchReport) -> str:
    """The STRONG / WEAK / GAPS / TOP 3 part of the match report."""
    strong = [match_line(item) for item in report.strong_matches]
    weak = [match_line(item) for item in report.weak_matches]
    improvements = "\n".join(
        f"{number}. {text}" for number, text in enumerate(report.top_improvements, start=1)
    )
    return (
        f"## STRONG MATCHES\n{bullet_list(strong)}\n\n"
        f"## WEAK MATCHES\n{bullet_list(weak)}\n\n"
        f"## GAPS\n{bullet_list(report.gaps)}\n\n"
        f"## TOP 3 IMPROVEMENTS\n{improvements}\n"
    )


def render_match_report(analysis: JobAnalysis, report: MatchReport) -> str:
    """The full text saved to match_report.md."""
    return "# Match Report\n\n" + render_job_analysis(analysis) + "\n" + render_matches(report)


def add_review_section(resume_md: str, rewordings: list[str]) -> str:
    """Add a "Check these rewordings are true" section at the end, if there is anything to check."""
    if not rewordings:
        return resume_md

    lines = [
        "## Check these rewordings are true",
        "These phrases come from the job posting and are not word-for-word in your",
        "original resume. Keep them only if they describe what you really did.",
        "",
    ]
    for phrase in rewordings:
        lines.append(f'- "{phrase}"')

    return resume_md.rstrip("\n") + "\n\n" + "\n".join(lines) + "\n"


def add_unverified_notice(resume_md: str, items: list[UnverifiedItem]) -> str:
    """Put a "⚠ Unverified items" warning block at the top of the resume, if needed."""
    if not items:
        return resume_md

    notice_lines = [
        "> ⚠ Unverified items — these were not found in your original resume. Check each one",
        "> before sending:",
    ]
    for item in items:
        notice_lines.append(f"> - {item.text} ({item.kind})")

    return "\n".join(notice_lines) + "\n\n" + resume_md
