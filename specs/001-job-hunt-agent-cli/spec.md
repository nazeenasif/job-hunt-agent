# Feature Specification: Job Hunt Agent CLI

**Feature Branch**: `001-job-hunt-agent-cli`
**Created**: 2026-10-24
**Status**: Draft
**Input**: User description: "Build a Job Hunt Agent CLI. Input: job_posting.txt and resume.md. Three CrewAI agents run in sequence:
1. Researcher: extracts title, seniority, 5-8 must-have skills, nice-to-haves, responsibilities, ATS keywords.
2. Matcher: lists STRONG MATCHES (with proof line), WEAK MATCHES, GAPS, and top 3 improvements.
3. Writer: rewrites the resume using only true facts, reorders for relevance, adds \"What I changed\" and \"Gaps to work on\".
Output: tailored_resume.md. Clear error messages for a missing input file or missing API key."

## Clarifications

### Session 2026-10-24

- Q: When the truthfulness check finds items not in the input resume, what should happen? → A: Save the file with a "⚠ Unverified items" notice at the top listing each item, list them in the terminal, and exit with a failure status.
- Q: How much may the writer remove from the resume? → A: Keep every job and education entry (employer, title, dates); irrelevant bullet points and skills may be shortened or dropped.
- Q: Should the job analysis and match report be kept after the run? → A: Yes — also save them to a separate `match_report.md`.
- Q: What distinguishes a WEAK MATCH from a GAP? → A: A WEAK MATCH quotes a resume line showing a related skill or partial experience, plus a one-line note on the connection; if no line can be quoted, it is a GAP.
- Q: How long may each model answer be? → A: At most 4000 tokens by default, changeable with an optional `MAX_OUTPUT_TOKENS` setting in `.env` (added after the first live run was refused for requesting 64,000 tokens).
- Q: How should AI-service failures be shown? → A: Only the service's human-readable message plus a one-line hint, still naming the failed step with exit code 3; the AI framework's own error logs are hidden; full details are shown only with a `--debug` option.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get a tailored, truthful resume for one job (Priority: P1)

A job seeker has a job posting saved as `job_posting.txt` and their resume saved as
`resume.md`. They run one command. The tool studies the posting, compares it to the
resume, and writes `tailored_resume.md`: the same person's resume, reworded and
reordered so the most relevant experience comes first, with no invented facts. At the
end of the file are two sections: "What I changed" (so the user can review every edit)
and "Gaps to work on" (requirements the user does not yet meet).

**Why this priority**: This is the whole point of the tool. Without it, nothing else
delivers value.

**Independent Test**: Place a sample posting and resume in the folder, run the command,
and confirm `tailored_resume.md` exists, puts the most relevant experience first,
contains both closing sections, and contains no skill, tool, employer, date, or number
that is absent from `resume.md`.

**Acceptance Scenarios**:

1. **Given** a valid `job_posting.txt` and `resume.md` and a configured credential,
   **When** the user runs the command, **Then** `tailored_resume.md` is created and the
   user sees a message telling them where it was saved.
2. **Given** the posting emphasizes a skill the resume mentions only briefly, **When**
   the tool runs, **Then** the experience showing that skill appears earlier or more
   prominently in the tailored resume than in the original.
3. **Given** the posting requires a skill the resume does not contain, **When** the
   tool runs, **Then** that skill does NOT appear as a claimed skill in the tailored
   resume and DOES appear under "Gaps to work on".
4. **Given** any run, **When** the user reads "What I changed", **Then** each listed
   change describes a rewording, reordering, emphasis, or removal of a bullet point or
   skill — never an addition of a new fact.
5. **Given** a resume with a job unrelated to the posting, **When** the tool runs,
   **Then** that job still appears with its employer, title, and dates, though its
   bullet points may be shortened or removed.

---

### User Story 2 - Understand how well I match before applying (Priority: P2)

Before (or instead of) sending the tailored resume, the user wants to see an honest
breakdown: what the job asks for, where they match strongly (with the exact line from
their resume that proves it), where they match only partly, where they don't match at
all, and the three changes that would help most.

