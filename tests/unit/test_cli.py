import logging

import pytest

from job_hunt_agent import cli, config, crew
from job_hunt_agent.crew import CrewResult
from job_hunt_agent.models import JobAnalysis, MatchItem, MatchReport

RESUME = "# Sam Lee\n\n### Data Engineer — Acme Corp (2020 - 2023)\n- Wrote SQL.\n"

ANALYSIS = JobAnalysis(
    title="Data Engineer",
    seniority="Mid",
    must_have_skills=["SQL", "Kubernetes"],
    nice_to_have_skills=[],
    responsibilities=["Build pipelines"],
    ats_keywords=["SQL"],
)

REPORT = MatchReport(
    strong_matches=[MatchItem(requirement="SQL", proof_line="- Wrote SQL.")],
    weak_matches=[],
    gaps=["Kubernetes"],
    top_improvements=["Lead with SQL", "Mention Acme first", "Learn Kubernetes"],
)

CLEAN_RESUME = RESUME + "\n## What I changed\n- Nothing big.\n\n## Gaps to work on\n- Kubernetes\n"


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    """Run each test in an empty folder with sample inputs and fake settings."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "load_dotenv", lambda *args: None)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-secret-123")
    monkeypatch.setenv("OPENROUTER_MODEL", "x/y")
    (tmp_path / "job_posting.txt").write_text("We need SQL and Kubernetes.", encoding="utf-8")
    (tmp_path / "resume.md").write_text(RESUME, encoding="utf-8")
    return tmp_path


def fake_crew(resume_md: str):
    """Return a stand-in for run_crew that skips the AI and returns fixed results."""

    def run(settings, job_posting, resume, progress=None):
        return CrewResult(analysis=ANALYSIS, report=REPORT, resume_md=resume_md)

    return run


def test_happy_path_clean_result_exits_0(workdir, monkeypatch, capsys):
    monkeypatch.setattr(crew, "run_crew", fake_crew(CLEAN_RESUME))
    assert cli.main([]) == 0
    tailored = (workdir / "tailored_resume.md").read_text(encoding="utf-8")
    assert tailored == CLEAN_RESUME
    assert "Saved:" in capsys.readouterr().out


def test_happy_path_invented_year_exits_1_with_notice(workdir, monkeypatch, capsys):
    monkeypatch.setattr(crew, "run_crew", fake_crew(CLEAN_RESUME.replace("2020", "2018")))
    assert cli.main([]) == 1
    tailored = (workdir / "tailored_resume.md").read_text(encoding="utf-8")
    assert tailored.startswith("> ⚠ Unverified items")
    assert "2018 (number)" in tailored
    out = capsys.readouterr().out
    assert "Warning: 1 unverified item(s)" in out
    assert "2018 (number)" in out


def test_happy_path_also_writes_match_report(workdir, monkeypatch):
    monkeypatch.setattr(crew, "run_crew", fake_crew(CLEAN_RESUME))
    cli.main([])
    match_report = (workdir / "match_report.md").read_text(encoding="utf-8")
    assert "## STRONG MATCHES" in match_report
    assert '"- Wrote SQL."' in match_report


# --- setup errors and step failures ---


def crew_that_must_not_run(settings, job_posting, resume, progress=None):
    raise AssertionError("run_crew should not be called when setup fails")


def crew_that_fails_in_step_2(settings, job_posting, resume, progress=None):
    progress.append("Research")
    raise RuntimeError("boom\nmore details")


def output_files(folder):
    return sorted(path.name for path in folder.glob("*.md") if path.name != "resume.md")


def test_missing_job_file_exits_2_before_ai(workdir, monkeypatch, capsys):
    (workdir / "job_posting.txt").unlink()
    monkeypatch.setattr(crew, "run_crew", crew_that_must_not_run)
    assert cli.main([]) == 2
    assert "job posting file not found" in capsys.readouterr().err
    assert output_files(workdir) == []


def test_missing_key_exits_2(workdir, monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY")
    monkeypatch.setattr(crew, "run_crew", crew_that_must_not_run)
    assert cli.main([]) == 2
    assert "OPENROUTER_API_KEY is not set" in capsys.readouterr().err


def test_step_failure_exits_3_and_writes_nothing(workdir, monkeypatch, capsys):
    monkeypatch.setattr(crew, "run_crew", crew_that_fails_in_step_2)
    assert cli.main([]) == 3
    err = capsys.readouterr().err
    assert "Step 2/3 (Matching) failed" in err
    assert "RuntimeError: boom" in err
    assert "more details" not in err
    assert "No files were written" in err
    assert output_files(workdir) == []


def test_step_failure_leaves_old_outputs_unchanged(workdir, monkeypatch):
    (workdir / "tailored_resume.md").write_text("old resume", encoding="utf-8")
    (workdir / "match_report.md").write_text("old report", encoding="utf-8")
    monkeypatch.setattr(crew, "run_crew", crew_that_fails_in_step_2)
    assert cli.main([]) == 3
    assert (workdir / "tailored_resume.md").read_text(encoding="utf-8") == "old resume"
    assert (workdir / "match_report.md").read_text(encoding="utf-8") == "old report"


def test_step_failure_message_never_shows_key(workdir, monkeypatch, capsys):
    def leaky_crew(settings, job_posting, resume, progress=None):
        raise RuntimeError("auth failed for key sk-secret-123")

    monkeypatch.setattr(crew, "run_crew", leaky_crew)
    assert cli.main([]) == 3
    err = capsys.readouterr().err
    assert "Step 1/3 (Research) failed" in err
    assert "sk-secret-123" not in err


# --- short API errors, --debug, and CrewAI log noise ---


class FakeCreditsError(Exception):
    def __init__(self):
        body = {"error": {"message": "This request requires more credits", "code": 402}}
        super().__init__(f"Error code: 402 - {body}")
        self.status_code = 402
        self.body = body


def crew_that_runs_out_of_credits(settings, job_posting, resume, progress=None):
    logging.error("OpenAI API call failed: noisy CrewAI log line")
    raise FakeCreditsError()


def test_api_failure_shows_short_message_and_hint(workdir, monkeypatch, capsys, caplog):
    monkeypatch.setattr(crew, "run_crew", crew_that_runs_out_of_credits)
    assert cli.main([]) == 3
    err = capsys.readouterr().err
    assert "Step 1/3 (Research) failed: This request requires more credits (HTTP 402)" in err
    assert "Hint: Add credits" in err
    assert "Error code: 402 - {" not in err
    assert "noisy CrewAI log line" not in caplog.text


def test_debug_flag_shows_full_details_and_logs(workdir, monkeypatch, capsys, caplog):
    monkeypatch.setattr(crew, "run_crew", crew_that_runs_out_of_credits)
    assert cli.main(["--debug"]) == 3
    err = capsys.readouterr().err
    assert "Full error details:" in err
    assert "Error code: 402 - {" in err
    assert "noisy CrewAI log line" in caplog.text


# --- two-level truthfulness check ---

PHRASE_ANALYSIS = ANALYSIS.model_copy(update={"ats_keywords": ["SQL", "batch data pipelines"]})


def test_reworded_phrase_only_warns_and_exits_0(workdir, monkeypatch, capsys):
    reworded = CLEAN_RESUME.replace("- Wrote SQL.", "- Wrote SQL for batch data pipelines.")

    def run(settings, job_posting, resume, progress=None):
        return CrewResult(analysis=PHRASE_ANALYSIS, report=REPORT, resume_md=reworded)

    monkeypatch.setattr(crew, "run_crew", run)
    assert cli.main([]) == 0
    out = capsys.readouterr().out
    assert "Check these rewordings are true:\n  - batch data pipelines" in out
    assert "Warning:" not in out
    tailored = (workdir / "tailored_resume.md").read_text(encoding="utf-8")
    assert not tailored.startswith("> ⚠")
    assert tailored.rstrip().endswith('- "batch data pipelines"')


def test_invented_fact_plus_rewording_exits_1_with_both(workdir, monkeypatch, capsys):
    reworded = CLEAN_RESUME.replace("- Wrote SQL.", "- Wrote SQL for batch data pipelines in 2019.")

    def run(settings, job_posting, resume, progress=None):
        return CrewResult(analysis=PHRASE_ANALYSIS, report=REPORT, resume_md=reworded)

    monkeypatch.setattr(crew, "run_crew", run)
    assert cli.main([]) == 1
    tailored = (workdir / "tailored_resume.md").read_text(encoding="utf-8")
    assert tailored.startswith("> ⚠ Unverified items")
    assert "## Check these rewordings are true" in tailored
