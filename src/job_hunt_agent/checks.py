"""Plain-Python checks that do not trust the AI.

`find_unverified_items` looks for facts in the tailored resume that are not in
the original resume (constitution Principle II).
"""

import re

from job_hunt_agent.models import JobAnalysis, MatchReport, UnverifiedItem

# Sections that are allowed to mention things the user does not have yet.
REVIEW_HEADING = "Check these rewordings are true"
CLOSING_SECTIONS = ("what i changed", "gaps to work on", REVIEW_HEADING.lower())

# Capitalized words that are normal resume vocabulary, not names to verify.
STOP_WORDS = {
    "summary", "profile", "objective", "about", "experience", "work",
    "professional", "employment", "history", "skills", "technical", "education",
    "projects", "certifications", "contact", "highlights", "achievements",
    "languages", "interests", "references", "present", "current", "remote",
    "hybrid", "onsite",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct",
    "nov", "dec",
    "e.g", "i.e", "etc",
}

NUMBER_PATTERN = re.compile(r"\d+(?:[.,]\d+)*")
WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-]*")
# Markdown at the start of a line: headings, quotes, bullets, numbered lists.
LINE_START_MARKUP = re.compile(r"^\s*(?:#+|>|[-*+]|\d+[.)])?\s*")

# Number words, so "three years" is checked like "3 years".
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
    "dozen": 12,
}

# Units that turn a number word into a claim. A lone "one" ("one of the team")
# is ordinary English and is not checked.
NUMBER_UNITS = (
    "years", "year", "yrs", "months", "month", "weeks", "week", "days", "day",
    "hours", "hour", "people", "person", "engineers", "developers", "members",
    "reports", "projects", "project", "clients", "customers", "users", "teams",
    "countries", "pipelines", "percent", "%",
)

# e.g. "three years", "five-year", "ten+ projects", "twenty percent"
NUMBER_WORD_WITH_UNIT = re.compile(
    r"\b(" + "|".join(NUMBER_WORDS) + r")(\+|\s*plus)?[\s-]*("
    + "|".join(re.escape(unit) for unit in NUMBER_UNITS) + r")(?![A-Za-z])",
    re.IGNORECASE,
)

# A placeholder the user fills in themselves, e.g. [X]% or [tool].
PLACEHOLDER = re.compile(r"\[[^\]]*\]")


def appears_in(term: str, text: str) -> bool:
    """True if `term` appears in `text` as a whole word (case is ignored)."""
    pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def heading_level(line: str) -> int:
    """Return 1 for "# x", 2 for "## x", and so on; 0 if the line is not a heading."""
    stripped = line.lstrip()
    level = len(stripped) - len(stripped.lstrip("#"))
    if level > 0 and stripped[level:].startswith(" "):
        return level
    return 0


def split_body(tailored_md: str) -> str:
    """Return the tailored resume without the "What I changed" and "Gaps to work on" sections."""
    body_lines = []
    skipping_level = 0  # heading level of the closing section we are inside, 0 = none

    for line in tailored_md.splitlines():
        level = heading_level(line)
        if level:
            title = line.strip().lstrip("#").strip().lower()
            if title in CLOSING_SECTIONS:
                skipping_level = level
                continue
            if skipping_level and level <= skipping_level:
                skipping_level = 0
        if not skipping_level:
            body_lines.append(line)

    return "\n".join(body_lines)


def clean_line(line: str) -> str:
    """Remove line-start Markdown and bold/italic/code markers from one line."""
    without_markup = LINE_START_MARKUP.sub("", line, count=1)
    return re.sub(r"[*_`]", " ", without_markup)


def find_new_numbers(body: str, resume: str) -> list[str]:
    """Numbers (years, percentages, counts) in the body that the resume never mentions."""
    resume_numbers = set(NUMBER_PATTERN.findall(resume))
    new_numbers = []
    for line in body.splitlines():
        for number in NUMBER_PATTERN.findall(clean_line(line)):
            if number not in resume_numbers and number not in new_numbers:
                new_numbers.append(number)
    return new_numbers


