# Phase 0 Research: Job Hunt Agent CLI

**Feature**: `001-job-hunt-agent-cli` | **Date**: 2026-10-24

Sources checked on 2026-10-24:
- CrewAI LLM docs — https://docs.crewai.com/en/concepts/llms
- CrewAI Tasks docs — https://docs.crewai.com/en/concepts/tasks
- PyPI `crewai` metadata — https://pypi.org/pypi/crewai/json (latest seen: 1.15.29,
  `requires_python >=3.10,<3.14`)

---

## R1. Calling OpenRouter from CrewAI

- **Decision**: Use `crewai.LLM` with `model="openrouter/<OPENROUTER_MODEL>"`,
  `base_url="https://openrouter.ai/api/v1"`, `api_key=<OPENROUTER_API_KEY>`. Install
  `crewai[litellm]`. The code adds the `openrouter/` prefix only if the user's model ID
  doesn't already have it.
- **Rationale**: This is the documented OpenRouter setup. CrewAI sends OpenRouter calls
  through LiteLLM, which the `litellm` extra provides.
- **Alternatives considered**: calling OpenRouter's OpenAI-compatible endpoint
  directly with the `openai` SDK (rejected: user asked for CrewAI); using
  `OPENAI_API_BASE` env tricks (rejected: implicit, harder for a beginner to follow).
- **Note from docs**: OpenRouter may return `200 OK` with an upstream failure in the
  body; CrewAI raises it as the upstream exception (e.g. `openai.InternalServerError`).
  The CLI catches all exceptions from the crew run and reports them as a failed step
  (see R6).

## R2. Python version and package tooling

- **Decision**: Python 3.12 (`requires-python = ">=3.12,<3.13"`, `.python-version` =
  `3.12`), managed with **uv**. `pyproject.toml` defines a `job-hunt` console script.
  A plain `venv` + `pip install -e .` path is documented in the README as an
  alternative.
- **Rationale**: Constitution fixes Python 3.12; CrewAI supports 3.10–3.13. uv gives
  one-command setup (`uv sync`) and a lockfile.
- **Alternatives considered**: Poetry (extra tool for beginners), requirements.txt only
  (no lockfile, no entry point).

## R3. Dependencies

- **Decision**: Runtime: `crewai[litellm]>=1.15,<2`, `python-dotenv`. Dev: `pytest`.
  `pydantic` is used for structured task outputs but comes with CrewAI, so it is not
  listed separately.
- **Rationale**: Principle IV only allows dependencies that are needed. The user named
  CrewAI and python-dotenv; pytest is the standard test runner.
- **Alternatives considered**: `rich` for nicer terminal output (rejected: plain `print`
  is enough).

## R4. Code structure for agents, tasks and crew

- **Decision**: Plain Python modules, with **one module per agent** in
  `src/job_hunt_agent/agents/` (`researcher.py`, `matcher.py`, `writer.py`). All three
  task builders go in `tasks.py`, and `crew.py` wires them into a sequential crew. Prompt
  text lives as string constants next to the agent and task that use it.
- **Rationale**: Principle I requires each agent in its own module. Principle V asks for
  beginner-readable code, and plain functions such as `make_researcher(llm)` are easier
  to follow than `@CrewBase`/`@agent` decorators plus YAML lookups.
- **Alternatives considered**: the `crewai create crew` scaffold (YAML config +
  `@CrewBase` decorators). Rejected: the decorators hide how the pieces connect, and
  splitting prompts across YAML and Python files makes them harder to follow.

## R5. Passing data between agents and enforcing quotes

- **Decision**:
  - Run the three tasks with `Process.sequential`. The match task gets the research task
    as `context`; the write task gets both.
  - The posting and resume text go in through `crew.kickoff(inputs={...})` placeholders
    (`{job_posting}`, `{resume}`).
  - The research task uses `output_pydantic=JobAnalysis`, the match task uses
    `output_pydantic=MatchReport`, and the write task returns raw Markdown.
  - The match task has a **function guardrail** that checks every STRONG/WEAK proof line
    appears word-for-word in the resume after whitespace is normalized. It also checks
    that every must-have skill appears in exactly one bucket and that there are exactly
    3 improvements. If a check fails, the error goes back to the agent, up to
    `guardrail_max_retries=2`.
- **Rationale**: Structured outputs let plain Python check FR-009, FR-009a and FR-010
  instead of trusting the model. Guardrails are CrewAI's documented retry mechanism.
- **Alternatives considered**: free-text outputs parsed with regex (fragile); no
  guardrail and a post-check only (rejected: a bad proof line would reach the user
  when a retry usually fixes it).
- **Writer has no retry guardrail**: in the clarification, the user chose to flag
  unverified items rather than retry (Q1 → B, not D). The truthfulness check (R7) runs
  after the crew finishes.

## R6. Progress display and step-failure reporting

