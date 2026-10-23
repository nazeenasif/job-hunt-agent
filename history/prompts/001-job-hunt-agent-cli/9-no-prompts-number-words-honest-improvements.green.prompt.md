---
id: 9
title: No Prompts, Number Words, Honest Improvements
stage: green
date: 2026-10-24
surface: agent
model: claude-opus-5-5
feature: 001-job-hunt-agent-cli
branch: 001-job-hunt-agent-cli
user: Nazeen Asif
command: follow-up to /sp.implement
labels: ["privacy", "tracing", "truthfulness-check", "guardrail"]
links:
  spec: specs/001-job-hunt-agent-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - src/job_hunt_agent/crew.py
 - src/job_hunt_agent/checks.py
 - src/job_hunt_agent/tasks.py
 - README.md
 - specs/001-job-hunt-agent-cli/spec.md
 - specs/001-job-hunt-agent-cli/tasks.md
tests:
 - tests/unit/test_no_prompts.py
 - tests/unit/test_checks.py
 - tests/unit/test_tasks.py
---

## Prompt

Yes, do all three, with these adjustments:
3 (do first): Disable CrewAI's trace-sharing prompt and any telemetry. Verify with one real run that no prompt appears, and add a test that fails if the run ever waits for input.
1: Flag number words only when next to units (years, months, people, projects, %, etc.), not every "one". Also add to the Writer's instructions: never compute or state durations or totals, even if derivable from dates.
2: Improvements may suggest adding details the candidate might have, but only with placeholders like [X]% or [tool], plus "only if true". Reject improvements with concrete numbers or tool/company names not in the resume, and retry as with proof lines.
Add tests for each, run the full suite, then stop. Don't commit yet.

## Response snapshot

3: crew.py sets CREWAI_DISABLE_TELEMETRY, OTEL_SDK_DISABLED and CREWAI_TRACING_ENABLED=false
before CrewAI loads, and passes Crew(tracing=False). The new test_no_prompts.py runs the
real crew offline with a fake BaseLLM, fresh CrewAI user-data state and a recording stdin,
and asserts that stdin/input() are never touched and no trace prompt is printed. It was
confirmed to FAIL before the fix. One real run with a fresh CREWAI_STORAGE_DIR: no prompt,
no consent file, 85 s, exit 1 (two posting phrases flagged).
1: find_new_number_words() flags number words followed by a unit; it accepts the digit
form found in the resume; the Writer prompt forbids computed durations and totals.
2: check_improvement() in the Matcher guardrail rejects numbers and names not found in the
resume or job posting, and requires "only if true" with [placeholders]; the match prompt
shows examples. 79 tests pass. Spec (FR-011a, FR-012a, FR-019, FR-022), tasks (T049–T051)
and README updated. Not committed.

## Outcome

- ✅ Impact: No vendor telemetry or trace prompts; two Principle II gaps from the live run closed
- 🧪 Tests: 79 passed (12 new)
- 📁 Files: see list above
- 🔁 Next prompts: optional real rerun to see the new guardrail live; commit when ready
- 🧠 Reflection: The first no-prompt test passed for the wrong reason (saved "declined" state); isolating CrewAI's user data made it a real test

## Evaluation notes (flywheel)

- Failure modes observed: heredoc and Windows newline handling corrupted escapes in checks.py (fixed with exact edits); two false positives ("ten+", "e.g") fixed
- Graders run and results (PASS/FAIL): pytest 79/79 PASS; live no-prompt run PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): consider not flagging multi-word ATS phrases that only paraphrase resume content
