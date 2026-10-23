from job_hunt_agent.tasks import MATCH_DESCRIPTION, WRITE_DESCRIPTION


def test_writer_is_told_never_to_compute_durations_or_totals():
    assert "Never compute or state durations or totals" in WRITE_DESCRIPTION
    assert "even if they could" in WRITE_DESCRIPTION


def test_matcher_is_told_to_use_placeholders_with_only_if_true():
    assert "[X]%" in MATCH_DESCRIPTION
    assert "only if true" in MATCH_DESCRIPTION
