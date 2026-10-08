from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    table: str
    source_key: str = "id"
    database_key: str = "id"
    requires_special_handling: bool = False


DATASETS = (
    DatasetConfig("bodies", "bodies"),
    DatasetConfig("persons", "persons"),
    DatasetConfig("memberships", "memberships"),
    DatasetConfig("groups", "groups"),
    DatasetConfig("interests", "interests"),
    DatasetConfig("affairs", "affairs"),
    DatasetConfig("meetings", "meetings"),
    DatasetConfig("agendas", "agendas"),
    DatasetConfig("events", "events"),
    DatasetConfig("votings", "votings"),
    DatasetConfig(
        "docs",
        "documents",
        source_key="id",
        database_key="source_id",
        requires_special_handling=True,
    ),
    DatasetConfig("texts", "texts"),
)


DATASETS_BY_NAME = {
    dataset.name: dataset
    for dataset in DATASETS
}
