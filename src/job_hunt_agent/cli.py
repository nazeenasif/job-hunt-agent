"""The `job-hunt` command: check inputs, run the agents, check the result, save files."""

import argparse
import logging
import sys
from pathlib import Path

from job_hunt_agent.checks import find_rewordings_to_review, find_unverified_items
from job_hunt_agent.config import SetupError, load_settings
from job_hunt_agent.errors import describe_failure
from job_hunt_agent.inputs import read_input_file
from job_hunt_agent.output import write_text_safely
from job_hunt_agent.report import add_review_section, add_unverified_notice, render_match_report

EXIT_OK = 0
EXIT_UNVERIFIED = 1
EXIT_SETUP = 2
EXIT_AI_FAILED = 3

TAILORED_RESUME_FILE = "tailored_resume.md"
MATCH_REPORT_FILE = "match_report.md"


def build_parser() -> argparse.ArgumentParser:
    """Describe the command-line options."""
    parser = argparse.ArgumentParser(
        prog="job-hunt",
        description="Tailor your resume to a job posting using only true facts.",
    )
    parser.add_argument("--job", default="job_posting.txt", help="job posting file (plain text)")
    parser.add_argument("--resume", default="resume.md", help="your resume (Markdown)")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="show CrewAI's log messages and the full error details if a step fails",
    )
    return parser


def save(path: Path, text: str) -> None:
    """Write a file and tell the user where it went."""
    overwrote = write_text_safely(path, text)
    if overwrote:
        print(f"Note: overwrote existing {path.resolve()}")
    print(f"Saved: {path.resolve()}")


def main(argv: list[str] | None = None) -> int:
    """Run the whole tool and return the exit code."""
    args = build_parser().parse_args(argv)

    # 1. Check everything we can before spending any AI calls.
    try:
        settings = load_settings()
        job_posting = read_input_file(Path(args.job), "job posting")
        resume = read_input_file(Path(args.resume), "resume")
    except SetupError as error:
        print(error, file=sys.stderr)
        return EXIT_SETUP

    # 2. Run the three agents. Nothing is written until all of them succeed.
    # CrewAI takes several seconds to load, so we import it only now, after
    # the quick checks above have passed.
    from job_hunt_agent import crew

    if not args.debug:
        # CrewAI logs every failed API call as a long ERROR line. We print our
        # own short message instead, so hide CrewAI's logs unless --debug is on.
        logging.disable(logging.CRITICAL)

    finished_steps: list[str] = []
    try:
        result = crew.run_crew(settings, job_posting, resume, finished_steps)
    except Exception as error:
        print(describe_failure(error, finished_steps, settings.api_key), file=sys.stderr)
        if args.debug:
            full_details = str(error).replace(settings.api_key, "***")
            print("Full error details:", file=sys.stderr)
            print(full_details, file=sys.stderr)
        return EXIT_AI_FAILED
    finally:
        logging.disable(logging.NOTSET)

    # 3. Check the tailored resume against the original, at two levels:
    #    invented facts are a hard failure (exit 1); reworded job-posting
    #    phrases are only a warning for the user to check (exit 0).
    unverified = find_unverified_items(result.resume_md, resume, result.analysis)
    rewordings = find_rewordings_to_review(result.resume_md, resume, result.analysis)
    tailored = add_review_section(result.resume_md, rewordings)
    tailored = add_unverified_notice(tailored, unverified)

    # 4. Save both files.
    save(Path(MATCH_REPORT_FILE), render_match_report(result.analysis, result.report))
    save(Path(TAILORED_RESUME_FILE), tailored)

    if rewordings:
        print("Check these rewordings are true:")
        for phrase in rewordings:
            print(f"  - {phrase}")

    if unverified:
        print(f"Warning: {len(unverified)} unverified item(s) found — "
              f"review the top of {TAILORED_RESUME_FILE}:")
        for item in unverified:
            print(f"  - {item.text} ({item.kind})")
        return EXIT_UNVERIFIED

    return EXIT_OK
