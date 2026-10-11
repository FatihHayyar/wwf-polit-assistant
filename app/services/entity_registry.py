"""Parliamentary datasets exposed by the monitoring application."""
from dataclasses import dataclass

from app.models.entities import Agenda, Affair, Document, Event, Meeting, ParliamentaryText, Voting, PoliticalGroup, Interest


@dataclass(frozen=True)
class EntitySpec:
    model: type
    date_field: str
    title_fields: tuple[str, ...]


ENTITIES = {
    "affairs": EntitySpec(Affair, "begin_date", ("title_de", "title_fr", "title_it", "number")),
    "agendas": EntitySpec(Agenda, "item_date", ("item_title", "item_description", "item_affair_number")),
    "meetings": EntitySpec(Meeting, "begin_date", ("name_de", "name_fr", "name_it", "description_de", "location")),
    "votings": EntitySpec(Voting, "date", ("title_de", "title_fr", "title_it", "decision")),
    "events": EntitySpec(Event, "date", ("title_de", "title_fr", "title_it", "details_text")),
    "documents": EntitySpec(Document, "date", ("name", "text")),
    "texts": EntitySpec(ParliamentaryText, "text_date", ("text_de", "text_fr", "text_it")),
    "groups": EntitySpec(PoliticalGroup, "updated_at", ("name_de", "name_fr", "name_it", "abbreviation_de", "abbreviation_fr", "abbreviation_it")),
    "interests": EntitySpec(Interest, "begin_date", ("name_de", "name_fr", "name_it", "declaration_doc_title", "role_name_de", "role_name_fr", "role_name_it")),
}

PRIMARY_DATASETS = ("affairs", "meetings", "groups", "interests")
