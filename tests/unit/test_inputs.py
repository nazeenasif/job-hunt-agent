import pytest

from job_hunt_agent.config import SetupError
from job_hunt_agent.inputs import read_input_file


def test_returns_text_of_valid_file(tmp_path):
    path = tmp_path / "resume.md"
    path.write_text("# Sam", encoding="utf-8")
    assert read_input_file(path, "resume") == "# Sam"


def test_missing_file_names_label_and_path(tmp_path):
    path = tmp_path / "job_posting.txt"
    with pytest.raises(SetupError) as error:
        read_input_file(path, "job posting")
    message = str(error.value)
    assert "job posting file not found" in message
    assert str(path.resolve()) in message
    assert "--job" in message


def test_missing_resume_suggests_resume_option(tmp_path):
    with pytest.raises(SetupError) as error:
        read_input_file(tmp_path / "resume.md", "resume")
    assert "--resume" in str(error.value)


@pytest.mark.parametrize("content", ["", "   \n\t  "])
def test_empty_file_is_rejected(tmp_path, content):
    path = tmp_path / "resume.md"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(SetupError) as error:
        read_input_file(path, "resume")
    assert "resume file is empty" in str(error.value)


def test_non_utf8_file_is_rejected(tmp_path):
    path = tmp_path / "resume.md"
    path.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(SetupError) as error:
        read_input_file(path, "resume")
    assert "could not read" in str(error.value)
