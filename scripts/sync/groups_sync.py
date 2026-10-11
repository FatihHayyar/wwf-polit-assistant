import argparse
from scripts.sync.organization_mapping import map_record, parse_datetime

API_URL = "https://api.openparldata.ch/v1/groups/"

# Preserve the enum codes used by the normalized snapshot import. Upstream
# returns localized display labels rather than those codes.
GROUP_TYPES = {
    "Ratsbüro": "council_office", "Departement": "departement",
    "Delegation": "delegation", "Arbeitsgruppe": "working_group",
    "Partei": "party", "Gericht": "court", "Parlament (Legislativrat)": "council_legislative",
    "Andere": "other", "Interessengruppe": "interest_group",
    "Regierung (Exekutivrat)": "council_executive", "Verein": "association",
    "Ratssekretariat / Kanzlei": "council_secretariat", "Versammlung": "assembly",
    "Ad-Hoc Kommission": "committee_ad_hoc", "Kommission": "committee",
    "Parlament (Stellvertretung)": "council_legislative_substitute",
    "Fraktion": "parliamentary_group", "Ratsleitung": "council_management",
}


def map_group(record):
    values = map_record(record, ("body_id", "body_key", "external_id", "active"),
                      ("updated_at", "created_at"), ("name", "abbreviation", "type_harmonized"))
    if "type_harmonized" in record:
        terms = record["type_harmonized"] or {}
        values["type_harmonized"] = GROUP_TYPES.get(terms.get("de"))
        if terms and values["type_harmonized"] is None:
            # Do not replace an imported code with an unknown display label.
            raise ValueError(f"Group {record['id']}: unknown harmonized type {terms}")
    return values


def run_sync(recheck=False):
    from scripts.sync.entity_sync import run_dataset
    return run_dataset("groups", recheck=recheck)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--recheck", action="store_true")
    run_sync(parser.parse_args().recheck)
