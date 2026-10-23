# Job Hunt Agent

Tailors your resume to a specific job posting, and **refuses to let the AI invent anything.**

Python 3.12 · CrewAI · OpenRouter · 87 tests · built spec-first with Spec-Kit Plus + Claude Code

## What makes it different
Most AI resume tools happily add skills you don't have. This one runs a plain-Python
truthfulness check after the AI finishes: any invented number, tool, employer, title or
date fails the run (exit code 1) and is flagged at the top of the output.

## How it works
job_posting.txt + resume.md
        │
   Researcher  →  Matcher  →  Writer  →  truthfulness check
   (what they     (honest     (rewrites,     (no AI: catches
    want)          gaps)       invents        invented facts)
                               nothing)
        │
tailored_resume.md + match_report.md

## Example
[before/after bullet + screenshot here, using the fictional sample in examples/]

## How it was built
Spec-driven development with [Spec-Kit Plus](https://github.com/panaversity/spec-kit-plus)
and Claude Code: constitution → spec → plan → tasks → implementation.
The full trail is in the repo: [`specs/`](specs/) and prompt history in [`history/`](history/).

## The no-invention promise

The writer is told never to add skills, tools, employers, job titles, dates or
numbers. After it finishes, the tool checks the result in plain Python (no AI)
for:

- numbers and years that are not in your original resume, including numbers
  written as words next to a unit ("three years", "ten+ projects"),
- job-posting skills that your resume does not mention,
- names and tech terms (like `Google` or `PostgreSQL`) that your resume does not mention.

There are two levels of result:

- **Invented facts** (a number, tool, employer, title or date that isn't in your
  resume): the file is still saved, but it starts with a **⚠ Unverified items**
  notice listing each one, and the command exits with code `1`. Fix or remove
  them before you send the resume.
- **Rewordings to check** (a general phrase from the job posting, like "batch data
  pipelines", that isn't word-for-word in your resume): these are often fair
  rewordings, so the run still succeeds (exit code `0`). They are printed under
  "Check these rewordings are true:" and listed in a final section of
  `tailored_resume.md`. Keep each one only if it's true, then delete that section.

The writer is also told never to work out durations or totals from your dates
(no "three years of experience" unless your resume says so).

The check cannot catch every kind of exaggeration. For example, it won't notice
if "member of the team" becomes "led the team". Always read the "What I changed"
section.

The Matcher is checked too:

- every quoted proof line must appear word-for-word in your resume, and
- its top 3 improvements may not contain numbers, tools or company names that
  aren't in your resume or the job posting. A detail you might have is written as
  a placeholder, like "add [X]%, only if true".

If a check fails, the Matcher is asked to try again (up to 2 times).

## Setup

You need Python 3.12 and an [OpenRouter](https://openrouter.ai) API key.

### With uv (recommended)

```bash
uv sync --all-extras
```

### Or with a plain virtual environment

```bash
python3.12 -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -e ".[dev]"
```

### Configure your key

```bash
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
```

Then edit `.env`:

```text
OPENROUTER_API_KEY=your-key
OPENROUTER_MODEL=<provider>/<model>
```

Optional setting:

```text
MAX_OUTPUT_TOKENS=4000    # most text the model may write per step (default 4000)
```

OpenRouter checks `MAX_OUTPUT_TOKENS` against your credit balance. If a run fails
with "requires more credits", add credits, pick a cheaper model, or lower this number.

Pick a model ID from <https://openrouter.ai/models>. Choose a capable model:
very small or free models often fail to return the structured answers the
agents need, and the run will stop with a "Step N/3 failed" message.

`.env` is listed in `.gitignore`. **Never commit it.**

## Run

Put `job_posting.txt` and `resume.md` in the current folder, then:

```bash
uv run job-hunt
```

Or point to other files:

```bash
uv run job-hunt --job examples/job_posting.txt --resume examples/resume.md
```

(Without uv: activate the venv and run `job-hunt` or `python -m job_hunt_agent`.)

You will see each step as it runs, plus the job analysis and match report.

If a step fails, you get one short message and a hint, for example:

```text
Error: Step 1/3 (Research) failed: This request requires more credits, ... (HTTP 402). No files were written.
Hint: Add credits at https://openrouter.ai/settings/credits, switch to a cheaper model, or lower MAX_OUTPUT_TOKENS in .env.
```

Add `--debug` to see the full error details and CrewAI's own log messages
(your key is still hidden).

## Output

| File | What's in it |
|------|--------------|
| `tailored_resume.md` | Your rewritten resume, ending with "What I changed" and "Gaps to work on" |
| `match_report.md` | The job analysis and match report, to keep for interview prep |

Both files are written to the current folder, and only after every step
succeeds. Existing files with the same names are overwritten, and you'll be told
when that happens. Both are git-ignored because they contain your personal data.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Done, no invented facts (there may still be rewordings to check at the end of `tailored_resume.md`) |
| 1 | Done, but invented facts were found (see the top of `tailored_resume.md`) |
| 2 | Setup problem: missing or empty input file, or a missing or invalid `.env` setting |
| 3 | An AI step failed (network, key, rate limit, or bad answer); no files written |

## Privacy

Your resume and the job posting are sent only to the OpenRouter model you
choose. The tool always turns off CrewAI's anonymous telemetry and its trace
collection, so CrewAI never asks to "share an execution trace" and never pauses
for input. You don't need to set anything for this.

CrewAI does keep a local copy of the latest run's task outputs in its app-data
folder (on Windows: `%LOCALAPPDATA%\CrewAI\<folder name>\`). Delete that folder
if you don't want your resume stored there.

## Tests

The tests don't call any AI and don't need a key:

```bash
uv run pytest
```

## Project layout

```text
src/job_hunt_agent/
├── cli.py          # the job-hunt command
├── config.py       # reads settings from .env
├── inputs.py       # reads and checks input files
├── models.py       # data passed between agents
├── agents/         # one file per agent: researcher, matcher, writer
├── tasks.py        # what each agent is asked to do
├── crew.py         # connects to OpenRouter and runs the three steps in order
├── errors.py       # short, readable failure messages with a hint
├── checks.py       # proof-line and no-invention checks (no AI)
├── report.py       # builds match_report.md and the warning notice
└── output.py       # writes files safely
```
