"""Write output files safely, so a crash never leaves half a file behind."""

import os
from pathlib import Path


def write_text_safely(path: Path, text: str) -> bool:
    """Write `text` to `path` in one step.

    We first write a temporary file next to the target, then swap it into place
    with os.replace (which happens all at once). Returns True if an older file
    was overwritten.
    """
    already_existed = path.exists()
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(text, encoding="utf-8")
    os.replace(temp_path, path)
    return already_existed
