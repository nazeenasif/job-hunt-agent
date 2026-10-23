# Output File Contract

## `tailored_resume.md`

```markdown
> ⚠ Unverified items — these were not found in your original resume. Check each one
> before sending:
> - 2019 (number)
> - Kubernetes (skill)

<rewritten resume body>

## What I changed
- Moved "Data Engineer at Acme" above "Intern at Foo" because it shows Python and SQL.
- Reworded summary to lead with data-pipeline experience.

## Gaps to work on
- Kubernetes
- Terraform
```

- The `⚠ Unverified items` block appears **only** when the check flags something
  (FR-020). It is a Markdown blockquote at the very top.
- `## What I changed` and `## Gaps to work on` are always present, in that order. If
  there are no gaps, the section says `- None found`.
- `## Check these rewordings are true` is added as the very last section **only** when
  general job-posting phrases were used that are not word-for-word in the original
  resume (FR-020a). It lists each phrase as `- "<phrase>"` and does not affect the exit code:

```markdown
## Check these rewordings are true
These phrases come from the job posting and are not word-for-word in your
original resume. Keep them only if they describe what you really did.

- "batch data pipelines"
- "cloud data warehouse"
```

## `match_report.md`

```markdown
# Match Report

## Job Analysis
- **Title**: <title>
- **Seniority**: <seniority>

### Must-have skills
- ...
### Nice-to-have skills
- ...
### Responsibilities
- ...
### ATS keywords
- ...

## STRONG MATCHES
- **<requirement>** — "<proof line>"

## WEAK MATCHES
- **<requirement>** — "<proof line>" — <note>

## GAPS
- <requirement>

## TOP 3 IMPROVEMENTS
1. ...
2. ...
3. ...
```

The code builds this from `JobAnalysis` and `MatchReport` (it is not written by the
model), so the layout is always the same. The terminal shows the same text (FR-016).
