"""Readable German notifications, independent of technical dataset names."""
from html import escape

from app.core.config import settings
from app.services.notification_policy import comparable, meaningful_fields, VisibleText

NAMES = {"affairs": "Geschäft", "agendas": "Traktandum", "meetings": "Sitzung",
         "votings": "Abstimmung", "events": "Ereignis", "documents": "Dokument",
         "texts": "Text", "groups": "Gremium", "interests": "Interessenbindung"}
LABELS = {"end_date": "Abschlussdatum", "begin_date": "Beginn", "date": "Datum",
          "text_date": "Textdatum", "item_date": "Datum", "item_status": "Status",
          "item_result": "Ergebnis", "decision": "Entscheidung", "location": "Ort",
          "state": "Status", "active": "Aktiv", "meeting_id": "Zugehörige Sitzung",
          "hash": "Dokumentinhalt", "results_yes": "Ja-Stimmen", "results_no": "Nein-Stimmen",
          "results_abstention": "Enthaltungen", "results_absent": "Abwesend",
          "person_id": "Zugehörige Person", "ex_officio": "Von Amts wegen"}


def label(field):
    if field in LABELS:
        return LABELS[field]
    for prefix, name in (("state_name", "Status"), ("title", "Titel"), ("name", "Bezeichnung"),
                         ("text", "Textinhalt"), ("description", "Beschreibung"),
                         ("role_name", "Funktion"), ("actor", "Beteiligte")):
        if field.startswith(prefix):
            return name
    return "Inhalt"


def value(raw):
    if raw is None or raw == "":
        return "nicht angegeben"
    parser = VisibleText()
    parser.feed(str(raw))
    return ' '.join(''.join(parser.parts).split())[:160]


def entry(event, entity, title):
    lines = [f"{NAMES.get(event.dataset, 'Inhalt')} – {'Neu' if event.change_type == 'created' else 'Aktualisiert'}: {title}"]
    fields = meaningful_fields(event.dataset, event.changes or [])
    if not event.changes and event.description and event.description.startswith("Changed fields: "):
        fields = meaningful_fields(event.dataset, [part.strip() for part in event.description[16:].split(',')])
    seen = set()
    for field in fields:
        name = label(field)
        if name in seen:
            continue
        if event.changes:
            change = event.changes[field]
            if comparable(change.get('before')) == comparable(change.get('after')):
                continue
            lines.append(f"{name}: {value(change.get('before'))} → {value(change.get('after'))}")
        else:
            current = getattr(entity, field, None) if entity is not None else None
            lines.append(f"{name}: {value(current)} (aktualisiert)" if current is not None else f"{name} wurde aktualisiert.")
        seen.add(name)
    lines.append(f"{settings.verification_base_url.rstrip('/')}/?dataset={event.dataset}&record={event.source_id}")
    return '\n'.join(lines)


def render_html(body):
    blocks = []
    for block in body.split('\n\n'):
        lines = []
        for line in block.splitlines():
            if line.startswith(('https://', 'http://')):
                lines.append(f'<a href="{escape(line, quote=True)}">Details in der Anwendung ansehen</a>')
            else:
                lines.append(escape(line))
        blocks.append('<p style="line-height:1.6">' + '<br>'.join(lines) + '</p>')
    return '<html lang="de"><body style="font-family:Arial,sans-serif;color:#19382e;max-width:680px;margin:24px auto;padding:24px"><h2>WWF Polit-Assistant</h2>' + ''.join(blocks) + '</body></html>'
