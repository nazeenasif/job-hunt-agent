# Data Model: Job Hunt Agent CLI

**Feature**: `001-job-hunt-agent-cli` | **Date**: 2026-10-24

Everything lives in memory for one run. Nothing is stored between runs except the two
output files. The structured models are Pydantic classes in
`src/job_hunt_agent/models.py`.

## Inputs

### JobPosting (plain text)
- Source: `job_posting.txt`, or the path given with `--job`.
- Validation: the file must exist, decode as UTF-8, and not be empty or whitespace-only
  (FR-003). Otherwise exit with code 2.

### Resume (Markdown text)
- Source: `resume.md`, or the path given with `--resume`.
- Validation: same as JobPosting.
- Role: **the only source of truth** for every fact in the outputs (Principle II).

### Settings
| Field | Source | Rule |
|-------|--------|------|
| `api_key` | `OPENROUTER_API_KEY` in `.env` / environment | required, non-empty; never printed |
| `model` | `OPENROUTER_MODEL` in `.env` / environment | required, non-empty; `openrouter/` prefix added if missing |
| `max_output_tokens` | `MAX_OUTPUT_TOKENS` in `.env` / environment | optional, default 4000; whole number > 0; passed to the LLM as `max_tokens` |

If a required value is missing, or `MAX_OUTPUT_TOKENS` is invalid, exit with code 2 and a
message that names the variable.

## Step 1 output — `JobAnalysis`

| Field | Type | Rule |
|-------|------|------|
| `title` | `str` | from the posting; `"Not stated"` if absent |
| `seniority` | `str` | from the posting; `"Not stated"`, or ends with `" (inferred)"` if inferred (FR-007) |
| `must_have_skills` | `list[str]` | at most 8; fewer than 5 only if the posting states fewer; never padded |
| `nice_to_have_skills` | `list[str]` | may be empty |
| `responsibilities` | `list[str]` | main duties, in the posting's own words or close to them |
| `ats_keywords` | `list[str]` | terms and phrases that appear in the posting |

## Step 2 output — `MatchReport`

### `MatchItem`
| Field | Type | Rule |
|-------|------|------|
| `requirement` | `str` | a must-have skill from `JobAnalysis` |
| `proof_line` | `str` | **exact** quote from the resume (checked after whitespace is normalized) |
| `note` | `str` | required for WEAK matches: one line explaining the connection; may be empty for STRONG |

### `MatchReport`
| Field | Type | Rule |
|-------|------|------|
| `strong_matches` | `list[MatchItem]` | each `proof_line` is in the resume (FR-009) |
| `weak_matches` | `list[MatchItem]` | each `proof_line` is in the resume and `note` is non-empty (FR-009a) |
| `gaps` | `list[str]` | must-haves with no line to quote |
| `top_improvements` | `list[str]` | exactly 3; truthful actions only (FR-011) |

**Guardrail rules** (enforced on the match task; on failure CrewAI retries up to 2
times, then step 2 fails):
1. Every `proof_line` is found in the resume.
2. Every must-have skill appears in exactly one of `strong_matches`, `weak_matches` or
   `gaps` (FR-010). Comparison is case-insensitive.
3. `len(top_improvements) == 3`.
4. Every WEAK match has a non-empty `note`.

## Step 3 output — tailored resume (Markdown string)

The writer produces this layout:

```text
<rewritten resume body>
## What I changed
- <one bullet per change: reworded / reordered / emphasized / removed bullet or skill>
## Gaps to work on
- <one bullet per item in MatchReport.gaps>
```

Rules: no new facts (FR-012). Every job and education entry is kept with its
employer/institution, title and dates (FR-013a).

## Post-check — `UnverifiedItem`

| Field | Type | Meaning |
|-------|------|---------|
| `text` | `str` | the flagged token or phrase |
| `kind` | `str` | one of `number`, `skill`, `name` |

`find_unverified_items()` returns `list[UnverifiedItem]`. An empty list means the
output is clean.

## Run lifecycle

```text
start
  → check files & settings ──fail──▶ exit 2 (nothing written)
  → Step 1 Research        ──fail──▶ exit 3 (nothing written)
  → Step 2 Match (+guardrail) ─fail─▶ exit 3 (nothing written)
  → Step 3 Write           ──fail──▶ exit 3 (nothing written)
  → truthfulness check
  → write match_report.md, then tailored_resume.md (prepend notice if any flagged)
  → exit 0 (clean) or exit 1 (unverified items)
```
