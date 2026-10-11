"""Explicit, deterministic notification rules; data persistence is independent."""
import html
import re
import unicodedata
from html.parser import HTMLParser
from difflib import SequenceMatcher

VERSION = "meaningful-v3"


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "td", "th"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        self.handle_starttag(tag, [])
RULES = {
    "affairs": {"active"},
    "agendas": {"item_status", "item_result", "item_date"},
    "meetings": {"begin_date", "end_date", "state", "location"},
    "votings": {"date", "decision", "results_yes", "results_no", "results_abstention", "results_absent", "results_string",
                "meaning_of_yes_de", "meaning_of_yes_fr", "meaning_of_yes_it", "meaning_of_no_de", "meaning_of_no_fr", "meaning_of_no_it"},
    "events": {"date", "details_text"},
    "documents": {"text"},
    "texts": {"text_de", "text_fr", "text_it", "text_rm"},
    "groups": {"begin_date", "end_date", "active"},
    "interests": {"person_id", "begin_date", "end_date", "ex_officio"},
}
PREFIXES = {
    "affairs": ("state_name_",),
    "events": ("title_",),
    "interests": ("role_name_",),
}


def comparable(value):
    if value is None:
        return ""
    if isinstance(value, str):
        parser = VisibleText()
        parser.feed(value)
        value = unicodedata.normalize("NFKC", html.unescape("".join(parser.parts)))
        value = value.translate(str.maketrans({"\u2019": "'", "\u2018": "'", "\u201c": '"',
                                              "\u201d": '"', "\u00ad": "", "\u200b": ""}))
        # Ignore spacing around punctuation but preserve numbers, signs and words.
        return " ".join(re.findall(r"\w+|[^\w\s]", value))
    return value


def meaningful_fields(dataset, fields):
    return [field for field in fields if field in RULES.get(dataset, set())
            or (field.startswith(PREFIXES.get(dataset, ())) and not field.startswith(("title_harmonized", "state_name_harmonized")))]


def eligible(dataset, change_type, description=None, changes=None):
    if change_type == "ignored":
        return False
    if change_type == "created":
        return dataset in RULES
    if changes is not None:
        return any(substantive(changes[field].get("before"), changes[field].get("after"))
                   for field in meaningful_fields(dataset, changes))
    # Legacy events lack old/new values: field-level rules are possible, but
    # formatting-only differences cannot be reconstructed retrospectively.
    if description and description.startswith("Changed fields: "):
        # Historical records lack evidence of actual content change; suppress them.
        return False
    return False


def substantive(before, after):
    before, after = comparable(before), comparable(after)
    if before == after:
        return False
    if not isinstance(before, str) or not isinstance(after, str):
        return True
    if before.casefold() == after.casefold():
        return False
    old, new = before.split(), after.split()
    differences = [op for op in SequenceMatcher(None, old, new, autojunk=False).get_opcodes() if op[0] != 'equal']
    # Suppress only isolated one-character corrections in long alphabetic words.
    # Numbers, negation, inserted/deleted words and larger replacements stay eligible.
    if len(differences) == 1:
        kind, a, b, c, d = differences[0]
        if kind == 'replace' and b-a == d-c == 1:
            left, right = old[a], new[c]
            if left.isalpha() and right.isalpha() and min(len(left), len(right)) >= 6:
                edits = [op for op in SequenceMatcher(None, left, right, autojunk=False).get_opcodes() if op[0] != 'equal']
                if len(edits) == 1 and max(edits[0][2]-edits[0][1], edits[0][4]-edits[0][3]) == 1:
                    return False
    return True


def event_eligible(event):
    return eligible(event.dataset, event.change_type, event.description, event.changes)


def summary(event):
    labels = {"item_result": "Result", "item_status": "Status", "item_date": "Date",
              "item_title": "Title", "item_description": "Description", "date": "Date",
              "text_date": "Date", "begin_date": "Start", "end_date": "End",
              "results_yes": "Yes", "results_no": "No", "results_abstention": "Abstentions",
              "results_absent": "Absent", "decision": "Decision", "location": "Location",
              "state": "Status", "active": "Active", "meeting_id": "Meeting", "hash": "Document content"}
    fields = meaningful_fields(event.dataset, event.changes or [])
    if not event.changes and event.description and event.description.startswith("Changed fields: "):
        fields = meaningful_fields(event.dataset, [part.strip() for part in event.description[16:].split(",")])
    lines = []
    for field in fields[:4]:
        label = labels.get(field, re.sub(r"_(de|fr|it|rm|en)$", "", field).replace("_", " ").capitalize())
        if event.changes:
            before, after = comparable(event.changes[field]["before"]), comparable(event.changes[field]["after"])
            if before == after:
                continue
            lines.append(f"{label}: {str(before)[:120]} → {str(after)[:120]}")
        else:
            lines.append(f"Changed: {label}")
    return "\n".join(lines)
