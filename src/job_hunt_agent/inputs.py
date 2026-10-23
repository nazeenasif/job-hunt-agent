"""Read the job posting and resume files, with clear errors when something is wrong."""

from pathlib import Path

from job_hunt_agent.config import SetupError

# Which command-line option lets the user point to a different file.
OPTION_FOR_LABEL = {"job posting": "--job", "resume": "--resume"}


def read_input_file(path: Path, label: str) -> str:
    """Return the text of an input file.

    `label` is a friendly name used in error messages, e.g. "job posting".
    Raises SetupError if the file is missing, empty, or not readable text.
    """
    full_path = path.resolve()

    if not path.is_file():
        option = OPTION_FOR_LABEL.get(label, "the right option")
        raise SetupError(
            f"Error: {label} file not found: {full_path}. "
            f"Fix: create it or pass {option} PATH."
        )

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise SetupError(
            f"Error: could not read {full_path} as text. "
            "Fix: save it as UTF-8 plain text."
        )

    if not text.strip():
        raise SetupError(
            f"Error: {label} file is empty: {full_path}. "
            f"Fix: paste your {label} into it."
        )

    return text