**Why this priority**: The analysis builds trust in the rewrite and helps the user
decide whether to apply. It is produced on the way to Story 1, so it can be shown and
tested on its own.

**Independent Test**: Run the command and confirm the job analysis and match report are
shown to the user, that every STRONG MATCH has a proof line that appears word-for-word
in `resume.md`, and that exactly three improvements are listed.

**Acceptance Scenarios**:

1. **Given** a posting, **When** the job analysis is produced, **Then** it lists the job
   title, seniority level, 5–8 must-have skills, nice-to-have skills, main
   responsibilities, and ATS keywords.
2. **Given** a posting that states no seniority level, **When** the analysis is
   produced, **Then** seniority is shown as "Not stated" (or inferred and labeled as
   inferred) rather than guessed silently.
3. **Given** the analysis and resume, **When** the match report is produced, **Then** it
   has four labeled parts: STRONG MATCHES (each with a proof line quoted from the
   resume), WEAK MATCHES (each with a quoted proof line and a note on the connection),
   GAPS, and TOP 3 IMPROVEMENTS.
4. **Given** a must-have skill with no evidence in the resume, **When** the match report
   is produced, **Then** that skill is listed under GAPS, not under any match section.
5. **Given** a successful run, **When** the user opens `match_report.md`, **Then** it
   contains the same job analysis and match report shown in the terminal.

---

### User Story 3 - Fix setup problems quickly (Priority: P3)

A user who forgot a file or hasn't configured their AI service credential gets a short,
plain-English message saying exactly what is wrong and how to fix it, instead of a
confusing crash.

**Why this priority**: Important for first-time use, but only matters once the main flow
exists.

**Independent Test**: Run the command with each input file missing in turn, then with
the credential missing, and confirm each produces the matching clear message, no
output file, and a failure exit status — before any AI work starts.

**Acceptance Scenarios**:

1. **Given** `job_posting.txt` is missing, **When** the user runs the command, **Then**
   the tool stops and says the job posting file was not found, naming the file and the
   folder it looked in.
2. **Given** `resume.md` is missing, **When** the user runs the command, **Then** the
   tool stops with an equivalent message naming the resume file.
3. **Given** the AI service credential is not configured, **When** the user runs the
   command, **Then** the tool stops, names the missing setting, tells the user to add it
   to their `.env` file, and never prints any secret value.
4. **Given** any of the above errors, **When** the tool stops, **Then** neither
   `tailored_resume.md` nor `match_report.md` is created or modified.

---

### Edge Cases

- **Empty input file**: an input file exists but is empty or only whitespace → stop with
  a clear message naming the empty file.
- **Posting lists fewer than 5 must-haves**: list only the must-haves actually stated;
  never pad the list with invented requirements. More than 8 → keep the 8 most
  important.
- **Resume shares almost nothing with the posting**: still produce a tailored resume
  (reordered, truthful) with most requirements under "Gaps to work on"; never fill gaps
  with invented experience.
- **`tailored_resume.md` or `match_report.md` already exists**: it is replaced by the
  new result, and the user is told it was overwritten.
- **AI service fails mid-run** (network error, invalid or rejected credential, rate
  limit): stop with a plain-English message saying which step failed; do not write
  either output file.
- **Truthfulness check flags items**: the file is still saved, but it opens with a
  "⚠ Unverified items" notice and the run ends with a failure status (see FR-020), so
  neither the user nor a script can mistake it for a clean result.
- **Writer rewords a job-posting phrase**: if the phrase is general wording rather than
  a tool or name, it is listed for review at the end of the file and in the terminal,
  and the run still succeeds (see FR-020a).
- **Input file is not readable text** (wrong encoding / binary): stop with a clear
  message naming the file.

## Requirements *(mandatory)*

### Functional Requirements

**Inputs and startup checks**

- **FR-001**: The tool MUST be run as a single terminal command.
- **FR-002**: The tool MUST read the job posting from `job_posting.txt` and the resume
  from `resume.md` in the current folder by default, and SHOULD let the user point to
  different file paths.
