"""Independent factuality gate for PH Infra static exports.

This intentionally does not import the project parser. It re-opens the official PDF,
checks each exported row against its claimed physical page, and reconciles page 718.
"""
import argparse
import json
import re
from pathlib import Path
from pypdf import PdfReader


def normalized_text(value):
    text = str(value).lower().replace("pifas", "pinas")
    return re.sub(r"[^a-z0-9]", "", text)

def label_supported_by_source(label, text):
    tokens = {token for token in re.findall(r"[a-z]{4,}", str(label).lower()) if token not in {"region", "office", "district", "engineering"}}
    source_normalized = normalized_text(text)
    supported = {token for token in tokens if token in source_normalized}
    return not tokens or len(supported) / len(tokens) >= 0.75


def money_tokens(value):
    clean = re.sub(r"\s+,", ",", str(value))
    clean = re.sub(r"(\d)\.,(?=\d{3},)", r"\1,", clean)
    return [int(re.sub(r"\D", "", token)) for token in re.findall(r"\d{1,3}(?:[,.]\s?\d{3})+", clean)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    rows = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    reader = PdfReader(args.pdf)
    page_text = {}
    failures = []
    source_hits = 0

    for row in rows:
        pdf_page = row.get("source_pdf_page")
        if not isinstance(pdf_page, int) or not 1 <= pdf_page <= len(reader.pages):
            failures.append({"id": row.get("id"), "check": "pdf_page_range"})
            continue
        if str(row.get("source_page")) != str(pdf_page + 713):
            failures.append({"id": row.get("id"), "check": "printed_page_mapping"})
        text = page_text.setdefault(pdf_page, reader.pages[pdf_page - 1].extract_text() or "")
        label = row.get("raw_text") or row.get("implementing_office") or row.get("project_title")
        if normalized_text(label) and not label_supported_by_source(label, text):
            failures.append({"id": row.get("id"), "check": "label_missing_from_source", "page": pdf_page})
        if int(row.get("amount") or 0) not in money_tokens(text):
            failures.append({"id": row.get("id"), "check": "amount_missing_from_source", "page": pdf_page})
        else:
            source_hits += 1

    page5 = [row for row in rows if row.get("source_pdf_page") == 5]
    reconciliation = {"checked": False}
    if page5:
        total = next((row["amount"] for row in page5 if row.get("row_level") == "agency_total"), None)
        central = next((row["amount"] for row in page5 if row.get("row_level") == "central_office_summary"), None)
        regional_total = next((row["amount"] for row in page5 if row.get("project_title") == "Regional Allocation"), None)
        regions = sum(row["amount"] for row in page5 if row.get("row_level") == "regional_summary" and row.get("region"))
        reconciliation = {"checked": True, "central": central, "regional_total": regional_total, "regional_rows_total": regions, "agency_total": total, "regions_match": regions == regional_total, "agency_match": central + regional_total == total if central is not None and regional_total is not None and total is not None else False}
        if not reconciliation["regions_match"] or not reconciliation["agency_match"]:
            failures.append({"check": "page_718_reconciliation", **reconciliation})

    report = {"dataset": str(Path(args.dataset)), "records_checked": len(rows), "source_pages_read": len(page_text), "amount_source_hits": source_hits, "failures": failures, "page_718_reconciliation": reconciliation, "verdict": "VERIFIED" if not failures else "FAILED"}
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()