def find_new_number_words(body: str, resume: str) -> list[str]:
    """Number words next to a unit ("three years") that the resume does not state.

    "three years" is fine if the resume says "three years" or "3 years".
    """
    new_phrases = []
    for match in NUMBER_WORD_WITH_UNIT.finditer(body):
        phrase = " ".join(match.group(0).split())
        word = match.group(1).lower()
        unit = match.group(3)
        as_digits = f"{NUMBER_WORDS[word]} {unit}"
        if appears_in(phrase, resume) or appears_in(as_digits, resume):
            continue
        if phrase.lower() not in [item.lower() for item in new_phrases]:
            new_phrases.append(phrase)
    return new_phrases


def is_tool_like(term: str, resume: str) -> bool:
    """True if a job-posting term names a specific skill or tool, not a general phrase.

    A single word ("Kubernetes", "dbt") counts as a tool. A longer phrase only
    counts if it contains a name or tech word that is not in the resume
    ("Apache Airflow"). Phrases like "batch data pipelines" are general wording.
    """
    words = term.split()
    if len(words) == 1:
        return True
    for word in words:
        if looks_like_a_name(word, at_sentence_start=False) and not appears_in(word, resume):
            return True
    return False


def find_new_skills(body: str, resume: str, analysis: JobAnalysis) -> list[str]:
    """Skills from the job posting that the body uses but the resume does not have."""
    job_terms = analysis.must_have_skills + analysis.nice_to_have_skills + analysis.ats_keywords
    new_skills = []
    for term in job_terms:
        term = term.strip()
        if not term or term.lower() in [skill.lower() for skill in new_skills]:
            continue
        if appears_in(term, body) and not appears_in(term, resume):
            new_skills.append(term)
    return new_skills


def looks_like_a_name(word: str, at_sentence_start: bool) -> bool:
    """True for words worth checking: tech-style tokens, or capitalized words mid-sentence."""
    rest = word[1:]
    is_tech_style = any(char.isupper() or char.isdigit() or char in "+#." for char in rest)
    is_capitalized = word[0].isupper()
    return is_tech_style or (is_capitalized and not at_sentence_start)


def find_new_names(body: str, resume: str) -> list[str]:
    """Proper nouns and tech terms (employers, tools, titles) not found in the resume."""
    new_names = []
    for line in body.splitlines():
        text = clean_line(line)
        for match in WORD_PATTERN.finditer(text):
            word = match.group().rstrip(".-")
            text_before = text[: match.start()].rstrip()
            at_sentence_start = text_before == "" or text_before[-1] in ".!?:"

            if len(word) < 2 or word.lower() in STOP_WORDS:
                continue
            if word.rstrip("+").lower() in NUMBER_WORDS:
                continue  # number words are checked by find_new_number_words
            if not looks_like_a_name(word, at_sentence_start):
                continue
            if appears_in(word, resume) or word in new_names:
                continue
            new_names.append(word)
    return new_names


def find_unverified_items(
    tailored_md: str, resume_md: str, analysis: JobAnalysis
) -> list[UnverifiedItem]:
    """List invented facts: numbers, tools, skills or names that are not in the original.

    These are hard failures. General job-posting phrases that are only reworded
    are not listed here; see `find_rewordings_to_review`.

    The "What I changed" and "Gaps to work on" sections are skipped, because
    they are supposed to mention skills the user does not have yet.
    """
    body = split_body(tailored_md)
    items = []

    for number in find_new_numbers(body, resume_md):
        items.append(UnverifiedItem(text=number, kind="number"))
    for phrase in find_new_number_words(body, resume_md):
        items.append(UnverifiedItem(text=phrase, kind="number"))

    already_flagged = set()
    for skill in find_new_skills(body, resume_md, analysis):
        if is_tool_like(skill, resume_md):
            items.append(UnverifiedItem(text=skill, kind="skill"))
            already_flagged.add(skill.lower())

    for name in find_new_names(body, resume_md):
        if name.lower() not in already_flagged:
            items.append(UnverifiedItem(text=name, kind="name"))
            already_flagged.add(name.lower())

    return items


