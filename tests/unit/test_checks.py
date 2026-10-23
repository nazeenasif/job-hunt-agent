from job_hunt_agent.checks import (
    check_match_report,
    find_rewordings_to_review,
    find_unverified_items,
    is_tool_like,
)
from job_hunt_agent.models import JobAnalysis, MatchItem, MatchReport

RESUME = """# Sam Lee

## Experience

### Data Engineer — Acme Corp (2020 - 2023)
- Built Python pipelines that cut report time by 30%.
- Wrote SQL for the finance team.

## Skills
Python, SQL, Airflow
"""

ANALYSIS = JobAnalysis(
    title="Data Engineer",
    seniority="Mid",
    must_have_skills=["Python", "SQL", "Kubernetes"],
    nice_to_have_skills=["Terraform"],
    responsibilities=["Build pipelines"],
    ats_keywords=["ETL"],
)


def unverified_texts(tailored: str) -> list[str]:
    return [item.text for item in find_unverified_items(tailored, RESUME, ANALYSIS)]


def test_clean_rewrite_has_no_items():
    tailored = """# Sam Lee

## Experience

### Data Engineer — Acme Corp (2020 - 2023)
- Wrote SQL for the finance team.
- Built Python pipelines that cut report time by 30%.

## What I changed
- Moved the SQL bullet up.

## Gaps to work on
- Kubernetes
"""
    assert unverified_texts(tailored) == []


def test_flags_new_year():
    assert "2019" in unverified_texts("Data Engineer at Acme Corp since 2019.")


def test_flags_new_percentage():
    assert "40" in unverified_texts("Cut report time by 40%.")


def test_ignores_numbers_in_resume():
    assert unverified_texts("Cut report time by 30% from 2020 to 2023.") == []


def test_flags_job_skill_missing_from_resume():
    items = find_unverified_items("- Ran Python jobs on Kubernetes.", RESUME, ANALYSIS)
    assert [(i.text, i.kind) for i in items] == [("Kubernetes", "skill")]


def test_ignores_skill_only_in_closing_sections():
    tailored = """- Built Python pipelines.

## What I changed
- Did not add Kubernetes because it is not in the resume.

## Gaps to work on
- Kubernetes
- Terraform
"""
    assert unverified_texts(tailored) == []


def test_flags_new_proper_noun_mid_sentence():
    items = find_unverified_items("- Built pipelines at Google.", RESUME, ANALYSIS)
    assert [(i.text, i.kind) for i in items] == [("Google", "name")]


def test_flags_tech_token():
    assert "PostgreSQL" in unverified_texts("- Wrote SQL and PostgreSQL queries.")


def test_does_not_flag_capitalized_word_at_line_or_bullet_start():
    assert unverified_texts("Delivered pipelines.\n- Designed reports.") == []


def test_does_not_flag_capitalized_word_after_full_stop():
    assert unverified_texts("Wrote SQL. Designed reports.") == []


def test_does_not_flag_stop_words():
    assert unverified_texts("## Professional Summary\nWork in January and Present.") == []


def test_matching_is_case_insensitive():
    assert unverified_texts("- Strong in python and AIRFLOW.") == []


def test_each_item_reported_once():
    assert unverified_texts("Used Kubernetes. Loved Kubernetes daily with Kubernetes.") == [
        "Kubernetes"
    ]


# --- check_match_report (the Matcher guardrail rules) ---


GOOD_REPORT = MatchReport(
    strong_matches=[
        MatchItem(requirement="Python", proof_line="Built Python pipelines that cut report time by 30%."),
    ],
    weak_matches=[
        MatchItem(
            requirement="SQL",
            proof_line="Wrote SQL for the finance team.",
            note="SQL used for reporting, not pipelines.",
        ),
    ],
    gaps=["Kubernetes"],
    top_improvements=["Lead with pipelines", "Mention Airflow earlier", "Learn Kubernetes"],
)


def report_with(**changes) -> MatchReport:
    return GOOD_REPORT.model_copy(update=changes)


def test_check_match_report_valid_report_has_no_problems():
    assert check_match_report(GOOD_REPORT, ANALYSIS, RESUME) == []


def test_check_match_report_strong_proof_not_in_resume():
    bad = report_with(strong_matches=[MatchItem(requirement="Python", proof_line="Expert in Python.")])
    problems = check_match_report(bad, ANALYSIS, RESUME)
    assert any("Expert in Python." in problem for problem in problems)


def test_check_match_report_weak_match_needs_note():
    bad = report_with(
        weak_matches=[MatchItem(requirement="SQL", proof_line="Wrote SQL for the finance team.")]
    )
    problems = check_match_report(bad, ANALYSIS, RESUME)
    assert any("note" in problem for problem in problems)


def test_check_match_report_skill_in_two_buckets():
    bad = report_with(gaps=["Kubernetes", "Python"])
    problems = check_match_report(bad, ANALYSIS, RESUME)
    assert any("Python" in problem for problem in problems)


def test_check_match_report_skill_in_no_bucket():
    bad = report_with(gaps=[])
    problems = check_match_report(bad, ANALYSIS, RESUME)
    assert any("Kubernetes" in problem for problem in problems)


