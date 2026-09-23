"""Build the small browser search index from the audited static dataset.

This intentionally keeps only fields required by the public search UI. The full
projects.json remains available for audit and factuality verification, but is
not fetched during normal page use.
"""
import argparse
import json
from pathlib import Path

PUBLIC_FIELDS = (
    "id", "fiscal_year", "region", "province", "city_municipality",
    "implementing_office", "project_title", "project_type", "amount",
    "amount_display", "source_url", "source_page", "source_pdf_page",
)


def build(records):
    return [{field: record.get(field) for field in PUBLIC_FIELDS}
            for record in records if int(record.get("is_leaf") or 0) != 0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    records = json.loads(Path(args.input).read_text(encoding="utf-8"))
    index = build(records)
    Path(args.out).write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Built {len(index)} searchable leaf records")


if __name__ == "__main__":
    main()
