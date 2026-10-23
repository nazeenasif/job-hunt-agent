---
id: 1
title: Ratify Job Hunt Agent Constitution
stage: constitution
date: 2026-10-24
surface: agent
model: claude-opus-5-5
feature: none
branch: master
user: Nazeen Asif
command: /sp.constitution
labels: ["constitution", "principles", "security", "simplicity", "truthfulness"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
tests:
 - none
---

## Prompt

Python 3.12 CLI project. Single responsibility per agent. Secrets only from .env, never hardcoded, never committed.
The resume writer must NEVER invent skills, tools, employers, dates or numbers. Only facts from the input resume.
Keep it simple: no web framework, no database. Code must be readable by a beginner.

## Response snapshot

Filled the constitution template as v1.0.0 (ratified 2026-10-24) with five principles:
I. Single Responsibility per Agent; II. Truthful Resume Output (NON-NEGOTIABLE, with an
automated no-fabrication check); III. Secrets Only from .env (NON-NEGOTIABLE); IV. Simplicity
First (no web framework, no DB, justified deps only); V. Beginner-Readable Code. Added
Technology Constraints (Python 3.12, argparse CLI, files only, src/ + tests/) and Development
Workflow & Quality Gates (SDD flow, merge checklist). Dropped unused sixth principle slot.
Templates checked — no edits needed. Flagged missing .gitignore.

## Outcome

- ✅ Impact: Project constitution ratified at v1.0.0
- 🧪 Tests: none (documentation change)
- 📁 Files: .specify/memory/constitution.md
- 🔁 Next prompts: create .gitignore with .env; /sp.specify for the first feature
- 🧠 Reflection: Turned the no-fabrication rule into a testable gate so it can be enforced, not just stated

## Evaluation notes (flywheel)

- Failure modes observed: create-phr.sh not present; used agent-native PHR creation
- Graders run and results (PASS/FAIL): placeholder scan PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
