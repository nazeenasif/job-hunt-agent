from job_hunt_agent.models import JobAnalysis, MatchItem, MatchReport, UnverifiedItem
from job_hunt_agent.report import add_review_section, add_unverified_notice, render_match_report


def test_add_unverified_notice_puts_block_at_top():
    items = [
        UnverifiedItem(text="2019", kind="number"),
        UnverifiedItem(text="Kubernetes", kind="skill"),
    ]
    result = add_unverified_notice("# Sam Lee\n", items)
    assert result.startswith("> ⚠ Unverified items")
    assert "> - 2019 (number)" in result
    assert "> - Kubernetes (skill)" in result
    assert result.endswith("# Sam Lee\n")


def test_add_unverified_notice_without_items_returns_text_unchanged():
    assert add_unverified_notice("# Sam Lee\n", []) == "# Sam Lee\n"


# --- render_match_report ---


ANALYSIS = JobAnalysis(
    title="Data Engineer",
    seniority="Not stated",
    must_have_skills=["Python", "Kubernetes"],
    nice_to_have_skills=[],
    responsibilities=["Build pipelines"],
    ats_keywords=["ETL"],
)

REPORT = MatchReport(
    strong_matches=[MatchItem(requirement="Python", proof_line="Built Python pipelines.")],
    weak_matches=[],
    gaps=["Kubernetes"],
    top_improvements=["First", "Second", "Third"],
)


def test_render_match_report_headings_in_order():
    text = render_match_report(ANALYSIS, REPORT)
    headings = [
        "# Match Report",
        "## Job Analysis",
        "## STRONG MATCHES",
        "## WEAK MATCHES",
        "## GAPS",
        "## TOP 3 IMPROVEMENTS",
    ]
    positions = [text.index(heading) for heading in headings]
    assert positions == sorted(positions)


def test_render_match_report_quotes_proof_and_numbers_improvements():
    text = render_match_report(ANALYSIS, REPORT)
    assert '- **Python** — "Built Python pipelines."' in text
    assert "1. First\n2. Second\n3. Third" in text
    assert "**Seniority**: Not stated" in text


def test_render_match_report_empty_sections_show_none():
    text = render_match_report(ANALYSIS, REPORT)
    weak_section = text.split("## WEAK MATCHES")[1].split("## GAPS")[0]
    assert "- None" in weak_section


def test_add_review_section_goes_at_the_end():
    result = add_review_section("# Sam\n\n## Gaps to work on\n- Docker\n", ["batch data pipelines"])
    assert result.endswith('- "batch data pipelines"\n')
    assert result.index("## Gaps to work on") < result.index("## Check these rewordings are true")


def test_add_review_section_without_phrases_returns_text_unchanged():
    assert add_review_section("# Sam\n", []) == "# Sam\n"
