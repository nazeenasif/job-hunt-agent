# CLI Contract: `job-hunt`

This tool has no network API. The contract is the command line, the exit codes, the
messages, and the output files.

## Invocation

```text
uv run job-hunt [--job PATH] [--resume PATH] [--debug]
python -m job_hunt_agent [same options]
```

| Option | Default | Meaning |
|--------|---------|---------|
| `--job` | `job_posting.txt` | path to the job posting (plain text) |
| `--resume` | `resume.md` | path to the resume (Markdown) |
| `--debug` | off | on a failed step, also print the full error details and CrewAI's log lines (key still masked) |

Outputs are always written to the current folder (spec FR-017).

## Environment (`.env`)

| Variable | Required | Notes |
|----------|----------|-------|
| `OPENROUTER_API_KEY` | yes | never printed or logged |
| `OPENROUTER_MODEL` | yes | OpenRouter model ID, e.g. `<provider>/<model>`; `openrouter/` prefix optional |
| `MAX_OUTPUT_TOKENS` | no | most tokens the model may write per step; default `4000`; must be a whole number above 0 |

## Exit codes

| Code | Meaning | Files written |
|------|---------|---------------|
| 0 | Success, truthfulness check clean | both |
| 0 | Success, but reworded job-posting phrases need review (FR-020a) | both, resume ends with a review section |
| 1 | Finished, but invented facts were found (FR-020) | both, resume starts with notice |
| 2 | Setup error: input file missing/empty/unreadable, or env var missing | none |
| 3 | An AI step failed (network, auth, rate limit, guardrail exhausted) | none |

## Messages (stderr for errors, stdout for progress)

| Situation | Message (exact wording may vary slightly; the parts shown here are required) |
|-----------|-------------------------------------------|
| file missing | `Error: job posting file not found: <abs path>. Fix: create it or pass --job PATH.` |
| file empty | `Error: resume file is empty: <abs path>. Fix: paste your resume into it.` |
| not UTF-8 | `Error: could not read <abs path> as text. Fix: save it as UTF-8 plain text.` |
| key missing | `Error: OPENROUTER_API_KEY is not set. Fix: copy .env.example to .env and add your key.` |
| model missing | `Error: OPENROUTER_MODEL is not set. Fix: add a model ID to .env (see .env.example).` |
| bad token limit | `Error: MAX_OUTPUT_TOKENS must be a whole number above 0 (got '<value>'). Fix: ...` |
| step running | `Step 1/3: Researching the job posting...` (and `2/3 Matching...`, `3/3 Writing...`) |
| step failed | `Error: Step 2/3 (Matching) failed: <short reason>. No files were written.` then `Hint: <one-line fix>`. For API errors, `<short reason>` is only the service's message plus `(HTTP <code>)`, e.g. `This request requires more credits... (HTTP 402)`; no raw JSON. |
| step failed + `--debug` | the two lines above, then `Full error details:` and the full error text |
| overwrite | `Note: overwrote existing <path>` |
| done | `Saved: <path to tailored_resume.md>` and `Saved: <path to match_report.md>` |
| rewordings | `Check these rewordings are true:` then one `  - <phrase>` per phrase (does not change the exit code) |
| unverified | `Warning: N unverified item(s) found — review the top of tailored_resume.md:` then one `  - <text> (<kind>)` per item |

**Hints by cause**: 400/404 → check `OPENROUTER_MODEL`; 401 → check `OPENROUTER_API_KEY`;
402 → add credits, use a cheaper model, or lower `MAX_OUTPUT_TOKENS`; 403 → try another
model; 408 → try again; 429 → wait and retry; 5xx → provider problem, try later;
guardrail retries used up → use a more capable model; anything else → rerun with `--debug`.

CrewAI's own `logging` output is turned off during the run unless `--debug` is given.

**Invariant**: no message ever contains the value of `OPENROUTER_API_KEY`.
