from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Body(Base):
    __tablename__ = "bodies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    body_key: Mapped[str | None] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(Text)
    name_de: Mapped[str | None] = mapped_column(Text)
    name_fr: Mapped[str | None] = mapped_column(Text)
    name_it: Mapped[str | None] = mapped_column(Text)
    name_en: Mapped[str | None] = mapped_column(Text)
    lang: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str | None] = mapped_column(Text)
    canton_key: Mapped[str | None] = mapped_column(Text)
    country_key: Mapped[str | None] = mapped_column(Text)
    has_parliament: Mapped[bool | None] = mapped_column(Boolean)
    population: Mapped[int | None] = mapped_column(BigInteger)


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    body_id: Mapped[int | None] = mapped_column(BigInteger)
    body_key: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    fullname: Mapped[str | None] = mapped_column(Text)
    firstname: Mapped[str | None] = mapped_column(Text)
    lastname: Mapped[str | None] = mapped_column(Text)
    party_de: Mapped[str | None] = mapped_column(Text)
    party_fr: Mapped[str | None] = mapped_column(Text)
    party_it: Mapped[str | None] = mapped_column(Text)
    party_harmonized_de: Mapped[str | None] = mapped_column(Text)
    party_harmonized_fr: Mapped[str | None] = mapped_column(Text)
    party_harmonized_it: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    gender: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool | None] = mapped_column(Boolean)
    language: Mapped[str | None] = mapped_column(Text)
    wikidata_id: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class PoliticalGroup(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    body_id: Mapped[int | None] = mapped_column(BigInteger)
    body_key: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    type_harmonized: Mapped[str | None] = mapped_column(Text)
    type_harmonized_de: Mapped[str | None] = mapped_column(Text)
    type_harmonized_fr: Mapped[str | None] = mapped_column(Text)
    type_harmonized_it: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool | None] = mapped_column(Boolean)
    name_de: Mapped[str | None] = mapped_column(Text)
    name_fr: Mapped[str | None] = mapped_column(Text)
    name_it: Mapped[str | None] = mapped_column(Text)
    abbreviation_de: Mapped[str | None] = mapped_column(Text)
    abbreviation_fr: Mapped[str | None] = mapped_column(Text)
    abbreviation_it: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    body_id: Mapped[int | None] = mapped_column(BigInteger)
    body_key: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    person_id: Mapped[int | None] = mapped_column(BigInteger)
    person_fullname: Mapped[str | None] = mapped_column(Text)
    group_id: Mapped[int | None] = mapped_column(BigInteger)
    group_name_de: Mapped[str | None] = mapped_column(Text)
    group_name_fr: Mapped[str | None] = mapped_column(Text)
    group_name_it: Mapped[str | None] = mapped_column(Text)
    role_name_de: Mapped[str | None] = mapped_column(Text)
    role_name_fr: Mapped[str | None] = mapped_column(Text)
    role_name_it: Mapped[str | None] = mapped_column(Text)
    begin_date: Mapped[datetime | None] = mapped_column(DateTime)
    end_date: Mapped[datetime | None] = mapped_column(DateTime)
    active: Mapped[bool | None] = mapped_column(Boolean)
    type_harmonized: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    body_id: Mapped[int | None] = mapped_column(BigInteger)
    body_key: Mapped[str | None] = mapped_column(Text)
    person_id: Mapped[int | None] = mapped_column(BigInteger)
    external_id: Mapped[str | None] = mapped_column(Text)
    type_de: Mapped[str | None] = mapped_column(Text)
    type_fr: Mapped[str | None] = mapped_column(Text)
    type_it: Mapped[str | None] = mapped_column(Text)
    name_de: Mapped[str | None] = mapped_column(Text)
    name_fr: Mapped[str | None] = mapped_column(Text)
    name_it: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    role_name_de: Mapped[str | None] = mapped_column(Text)
    role_name_fr: Mapped[str | None] = mapped_column(Text)
    role_name_it: Mapped[str | None] = mapped_column(Text)
    begin_date: Mapped[datetime | None] = mapped_column(DateTime)
    end_date: Mapped[datetime | None] = mapped_column(DateTime)
    declaration_doc_url: Mapped[str | None] = mapped_column(Text)
    declaration_doc_title: Mapped[str | None] = mapped_column(Text)
    place: Mapped[str | None] = mapped_column(Text)
    ex_officio: Mapped[bool | None] = mapped_column(Boolean)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Affair(Base):
    __tablename__ = "affairs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    body_id: Mapped[int | None] = mapped_column(BigInteger)
    body_key: Mapped[str | None] = mapped_column(Text)
    number: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    external_alternative_id: Mapped[str | None] = mapped_column(Text)

    title_de: Mapped[str | None] = mapped_column(Text)
    title_fr: Mapped[str | None] = mapped_column(Text)
    title_it: Mapped[str | None] = mapped_column(Text)
    title_rm: Mapped[str | None] = mapped_column(Text)

    title_long_de: Mapped[str | None] = mapped_column(Text)
    title_long_fr: Mapped[str | None] = mapped_column(Text)
    title_long_it: Mapped[str | None] = mapped_column(Text)
    title_long_rm: Mapped[str | None] = mapped_column(Text)

    type_name_de: Mapped[str | None] = mapped_column(Text)
    type_name_fr: Mapped[str | None] = mapped_column(Text)
    type_name_it: Mapped[str | None] = mapped_column(Text)

    type_harmonized_de: Mapped[str | None] = mapped_column(Text)
    type_harmonized_fr: Mapped[str | None] = mapped_column(Text)
    type_harmonized_it: Mapped[str | None] = mapped_column(Text)
    type_harmonized_en: Mapped[str | None] = mapped_column(Text)

    state_name_de: Mapped[str | None] = mapped_column(Text)
    state_name_fr: Mapped[str | None] = mapped_column(Text)
    state_name_it: Mapped[str | None] = mapped_column(Text)

    state_name_harmonized_de: Mapped[str | None] = mapped_column(Text)
    state_name_harmonized_fr: Mapped[str | None] = mapped_column(Text)
    state_name_harmonized_it: Mapped[str | None] = mapped_column(Text)

    begin_date: Mapped[datetime | None] = mapped_column(DateTime)
    end_date: Mapped[datetime | None] = mapped_column(DateTime)
    active: Mapped[bool | None] = mapped_column(Boolean)

    url_external_de: Mapped[str | None] = mapped_column(Text)
    url_external_fr: Mapped[str | None] = mapped_column(Text)
    url_external_it: Mapped[str | None] = mapped_column(Text)

    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    body_id: Mapped[int | None] = mapped_column(BigInteger)
    body_key: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str | None] = mapped_column(Text)
    parent_type: Mapped[str | None] = mapped_column(Text)
    parent_external_id: Mapped[str | None] = mapped_column(Text)
    number: Mapped[str | None] = mapped_column(Text)
    abbreviation: Mapped[str | None] = mapped_column(Text)

    name_de: Mapped[str | None] = mapped_column(Text)
    name_fr: Mapped[str | None] = mapped_column(Text)
    name_it: Mapped[str | None] = mapped_column(Text)
    name_rm: Mapped[str | None] = mapped_column(Text)

    group_id: Mapped[int | None] = mapped_column(BigInteger)
    begin_date: Mapped[datetime | None] = mapped_column(DateTime)
    end_date: Mapped[datetime | None] = mapped_column(DateTime)
    state: Mapped[str | None] = mapped_column(Text)

    description_de: Mapped[str | None] = mapped_column(Text)
    description_fr: Mapped[str | None] = mapped_column(Text)
    description_it: Mapped[str | None] = mapped_column(Text)

    location: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Agenda(Base):
    __tablename__ = "agendas"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    body_id: Mapped[int | None] = mapped_column(BigInteger)
    body_key: Mapped[str | None] = mapped_column(Text)
    meeting_id: Mapped[int | None] = mapped_column(BigInteger)
    item_date: Mapped[datetime | None] = mapped_column(DateTime)
    item_external_id: Mapped[str | None] = mapped_column(Text)
    item_title: Mapped[str | None] = mapped_column(Text)
    item_number_display: Mapped[str | None] = mapped_column(Text)
    item_number: Mapped[str | None] = mapped_column(Text)
    item_description: Mapped[str | None] = mapped_column(Text)
    item_status: Mapped[str | None] = mapped_column(Text)
    item_result: Mapped[str | None] = mapped_column(Text)
    item_category: Mapped[str | None] = mapped_column(Text)
    item_url: Mapped[str | None] = mapped_column(Text)
    item_affair_number: Mapped[str | None] = mapped_column(Text)
    item_affair_id: Mapped[int | None] = mapped_column(BigInteger)
    item_language: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    body_id: Mapped[int | None] = mapped_column(BigInteger)
    body_key: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    date: Mapped[datetime | None] = mapped_column(DateTime)
    position: Mapped[int | None] = mapped_column(BigInteger)

    title_de: Mapped[str | None] = mapped_column(Text)
    title_fr: Mapped[str | None] = mapped_column(Text)
    title_it: Mapped[str | None] = mapped_column(Text)

    title_harmonized: Mapped[str | None] = mapped_column(Text)
    title_harmonized_de: Mapped[str | None] = mapped_column(Text)
    title_harmonized_fr: Mapped[str | None] = mapped_column(Text)
    title_harmonized_it: Mapped[str | None] = mapped_column(Text)
    title_harmonized_en: Mapped[str | None] = mapped_column(Text)

    last: Mapped[bool | None] = mapped_column(Boolean)

    actor_de: Mapped[str | None] = mapped_column(Text)
    actor_fr: Mapped[str | None] = mapped_column(Text)
    actor_it: Mapped[str | None] = mapped_column(Text)
    actor_type: Mapped[str | None] = mapped_column(Text)

    affair_id: Mapped[int | None] = mapped_column(BigInteger)
    meeting_id: Mapped[int | None] = mapped_column(BigInteger)
    details_url: Mapped[str | None] = mapped_column(Text)
    details_text: Mapped[str | None] = mapped_column(Text)

    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Voting(Base):
    __tablename__ = "votings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    body_id: Mapped[int | None] = mapped_column(BigInteger)
    body_key: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    date: Mapped[datetime | None] = mapped_column(DateTime)
    affair_id: Mapped[int | None] = mapped_column(BigInteger)

    title_de: Mapped[str | None] = mapped_column(Text)
    title_fr: Mapped[str | None] = mapped_column(Text)
    title_it: Mapped[str | None] = mapped_column(Text)

    type_de: Mapped[str | None] = mapped_column(Text)
    type_fr: Mapped[str | None] = mapped_column(Text)
    type_it: Mapped[str | None] = mapped_column(Text)

    meaning_of_yes_de: Mapped[str | None] = mapped_column(Text)
    meaning_of_yes_fr: Mapped[str | None] = mapped_column(Text)
    meaning_of_yes_it: Mapped[str | None] = mapped_column(Text)

    meaning_of_no_de: Mapped[str | None] = mapped_column(Text)
    meaning_of_no_fr: Mapped[str | None] = mapped_column(Text)
    meaning_of_no_it: Mapped[str | None] = mapped_column(Text)

    results_yes: Mapped[int | None] = mapped_column(BigInteger)
    results_no: Mapped[int | None] = mapped_column(BigInteger)
    results_abstention: Mapped[int | None] = mapped_column(BigInteger)
    results_absent: Mapped[int | None] = mapped_column(BigInteger)

    results_string: Mapped[str | None] = mapped_column(Text)
    decision: Mapped[str | None] = mapped_column(Text)

    meeting_id: Mapped[int | None] = mapped_column(BigInteger)
    group_id: Mapped[int | None] = mapped_column(BigInteger)

    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Document(Base):
    __tablename__ = "documents"

    pk: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    source_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    date: Mapped[datetime | None] = mapped_column(DateTime)
    hash: Mapped[str | None] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(Text)
    size: Mapped[int | None] = mapped_column(BigInteger)
    text: Mapped[str | None] = mapped_column(Text)
    format: Mapped[str | None] = mapped_column(Text)
    body_id: Mapped[int | None] = mapped_column(BigInteger)
    body_key: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    affair_id: Mapped[int | None] = mapped_column(BigInteger)
    agenda_id: Mapped[int | None] = mapped_column(BigInteger)
    meeting_id: Mapped[int | None] = mapped_column(BigInteger)
    url_oparl: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    category_de: Mapped[str | None] = mapped_column(Text)
    category_fr: Mapped[str | None] = mapped_column(Text)
    category_it: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    parent_type: Mapped[str | None] = mapped_column(Text)
    category_harmonized: Mapped[str | None] = mapped_column(Text)


class ParliamentaryText(Base):
    __tablename__ = "texts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    body_id: Mapped[int | None] = mapped_column(BigInteger)
    body_key: Mapped[str | None] = mapped_column(Text)
    affair_id: Mapped[int | None] = mapped_column(BigInteger)
    external_id: Mapped[str | None] = mapped_column(Text)

    text_de: Mapped[str | None] = mapped_column(Text)
    text_fr: Mapped[str | None] = mapped_column(Text)
    text_it: Mapped[str | None] = mapped_column(Text)
    text_rm: Mapped[str | None] = mapped_column(Text)

    type_de: Mapped[str | None] = mapped_column(Text)
    type_fr: Mapped[str | None] = mapped_column(Text)
    type_it: Mapped[str | None] = mapped_column(Text)
    type_rm: Mapped[str | None] = mapped_column(Text)

    text_date: Mapped[datetime | None] = mapped_column(DateTime)
    text_format: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)