- **FR-003**: Before doing any AI work, the tool MUST check that both input files exist,
  are readable, and are not empty, and that the AI service credential is configured.
- **FR-004**: Each failed check MUST produce its own clear message naming the problem
  (which file, or which setting) and a one-line fix, and MUST end with a failure exit
  status.
- **FR-005**: The tool MUST NOT display, log, or write any secret value in any message
  or file.

**Step 1 – Job research**

- **FR-006**: The tool MUST extract from the posting: job title, seniority level,
  5–8 must-have skills, nice-to-have skills, key responsibilities, and ATS keywords.
- **FR-007**: The research step MUST use only what is in the posting; if a field is not
  stated, it MUST be marked "Not stated" (or labeled as inferred), and the must-have list
  MUST NOT be padded beyond what the posting supports.

**Step 2 – Matching**

- **FR-008**: The tool MUST compare the research results against the resume and produce
  four sections: STRONG MATCHES, WEAK MATCHES, GAPS, and TOP 3 IMPROVEMENTS.
- **FR-009**: Every STRONG MATCH MUST include a proof line quoted exactly from the
  resume.
- **FR-009a**: Every WEAK MATCH MUST include a proof line quoted exactly from the resume
  that shows a related skill or partial experience, plus a one-line note explaining the
  connection. A requirement with no quotable resume line MUST be listed under GAPS.
- **FR-010**: Every must-have skill MUST appear in exactly one of STRONG MATCHES,
  WEAK MATCHES, or GAPS.
- **FR-011**: The TOP 3 IMPROVEMENTS MUST be things the user can truthfully do with the
  resume (e.g., reorder, emphasize, reword existing facts) or real-world actions (e.g.,
  learn a skill) — never suggestions to claim something untrue.
- **FR-011a**: An improvement MUST NOT contain a number, tool, product or company name
  that is not in the resume (skills named in the job posting are allowed). A detail the
  candidate might have MUST be written as a placeholder (e.g. `[X]%`, `[tool]`) together
  with the words "only if true". Improvements that break this MUST be sent back to the
  matching step for a retry, like proof lines.

**Step 3 – Writing**

- **FR-012**: The tool MUST produce a rewritten resume that uses only facts from the
  input resume. It MUST NOT add any skill, tool, employer, job title, date, or number
  (metric, percentage, team size, years of experience) that is not in the input resume.
- **FR-013**: The rewritten resume MUST reorder and reword content so the experience
  most relevant to the posting appears first, and SHOULD naturally use posting keywords
  only where the resume genuinely supports them.
- **FR-013a**: The rewritten resume MUST keep every job and education entry from the
  input, each with its employer/institution, title, and dates. The writer MAY shorten
  or drop individual bullet points and listed skills that are not relevant to the
  posting; it MUST NOT drop a whole job, education entry, or its dates.
- **FR-014**: The output MUST end with a "What I changed" section listing each change
  made and a "Gaps to work on" section listing requirements from the GAPS section.

**Flow and output**

- **FR-015**: The three steps MUST run in order (research → matching → writing), each
  using the previous step's results.
- **FR-016**: The tool MUST show the user which step is running, and MUST show the
  research results and the match report in the terminal.
- **FR-017**: The tool MUST save the final result to `tailored_resume.md` and the job
  analysis plus match report to `match_report.md` (both Markdown), overwriting any
  existing files of those names and telling the user it did so.
- **FR-018**: If any step fails, the tool MUST stop with a message naming the failed
  step and MUST NOT write or modify either output file.
- **FR-018a**: The failure message MUST show only the AI service's human-readable error
  text (not raw response data) followed by a one-line hint on how to fix it (e.g. add
  credits, check the model ID, check the key, wait and retry). The AI framework's own
  log lines MUST NOT be shown by default.
- **FR-018b**: A `--debug` option MUST show the full error details and the AI
  framework's log lines, still without any secret value.

**Output length**

