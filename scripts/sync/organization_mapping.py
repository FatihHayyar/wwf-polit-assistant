"""Map organization endpoints to existing normalized columns."""
from datetime import datetime, timezone


def parse_datetime(value):
    if value is None or value == "":
        return None
    result = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return result.astimezone(timezone.utc).replace(tzinfo=None) if result.tzinfo else result


def map_record(record, direct, dates, translations):
    values = {"id": int(record["id"])}
    for field in direct:
        if field in record:
            values[field] = record[field]
    for field in dates:
        if field in record:
            values[field] = parse_datetime(record[field])
    for field in translations:
        if field not in record:
            continue
        terms = record[field] or {}
        if not isinstance(terms, dict):
            raise ValueError(f"Record {record['id']}: {field} must be a translation dictionary")
        for language in ("de", "fr", "it"):
            values[f"{field}_{language}"] = terms.get(language)
        if field == "type_harmonized":
            values[field] = terms.get("en") or terms.get("de") or terms.get("fr") or terms.get("it")
    return values
