"""Fail-fast audit for a static PH Infra budget export."""
import argparse
import json
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    rows = json.loads(Path(args.input).read_text(encoding="utf-8"))
    required = ("id", "amount", "row_level", "is_leaf", "source_url", "source_page", "source_pdf_page", "extraction_confidence")
    missing = {key: sum(not row.get(key) and key != "is_leaf" for row in rows) for key in required}
    duplicates = len(rows) - len({row["id"] for row in rows})
    bad_amounts = sum(not isinstance(row.get("amount"), (int, float)) or row["amount"] <= 0 for row in rows)
    invalid_pdf_pages = sum(not isinstance(row.get("source_pdf_page"), int) or row["source_pdf_page"] < 1 for row in rows)
    report = {"record_count": len(rows), "row_levels": dict(Counter(row.get("row_level") for row in rows)), "source_pdf_pages_covered": len({row.get("source_pdf_page") for row in rows}), "review_labels_present": sum(bool(row.get("review_label")) for row in rows), "missing_required_fields": missing, "duplicate_ids": duplicates, "nonpositive_or_invalid_amounts": bad_amounts, "invalid_source_pdf_pages": invalid_pdf_pages, "pass": not any(missing.values()) and not duplicates and not bad_amounts and not invalid_pdf_pages}
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit("Dataset audit failed")


if __name__ == "__main__":
    main()