def find_rewordings_to_review(tailored_md: str, resume_md: str, analysis: JobAnalysis) -> list[str]:
    """Job-posting phrases used in the tailored resume but not found word-for-word in the original.

    These are usually fair rewordings ("batch data pipelines" for "batch
    pipelines"), so they are a warning for the user to check, not a failure.
    """
    body = split_body(tailored_md)
    rewordings = []
    for phrase in find_new_skills(body, resume_md, analysis):
        if not is_tool_like(phrase, resume_md):
            rewordings.append(phrase)
    return rewordings


def normalize(text: str) -> str:
    """Collapse all whitespace to single spaces and drop surrounding quote marks."""
    return " ".join(text.split()).strip("\"'“”‘’ ")


def check_match_report(report: MatchReport, analysis: JobAnalysis, resume: str) -> list[str]:
    """Return a list of problems with the match report (an empty list means it is OK).

    This is the Matcher's guardrail: every proof line must really be in the
    resume, and every must-have skill must be in exactly one list.
    """
    problems = []
    flat_resume = normalize(resume)

    for item in report.strong_matches + report.weak_matches:
        if normalize(item.proof_line) not in flat_resume:
            problems.append(
                f'Proof line for "{item.requirement}" is not copied word-for-word '
                f'from the resume: "{item.proof_line}"'
            )

    for item in report.weak_matches:
        if not item.note.strip():
            problems.append(f'Weak match "{item.requirement}" needs a note explaining the connection.')

    placed = [item.requirement for item in report.strong_matches]
    placed += [item.requirement for item in report.weak_matches]
    placed += report.gaps
    placed_lower = [name.strip().lower() for name in placed]

    for skill in analysis.must_have_skills:
        count = placed_lower.count(skill.strip().lower())
        if count != 1:
            problems.append(
                f'Must-have skill "{skill}" must appear in exactly one of strong_matches, '
                f"weak_matches or gaps (found {count} times)."
            )

    if len(report.top_improvements) != 3:
        problems.append(
            f"top_improvements must have exactly 3 items (found {len(report.top_improvements)})."
        )

    for improvement in report.top_improvements:
        problems.extend(check_improvement(improvement, analysis, resume))

    return problems


def check_improvement(improvement: str, analysis: JobAnalysis, resume: str) -> list[str]:
    """Problems with one suggested improvement (an empty list means it is OK).

    An improvement may not contain a concrete number, tool or company name that
    is not in the resume. Details the candidate might have must be written as
    placeholders like [X]% or [tool], together with "only if true". Names from
    the job posting are allowed, because "learn Docker" is an honest suggestion.
    """
    problems = []
    without_placeholders = PLACEHOLDER.sub(" ", improvement)

    job_terms = [analysis.title] + analysis.must_have_skills + analysis.nice_to_have_skills
    job_terms += analysis.ats_keywords + analysis.responsibilities
    known_text = resume + "\n" + "\n".join(job_terms)

    new_numbers = find_new_numbers(without_placeholders, resume)
    new_numbers += find_new_number_words(without_placeholders, resume)
    new_names = find_new_names(without_placeholders, known_text)

    if new_numbers or new_names:
        made_up = ", ".join(new_numbers + new_names)
        problems.append(
            f'Improvement "{improvement}" contains details that are not in the resume '
            f"({made_up}). Use placeholders like [X]% or [tool] and add \"only if true\"."
        )

    if PLACEHOLDER.search(improvement) and "only if true" not in improvement.lower():
        problems.append(
            f'Improvement "{improvement}" uses a placeholder, so it must also say "only if true".'
        )

    return problems
