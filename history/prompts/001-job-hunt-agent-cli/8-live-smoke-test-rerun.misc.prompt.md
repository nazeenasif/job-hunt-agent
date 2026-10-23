---
id: 8
title: Live Smoke Test Rerun
stage: misc
date: 2026-10-24
surface: agent
model: claude-opus-5-5
feature: 001-job-hunt-agent-cli
branch: 001-job-hunt-agent-cli
user: Nazeen Asif
command: rerun
labels: ["smoke-test", "openrouter", "validation"]
links:
  spec: specs/001-job-hunt-agent-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-job-hunt-agent-cli/tasks.md
tests:
 - live run on examples/ (exit 0, 93 s)
---

## Prompt

rerun

## Response snapshot

Ran job-hunt on examples/ in a scratch folder with the project .env copied unread
(shell OPENROUTER_* unset; copy deleted afterwards). Exit 0 in 93 s (SC-001 met). All 6
proof lines were found in the resume; all 4 job/education entries were kept with their
dates; the most relevant job comes first; Docker is listed under GAPS and "Gaps to work
on"; the truthfulness check flagged nothing. Findings: (1) the summary says "three years",
a spelled-out number the check does not catch; (2) TOP 3 improvement #3 suggests an
invented tool and metric ("Great Expectations… 95%"), which breaks FR-011, and the
guardrail does not check improvements; (3) CrewAI showed an interactive "Share this
execution trace with CrewAI? [y/N] (20s timeout)" prompt mid-run. T026/T033/T044 marked done.

## Outcome

- ✅ Impact: End-to-end flow verified live; three quality issues found
- 🧪 Tests: live smoke test PASS (exit 0); proof-line and kept-entry checks PASS
- 📁 Files: specs/001-job-hunt-agent-cli/tasks.md
- 🔁 Next prompts: decide on fixes for spelled-out numbers, improvement suggestions that invent facts, and the CrewAI trace prompt
- 🧠 Reflection: The deterministic check passed while two Principle II slips got through, so the check has real limits

## Evaluation notes (flywheel)

- Failure modes observed: spelled-out numbers bypass the check; LLM invents facts in improvement suggestions; third-party interactive prompt
- Graders run and results (PASS/FAIL): SC-001 PASS (93 s); SC-003 PASS (6/6); FR-013a PASS; FR-011 FAIL (improvement #3)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): add number words to the check; extend the guardrail to reject improvements containing numbers/names not in the resume
