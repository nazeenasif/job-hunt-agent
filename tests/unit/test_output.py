from job_hunt_agent.output import write_text_safely


def test_creates_new_file(tmp_path):
    target = tmp_path / "out.md"
    overwrote = write_text_safely(target, "hello")
    assert target.read_text(encoding="utf-8") == "hello"
    assert overwrote is False


def test_replaces_existing_file(tmp_path):
    target = tmp_path / "out.md"
    target.write_text("old", encoding="utf-8")
    overwrote = write_text_safely(target, "new")
    assert target.read_text(encoding="utf-8") == "new"
    assert overwrote is True


def test_leaves_no_temp_file(tmp_path):
    write_text_safely(tmp_path / "out.md", "hello")
    assert list(tmp_path.glob("*.tmp")) == []
