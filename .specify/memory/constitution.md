<!--
Sync Impact Report
==================
Version change: (unversioned template) → 1.0.0
Bump rationale: first ratification; all placeholders replaced with concrete principles.

Modified principles (template slot → new title):
  - [PRINCIPLE_1_NAME] → I. Single Responsibility per Agent
  - [PRINCIPLE_2_NAME] → II. Truthful Resume Output (NON-NEGOTIABLE)
  - [PRINCIPLE_3_NAME] → III. Secrets Only from .env (NON-NEGOTIABLE)
  - [PRINCIPLE_4_NAME] → IV. Simplicity First
  - [PRINCIPLE_5_NAME] → V. Beginner-Readable Code
  - [PRINCIPLE_6_NAME] → removed (user supplied five principles; no sixth needed)

Added sections:
  - Technology Constraints (was [SECTION_2_NAME])
  - Development Workflow & Quality Gates (was [SECTION_3_NAME])

Removed sections: none (template slot 6 dropped, see above)

Templates requiring updates:
  - ✅ .specify/templates/plan-template.md — "Constitution Check" gates are derived
       dynamically from this file; no edit needed
  - ✅ .specify/templates/spec-template.md — no mandatory section changes
  - ✅ .specify/templates/tasks-template.md — "Single project" layout (src/, tests/)
       already fits a Python CLI; no edit needed
  - ✅ .claude/commands/*.md — no outdated principle references found
  - ⚠ .gitignore — does not exist yet; MUST be created with `.env` before any
       secret is added (Principle III)

Follow-up TODOs: none deferred.
-->

# Job Hunt Agent Constitution

## Core Principles

### I. Single Responsibility per Agent

- Each agent MUST do exactly one job (e.g., parse resume, analyze job posting,
  write resume). If an agent's purpose needs the word "and" to describe it, it
  MUST be split.
- Each agent MUST live in its own module with a clear input and a clear output.
- Agents MUST NOT reach into another agent's internals; they pass plain data
  (strings, dicts, dataclasses) to each other.

**Rationale**: Small, single-purpose agents are easier to test, debug, and
understand, and a fault in one does not silently corrupt the others.

### II. Truthful Resume Output (NON-NEGOTIABLE)

- The resume writer MUST NEVER invent skills, tools, employers, job titles,
  dates, or numbers (metrics, percentages, team sizes, years of experience).
- Every fact in generated output MUST come from the input resume. The writer
  MAY reword, reorder, or emphasize existing facts; it MUST NOT add new ones.
- If a job posting asks for something the input resume does not contain, the
  writer MUST leave it out (it MAY report the gap to the user separately).
- Prompts sent to the model MUST state this rule explicitly, and the feature
  MUST include an automated check that flags any skill, employer, date, or
  number in the output that is absent from the input.

**Rationale**: A fabricated resume can cost the user a job offer or their
credibility. Truthfulness outranks persuasiveness.

### III. Secrets Only from .env (NON-NEGOTIABLE)

- API keys, tokens, and passwords MUST be read only from environment variables
  loaded from a local `.env` file.
- Secrets MUST NEVER be hardcoded in source, tests, docs, or example output.
- `.env` MUST be listed in `.gitignore` and MUST NEVER be committed. A
  `.env.example` with placeholder values (no real secrets) SHOULD be committed.
- If a required secret is missing, the CLI MUST exit with a clear error naming
  the missing variable — never print the secret's value.

**Rationale**: Leaked keys are costly and hard to revoke everywhere; one simple
rule prevents it.

### IV. Simplicity First

- The project MUST NOT use a web framework (no Flask, FastAPI, Django, etc.)
  and MUST NOT use a database. Input and output are files and the terminal.
- Add a dependency only when the standard library cannot reasonably do the job;
  each new dependency MUST be justified in the feature plan.
- Build only what the current spec requires (YAGNI). No speculative layers,
  plugin systems, or abstractions without a present need.

**Rationale**: Fewer moving parts means fewer bugs and a codebase one person
can hold in their head.

### V. Beginner-Readable Code

- Code MUST be readable by a beginner Python programmer: descriptive names,
  short functions, plain control flow.
- Avoid clever tricks (nested comprehensions, metaclasses, heavy decorators,
  dense one-liners) when a straightforward version exists.
- Every module and public function MUST have a short docstring saying what it
  does. Comments explain *why*, not *what*.
- Type hints MUST be used on function signatures.

**Rationale**: The code is a learning resource as well as a tool; if a beginner
cannot follow it, it is too complex.

## Technology Constraints

- **Language**: Python 3.12.
- **Interface**: Command-line application only (stdlib `argparse` preferred).
- **Configuration**: environment variables via `.env` (e.g., `python-dotenv`).
- **Storage**: local files only (input resume, job posting, generated output).
- **Layout**: single project — `src/` for code, `tests/` for tests.
- **Errors**: user-facing errors go to stderr with a plain-English message and
  a non-zero exit code; no raw stack traces for expected failures.

## Development Workflow & Quality Gates

- Work follows Spec-Driven Development: spec → plan → tasks → implement.
- Every plan MUST pass the Constitution Check against Principles I–V before
  implementation begins; any violation MUST be justified in the plan's
  Complexity Tracking table.
- Before merging, a change MUST satisfy:
  - [ ] Each agent has one responsibility (I).
  - [ ] Resume-writer changes keep the no-fabrication check passing (II).
  - [ ] No secrets in the diff; `.env` is git-ignored (III).
  - [ ] No web framework, no database, no unjustified dependency (IV).
  - [ ] Code is readable, documented, and type-hinted (V).
- Changes SHOULD be small and focused; unrelated refactors go in separate
  changes.

## Governance

- This constitution supersedes all other practices and guidance in the repo.
  Runtime agent guidance lives in `CLAUDE.md` and MUST NOT contradict it.
- Amendments MUST be made via `/sp.constitution`, include a Sync Impact Report,
  and propagate to dependent templates in `.specify/templates/`.
- Versioning follows semantic versioning:
  - MAJOR: removing or redefining a principle in a backward-incompatible way.
  - MINOR: adding a principle or section, or materially expanding guidance.
  - PATCH: clarifications, wording, and typo fixes.
- Compliance is reviewed at every plan (Constitution Check) and every code
  review. Principles II and III are NON-NEGOTIABLE and cannot be waived by a
  plan's justification table.

**Version**: 1.0.0 | **Ratified**: 2026-10-24 | **Last Amended**: 2026-10-24
