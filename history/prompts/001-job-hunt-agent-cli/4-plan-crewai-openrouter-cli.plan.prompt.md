---
id: 4
title: Plan CrewAI OpenRouter CLI
stage: plan
date: 2026-10-24
surface: agent
model: claude-opus-5-5
feature: 001-job-hunt-agent-cli
branch: 001-job-hunt-agent-cli
user: Nazeen Asif
command: /sp.plan
labels: ["plan", "crewai", "openrouter", "dotenv", "uv", "truthfulness-check"]
links:
  spec: specs/001-job-hunt-agent-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-job-hunt-agent-cli/plan.md
 - specs/001-job-hunt-agent-cli/research.md
 - specs/001-job-hunt-agent-cli/data-model.md
 - specs/001-job-hunt-agent-cli/contracts/cli.md
 - specs/001-job-hunt-agent-cli/contracts/output-files.md
 - specs/001-job-hunt-agent-cli/quickstart.md
tests:
 - none
---

## Prompt

Use CrewAI with LLM routed through OpenRouter (OpenAI-compatible API).
Read OPENROUTER_API_KEY and OPENROUTER_MODEL from .env via python-dotenv. Use a venv or uv.
Keep the agents, tasks and crew in a clear structure. Include .gitignore, .env.example and README.md.

## Response snapshot

Verified the CrewAI OpenRouter setup (LLM model="openrouter/...", base_url
https://openrouter.ai/api/v1, crewai[litellm]) and Task features (output_pydantic, context,
guardrail) against the official docs; checked crewai 1.15.29 supports Python 3.12. Wrote:
- plan.md: Python 3.12 + uv, src/job_hunt_agent with agents/ (one module per agent),
  tasks.py, crew.py, and non-AI modules (config, inputs, checks, report, output);
  .gitignore/.env.example/README.md/pyproject in scope. Constitution Check passes before
  and after design.
- research.md R1–R10: plain modules rather than @CrewBase/YAML, Pydantic outputs, a
  guardrail on the match step only (the writer is flagged, not retried, per clarification
  Q1), a deterministic truthfulness check, atomic writes at the end, exit codes 0/1/2/3,
  and a telemetry/privacy note.
- data-model.md, contracts/cli.md, contracts/output-files.md, quickstart.md.
update-agent-context.ps1 found no tech section to update in CLAUDE.md and only added a
BOM, so that change was reverted.

## Outcome

- ✅ Impact: Plan and design artifacts ready for /sp.tasks
- 🧪 Tests: none (plan stage); unit test layout defined
- 📁 Files: plan.md, research.md, data-model.md, contracts/*, quickstart.md
- 🔁 Next prompts: /sp.tasks; optionally /sp.adr for the structure and truthfulness-check decisions
- 🧠 Reflection: Structured outputs let plain code check proof lines instead of trusting the model

## Evaluation notes (flywheel)

- Failure modes observed: update-agent-context.ps1 made no real change and added a BOM to CLAUDE.md (reverted)
- Graders run and results (PASS/FAIL): Constitution Check PASS (pre and post design)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): verify Task callback signature in installed CrewAI
