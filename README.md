# PH Infra Budget Finder

A lightweight static search tool for reorganizing publicly available DPWH budget/project records by area, project type, and keyword. It is **not** an accusation tool, corruption detector, or political endorsement. Review labels are data-quality prompts only; verify every record against its cited official source.

The public site reads only `site/data/` files in the browser. It has no backend, database connection, live API call, or API key in the frontend. This makes it cheap to host on Cloudflare Pages and usable on low-end phones.

## Windows quickstart

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m src.ingest_csv --input data/sample_projects.csv --db data/processed/budget.sqlite
python -m src.classify_jev --db data/processed/budget.sqlite --limit 30
python -m src.export_static --db data/processed/budget.sqlite --out site/data`npython -m src.audit_dataset --input site/data/projects.json --out data/processed/extraction_audit.json
python -m http.server 8000 --directory site
```

Open `http://localhost:8000`.

## Data workflow

Put raw files in `data/raw/`, normalize them offline into SQLite, then export `site/data/projects.json`, `projects.csv`, and `summary.json`. `ingest_csv` is the working normalized-file importer. Excel/PDF commands are deliberately source-specific adapters rather than unreliable generic parsers.

Current official release: 2,102 independently verified FY 2026 DPWH hierarchy rows. The browser defaults to 1,427 leaf rows; users can opt into summary rows without mixing them into the default total. Run `python -m src.verify_factuality --dataset site/data/projects.json --pdf data/raw/dpwh_fy2026_expenditure_program.pdf --report site/data/factuality_report.json` before publishing a changed export.`n`nJev is offline-only and defaults to `JEV_DRY_RUN=true`; no key is supplied or stored here. The budget guard assumes `$0.042 / 1M input tokens` and caps estimated input spend at `JEV_BUDGET_USD` (default `$1`). Keep usage logs in `data/processed/jev_usage.jsonl` when a real classifier integration is approved.

## Deploy and corrections

Cloudflare Pages: build command `none`; output directory `site`. Push the project to GitHub and connect it to Pages. To report a correction, open a Data correction issue with the project ID, current value, suggested correction, source link, and notes.


