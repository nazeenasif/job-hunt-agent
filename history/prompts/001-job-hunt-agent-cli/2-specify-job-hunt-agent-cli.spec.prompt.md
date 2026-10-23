---
id: 2
title: Specify Job Hunt Agent CLI
stage: spec
date: 2026-10-24
surface: agent
model: claude-opus-5-5
feature: 001-job-hunt-agent-cli
branch: 001-job-hunt-agent-cli
user: Nazeen Asif
command: /sp.specify
labels: ["spec", "resume", "agents", "cli", "truthfulness"]
links:
  spec: specs/001-job-hunt-agent-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-job-hunt-agent-cli/spec.md
 - specs/001-job-hunt-agent-cli/checklists/requirements.md
tests:
 - none
---

## Prompt

Build a Job Hunt Agent CLI. Input: job_posting.txt and resume.md. Three CrewAI agents run in sequence:
1. Researcher: extracts title, seniority, 5-8 must-have skills, nice-to-haves, responsibilities, ATS keywords.
2. Matcher: lists STRONG MATCHES (with proof line), WEAK MATCHES, GAPS, and top 3 improvements.
3. Writer: rewrites the resume using only true facts, reorders for relevance, adds "What I changed" and "Gaps to work on".
Output: tailored_resume.md. Clear error messages for a missing input file or missing API key.

## Response snapshot

Created branch 001-job-hunt-agent-cli and spec.md with 3 prioritized stories (P1 tailored
truthful resume, P2 match report in terminal, P3 clear setup errors), 19 functional
requirements (startup checks before AI work, no padded must-haves, exact-quote proof lines,
each must-have in exactly one match bucket, no-fabrication rule + automated post-write
check, no partial output on failure), 6 measurable success criteria, edge cases, and
assumptions. No clarifications needed. Quality checklist passed on first iteration.
create-new-feature.ps1 created the branch but errored on argument parsing; spec file was
present and filled manually.

## Outcome

- ✅ Impact: Feature spec ready for /sp.clarify or /sp.plan
- 🧪 Tests: none (spec stage)
- 📁 Files: spec.md, checklists/requirements.md
- 🔁 Next prompts: /sp.plan (or /sp.clarify to revisit defaults)
- 🧠 Reflection: Applied the truthfulness principle to the Researcher and Matcher too, not just the Writer

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 PositionalParameterNotFound ('prompts') after branch creation
- Graders run and results (PASS/FAIL): spec quality checklist PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): investigate script arg binding on Windows PowerShell 5.1
