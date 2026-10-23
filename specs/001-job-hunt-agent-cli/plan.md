# Implementation Plan: Job Hunt Agent CLI

**Branch**: `001-job-hunt-agent-cli` | **Date**: 2026-10-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-job-hunt-agent-cli/spec.md`

## Summary

A Python 3.12 command-line tool reads `job_posting.txt` and `resume.md` and runs three
CrewAI agents in order:
- **Researcher** produces a `JobAnalysis`.
- **Matcher** produces a `MatchReport` in which every match has a quoted proof line,
  enforced by a code guardrail.
- **Writer** produces a truthful, reordered resume in Markdown.

The model is reached through OpenRouter with `crewai.LLM(model="openrouter/…",
base_url="https://openrouter.ai/api/v1")`. The key and model ID are read from `.env`
with python-dotenv.

Once all three steps succeed, a plain Python truthfulness check scans the resume body
for numbers, skills and names that aren't in the original. The tool then writes
`match_report.md` and `tailored_resume.md`, adding a "⚠ Unverified items" notice to the
resume if anything was flagged. Each outcome has its own exit code. Setup is checked
before any AI call, and nothing is written if any step fails.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: crewai[litellm] (>=1.15,<2), python-dotenv; pytest (dev)
**Storage**: Local files only (2 inputs, 2 outputs); no database
**Testing**: pytest — unit tests for config, input checks, guardrail, truthfulness check, rendering, file writing, and CLI exit codes with the crew mocked
**Target Platform**: Local terminal on Windows, macOS, Linux
**Project Type**: single (CLI)
**Performance Goals**: under 3 minutes end-to-end for a 1-page posting + 2-page resume (SC-001); setup errors within 2 s (SC-005)
**Constraints**: no web framework, no DB (Principle IV); secrets only from `.env` (III); nothing written on failure (FR-018); beginner-readable code (V); model output capped at `MAX_OUTPUT_TOKENS` (default 4000, FR-021)
**Scale/Scope**: one user, one posting + one resume per run; three model calls, plus up to 2 guardrail retries on the match step

No NEEDS CLARIFICATION items remain; see [research.md](./research.md) R1–R10.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Pre-design | Post-design |
|-----------|------|-----------|-------------|
| I. Single Responsibility per Agent | Each agent has one job and its own module; plain data passes between them | ✅ 3 agents, 3 jobs | ✅ `agents/researcher.py`, `matcher.py`, `writer.py`; Pydantic models are the only shared data |
| II. Truthful Resume Output | No invented facts; the rule is stated in the prompt; an automated check exists | ✅ FR-012/019/020 | ✅ writer prompt rule + `checks.find_unverified_items()` + match guardrail on proof lines; unit-tested |
| III. Secrets Only from .env | Key read from env only; `.env` git-ignored; `.env.example`; clear error when missing | ✅ | ✅ `config.py`; `.gitignore` and `.env.example` in scope; no message prints the key |
| IV. Simplicity First | No web framework or DB; every dependency justified | ✅ | ✅ 2 runtime deps (both named by the user), 1 dev dep; CrewAI's `output_file` not used, so file writing stays in one place |
| V. Beginner-Readable Code | Plain functions, docstrings, type hints | ✅ | ✅ no `@CrewBase` decorators or YAML indirection (R4); prompts next to the code that uses them |
| Tech constraints | Python 3.12, CLI via argparse, `src/` + `tests/` | ✅ | ✅ |

**Result**: PASS. No violations, so Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-job-hunt-agent-cli/
├── plan.md              # This file
├── research.md          # Phase 0: decisions R1–R10
├── data-model.md        # Phase 1: models, guardrail rules, run lifecycle
├── quickstart.md        # Phase 1: install, configure, run, validate
├── contracts/
│   ├── cli.md           # options, env vars, exit codes, messages
│   └── output-files.md  # layout of tailored_resume.md and match_report.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/sp.tasks — not created here)
```

### Source Code (repository root)

