"""Readable German notifications, independent of technical dataset names."""
from html import escape
import json
from urllib.parse import urlencode

from app.core.config import settings
from app.services.notification_policy import comparable, meaningful_fields, VisibleText

NAMES = {"affairs": "Geschäft", "agendas": "Traktandum", "meetings": "Sitzung",
         "votings": "Abstimmung", "events": "Ereignis", "documents": "Dokument",
         "texts": "Text", "groups": "Gremium", "interests": "Interessenbindung"}


def change_identity(event, entity):
    identity = getattr(entity, "source_id", None) if event.dataset == "documents" else None
    fields = meaningful_fields(event.dataset, event.changes or [])
    changes = ({field: event.changes[field] for field in fields} if fields else getattr(event, "fingerprint", event.changes)) if event.changes else getattr(event, "fingerprint", event.description) if event.change_type != "created" else None
    return (event.dataset, identity or event.source_id, event.change_type,
            json.dumps(changes, sort_keys=True, default=str))


def record_url(dataset, record_id):
    return settings.verification_base_url.rstrip('/') + '/?' + urlencode({'dataset': dataset, 'record': record_id})


def render_digest(title, dataset, record_id, items):
    """Separate accessible plain text and HTML; all source text is escaped."""
    count = len(items)
    heading = "Eine neue Entwicklung" if count == 1 else f"{count} neue Entwicklungen"
    if count == 1:
        event, _, item_title = items[0]
        action = {"affairs": "Neues Geschäft", "agendas": "Neues Traktandum", "meetings": "Neue Sitzung",
                  "votings": "Neue Abstimmung", "events": "Neues Ereignis", "documents": "Neues Dokument",
                  "texts": "Neuer Text", "groups": "Neues Gremium", "interests": "Neue Interessenbindung"}.get(event.dataset, "Neue Entwicklung") if event.change_type == "created" else f"{NAMES.get(event.dataset, 'Inhalt')} aktualisiert"
        subject_title = item_title
    else:
        action, subject_title = f"{count} neue Entwicklungen", title
    subject_title = subject_title[:107].rstrip() + '…' if len(subject_title) > 110 else subject_title
    subject = f"WWF Polit-Assistant: {action} – {subject_title}"
    main_url = record_url(dataset, record_id)
    manage_url = settings.verification_base_url.rstrip('/') + '/'
    blocks = []
    text = ["WWF Polit-Assistant", heading, title, ""]
    for event, entity, item_title in items[:30]:
        content = entry(event, entity, item_title).splitlines()
        url = content.pop()
        text.extend(content + [f"{NAMES.get(event.dataset, 'Inhalt')} öffnen: {url}", ""])
        description = '<br>'.join(escape(line) for line in content[1:])
        blocks.append('<tr><td style="padding:20px 24px;border-bottom:1px solid #dce6dd">'
                      f'<p style="margin:0 0 8px;color:#52675c">{escape(NAMES.get(event.dataset, "Inhalt"))} · {"Neu hinzugefügt" if event.change_type == "created" else "Aktualisiert"}</p>'
                      f'<h3 style="margin:0 0 12px;font-size:18px">{escape(item_title)}</h3>'
                      + (f'<p style="line-height:1.6">{description}</p>' if description else '')
                      + f'<a style="color:#216147" href="{escape(url, quote=True)}">{escape(NAMES.get(event.dataset, "Inhalt"))} öffnen →</a></td></tr>')
    if count > 30:
        extra = f"{count - 30} weitere Änderungen finden Sie in der Anwendung."
        text.append(extra)
        blocks.append(f'<tr><td style="padding:20px 24px">{escape(extra)}</td></tr>')
    label = "Geschäft und Verlauf ansehen" if dataset == "affairs" else "Übersicht ansehen"
    show_main = dataset == "affairs" or count > 1
    if show_main:
        text.append(f"{label}: {main_url}")
    text.extend(["", "Sie erhalten diese Nachricht aufgrund Ihrer Abonnements.", f"Abonnements verwalten: {manage_url}"])
    button = f'<a href="{escape(main_url, quote=True)}" style="display:inline-block;background:#216147;color:white;padding:12px 18px;text-decoration:none;border-radius:6px">{label}</a>' if show_main else ''
    html = ('<!doctype html><html lang="de"><body style="margin:0;background:#f4f7f2;font-family:Arial,sans-serif;color:#19382e">'
            '<table role="presentation" style="width:100%;max-width:680px;margin:24px auto;background:white;border:1px solid #dce6dd;border-collapse:collapse">'
            f'<tr><td style="padding:24px;background:#eaf2e5"><p style="margin:0 0 16px;font-weight:bold">WWF Polit-Assistant</p><p>{heading}</p><h2 style="line-height:1.4;margin:0">{escape(title)}</h2></td></tr>'
            + ''.join(blocks) + f'<tr><td style="padding:24px">{button}<p style="color:#52675c;font-size:13px;line-height:1.6">Sie erhalten diese Nachricht aufgrund Ihrer Abonnements.<br><a href="{escape(manage_url, quote=True)}" style="color:#216147">Abonnements verwalten</a></p></td></tr></table></body></html>')
    return subject, '\n'.join(text), html
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
