---

description: "Task list for Job Hunt Agent CLI"
---

# Tasks: Job Hunt Agent CLI

**Input**: Design documents from `/specs/001-job-hunt-agent-cli/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, contracts/output-files.md, quickstart.md

**Tests**: Included. Constitution Principle II requires an automated no-fabrication
check, and plan.md defines a unit-test layout. Tests cover only the code that doesn't
use the AI; every AI call is mocked, so `uv run pytest` needs no key or network.

**Organization**: Tasks are grouped by user story so each story can be built and tested
on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story the task belongs to (US1, US2, US3)
- All paths are relative to the repo root `D:\Naz\Projects\job-hunt-agent\`

## Rules that apply to every task

- Principle V: every module and public function gets a short docstring; type hints on
  every signature; plain control flow; no `@CrewBase`/`@agent` decorators.
- Principle III: never print, log or write the value of `OPENROUTER_API_KEY`.
- Use the exact names from `data-model.md` and the exact message shapes from
  `contracts/cli.md`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project skeleton, tooling, and the files that keep secrets safe.

- [X] T001 Create `.gitignore` at repo root listing `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `tailored_resume.md`, `match_report.md` (do this first so no secret can be committed)
- [X] T002 Create `pyproject.toml` at repo root: project name `job-hunt-agent`, `requires-python = ">=3.12,<3.13"`, dependencies `crewai[litellm]>=1.15,<2` and `python-dotenv`, optional dev group with `pytest`, `[project.scripts] job-hunt = "job_hunt_agent.cli:main"`, hatchling build backend with `packages = ["src/job_hunt_agent"]`, and `[tool.pytest.ini_options] pythonpath = ["src"]`, `testpaths = ["tests"]`
- [X] T003 [P] Create `.python-version` at repo root containing `3.12`
- [X] T004 [P] Create `.env.example` at repo root with `OPENROUTER_API_KEY=` (empty), `OPENROUTER_MODEL=` (empty, with comment "pick an ID from https://openrouter.ai/models, e.g. <provider>/<model>"), and a commented-out telemetry opt-out line (exact variable name verified in T040)
- [X] T005 Create the empty package layout: `src/job_hunt_agent/__init__.py` (module docstring only), `src/job_hunt_agent/agents/__init__.py`, `tests/unit/__init__.py`
- [X] T006 [P] Create `src/job_hunt_agent/__main__.py` that imports `main` from `job_hunt_agent.cli` and calls `raise SystemExit(main())`
- [X] T007 Run `uv sync --all-extras` and confirm the `.venv` uses Python 3.12 and `crewai` imports (`uv run python -c "import crewai; print(crewai.__version__)"`); record the installed version in a comment in `pyproject.toml`

