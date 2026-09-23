import argparse, csv, uuid
from .db import connect
from .utils import peso, review_label

FIELDS = ["id","fiscal_year","budget_stage","agency","region","province","city_municipality","possible_congressional_district","implementing_office","project_title","project_type","amount","amount_display","location_clarity","title_specificity","needs_manual_review_score","review_label","review_reason","is_large_allocation_score","citizen_readability","source_name","source_url","source_page","source_pdf_page","row_level","parent_row_id","is_leaf","extraction_confidence","extraction_note","raw_text"]
def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--db",required=True); a=p.parse_args()
    con=connect(__import__('pathlib').Path(a.db)); count=0
    with open(a.input, encoding="utf-8-sig", newline="") as f:
      for row in csv.DictReader(f):
        row={k: row.get(k, "") for k in FIELDS}; row["id"] = row["id"] or f"SAMPLE-{uuid.uuid4().hex[:8]}"; row["amount"] = float(row["amount"] or 0)
        row["amount_display"] = peso(row["amount"]); score=row["needs_manual_review_score"] = float(row["needs_manual_review_score"] or 0); row["review_label"] = row["review_label"] or review_label(score)
        con.execute(f"INSERT OR REPLACE INTO projects ({','.join(FIELDS)}) VALUES ({','.join('?' for _ in FIELDS)})", [row[k] for k in FIELDS]); count+=1
    con.commit(); print(f"Imported {count} rows")
if __name__ == "__main__": main()

