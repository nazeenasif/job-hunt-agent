---
id: 7
title: Cap Tokens and Short API Errors
stage: green
date: 2026-10-24
surface: agent
model: claude-opus-5-5
feature: 001-job-hunt-agent-cli
branch: 001-job-hunt-agent-cli
user: Nazeen Asif
command: follow-up to /sp.implement
labels: ["max-tokens", "error-messages", "debug-flag", "openrouter"]
links:
  spec: specs/001-job-hunt-agent-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - src/job_hunt_agent/config.py
 - src/job_hunt_agent/crew.py
 - src/job_hunt_agent/errors.py
 - src/job_hunt_agent/cli.py
 - .env.example
 - README.md
 - specs/001-job-hunt-agent-cli/spec.md
 - specs/001-job-hunt-agent-cli/plan.md
 - specs/001-job-hunt-agent-cli/data-model.md
 - specs/001-job-hunt-agent-cli/contracts/cli.md
 - specs/001-job-hunt-agent-cli/research.md
 - specs/001-job-hunt-agent-cli/tasks.md
tests:
 - tests/unit/test_config.py
 - tests/unit/test_crew.py
 - tests/unit/test_errors.py
 - tests/unit/test_cli.py
---

## Prompt

Yes, make both changes:
1. Set max_tokens=4000 on the LLM in crew.py, and make it configurable via an optional MAX_OUTPUT_TOKENS in .env (default 4000). Update .env.example and the spec/plan to match.
2. On API failures, print only the human-readable message (e.g. the 402 "requires more credits" text) plus a one-line hint, keep exit code 3 and the failing step name, and suppress CrewAI's duplicate ERROR log lines. Keep the full JSON available behind a --debug flag.
Then run the existing tests. Don't rerun the real API call yet. I'll switch the model in .env and tell you "rerun".

## Response snapshot

Added optional MAX_OUTPUT_TOKENS (default 4000, validated as a setup error) and passed it
as max_tokens to crewai.LLM. Added errors.py, which pulls the readable message from the
API error body (regex fallback), appends (HTTP code), and adds a one-line hint chosen by
status code. Added --debug: by default logging.disable(CRITICAL) hides CrewAI's ERROR
lines during the run; with --debug the logs stay on and the full error text is printed,
key masked. Appended the commented setting to .env.example without reading it. Updated
spec (two clarifications, FR-018a, FR-018b, FR-021), plan, data-model, contracts/cli.md,
research notes, tasks (T045–T048) and README. 67 tests pass; no live API call was made.
CrewAIEventsBus mismatch warnings are printed directly by CrewAI and can only be silenced
through a private setting, so they were left as they are.

## Outcome

- ✅ Impact: Runs reserve at most 4000 output tokens; failures show one readable line plus a hint
- 🧪 Tests: 67 passed (18 new)
- 📁 Files: see list above
- 🔁 Next prompts: user switches model in .env, then "rerun" for T026/T033/T044
- 🧠 Reflection: Reading CrewAI's source showed the log noise came from logging.error's implicit basicConfig, so the fix is one line

## Evaluation notes (flywheel)

- Failure modes observed: a heredoc expanded \n inside an f-string (fixed); one plan edit anchor mismatch (retried)
- Graders run and results (PASS/FAIL): pytest PASS 67/67; offline CLI checks PASS (--help, invalid MAX_OUTPUT_TOKENS → exit 2)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
