import argparse, csv, json
from datetime import datetime, timezone
from pathlib import Path
from .db import connect
from .ingest_csv import FIELDS

def main():
 p=argparse.ArgumentParser(); p.add_argument("--db",required=True); p.add_argument("--out",required=True); a=p.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
 rows=[dict(r) for r in connect(Path(a.db)).execute("SELECT * FROM projects ORDER BY fiscal_year DESC, amount DESC")]
 (out/"projects.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2),encoding="utf-8")
 with (out/"projects.csv").open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
 summary={"generated_at":datetime.now(timezone.utc).isoformat(),"total_projects":len(rows),"total_budget":sum(r["amount"] or 0 for r in rows),"fiscal_years":sorted({r["fiscal_year"] for r in rows if r["fiscal_year"]}),"regions":sorted({r["region"] for r in rows if r["region"]}),"project_type_totals":{},"review_label_counts":{}}
 for r in rows: summary["project_type_totals"][r["project_type"]]=summary["project_type_totals"].get(r["project_type"],0)+1; summary["review_label_counts"][r["review_label"]]=summary["review_label_counts"].get(r["review_label"],0)+1
 (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8"); print(f"Exported {len(rows)} rows")
if __name__ == "__main__": main()
