"""Turn a question in natural language into search filters.

The rule-based interpreter recognises datasets, WWF topics (through the same
rules as the classifier), cantons, affair types, time ranges and quoted
phrases in German, French, Italian and English. It always reports what it
recognised, so users can check and correct the filters.

``QueryInterpreter`` is the extension point for a later AI component: an
LLM-based interpreter only needs to return the same ``Interpretation``.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.classification.classifier import AffairClassifier, normalize_text
from app.models.classification import ClassificationCategory
from app.services.canton_service import CANTON_NAMES

DATASET_WORDS = {
    "agendas": ["traktand", "tagesordnung", "ordre du jour", "ordine del giorno", "agenda item"],
    "meetings": ["sitzung", "session", "séance", "sedut", "sessione", "meeting"],
    "votings": ["abstimmung", "vote", "votation", "votazione", "voting"],
    "documents": ["dokument", "document", "documento", "bericht", "rapport", "rapporto", "report"],
    "events": ["ereignis", "événement", "evento", "event"],
    "texts": ["vorstosstext", "texte", "testo"],
    "groups": ["kommission", "fraktion", "commission", "commissione", "gruppo", "committee", "parlamentarische gruppe"],
    "interests": ["interessenbindung", "intérêt", "interesse", "interest"],
    "affairs": ["geschäft", "vorstoss", "vorstösse", "objet", "oggetto", "affair", "motion", "postulat", "interpellation",
                "anfrage", "initiative", "mozione", "interpellanza"],
}

CANTON_ALIASES = {
    "AG": ["aargau", "argovie", "argovia"], "AI": ["appenzell innerrhoden", "appenzell rhodes-intérieures"],
    "AR": ["appenzell ausserrhoden", "appenzell rhodes-extérieures"], "BE": ["bern", "berne", "berna"],
    "BL": ["basel-landschaft", "baselland", "bâle-campagne", "basilea campagna"],
    "BS": ["basel-stadt", "basel stadt", "bâle-ville", "basilea città"], "FR": ["freiburg", "fribourg", "friburgo"],
    "GE": ["genf", "genève", "geneve", "ginevra", "geneva"], "GL": ["glarus", "glaris", "glarona"],
    "GR": ["graubünden", "graubunden", "grisons", "grigioni"], "JU": ["jura", "giura"],
    "LU": ["luzern", "lucerne", "lucerna"], "NE": ["neuenburg", "neuchâtel", "neuchatel"],
    "NW": ["nidwalden", "nidwald", "nidvaldo"], "OW": ["obwalden", "obwald", "obvaldo"],
    "SG": ["st. gallen", "st.gallen", "sankt gallen", "saint-gall", "san gallo"],
    "SH": ["schaffhausen", "schaffhouse", "sciaffusa"], "SO": ["solothurn", "soleure", "soletta"],
    "SZ": ["schwyz", "schwytz", "svitto"], "TG": ["thurgau", "thurgovie", "turgovia"],
    "TI": ["tessin", "ticino"], "UR": ["uri"], "VD": ["waadt", "vaud"],
    "VS": ["wallis", "valais", "vallese"], "ZG": ["zug", "zoug", "zugo"], "ZH": ["zürich", "zurich", "zurigo"],
}

# Affair types are stored with their German name; these are the translations
# that the German name plus an ending does not already cover.
AFFAIR_TYPE_ALIASES = {
    "Motion": ["mozione", "mozioni"],
    "Postulat": ["postulato", "postulati"],
    "Interpellation": ["interpellanza", "interpellanze"],
    "Anfrage": ["interrogazione", "interrogazioni"],
}

# Where a canton is named, "Kanton" is the place and not the public sector as a topic.
CANTON_WORD = re.compile(r"(?<!\w)(?:kanton(?:s|e|en)?|canton(?:s|e|i)?)(?!\w)", re.IGNORECASE)

TOPIC_WORDS = {
    "climate_energy": ["klima", "energie", "climat", "énergie", "clima", "energia", "climate", "energy"],
    "biodiversity_landscape": ["biodiversität", "natur", "landschaft", "biodiversité", "nature", "paysage", "biodiversità",
                               "natura", "paesaggio", "biodiversity", "landscape"],
    "sustainable_economy_consumption": ["nachhaltige wirtschaft", "konsum", "économie durable", "consommation",
                                        "economia sostenibile", "consumo", "sustainable economy", "consumption"],
    "environment_policy": ["umwelt", "umweltpolitik", "environnement", "ambiente", "environment"],
}

SINCE = r"(?:seit|ab|depuis|dès|dal|dall'|da|since|from)"
UPCOMING = ["bevorstehend", "kommend", "nächste", "prochain", "à venir", "prossim", "imminent", "upcoming", "next"]
RELATIVE_PERIODS = [
    (r"(?:letzte[nm]?|vergangene[nm]?|derniers?|dernières?|ultim[ie]|past|last)\s+(\d{1,3})\s*(?:tage[n]?|jours?|giorni|days?)", "days"),
    (r"(?:letzte[nm]?|vergangene[nm]?|derniers?|ultim[ie]|past|last)\s+(\d{1,2})\s*(?:monate[n]?|mois|mesi|months?)", "months"),
    (r"(?:letzte[nm]?|vergangene[nm]?|derniers?|ultim[ie]|past|last)\s+(\d{1,2})\s*(?:jahre[n]?|ans|anni|years?)", "years"),
]
THIS_YEAR = ["dieses jahr", "diesem jahr", "cette année", "quest'anno", "questo anno", "this year"]
LAST_YEAR = ["letztes jahr", "letzten jahr", "vorjahr", "l'année dernière", "l'an dernier", "l'anno scorso", "last year"]
LAST_MONTH = ["letzten monat", "letzter monat", "le mois dernier", "il mese scorso", "last month"]
# Month names as matched in folded text (lower case, without accents).
MONTH_NAMES = {
    1: ["januar", "janner", "janvier", "gennaio", "january"], 2: ["februar", "fevrier", "febbraio", "february"],
    3: ["marz", "maerz", "mars", "marzo", "march"], 4: ["april", "avril", "aprile"], 5: ["mai", "maggio", "may"],
    6: ["juni", "juin", "giugno", "june"], 7: ["juli", "juillet", "luglio", "july"], 8: ["august", "aout", "agosto"],
    9: ["september", "septembre", "settembre"], 10: ["oktober", "octobre", "ottobre", "october"],
    11: ["november", "novembre"], 12: ["dezember", "decembre", "dicembre", "december"],
}
MONTHS = {name: number for number, names in MONTH_NAMES.items() for name in names}
MONTH = "(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + ")"
# A month without a year only after a preposition, so "may" or "august" alone stay words.
IN_MONTH = rf"(?<!\w)(?:im|in|en|a|nel|au mois de|nel mese di)\s+{MONTH}(?!\w)"


def month_end(year: int, month: int) -> date:
    return date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)


@dataclass
class Recognised:
    kind: str
    value: str
    text: str


@dataclass
class Interpretation:
    dataset: str = "affairs"
    category: str | None = None
    subcategory: str | None = None
    canton: str | None = None
    affair_type: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    q: str | None = None
    recognised: list[Recognised] = field(default_factory=list)

    def filters(self) -> dict:
        values = asdict(self)
        values.pop("recognised")
        values.pop("dataset")
        return {key: value for key, value in values.items() if value is not None}


class QueryInterpreter(Protocol):
    def interpret(self, db: Session, question: str, affair_types: list[str], today: date) -> Interpretation: ...


def fold(value: str) -> str:
    """Lower-case and strip accents for robust word matching."""
    return "".join(char for char in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(char))


def find_word(haystack: str, needle: str) -> re.Match | None:
    return re.search(rf"(?<!\w){re.escape(fold(needle))}\w*" if len(needle) >= 5 else rf"(?<!\w){re.escape(fold(needle))}(?!\w)", haystack)


class RuleBasedInterpreter:
    def interpret(self, db: Session, question: str, affair_types: list[str], today: date) -> Interpretation:
        result = Interpretation()
        folded = fold(question)
        quoted = re.findall(r"[\"«“„']([^\"»”“']{2,80})[\"»”“']", question)
        if quoted:
            result.q = quoted[0].strip()
            result.recognised.append(Recognised("keyword", result.q, quoted[0]))

        self._dataset(result, folded)
        self._affair_type(result, question, affair_types)
        self._canton(result, question, folded)
        self._dates(result, folded, today)
        self._topic(result, db, question, folded)
        return result

    def _dataset(self, result, folded):
        for dataset, words in DATASET_WORDS.items():
            for word in words:
                match = find_word(folded, word)
                if match:
                    result.dataset = dataset
                    result.recognised.append(Recognised("dataset", dataset, match.group()))
                    return

    def _affair_type(self, result, question, affair_types):
        folded = fold(question)
        for affair_type in sorted(affair_types, key=len, reverse=True):
            name = fold(affair_type)
            if len(name) >= 4 and re.search(rf"(?<!\w){re.escape(name)}(?:en|e|s|i)?(?!\w)", folded):
                result.affair_type = affair_type
                result.dataset = "affairs"
                result.recognised.append(Recognised("affair_type", affair_type, affair_type))
                return
        for affair_type, aliases in AFFAIR_TYPE_ALIASES.items():
            match = affair_type in affair_types and next(
                (match for alias in aliases if (match := re.search(rf"(?<!\w){alias}(?!\w)", folded))), None)
            if match:
                result.affair_type = affair_type
                result.dataset = "affairs"
                result.recognised.append(Recognised("affair_type", affair_type, match.group()))
                return

    def _canton(self, result, question, folded):
        for code, aliases in CANTON_ALIASES.items():
            for alias in sorted(aliases, key=len, reverse=True):
                match = re.search(rf"(?<!\w){re.escape(fold(alias))}(?!\w)", folded)
                if match:
                    result.canton = code
                    result.recognised.append(Recognised("canton", code, match.group()))
                    return
        # Two-letter codes only when written in capitals, e.g. "BE" (not "so").
        for match in re.finditer(r"(?<![\w.])([A-Z]{2})(?![\w.])", question):
            if match.group(1) in CANTON_NAMES:
                result.canton = match.group(1)
                result.recognised.append(Recognised("canton", match.group(1), match.group(1)))
                return

    def _dates(self, result, folded, today):
        between = re.search(r"(?:zwischen|entre|tra|between)\s+((?:19|20)\d{2})\s+(?:und|et|e|and)\s+((?:19|20)\d{2})", folded)
        since = re.search(rf"{SINCE}\s+(?:{MONTH}\s+)?((?:19|20)\d{{2}})", folded)
        in_month = re.search(rf"(?<!\w){MONTH}\s+((?:19|20)\d{{2}})(?!\d)", folded)
        if between:
            start, end = sorted((int(between.group(1)), int(between.group(2))))
            result.date_from, result.date_to = date(start, 1, 1), date(end, 12, 31)
            result.recognised.append(Recognised("period", f"{start}-{end}", between.group()))
            return
        if since:
            year, month = int(since.group(2)), MONTHS.get(since.group(1), 1)
            result.date_from = date(year, month, 1)
            result.recognised.append(Recognised("period", f"since {year}-{month:02d}", since.group()))
            return
        if in_month:
            year, month = int(in_month.group(2)), MONTHS[in_month.group(1)]
            result.date_from, result.date_to = date(year, month, 1), month_end(year, month)
            result.recognised.append(Recognised("period", f"{year}-{month:02d}", in_month.group()))
            return
        for pattern, unit in RELATIVE_PERIODS:
            match = re.search(pattern, folded)
            if match:
                amount = int(match.group(1))
                days = amount if unit == "days" else amount * 30 if unit == "months" else amount * 365
                result.date_from = today - timedelta(days=days)
                result.recognised.append(Recognised("period", f"last {amount} {unit}", match.group()))
                return
        for phrases, start, end, label in (
            (THIS_YEAR, date(today.year, 1, 1), None, "this year"),
            (LAST_YEAR, date(today.year - 1, 1, 1), date(today.year - 1, 12, 31), "last year"),
            (LAST_MONTH, (today.replace(day=1) - timedelta(days=1)).replace(day=1), today.replace(day=1) - timedelta(days=1), "last month"),
        ):
            phrase = next((phrase for phrase in phrases if fold(phrase) in folded), None)
            if phrase:
                result.date_from, result.date_to = start, end
                result.recognised.append(Recognised("period", label, phrase))
                return
        if any(fold(word) in folded for word in UPCOMING):
            result.date_from = today
            result.recognised.append(Recognised("period", "upcoming", "upcoming"))
            return
        named = re.search(IN_MONTH, folded)
        if named:
            # The most recent such month, including the current one.
            month = MONTHS[named.group(1)]
            year = today.year if month <= today.month else today.year - 1
            result.date_from, result.date_to = date(year, month, 1), month_end(year, month)
            result.recognised.append(Recognised("period", f"{year}-{month:02d}", named.group()))
            return
        year = re.search(r"(?<!\d)((?:19|20)\d{2})(?!\d)", folded)
        if year:
            value = int(year.group(1))
            result.date_from, result.date_to = date(value, 1, 1), date(value, 12, 31)
            result.recognised.append(Recognised("period", str(value), year.group(1)))

    def _topic(self, result, db, question, folded):
        categories = {category.id: category for category in db.scalars(
            select(ClassificationCategory).where(ClassificationCategory.active.is_(True)))}
        if result.canton:
            question = CANTON_WORD.sub(" ", question)
        probe = SimpleNamespace(id=0, title_de=question, title_fr=question, title_it=question, title_rm=None,
                                title_long_de=None, title_long_fr=None, title_long_it=None, title_long_rm=None)
        matches = [match for match in AffairClassifier(db).accepted_title_matches(probe)
                   if not categories[match.category_id].is_fallback or categories[match.category_id].parent_id]
        leaves = [categories[match.category_id] for match in matches]
        mains = {leaf.parent_id for leaf in leaves if leaf.parent_id}
        if len(mains) == 1:
            main = categories[mains.pop()]
            result.category = main.code
            specific = [leaf for leaf in leaves if not leaf.is_fallback]
            if len(specific) == 1:
                result.subcategory = specific[0].code
                terms = sorted({term for match in matches for term in match.matched_terms}, key=len, reverse=True)
                result.recognised.append(Recognised("subcategory", specific[0].code, terms[0] if terms else specific[0].name_de))
            else:
                result.recognised.append(Recognised("category", main.code, main.name_de))
            return
        if not mains:
            for code, words in TOPIC_WORDS.items():
                word = next((word for word in words if find_word(folded, word)), None)
                if word:
                    result.category = code
                    result.recognised.append(Recognised("category", code, word))
                    return
        if not result.q:
            # No topic: fall back to the most specific remaining word. Words
            # already recognised as canton, dataset or period are not repeated.
            used = " ".join(fold(item.text) for item in result.recognised)
            words = [word for word in re.findall(r"\w{5,}", normalize_text(question))
                     if fold(word) not in used and not any(word.startswith(fold(item)) for item in STOP_PREFIXES)]
            if words:
                result.q = max(words, key=len)
                result.recognised.append(Recognised("keyword", result.q, result.q))


STOP_PREFIXES = [
    "welche", "geschäft", "vorst", "gibt", "zeige", "suche", "finde", "kanton", "seit", "letzte", "dieses", "jahr", "monat",
    "quels", "quelles", "objet", "canton", "depuis", "derni", "année", "montre", "cherche", "quali", "oggett", "cantone",
    "ultim", "mostra", "cerca", "which", "affair", "show", "find", "since", "about", "zum", "thema", "sujet", "tema",
    "sitzung", "séance", "sedut", "abstimm", "votation", "votazion", "dokument", "document", "traktand", "parlament",
    "grossen", "grand", "consiglio", "conseil", "kommission", "commission", "bevorsteh", "kommend", "prochain", "prossim",
]


def get_interpreter() -> QueryInterpreter:
    """The configured interpreter; currently the rule-based implementation."""
    return RuleBasedInterpreter()