- **Decision**:
  - Turn CrewAI's verbose logging off and print our own lines: `Step 1/3: Researching
    the job posting...`.
  - Each task has a `callback` that prints its result (job analysis and match report,
    per FR-016) and records which step finished.
  - If `kickoff()` raises, the CLI names the first unfinished step ("Step 2/3 (Matching)
    failed: <short reason>") and exits with code 3.
- **Rationale**: Covers FR-016 and FR-018 with small, readable code.
- **To verify during implementation**: the exact signature of the `Task(callback=...)`
  argument in the installed CrewAI version. If it differs, fall back to running three
  one-task crews in a row, which gives the same behavior.

## R7. Truthfulness check (FR-019 / FR-020)

- **Decision**: a pure Python function `find_unverified_items(tailored_md, resume_md,
  job_analysis)` that runs **only on the resume body**, i.e. it skips the "What I
  changed" and "Gaps to work on" sections, which are allowed to name missing skills. It
  compares case-insensitively and flags:
  1. **Numbers and dates**: every number token (`2021`, `40%`, `3.5`, `10+`) not found
     in the resume.
  2. **Job-related skills/tools**: every must-have, nice-to-have and ATS keyword from
     `JobAnalysis` that appears in the body but not in the resume. This is the most
     likely kind of fabrication, because the writer has just read the job posting.
  3. **Proper nouns and tech terms**: capitalized words that are not at the start of a
     line, sentence or bullet, plus tokens like `PostgreSQL`, `C#`, `Node.js` and
     `AWS`, that don't appear in the resume. A short list of words to ignore
     (`Experience`, `Skills`, `Summary`, `Education`, month names) cuts false alarms.
- **Rationale**: Deterministic and testable without an AI call. It covers the five
  banned fabrication types in Principle II.
- **Known limits**:
  - It cannot catch invented claims made of ordinary words, such as "led the team" when
    the resume says "member of the team". The prompt rules and the "What I changed"
    list are the defence there.
  - It may raise false alarms. This is acceptable: per FR-020 the file is still saved
    and the user reviews the flagged items.
- **Alternatives considered**: a second LLM acting as a fact-check judge (rejected:
  not deterministic, adds cost, and is itself able to make things up).

## R8. Writing output files (FR-017, FR-018)

- **Decision**: Don't use CrewAI's `output_file`. After every step succeeds and the check
  has run, the CLI writes `match_report.md` and then `tailored_resume.md`. Each file is
  written to a temporary file in the same folder and then moved into place with
  `os.replace`.
- **Rationale**: `output_file` would save the analysis even if a later step fails, which
  breaks FR-018. `os.replace` replaces the file in one step, so a crash mid-write cannot
  leave half a file.

## R9. Exit codes and error messages

- **Decision**: `0` success · `1` finished but has unverified items (FR-020) · `2` setup
  error (missing/empty/unreadable file, missing env var) · `3` an AI step failed. All
  errors go to stderr as `Error: <what>. Fix: <how>.` and never print the key's value.
- **Rationale**: Gives FR-004, FR-018 and FR-020 their own codes so scripts and tests
  can tell the cases apart.

## R10. Telemetry and privacy

- **Decision**: `.env.example` includes a commented-out `CREWAI_DISABLE_TELEMETRY=true`
  line, and the README explains it. The README also states that the resume and posting
  are sent to the chosen OpenRouter model.
- **Rationale**: The user's resume is personal data; they should know where it goes
  and how to turn telemetry off.
- **To verify during implementation**: the exact name of the telemetry opt-out variable
  in the installed CrewAI version.

## Implementation notes (2026-10-24)

Checked against the installed crewai 1.15.29:

- **R1**: with an `openrouter/` model, CrewAI 1.15 uses its own OpenAI-compatible client
  (`OpenAICompatibleCompletion`) and removes the prefix internally. The setup from the
  docs works unchanged.
- **R5**: when a task has a guardrail, CrewAI passes the guardrail the **raw** text
  (`output.pydantic` is `None`). The guardrail parses `MatchReport` from the JSON
  itself and attaches it to the output before returning `(True, output)`. When retries
  run out, CrewAI raises `Exception("Task failed guardrail validation after N
  retries...")`, which the CLI reports as a failed step 2 (exit 3).
- **R6**: `Task.callback` is called with the `TaskOutput` after each task, so the
  three-crew fallback was not needed.
- **R10**: the telemetry opt-out is `CREWAI_DISABLE_TELEMETRY=true`. `OTEL_SDK_DISABLED`
  and `CREWAI_DISABLE_TRACKING` are also honored.
- **SC-005 change**: importing CrewAI takes about 8 s, so a setup error took 9.1 s.
  `make_llm` moved from `config.py` to `crew.py`, and `cli.py` imports `crew` only
  after the file and settings checks pass. Setup errors now appear in about 1–1.6 s.
- **Output limit (FR-021)**: with no `max_tokens`, CrewAI requested 64,000 output tokens
  for `anthropic/claude-sonnet-4.5`. OpenRouter checks that against the balance and
  returned HTTP 402. `crewai.LLM(..., max_tokens=N)` is accepted by
  `OpenAICompatibleCompletion` (checked: `llm.max_tokens == N`). Default 4000.
- **Failure output (FR-018a/b)**: CrewAI calls `logging.error("OpenAI API call failed:
  ...")` on the root logger for every attempt, which triggers Python's default
  `basicConfig` (`ERROR:root:` lines). `logging.disable(logging.CRITICAL)` during the run
  hides these. The `[CrewAIEventsBus] Warning: Event pairing mismatch` lines are printed
  directly to the console, not through `logging`, and can only be silenced through a
  private CrewAI context variable, so they are left as they are.
  The openai SDK's `APIStatusError` has `status_code` and `body`; `errors.py` reads the
  message from `body["error"]["message"]`, with a regex on the error text as a fallback.
