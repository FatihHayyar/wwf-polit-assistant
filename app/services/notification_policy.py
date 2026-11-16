"""Explicit, deterministic notification rules; data persistence is independent."""
import html
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from difflib import SequenceMatcher

VERSION = "meaningful-v4"

# Records describing a dated occurrence (an event, a vote, a session ...) are
# news only while that date is recent. New or corrected records dated further
# back are backfills or editorial clean-ups of the source, not news.
STALE_AFTER = timedelta(days=30)
DATED = {"agendas", "meetings", "votings", "events", "documents", "texts", "interests"}
ISO_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:?\d{2}|Z)?$")
LANGUAGE_FIELD = re.compile(r"^(.+)_(de|fr|it|rm|en)$")
LANGUAGES = ("de", "fr", "it", "rm", "en")
# Sentence punctuation alone does not change a statement; signs such as "-" do.
SENTENCE_PUNCTUATION = set(".,:;!?…")


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


def as_datetime(value):
    """Datetime at second precision, or None; ISO strings come from stored change records."""
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str) and ISO_DATETIME.match(value.strip()):
        try:
            result = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if result.tzinfo is not None:
        result = result.astimezone(timezone.utc).replace(tzinfo=None)
    return result.replace(microsecond=0)


MOJIBAKE = re.compile(r"[ÃÂâ][\u0080-¿‘-›€ŒœŠšŸŽžƒˆ˜]")


def repaired(value):
    """Undo UTF-8 text that was decoded as Latin-1/Windows-1252 («SekretÃ¤r» -> «Sekretär»).

    The source sometimes delivers such broken characters and fixes them later;
    the fix is not a content change.
    """
    if not MOJIBAKE.search(value):
        return value
    for encoding in ("cp1252", "latin-1"):
        try:
            return value.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return value


def comparable(value):
    if value is None:
        return ""
    moment = as_datetime(value)
    if moment is not None:
        return moment
    if isinstance(value, str):
        parser = VisibleText()
        parser.feed(value)
        value = unicodedata.normalize("NFKC", repaired(html.unescape("".join(parser.parts))))
        value = value.translate(str.maketrans({"\u2019": "'", "\u2018": "'", "\u201c": '"',
                                              "\u201d": '"', "\u00ad": "", "\u200b": ""}))
        # Ignore spacing around punctuation but preserve numbers, signs and words.
        return " ".join(re.findall(r"\w+|[^\w\s]", value))
    return value


def folded(value):
    """Case- and accent-insensitive form: «Conseil des Etats» equals «Conseil des États»."""
    if not isinstance(value, str):
        return value
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def stale(dataset, record, reference=None):
    """True when a dated record lies clearly before the time the change was detected."""
    from app.services.entity_registry import ENTITIES
    if dataset not in DATED or record is None:
        return False
    moment = as_datetime(getattr(record, ENTITIES[dataset].date_field, None))
    if moment is None:
        return False
    reference = as_datetime(reference or datetime.now(timezone.utc))
    return moment < reference - STALE_AFTER


def translation_only(field, change, changes, record):
    """True when only the translation of a language field changed, not its content.

    Two cases:
    - The field held (or now holds) a copy of another language: «state_name_it»
      changes from the French «Liquidé» to «Liquidato».
    - A French, Italian, ... version changes while another version exists and
      stayed the same: «state_name_it» becomes «Il parere sull'intervento è
      disponibile» while the German «Stellungnahme zum Vorstoss liegt vor» is
      unchanged. A real change (a new state, a new text) changes every
      language version that exists.
    """
    match = LANGUAGE_FIELD.match(field)
    if not match:
        return False
    base, language = match.groups()
    values = {folded(comparable(change.get("before"))), folded(comparable(change.get("after")))} - {""}
    for other in LANGUAGES:
        sibling = f"{base}_{other}"
        if other == language:
            continue
        if sibling in changes:
            candidates = [changes[sibling].get("before"), changes[sibling].get("after")]
        elif record is not None:
            current = getattr(record, sibling, None)
            if language != "de" and comparable(current) != "":
                # Another language version exists and did not change. German is
                # WWF's primary language, so a German-only change stays news.
                return True
            candidates = [current]
        else:
            candidates = []
        if any(folded(comparable(candidate)) in values for candidate in candidates if comparable(candidate) != ""):
            return True
    return False


def meaningful_fields(dataset, fields):
    return [field for field in fields if field in RULES.get(dataset, set())
            or (field.startswith(PREFIXES.get(dataset, ())) and not field.startswith(("title_harmonized", "state_name_harmonized")))]


def eligible(dataset, change_type, description=None, changes=None, record=None, reference=None):
    """Decide whether a change is news for subscribers.

    ``record`` is the stored record after the change and ``reference`` the
    detection time; both are optional and enable the record-aware rules.
    """
    if change_type == "ignored":
        return False
    if stale(dataset, record, reference):
        return False
    if change_type == "created":
        return dataset in RULES
    if changes is not None:
        return any(substantive(changes[field].get("before"), changes[field].get("after"))
                   and not translation_only(field, changes[field], changes, record)
                   for field in meaningful_fields(dataset, changes))
    # Legacy events lack old/new values: field-level rules are possible, but
    # formatting-only differences cannot be reconstructed retrospectively.
    if description and description.startswith("Changed fields: "):
        # Historical records lack evidence of actual content change; suppress them.
        return False
    return False


def substantive(before, after):
    raw_before, raw_after = before, after
    before, after = comparable(before), comparable(after)
    if before == after:
        return False
    if isinstance(before, datetime) and isinstance(after, datetime):
        # A plain date gains its time of day (00:00 -> 08:26) on the same day.
        midnight = before.time().isoformat() == "00:00:00" or after.time().isoformat() == "00:00:00"
        return not (midnight and before.date() == after.date())
    if (raw_before is None and raw_after is False) or (raw_after is None and raw_before is False):
        return False  # «unknown» becomes «no» (or vice versa): no new information.
    if not isinstance(before, str) or not isinstance(after, str):
        return True
    if folded(before) == folded(after):
        return False
    old, new = folded(before).split(), folded(after).split()
    differences = [op for op in SequenceMatcher(None, old, new, autojunk=False).get_opcodes() if op[0] != 'equal']
    if differences and all(set("".join(old[a:b] + new[c:d])) <= SENTENCE_PUNCTUATION for _, a, b, c, d in differences):
        return False
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


def event_record(event):
    """The stored record a change event refers to, when the event is attached to a session."""
    from sqlalchemy.orm import object_session
    from app.services.entity_registry import ENTITIES
    session = object_session(event)
    spec = ENTITIES.get(event.dataset)
    if session is None or spec is None or event.source_id is None:
        return None
    return session.get(spec.model, event.source_id)


def event_eligible(event, record=None):
    record = record if record is not None else event_record(event)
    return eligible(event.dataset, event.change_type, event.description, event.changes,
                    record=record, reference=event.detected_at)


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
