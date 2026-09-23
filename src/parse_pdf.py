"""Extract source-grounded DPWH office allocations from DBM expenditure PDFs."""
import argparse
import re
from pathlib import Path
from pypdf import PdfReader
from .db import connect
from .utils import normalize_type, peso

DB_FIELDS = ("id,fiscal_year,budget_stage,agency,region,province,city_municipality,"
             "possible_congressional_district,implementing_office,project_title,project_type,"
             "amount,amount_display,location_clarity,title_specificity,needs_manual_review_score,"
             "review_label,review_reason,is_large_allocation_score,citizen_readability,source_name,"
             "source_url,source_page,source_pdf_page,row_level,parent_row_id,is_leaf,extraction_confidence,extraction_note,raw_text")
SOURCE_URL = "https://www.dbm.gov.ph/wp-content/uploads/NEP2026/DPWH/DPWH.pdf"

REGIONS = {
    "I": "Region I - Ilocos", "II": "Region II - Cagayan Valley",
    "III": "Region III - Central Luzon", "IVA": "Region IVA - CALABARZON",
    "IVB": "Region IVB - MIMAROPA", "V": "Region V - Bicol",
    "VI": "Region VI - Western Visayas", "VII": "Region VII - Central Visayas",
    "VIII": "Region VIII - Eastern Visayas", "IX": "Region IX - Zamboanga Peninsula",
    "X": "Region X - Northern Mindanao", "XI": "Region XI - Davao",
    "XII": "Region XII - SOCCSKSARGEN", "XIII": "Region XIII - CARAGA",
}

def clean_label(label):
    """Remove numeric PDF columns that pypdf sometimes joins into left-column text."""
    cleaned = re.sub(r"(?:\s+\d{1,3}(?:,\d{3})+)+", "", label)
    cleaned = re.sub(r"^(?:\d{1,3}(?:,\d{3})+\s+)+", "", cleaned)
    return cleaned.replace(" .", "").strip(" .")

def canonical_region(label):
    clean = label.replace("~", "-").replace("�", "").replace("‘", "(")
    if "National Capital Region" in clean:
        return "National Capital Region (NCR)"
    if "Cordillera Administrative" in clean:
        return "Cordillera Administrative Region (CAR)"
    if "Negros Island Region" in clean:
        return "Negros Island Region"
    match = re.search(r"Region\s+(XIII|XII|VIII|VII|III|II|XI|IX|IV[AB]?|VI|V|X|I)\b", clean)
    return REGIONS.get(match.group(1)) if match else ""

def blocks(page):
    found = []
    page.extract_text(visitor_text=lambda text, cm, tm, *args: found.append((round(cm[4]), round(cm[5]), text.strip())) if text.strip() else None)
    return found

def grouped_left(items, x_limit=330, gap=11):
    left = sorted(((y, x, t) for x, y, t in items if x < x_limit and "DEPARTMENT OF PUBLIC" not in t and "EXPENDITURE PROGRAM" not in t), reverse=True)
    groups, current, last_y = [], [], None
    for y, _x, text in left:
        if last_y is not None and last_y - y > gap:
            groups.append((last_y, " ".join(current)))
            current = []
        current.append(text)
        last_y = y
    if current:
        groups.append((last_y, " ".join(current)))
    return groups

def money_values(text):
    normalized = re.sub(r"\s+,", ",", text)
    normalized = re.sub(r"(\d)\.,(?=\d{3},)", r"\1,", normalized)
    tokens = re.findall(r"\d{1,3}(?:[,.]\s?\d{3})+", normalized)
    return [int(re.sub(r"\D", "", token)) for token in tokens]

def total_amount_for(y, items, tolerance=9):
    """Read the rightmost numeric column on a rendered row as its printed total."""
    candidates = []
    for x, ay, text in items:
        if x < 330 or abs(ay - y) > tolerance:
            continue
        values = money_values(text)
        if values:
            candidates.append((x, max(values)))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None

def amount_from_text(text):
    values = money_values(text)
    return values[-1] if values else None
def summary_specs(pdf_index, items):
    """Dedicated adapters for printed pages 716–718 (physical PDF pages 3–5)."""
    bands = {
        3: ((125, 248, 180, "agency_summary"),),
        4: ((424, 700, 240, "agency_summary"), (133, 210, 240, "program_summary")),
        5: ((470, 631, 250, "regional_summary"),),
    }
    for low, high, x_limit, default_level in bands.get(pdf_index, ()):
        for y, raw_label in grouped_left(items, x_limit=x_limit, gap=5 if pdf_index in {3, 4, 5} else 11):
            if not low <= y <= high:
                continue
            label = clean_label(re.sub(r"\s+", " ", raw_label).strip(" ."))
            if not label:
                continue
            upper = label.upper()
            if any(token in upper for token in ("EXPENDITURE PROGRAM", "OPERATIONS BY PROGRAM", "CASH-BASED", "ACTUAL CURRENT PROPOSED", "GAS / STO")):
                continue
            amount = (amount_from_text(raw_label) or total_amount_for(y, items, tolerance=3)) if pdf_index == 5 else (total_amount_for(y, items, tolerance=3) or amount_from_text(raw_label))
            if not amount or amount > 2_000_000_000_000:
                continue
            level = "agency_total" if "TOTAL AGENCY BUDGET" in upper else default_level
            if label.upper() == "CENTRAL OFFICE":
                level = "central_office_summary"
            region = canonical_region(label)
            if region:
                level, label = "regional_summary", region
            yield {"label": label, "amount": amount, "row_level": level, "region": region}