- **FR-021**: Each model answer MUST be limited to 4000 tokens by default. The user MAY
  change the limit with an optional `MAX_OUTPUT_TOKENS` setting in `.env`. A value that
  is not a whole number above 0 MUST be reported as a setup error (FR-004) before any
  AI work begins.

**Privacy**

- **FR-022**: The tool MUST NOT send usage telemetry or execution traces to the AI
  framework's vendor, and MUST NEVER pause to ask the user for input during a run.

**Truthfulness check**

- **FR-019**: After writing, the tool MUST automatically check the tailored resume for
  skills, tools, employers, dates, and numbers that do not appear in the input resume.
  Numbers written as words count when they sit next to a unit (e.g. "three years",
  "five-year", "ten+ projects"); a lone "one" does not.
- **FR-012a**: The rewritten resume MUST NOT compute or state durations or totals (e.g.
  "three years of experience") even when they could be worked out from the dates.
- **FR-020**: If the check finds any such items, the tool MUST (a) still save
  `tailored_resume.md`, (b) place a "⚠ Unverified items" notice at the very top of the
  file listing each flagged item, (c) list the same items in the terminal, and (d) exit
  with a failure status. If the check finds nothing, no notice is added and the tool
  exits with a success status.
- **FR-020a**: The check has two levels. **Hard failures** (FR-020, failure status) are
  invented numbers, tools, skills, employers, titles and dates. This includes any
  job-posting term that is a single word or contains a name or tech word missing from
  the resume. **Review warnings** are general job-posting phrases that appear in the
  tailored resume but are not word-for-word in the original (e.g. "batch data
  pipelines" for "batch pipelines"). Review warnings MUST NOT change the exit status.
  They MUST be printed under "Check these rewordings are true:" and added as a final
  `## Check these rewordings are true` section of `tailored_resume.md`.

### Key Entities

- **Job Posting**: the raw text of the job ad provided by the user.
- **Resume**: the user's original resume in Markdown; the single source of truth for
  every fact in the output.
- **Job Analysis**: the research result — title, seniority, must-have skills (5–8),
  nice-to-haves, responsibilities, ATS keywords.
- **Match Report**: strong matches (each with a proof line from the resume), weak
  matches (each with a proof line and a connection note), gaps, and top 3 improvements.
- **Tailored Resume**: the rewritten resume plus "What I changed" and "Gaps to work on"
  sections, saved as `tailored_resume.md`.
- **Match Report File**: the Job Analysis followed by the Match Report, saved as
  `match_report.md` for later reference (e.g., interview prep).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with both files and a configured credential gets
  `tailored_resume.md` from a single command, with no other steps, in under 3 minutes
  for a typical one-page posting and two-page resume.
- **SC-002**: Across a test set of at least 5 posting/resume pairs, 100% of skills,
  tools, employers, dates, and numbers in each tailored resume appear in the
  corresponding input resume.
- **SC-003**: 100% of STRONG and WEAK MATCH proof lines can be found word-for-word in
  the input resume.
- **SC-004**: 100% of must-have skills absent from the resume appear under "Gaps to
  work on".
- **SC-005**: For each setup error (missing posting, missing resume, missing
  credential), a first-time user can tell from the message alone what to fix, and the
  message appears within 2 seconds, before any AI work begins.
- **SC-006**: In a review of the test set, the reviewer agrees the tailored resume
  places the most job-relevant experience before less relevant experience in at least
  4 of 5 cases.

## Assumptions

- Single user running the tool locally on their own files; no accounts, sharing, or
  multi-user features.
- One posting and one resume per run; batch processing is out of scope.
- The resume is in English Markdown; the posting is plain English text.
- The AI service credential is supplied via a local `.env` file (per constitution
  Principle III).
- The user has specified CrewAI as the agent framework; that choice, the AI provider,
  and the model are confirmed in the plan, not this spec.
- Output overwrites existing `tailored_resume.md` and `match_report.md` rather than
  creating numbered copies.

## Out of Scope

- Cover letters, application submission, or job searching/scraping.
- Formats other than Markdown output (PDF, Word).
- A web interface or saved history of past runs (per constitution Principle IV).
