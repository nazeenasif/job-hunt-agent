---
id: 10
title: Two-Level Truthfulness Check
stage: green
date: 2026-10-24
surface: agent
model: claude-opus-5-5
feature: 001-job-hunt-agent-cli
branch: 001-job-hunt-agent-cli
user: Nazeen Asif
command: follow-up to /sp.implement
labels: ["truthfulness-check", "review-warnings", "cleanup"]
links:
  spec: specs/001-job-hunt-agent-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - src/job_hunt_agent/checks.py
 - src/job_hunt_agent/report.py
 - src/job_hunt_agent/cli.py
 - README.md
 - specs/001-job-hunt-agent-cli/spec.md
 - specs/001-job-hunt-agent-cli/tasks.md
 - specs/001-job-hunt-agent-cli/contracts/cli.md
 - specs/001-job-hunt-agent-cli/contracts/output-files.md
tests:
 - tests/unit/test_checks.py
 - tests/unit/test_report.py
 - tests/unit/test_cli.py
 - tests/unit/test_no_prompts.py
---

## Prompt

Decisions:
- Keep allowing job-posting skills in improvements ("Learn Docker").
- Split the truthfulness check into two levels: hard fail (exit 1) for invented numbers, tools, employers, titles or dates; review warning (exit 0) for posting phrases not found verbatim in the resume, printed as a short "Check these rewordings are true:" list and added to the end of tailored_resume.md. Update spec, tests and README.
- Delete the three old CrewAI storage folders.
Run the full suite, then stop.

## Response snapshot

Added is_tool_like() (a single-word term, or a phrase containing a name or tech word not
in the resume, counts as a tool) and find_rewordings_to_review(). find_unverified_items()
now returns hard failures only. add_review_section() appends "## Check these rewordings
are true" at the end; the CLI prints the list and leaves the exit code at 0 unless there
are hard failures. Updated spec (FR-020a plus an edge case), contracts, README and tasks
(T052). Deleted the CrewAI storage folders realrun, smoke and job-hunt-agent;
test_no_prompts now sends CrewAI storage to tmp_path. 87 tests pass.

## Outcome

- ✅ Impact: Fair rewordings no longer fail a run; invented facts still do
- 🧪 Tests: 87 passed (8 new)
- 📁 Files: see list above
- 🔁 Next prompts: optional real rerun; commit when ready
- 🧠 Reflection: Classifying posting terms by whether they carry a name or tech word keeps "Apache Spark" hard and "batch data pipelines" soft

## Evaluation notes (flywheel)

- Failure modes observed: importing crewai creates an empty %LOCALAPPDATA%\CrewAI\<cwd name> folder; unavoidable without setting CREWAI_STORAGE_DIR before import
- Graders run and results (PASS/FAIL): pytest 87/87 PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