def row_level(label, has_code):
    if has_code:
        return "program_summary"
    if label.startswith("Sub-total"):
        return "subtotal"
    if label.startswith("TOTAL"):
        return "agency_total"
    if canonical_region(label):
        return "regional_summary"
    if ("Engineering" in label and "Office" in label) or label == "Central Office":
        return "office_allocation"
    return "budget_line"

def parse(pdf_path, include_hierarchy=False):
    reader = PdfReader(pdf_path)
    rows, current_title, current_region, sequence = [], "Unclassified DPWH allocation", "", 0
    current_program_id, current_region_id = "", ""

    def add_row(**row):
        nonlocal sequence
        sequence += 1
        row["id"] = f"DPWH-2026-{row['source_pdf_page']:03}-{sequence:05}"
        rows.append(row)
        return row["id"]

    for pdf_index, page in enumerate(reader.pages, start=1):
        if include_hierarchy and pdf_index < 3:
            continue  # Pages 714–715 use a different summary layout; quarantine until a dedicated adapter exists.
        text = page.extract_text() or ""
        items = blocks(page)
        source_page = str(pdf_index + 713)  # Physical page 1 is printed budget page 714.
        if include_hierarchy and pdf_index in {3, 4, 5}:
            for spec in summary_specs(pdf_index, items):
                add_row(
                    fiscal_year=2026, budget_stage="NEP", agency="DPWH", region=spec["region"],
                    province="", city_municipality="", possible_congressional_district="", implementing_office="",
                    project_title=spec["label"], project_type=normalize_type(spec["label"]), amount=spec["amount"],
                    amount_display=peso(spec["amount"]), location_clarity="partial" if spec["region"] else "unclear",
                    title_specificity="broad", needs_manual_review_score=None, review_label="",
                    review_reason="No review classification has been applied. Verify the cited DBM source before interpretation.",
                    is_large_allocation_score=None, citizen_readability="moderate",
                    source_name="DBM FY 2026 NEP DPWH Expenditure Program", source_url=SOURCE_URL,
                    source_page=source_page, source_pdf_page=pdf_index, row_level=spec["row_level"],
                    parent_row_id="", is_leaf=0, extraction_confidence="summary_adapter",
                    extraction_note="Extracted by the dedicated summary-page adapter for this official PDF layout.", raw_text=spec["label"],
                )
            continue
        for y, raw_label in grouped_left(items):
            label = re.sub(r"\s+", " ", raw_label).replace("Pifas", "Piñas").replace("�", "ñ").strip(" .")
            if not label or "EXPENDITURE PROGRAM FY" in label or "DEPARTMENT OF PUBLIC" in label:
                continue
            code_match = re.search(r"\d{15}", label)
            has_code = bool(code_match)
            if code_match:
                current_title = clean_label(label[:code_match.start()] + " " + label[code_match.end():])
            candidate_title = current_title
            detected_region = canonical_region(label)
            if detected_region:
                current_region = detected_region
            clean = clean_label(re.sub(r"\d{15}", "", label))
            level = row_level(clean, has_code)
            amount = total_amount_for(y, items)
            if not amount or amount < 1 or amount > 2_000_000_000_000:
                continue
            if not include_hierarchy and level != "office_allocation":
                continue
            is_leaf = 1 if level in {"office_allocation", "budget_line"} else 0
            parent_id = current_region_id or current_program_id
            if level == "program_summary":
                parent_id = ""
            elif level == "regional_summary":
                parent_id = current_program_id
            title = candidate_title if level in {"office_allocation", "regional_summary"} else clean
            confidence = "source_linked" if level == "office_allocation" else "coordinate_extracted"
            row_id = add_row(
                fiscal_year=2026, budget_stage="NEP", agency="DPWH", region=current_region,
                province="", city_municipality="", possible_congressional_district="",
                implementing_office=clean if level == "office_allocation" else "",
                project_title=title, project_type=normalize_type(title), amount=amount,
                amount_display=peso(amount), location_clarity="partial" if current_region else "unclear",
                title_specificity="broad", needs_manual_review_score=None, review_label="",
                review_reason="No review classification has been applied. Verify the cited DBM source before interpretation.",
                is_large_allocation_score=None, citizen_readability="moderate",
                source_name="DBM FY 2026 NEP DPWH Expenditure Program", source_url=SOURCE_URL,
                source_page=source_page, source_pdf_page=pdf_index, row_level=level,
                parent_row_id=parent_id, is_leaf=is_leaf, extraction_confidence=confidence,
                extraction_note="Coordinate-extracted from the official PDF; check the source page before interpretation.",
                raw_text=clean,
            )
            if level == "program_summary":
                current_program_id, current_region_id = row_id, ""
            elif level == "regional_summary":
                current_region_id = row_id
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--include-hierarchy", action="store_true", help="Extract typed non-office hierarchy rows for staging/audit.")
    args = parser.parse_args()
    rows = parse(Path(args.input), include_hierarchy=args.include_hierarchy)
    con = connect(Path(args.db)); fields = DB_FIELDS.split(","); placeholders = ",".join("?" for _ in fields)
    for row in rows:
        con.execute(f"INSERT OR REPLACE INTO projects ({DB_FIELDS}) VALUES ({placeholders})", [row[k] for k in fields])
    con.commit()
    print(f"Imported {len(rows)} source-grounded DPWH hierarchy rows")

if __name__ == "__main__":
    main()





















