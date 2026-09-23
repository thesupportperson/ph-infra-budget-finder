import argparse, json
from pathlib import Path
from .config import JEV_DRY_RUN
from .db import connect
from .utils import normalize_type, review_label

def main():
 p=argparse.ArgumentParser();p.add_argument("--db",required=True);p.add_argument("--limit",type=int,default=100);a=p.parse_args(); con=connect(Path(a.db)); rows=con.execute("SELECT * FROM projects LIMIT ?",(a.limit,)).fetchall()
 for r in rows:
  kind=normalize_type(r["project_title"]); score=.75 if not r["city_municipality"] or len(r["project_title"] or "")<35 else .25
  con.execute("UPDATE projects SET project_type=?, needs_manual_review_score=?, review_label=?, review_reason=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",(kind,score,review_label(score),"Dry-run heuristic: confirm against the cited source." if JEV_DRY_RUN else "Classification pending source review.",r["id"]))
 con.commit(); print(f"Classified {len(rows)} rows ({'dry run' if JEV_DRY_RUN else 'no remote call implemented'})")
if __name__=="__main__": main()