```text
.gitignore               # .env, .venv/, __pycache__/, outputs (tailored_resume.md, match_report.md)
.env.example             # OPENROUTER_API_KEY=, OPENROUTER_MODEL=, commented telemetry opt-out
.python-version          # 3.12
README.md                # what it does, setup (uv or venv), run, privacy note, exit codes
pyproject.toml           # deps, [project.scripts] job-hunt = "job_hunt_agent.cli:main"

examples/
├── job_posting.txt      # sample input for the smoke test
└── resume.md

src/job_hunt_agent/
├── __init__.py
├── __main__.py          # enables `python -m job_hunt_agent`
├── cli.py               # argparse + main(): checks → crew → truthfulness check → write → exit code
├── config.py            # load .env; Settings(api_key, model, max_output_tokens); no CrewAI import
├── inputs.py            # read_input_file(path, label) -> str  (missing/empty/not-UTF-8 errors)
├── models.py            # JobAnalysis, MatchItem, MatchReport, UnverifiedItem (Pydantic)
├── agents/
│   ├── __init__.py
│   ├── researcher.py    # make_researcher(llm) -> Agent
│   ├── matcher.py       # make_matcher(llm) -> Agent
│   └── writer.py        # make_writer(llm) -> Agent
├── tasks.py             # make_research_task / make_match_task (+guardrail) / make_write_task
├── crew.py              # make_llm(settings) (max_tokens=max_output_tokens); run_crew(settings, ...) -> CrewResult
├── errors.py            # describe_failure(): short API message + one-line hint (FR-018a)
├── checks.py            # proof-line / bucket checks; find_unverified_items()
├── report.py            # render_match_report(), add_unverified_notice()
└── output.py            # write_text_safely() (temp file + os.replace)

tests/
└── unit/
    ├── test_config.py
    ├── test_inputs.py
    ├── test_checks.py       # guardrail rules + truthfulness check (many small cases)
    ├── test_report.py
    ├── test_output.py
    ├── test_crew.py         # make_llm passes max_tokens
    ├── test_errors.py       # short reasons and hints for API errors
    └── test_cli.py          # exit codes 0/1/2/3, --debug, log suppression, with run_crew mocked
```

**Structure Decision**: a single project in a `src/` layout. Agents, tasks and the crew
are kept apart as the user asked:
- `agents/` holds one module per agent (Principle I).
- `tasks.py` defines what each agent is asked to do.
- `crew.py` wires the tasks together.

Code that doesn't use the AI (`checks`, `report`, `output`, `inputs`, `config`) lives in
small separate modules, so it can be unit-tested without a key or network. There are no
contract or integration test folders because there is no service API. The real-model run
is the quickstart smoke test.

## Key Design Notes

1. **Step order and data flow**: Research (`output_pydantic=JobAnalysis`) → Match
   (`context=[research]`, `output_pydantic=MatchReport`, `guardrail=check_match_report`,
   `guardrail_max_retries=2`) → Write (`context=[research, match]`, raw Markdown). The
   posting and resume go in through `kickoff(inputs={"job_posting": ..., "resume": ...})`.
2. **Writer prompt** spells out Principle II and FR-013a. It must not add any skill,
   tool, employer, title, date or number; it must keep every job and education entry with
   its dates; it may drop irrelevant bullets; and it must end with the two required
   sections.
3. **Truthfulness check** runs on the resume body only, never on "What I changed" or
   "Gaps to work on". It flags numbers, job-analysis skills and proper nouns or tech
   terms missing from the resume (R7).
4. **Writes happen at the end**: `match_report.md` first, then `tailored_resume.md`, both
   through temp file + `os.replace` (R8).
5. **Agents**: `allow_delegation=False`, no tools, and `verbose=False`. Progress comes
   from our own prints and task callbacks (R6).
6. **Output limit**: `make_llm` sets `max_tokens` from `MAX_OUTPUT_TOKENS` (default 4000).
   Without a limit, CrewAI asks for the model's maximum (64,000 for some models), and
   OpenRouter turns the request down when that exceeds the user's credit (HTTP 402).
7. **Failure messages** (FR-018a/b): `errors.py` pulls the human-readable message out of
   the API error's body (or its text), adds `(HTTP <code>)` and a hint chosen by status
   code. `logging.disable(CRITICAL)` hides CrewAI's duplicate ERROR lines during the run.
   `--debug` keeps the logs and also prints the full error text, with the key masked.

## Risks

- **The model ignores the "no new facts" rule.** Mitigations: the explicit prompt rule,
  the deterministic check with notice and exit code 1, and the "What I changed" list.
  The check cannot catch invented claims made of ordinary words (R7 known limits).
- **CrewAI API drift** (callback signature, guardrail behavior, telemetry variable).
  Mitigation: the version is pinned to `>=1.15,<2`; these points are marked "verify
  during implementation" in R6/R10; the three-crew fallback is documented.
- **Free or small OpenRouter models may not follow `output_pydantic` reliably.**
  Mitigation: the guardrail retries and a clear step-failure message. The README
  recommends a capable model.

## Complexity Tracking

No constitution violations; nothing to justify.