**Checkpoint**: `uv run python -c "import job_hunt_agent"` succeeds; `git status` does not show `.env`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data models, settings, file reading and safe writing, which every story uses.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [X] T008 [P] Create `src/job_hunt_agent/models.py` with Pydantic models exactly as in `data-model.md`: `JobAnalysis(title, seniority, must_have_skills, nice_to_have_skills, responsibilities, ats_keywords)`, `MatchItem(requirement, proof_line, note="")`, `MatchReport(strong_matches, weak_matches, gaps, top_improvements)`, `UnverifiedItem(text, kind)` where `kind` is `Literal["number", "skill", "name"]`
- [X] T009 [P] Create `src/job_hunt_agent/config.py` with `Settings` dataclass (`api_key: str`, `model: str`), a `SetupError(Exception)` class (shared by config and inputs; message already formatted as `Error: ... Fix: ...`), `load_settings() -> Settings` that calls `load_dotenv()` then reads `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` with `os.getenv` (basic version: raise `SetupError` if either is empty; exact messages finished in T038), and `make_llm(settings) -> crewai.LLM` building `LLM(model=..., base_url="https://openrouter.ai/api/v1", api_key=settings.api_key)` with the `openrouter/` prefix added only when missing (research R1)
- [X] T010 [P] Create `src/job_hunt_agent/inputs.py` with `read_input_file(path: Path, label: str) -> str` that reads the file as UTF-8 and returns its text (basic version; validation added in T037)
- [X] T011 [P] Create `src/job_hunt_agent/output.py` with `write_text_safely(path: Path, text: str) -> bool` that writes to a temp file in the same folder and moves it into place with `os.replace`, returning `True` if the file already existed (so the CLI can print the "overwrote" note) (research R8)
- [X] T012 [P] Write `tests/unit/test_output.py`: new file is created with exact content; existing file is replaced and function returns `True`; no `*.tmp` file is left behind
- [X] T013 [P] Write `tests/unit/test_config.py` (happy path only for now): with both env vars set via `monkeypatch.setenv`, `load_settings()` returns them; `make_llm` adds `openrouter/` to `"x/y"` and does not double it for `"openrouter/x/y"` (check the LLM's `model` attribute)

**Checkpoint**: `uv run pytest` passes; models import cleanly.

---

## Phase 3: User Story 1 - Get a tailored, truthful resume for one job (Priority: P1) 🎯 MVP

**Goal**: One command turns `job_posting.txt` + `resume.md` into a truthful, reordered `tailored_resume.md` that ends with "What I changed" and "Gaps to work on", and is flagged when anything can't be verified.

**Independent Test**: With `examples/` files and a real key, run `uv run job-hunt --job examples/job_posting.txt --resume examples/resume.md`. `tailored_resume.md` exists, the most relevant job comes first, both closing sections are present, every employer, title and date is kept, and the exit code is 0 (or 1 with a notice listing the unverified items).

### Tests for User Story 1 ⚠️ (write first; they must fail before T017–T024)

- [X] T014 [P] [US1] Write `tests/unit/test_checks.py::test_find_unverified_*` cases for `find_unverified_items(tailored_md, resume_md, job_analysis)`: flags a new year `2019`; flags a new `40%`; ignores numbers present in resume; flags a posting must-have `Kubernetes` in the body when it is absent from the resume; ignores `Kubernetes` when it appears only under `## Gaps to work on` or `## What I changed`; flags a new mid-sentence proper noun `Google`; flags a tech token `PostgreSQL`; does not flag a capitalized word at the start of a line or bullet; does not flag stop-list words (`Experience`, `Skills`, `Summary`, `Education`, month names); matching is case-insensitive; returns an empty list for a clean rewrite
- [X] T015 [P] [US1] Write `tests/unit/test_report.py::test_add_unverified_notice_*`: with items, output starts with the `> ⚠ Unverified items` blockquote listing `- <text> (<kind>)` lines exactly as in `contracts/output-files.md`; with an empty list, text is returned unchanged
- [X] T016 [P] [US1] Write `tests/unit/test_cli.py::test_happy_path_*` with `job_hunt_agent.cli.run_crew` monkeypatched to return a fixed `CrewResult` and run in `tmp_path` (`monkeypatch.chdir`) with env vars set: clean result → exit 0 and `tailored_resume.md` written without notice; result containing an invented year → exit 1, file starts with notice, warning printed to stdout listing the item

### Implementation for User Story 1

- [X] T017 [P] [US1] Create `src/job_hunt_agent/agents/researcher.py` with `make_researcher(llm) -> Agent`: role "Job Posting Researcher", goal "Extract exactly what the job posting asks for", backstory, `allow_delegation=False`, `verbose=False`, no tools
- [X] T018 [P] [US1] Create `src/job_hunt_agent/agents/matcher.py` with `make_matcher(llm) -> Agent`: role "Resume Matcher", goal "Compare the resume to the job requirements honestly, quoting proof from the resume", same settings as T017
- [X] T019 [P] [US1] Create `src/job_hunt_agent/agents/writer.py` with `make_writer(llm) -> Agent`: role "Truthful Resume Writer", goal "Rewrite the resume for this job using only facts already in it", backstory stating it never invents skills, tools, employers, titles, dates or numbers; same settings as T017
- [X] T020 [US1] Create `src/job_hunt_agent/tasks.py` with:
  - `make_research_task(agent) -> Task`. Description uses `{job_posting}` and states FR-006/FR-007: 5–8 must-haves, never padded, "Not stated" or "(inferred)". `output_pydantic=JobAnalysis`.
  - `make_match_task(agent, research_task) -> Task`. Description uses `{resume}` and states FR-008–FR-011: exact quotes, WEAK needs quote + note, no quote → GAP, exactly 3 truthful improvements. `context=[research_task]`, `output_pydantic=MatchReport`. No guardrail yet; that is added in T029.
  - `make_write_task(agent, research_task, match_task) -> Task`. Description uses `{resume}` and states FR-012, FR-013, FR-013a and FR-014 word for word as rules: keep every job and education entry with employer, title and dates; may drop irrelevant bullets; end with `## What I changed` then `## Gaps to work on`, listing every GAP. `context=[research_task, match_task]`, raw Markdown output.
- [X] T021 [US1] Create `src/job_hunt_agent/crew.py` with a `CrewResult` dataclass (`analysis: JobAnalysis`, `report: MatchReport`, `resume_md: str`) and `run_crew(llm, job_posting: str, resume: str) -> CrewResult`. It builds the three agents and tasks, runs `Crew(agents=[...], tasks=[...], process=Process.sequential, verbose=False).kickoff(inputs={"job_posting": job_posting, "resume": resume})`, and reads each task's `.output.pydantic` / `.output.raw`.
- [X] T022 [US1] Implement `find_unverified_items()` in `src/job_hunt_agent/checks.py` per research R7, with small helpers:
  - `split_body(tailored_md) -> str` removes the `## What I changed` and `## Gaps to work on` sections.
  - `find_new_numbers(body, resume)`.
  - `find_new_skills(body, resume, analysis)` uses must-haves + nice-to-haves + ATS keywords.
  - `find_new_names(body, resume)` checks mid-sentence capitalized words and tech-style tokens against a `STOP_WORDS` set.
  - Results are de-duplicated and kept in order. T014 must pass.
- [X] T023 [US1] Create `src/job_hunt_agent/report.py` with `add_unverified_notice(resume_md: str, items: list[UnverifiedItem]) -> str` producing the blockquote from `contracts/output-files.md`; T015 must pass
- [X] T024 [US1] Create `src/job_hunt_agent/cli.py` with exit-code constants `EXIT_OK=0`, `EXIT_UNVERIFIED=1`, `EXIT_SETUP=2`, `EXIT_AI_FAILED=3`, `build_parser()` (argparse `--job` default `job_posting.txt`, `--resume` default `resume.md`), and `main(argv: list[str] | None = None) -> int`, in this order:
  1. load settings and both inputs;
  2. `run_crew`;
  3. `find_unverified_items`;
  4. `add_unverified_notice`;
  5. `write_text_safely` to `tailored_resume.md` in the current folder;
  6. print the `Saved:` / `Note: overwrote` lines and the warning block from `contracts/cli.md`;
  7. return 0 or 1.

  Catch `SetupError` → print to stderr, return 2. T016 must pass.
- [X] T025 [P] [US1] Create sample inputs `examples/job_posting.txt` (a realistic ~1-page posting with 6 must-haves, at least one the resume lacks) and `examples/resume.md` (fictional person, 2–3 jobs with dates and at least one number, one job unrelated to the posting)
- [X] T026 [US1] Manual smoke test per `quickstart.md` "Happy path": run with `examples/`. Confirm acceptance scenarios 1–5 of User Story 1 in `spec.md`, especially that the unrelated job keeps its employer, title and dates. Note results in the PR description.

**Checkpoint**: User Story 1 works end to end and `uv run pytest` passes. This is the MVP.

---

## Phase 4: User Story 2 - Understand how well I match before applying (Priority: P2)

**Goal**: The job analysis and the four-part match report (STRONG and WEAK matches with proof lines, GAPS, TOP 3 IMPROVEMENTS) are shown in the terminal and saved to `match_report.md`. Proof lines are checked in code.

**Independent Test**: Run the command. The terminal shows the analysis and match report while steps run, `match_report.md` matches `contracts/output-files.md`, every quoted proof line is found word-for-word in `resume.md`, and exactly 3 improvements are listed.

### Tests for User Story 2 ⚠️ (write first)

- [X] T027 [P] [US2] Write `tests/unit/test_checks.py::test_check_match_report_*` for `check_match_report(report, analysis, resume) -> list[str]` (list of problems; empty = OK): a STRONG proof line not in the resume → problem; a WEAK item with an empty note → problem; a must-have in two buckets → problem; a must-have in no bucket → problem; 2 or 4 improvements → problem; whitespace and line-break differences in the proof line are tolerated; bucket comparison is case-insensitive; a valid report → empty list
- [X] T028 [P] [US2] Write `tests/unit/test_report.py::test_render_match_report_*`: output contains the headings `# Match Report`, `## Job Analysis`, `## STRONG MATCHES`, `## WEAK MATCHES`, `## GAPS`, `## TOP 3 IMPROVEMENTS` in order, proof lines in quotes, numbered improvements 1–3, and empty sections show `- None`

### Implementation for User Story 2

- [X] T029 [US2] Add `check_match_report()` to `src/job_hunt_agent/checks.py` (T027 must pass). In `src/job_hunt_agent/tasks.py`, change `make_match_task` to take `resume: str`. Attach a function guardrail that reads `output.pydantic` and the research task's `JobAnalysis`, calls `check_match_report`, and returns `(False, "Fix these problems: ...")` or `(True, output)`. Set `guardrail_max_retries=2` (research R5). Update the call in `src/job_hunt_agent/crew.py`.
- [X] T030 [US2] Add `render_match_report(analysis, report) -> str` to `src/job_hunt_agent/report.py` following `contracts/output-files.md` (T028 must pass)
- [X] T031 [US2] Add progress output in `src/job_hunt_agent/crew.py`:
  - Print `Step 1/3: Researching the job posting...` before kickoff.
  - Give each task a `callback` that prints its result (the analysis/report section of `render_match_report` for steps 1 and 2) and the next step's header (`Step 2/3: Matching your resume to the job...`, `Step 3/3: Writing your tailored resume...`).
  - Track finished steps in a `progress` list on `CrewResult`'s builder so the CLI can name a failed step later.
  - First check the `Task(callback=...)` signature in the installed CrewAI (research R6). If it doesn't work, switch `run_crew` to three one-task crews in sequence.
- [X] T032 [US2] Update `main()` in `src/job_hunt_agent/cli.py` to also write `match_report.md` via `write_text_safely` **before** `tailored_resume.md`, printing `Saved:` / `Note: overwrote` for it. Extend `tests/unit/test_cli.py` so the happy path asserts both files exist and `match_report.md` contains `## STRONG MATCHES`.
- [X] T033 [US2] Manual check: run with `examples/` and confirm acceptance scenarios 1–5 of User Story 2 in `spec.md`, and that every proof line in `match_report.md` can be found in `examples/resume.md`

**Checkpoint**: User Stories 1 and 2 both work; `match_report.md` and the terminal show the same report.

---

## Phase 5: User Story 3 - Fix setup problems quickly (Priority: P3)

**Goal**: A missing, empty or unreadable input file, or a missing env var, gives a clear `Error: ... Fix: ...` message and exit code 2 before any AI call. A failed AI step names the step and exits with code 3. Neither case writes any file.

**Independent Test**: Run with each input file missing in turn, with each env var blank, and with `run_crew` forced to raise. Each run prints the matching message from `contracts/cli.md`, returns the right exit code, never shows the key, and leaves no output files.

### Tests for User Story 3 ⚠️ (write first)

- [X] T034 [P] [US3] Create `tests/unit/test_inputs.py`: missing file → `SetupError` whose message contains `not found`, the label and the absolute path; empty / whitespace-only file → message contains `is empty`; non-UTF-8 bytes (`b"\xff\xfe\x00"`) → message contains `could not read`; valid file → text returned
- [X] T035 [P] [US3] Extend `tests/unit/test_config.py`: missing `OPENROUTER_API_KEY` → `SetupError` naming the variable and `.env.example`; missing `OPENROUTER_MODEL` → `SetupError` naming it; with the key set to `sk-secret-123` and the model missing, the message does not contain `sk-secret-123`. Use `monkeypatch.delenv` and monkeypatch `load_dotenv` to do nothing, so a real `.env` cannot leak into tests.
- [X] T036 [P] [US3] Extend `tests/unit/test_cli.py`:
  - Missing job file → exit 2, stderr names the file, `run_crew` is never called (assert with a mock), and no output files are created.
  - Missing key → exit 2.
  - `run_crew` raising `RuntimeError("boom")` after step 1 finished → exit 3; stderr contains `Step 2/3 (Matching) failed` and `No files were written`; no output files exist even if they did not exist before.
  - Pre-existing output files are left unchanged on exit 3.

### Implementation for User Story 3

- [X] T037 [US3] Finish `read_input_file()` in `src/job_hunt_agent/inputs.py`: raise `SetupError` with the exact messages from `contracts/cli.md` for missing file (show `path.resolve()`, and the `--job`/`--resume` fix depending on `label`), empty or whitespace-only file, and `UnicodeDecodeError`. T034 must pass.
- [X] T038 [US3] Finish `load_settings()` in `src/job_hunt_agent/config.py` with the exact missing-key and missing-model messages from `contracts/cli.md`. Treat whitespace-only values as missing. Never put the value into any message. T035 must pass.
- [X] T039 [US3] In `main()` in `src/job_hunt_agent/cli.py`:
  - Make sure settings and both inputs are checked before `make_llm`/`run_crew` (SC-005).
  - Wrap `run_crew` in `try/except Exception`. Use the progress list from T031 to name the first unfinished step (`1/3 (Research)`, `2/3 (Matching)`, `3/3 (Writing)`).
  - Print `Error: Step N/3 (<name>) failed: <short reason>. No files were written.` to stderr and return 3.
  - The short reason is the exception class name plus its first line; check it never includes the API key by masking `settings.api_key` if it is present.

  T036 must pass.

**Checkpoint**: All three user stories work independently; `uv run pytest` is green.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, privacy, and final validation.

- [X] T040 [P] Find the CrewAI telemetry opt-out variable name for the installed version (research R10, docs.crewai.com telemetry page) and put it, commented out, in `.env.example`
- [X] T041 [P] Write `README.md` at repo root covering:
  - what the tool does (the three agents in one line each);
  - the no-invention promise and its limits (research R7 known limits);
  - setup with uv, and the venv alternative, as in `quickstart.md`;
  - `.env` configuration with a link to openrouter.ai/models, and a tip to choose a capable model;
  - how to run, with `--job`/`--resume`;
  - the outputs (`tailored_resume.md`, `match_report.md`) and the meaning of the "⚠ Unverified items" notice;
  - the exit code table from `contracts/cli.md`;
  - a privacy note: the resume and posting are sent to the chosen model, and how to turn telemetry off;
  - how to run the tests.
- [X] T042 Readability pass over `src/job_hunt_agent/` (Principle V): every module and public function has a docstring, every signature has type hints, there are no nested comprehensions or dense one-liners, and prompts sit next to the agent or task that uses them
- [X] T043 Secret-safety check: run `git status` and confirm `.env` is untracked and ignored; search the tree for any `sk-`/`OPENROUTER_API_KEY=` value with real content (only `.env.example` with an empty value is allowed)
- [X] T044 Run the full `quickstart.md` validation table (missing posting, missing key, happy path, proof lines, no invented facts, jobs kept) and `uv run pytest`; confirm SC-001 (under 3 min) and SC-005 (errors under 2 s) on the sample inputs


---

## Phase 7: Follow-up after the first live runs (FR-018a, FR-018b, FR-021)

**Purpose**: The first live runs showed that CrewAI asks OpenRouter for the model's full
output size (64,000 tokens), which is refused on small balances, and that failures print
raw JSON plus repeated CrewAI ERROR log lines.

- [X] T045 Add optional `MAX_OUTPUT_TOKENS` (default 4000, whole number > 0, else `SetupError`) to `Settings`/`load_settings()` in `src/job_hunt_agent/config.py`, and pass it as `max_tokens` in `make_llm()` in `src/job_hunt_agent/crew.py`; tests in `tests/unit/test_config.py` and `tests/unit/test_crew.py`
- [X] T046 Create `src/job_hunt_agent/errors.py` with `describe_failure()` that shows only the API's readable message plus `(HTTP <code>)` and a one-line `Hint:` chosen by status code; tests in `tests/unit/test_errors.py`
- [X] T047 Add `--debug` to `src/job_hunt_agent/cli.py`. Without it, `logging.disable(CRITICAL)` hides CrewAI's log lines during the run; with it, the logs stay on and the full error text (key masked) is printed. Tests in `tests/unit/test_cli.py`
- [X] T048 Update `.env.example` (append the commented `MAX_OUTPUT_TOKENS` line), `README.md`, `spec.md`, `plan.md`, `data-model.md` and `contracts/cli.md`
- [X] T049 Turn off CrewAI telemetry and tracing in `src/job_hunt_agent/crew.py` (env vars set before CrewAI loads, plus `Crew(tracing=False)`); add `tests/unit/test_no_prompts.py`, which runs the real crew with a fake model and fresh CrewAI state and fails if stdin or `input()` is touched (FR-022)
- [X] T050 Flag number words next to units in `find_new_number_words()` in `src/job_hunt_agent/checks.py`, and tell the Writer never to compute durations or totals (`src/job_hunt_agent/tasks.py`); tests in `tests/unit/test_checks.py` and `tests/unit/test_tasks.py` (FR-019, FR-012a)
- [X] T051 Add `check_improvement()` to the Matcher guardrail in `src/job_hunt_agent/checks.py`: reject made-up numbers and names, require "only if true" with `[placeholders]`; update the match prompt in `src/job_hunt_agent/tasks.py` (FR-011a)
- [X] T052 Split the truthfulness check into two levels in `src/job_hunt_agent/checks.py` (`is_tool_like()`, `find_rewordings_to_review()`): invented facts stay a hard failure (exit 1); general job-posting phrases are a review warning (exit 0), printed and added by `add_review_section()` in `src/job_hunt_agent/report.py`; tests in `tests/unit/test_checks.py`, `tests/unit/test_report.py`, `tests/unit/test_cli.py` (FR-020a)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies. Do T001 first.
- **Foundational (Phase 2)**: depends on Setup. Blocks all stories.
- **US1 (Phase 3)**: depends on Foundational. This is the MVP.
- **US2 (Phase 4)**: depends on US1. It changes `tasks.py`, `crew.py` and `cli.py`, which US1 creates.
- **US3 (Phase 5)**: depends on Foundational for the `inputs.py`/`config.py` error paths (T034, T035, T037, T038 can start right after Phase 2). T036 and T039 depend on `cli.py` from US1 and on the progress list from T031 (US2).
- **Polish (Phase 6)**: after all stories.

### User Story Dependencies

```text
Setup → Foundational ─┬─▶ US1 (P1, MVP) ──▶ US2 (P2) ──▶ US3 cli part (T036, T039)
                      └─▶ US3 input/config part (T034, T035, T037, T038)
```

### Within Each User Story

- Tests are written first and fail before implementation.
- Models (Phase 2) → agents → tasks → crew → checks/report → cli.
- Run the story's checkpoint before moving on.

### Parallel Opportunities

- Setup: T003, T004, T006 run in parallel after T002/T005.
- Foundational: T008–T013 are all in different files and can run in parallel.
- US1: tests T014–T016 in parallel; agents T017–T019 in parallel; T025 (examples) any time.
- US2: tests T027 and T028 in parallel.
- US3: T034/T035/T037/T038 can run alongside US1 or US2 work, since they touch different files.
- Polish: T040 and T041 in parallel.

---

## Parallel Example: User Story 1

```bash
# Tests first, together:
Task: "T014 find_unverified_items cases in tests/unit/test_checks.py"
Task: "T015 add_unverified_notice cases in tests/unit/test_report.py"
Task: "T016 happy-path exit codes in tests/unit/test_cli.py"

# Then the three agents, together:
Task: "T017 make_researcher in src/job_hunt_agent/agents/researcher.py"
Task: "T018 make_matcher in src/job_hunt_agent/agents/matcher.py"
Task: "T019 make_writer in src/job_hunt_agent/agents/writer.py"
```

## Parallel Example: User Story 3

```bash
Task: "T034 input-file error tests in tests/unit/test_inputs.py"
Task: "T035 env-var error tests in tests/unit/test_config.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (T001 `.gitignore` first)
2. Phase 2: Foundational
3. Phase 3: US1. You get a truthful tailored resume, with the notice and exit code 1 when anything can't be verified.
4. **Stop and validate** with T026 before continuing.

### Incremental Delivery

1. Setup + Foundational → skeleton runs and tests pass.
2. + US1 → MVP: `tailored_resume.md`.
3. + US2 → match report in the terminal and `match_report.md`; proof lines checked in code.
4. + US3 → friendly setup and step-failure errors.
5. Polish → README, privacy, final validation.

---

## Notes

- Total: 52 tasks. Setup 7 · Foundational 6 · US1 13 · US2 7 · US3 6 · Polish 5 · Follow-up 8.
- Commit after each task or checkpoint. Never commit `.env`.
- If CrewAI behaves differently from research R5/R6 (guardrail or callback), follow the
  fallback written in the task and note the change in `research.md`.
