import argparse
from scripts.sync.organization_mapping import map_record, parse_datetime

API_URL = "https://api.openparldata.ch/v1/interests/"


def map_interest(record):
    return map_record(record,
        ("body_id", "body_key", "person_id", "external_id", "url", "declaration_doc_url",
         "declaration_doc_title", "place", "ex_officio"),
        ("begin_date", "end_date", "updated_at", "created_at"), ("name", "type", "role_name"))


def run_sync(recheck=False):
    from scripts.sync.entity_sync import run_dataset
    return run_dataset("interests", recheck=recheck)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--recheck", action="store_true")
    run_sync(parser.parse_args().recheck)
