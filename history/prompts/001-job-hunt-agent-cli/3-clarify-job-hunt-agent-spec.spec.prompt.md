---
id: 3
title: Clarify Job Hunt Agent Spec
stage: spec
date: 2026-10-24
surface: agent
model: claude-opus-5-5
feature: 001-job-hunt-agent-cli
branch: 001-job-hunt-agent-cli
user: Nazeen Asif
command: /sp.clarify
labels: ["clarify", "spec", "truthfulness", "match-report", "outputs"]
links:
  spec: specs/001-job-hunt-agent-cli/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-job-hunt-agent-cli/spec.md
tests:
 - none
---

## Prompt

/sp.clarify (no arguments)

Follow-up answers during the session:
- Q1 (truthfulness check outcome): "B"
- Q2 (writer removal scope): "yes"
- Q3 (persist analysis/match report): "yes"
- Q4 (WEAK MATCH definition): "yes"

## Response snapshot

Asked 4 of max 5 questions, integrating each answer into spec.md:
1. Truthfulness check hits → save file with "⚠ Unverified items" notice at top, list in
   terminal, exit with failure status (FR-019 split, new FR-020, new edge case).
2. Writer keeps every job/education entry with employer, title, dates; may shorten or drop
   irrelevant bullets/skills (new FR-013a, Story 1 scenario 5, scenario 4 reworded).
3. Job analysis + match report also saved to match_report.md; failure writes neither file
   (FR-017/018, Key Entities, Edge Cases, Assumptions, Story 2 scenario 5, Story 3 scenario 4).
4. WEAK MATCH requires an exact quoted resume line + connection note; no quote → GAP
   (new FR-009a, Story 2 scenario 3, SC-003, Key Entities).
Remaining categories judged Clear or low impact; recommended /sp.plan.

## Outcome

- ✅ Impact: Four high-impact ambiguities resolved; spec ready for planning
- 🧪 Tests: none (spec stage)
- 📁 Files: specs/001-job-hunt-agent-cli/spec.md
- 🔁 Next prompts: /sp.plan
- 🧠 Reflection: Requiring quotes for WEAK matches makes the no-fabrication rule testable across the matcher, not just the writer

## Evaluation notes (flywheel)

- Failure modes observed: one Edit missed due to line-wrap mismatch; retried with shorter anchor
- Graders run and results (PASS/FAIL): post-integration consistency scan PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