def test_check_match_report_needs_exactly_three_improvements():
    assert check_match_report(report_with(top_improvements=["a", "b"]), ANALYSIS, RESUME)
    assert check_match_report(report_with(top_improvements=["a", "b", "c", "d"]), ANALYSIS, RESUME)


def test_check_match_report_tolerates_whitespace_and_quotes():
    spaced = report_with(
        strong_matches=[
            MatchItem(
                requirement="Python",
                proof_line='"Built Python   pipelines that cut\nreport time by 30%."',
            )
        ]
    )
    assert check_match_report(spaced, ANALYSIS, RESUME) == []


def test_check_match_report_bucket_names_ignore_case():
    assert check_match_report(report_with(gaps=["kubernetes"]), ANALYSIS, RESUME) == []


# --- number words next to units ---


def test_flags_number_word_with_unit():
    items = find_unverified_items("Data Engineer with three years of experience.", RESUME, ANALYSIS)
    assert [(i.text, i.kind) for i in items] == [("three years", "number")]


def test_flags_hyphenated_and_plus_number_words():
    texts = unverified_texts("A five-year veteran of ten+ projects with twenty percent growth.")
    assert texts == ["five-year", "ten+ projects", "twenty percent"]


def test_does_not_flag_number_word_without_unit():
    assert unverified_texts("Wrote SQL as one of the finance team.") == []


def test_number_word_matching_resume_digits_is_fine():
    resume = RESUME + "- Supported 2 teams.\n"
    items = find_unverified_items("- Supported two teams.", resume, ANALYSIS)
    assert items == []


def test_number_word_only_in_closing_sections_is_ignored():
    tailored = "- Wrote SQL.\n\n## Gaps to work on\n- Two years of Kubernetes would help.\n"
    assert unverified_texts(tailored) == []


# --- improvements must not invent details ---


def test_check_match_report_rejects_improvement_with_invented_tool_and_number():
    bad = report_with(
        top_improvements=[
            "Lead with pipelines",
            "Mention Airflow earlier",
            "Write that you implemented Great Expectations checks that caught 95% of bad rows.",
        ]
    )
    problems = check_match_report(bad, ANALYSIS, RESUME)
    assert len(problems) == 1
    assert "95" in problems[0]
    assert "Great" in problems[0]
    assert "[X]%" in problems[0]


def test_check_match_report_accepts_placeholders_with_only_if_true():
    good = report_with(
        top_improvements=[
            "Add the share of bad rows your checks caught, e.g. [X]%, only if true.",
            "Name the [tool] you used for data quality checks, only if true.",
            "Learn Kubernetes and Terraform.",
        ]
    )
    assert check_match_report(good, ANALYSIS, RESUME) == []


def test_check_match_report_rejects_placeholder_without_only_if_true():
    bad = report_with(
        top_improvements=["Add [X]% to the pipeline bullet.", "Lead with SQL", "Learn Kubernetes"]
    )
    problems = check_match_report(bad, ANALYSIS, RESUME)
    assert any("only if true" in problem for problem in problems)


def test_check_match_report_rejects_invented_company_in_improvement():
    bad = report_with(
        top_improvements=["Mention your work for Google.", "Lead with SQL", "Learn Kubernetes"]
    )
    problems = check_match_report(bad, ANALYSIS, RESUME)
    assert any("Google" in problem for problem in problems)


# --- two levels: invented facts (hard) vs. reworded posting phrases (review) ---

PHRASE_ANALYSIS = ANALYSIS.model_copy(
    update={"ats_keywords": ["batch data pipelines", "SQL queries", "Apache Spark"]}
)


def test_is_tool_like():
    assert is_tool_like("Kubernetes", RESUME)
    assert is_tool_like("dbt", RESUME)
    assert is_tool_like("Apache Spark", RESUME)
    assert not is_tool_like("batch data pipelines", RESUME)
    assert not is_tool_like("SQL queries", RESUME)  # SQL is in the resume


def test_reworded_posting_phrase_is_review_not_failure():
    tailored = "- Built batch data pipelines and wrote SQL queries in Python."
    assert find_unverified_items(tailored, RESUME, PHRASE_ANALYSIS) == []
    assert find_rewordings_to_review(tailored, RESUME, PHRASE_ANALYSIS) == [
        "batch data pipelines",
        "SQL queries",
    ]


def test_posting_tool_phrase_is_still_a_hard_failure():
    tailored = "- Built pipelines with Apache Spark."
    items = find_unverified_items(tailored, RESUME, PHRASE_ANALYSIS)
    assert ("Apache Spark", "skill") in [(i.text, i.kind) for i in items]
    assert find_rewordings_to_review(tailored, RESUME, PHRASE_ANALYSIS) == []


def test_rewordings_in_closing_sections_are_ignored():
    tailored = "- Wrote SQL.\n\n## Gaps to work on\n- batch data pipelines\n"
    assert find_rewordings_to_review(tailored, RESUME, PHRASE_ANALYSIS) == []
