# Quickstart: Job Hunt Agent CLI

## 1. Install (once)

```bash
# Install uv: https://docs.astral.sh/uv/
uv sync                       # creates .venv with Python 3.12 and installs dependencies
```

No uv? Use plain venv instead:

```bash
python3.12 -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

## 2. Configure (once)

```bash
cp .env.example .env          # Windows PowerShell: Copy-Item .env.example .env
```

Edit `.env`:

```text
OPENROUTER_API_KEY=your-key-from-openrouter.ai
OPENROUTER_MODEL=<provider>/<model>      # pick one at https://openrouter.ai/models
```

`.env` is git-ignored. Never commit it.

## 3. Run

Put `job_posting.txt` and `resume.md` in the current folder, then:

```bash
uv run job-hunt
# or with other paths:
uv run job-hunt --job jobs/acme.txt --resume my_resume.md
```

Expected output:

```text
Step 1/3: Researching the job posting...
<job analysis>
Step 2/3: Matching your resume to the job...
<match report>
Step 3/3: Writing your tailored resume...
Saved: .../match_report.md
Saved: .../tailored_resume.md
```

## 4. Validate the feature (acceptance smoke test)

| Check | How | Expected |
|-------|-----|----------|
| Missing posting | rename `job_posting.txt`, run | exit 2, message names file, no outputs |
| Missing key | blank `OPENROUTER_API_KEY`, run | exit 2, message names variable, key never shown |
| Happy path | sample files in `examples/`, run | exit 0 or 1; both files exist |
| Proof lines | open `match_report.md` | every quoted line exists in `resume.md` |
| No invented facts | read top of `tailored_resume.md` | no notice (exit 0), or notice lists items (exit 1) |
| Jobs kept | compare to `resume.md` | every employer/title/date still present |

Automated tests (no AI calls, no key needed):

```bash
uv run pytest
```
