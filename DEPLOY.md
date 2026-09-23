# Cloudflare Pages deployment

This is a static site. Connect the GitHub repository to Cloudflare Pages with:

- Production branch: `main`
- Build command: `exit 0`
- Build output directory: `site`
- No environment variables, functions, Workers, database, or API keys

Release gate:

```powershell
python -m unittest discover -s tests -v
python -m src.audit_dataset --input site/data/projects.json --out data/processed/extraction_audit.json
python -m src.verify_factuality --dataset site/data/projects.json --pdf data/raw/dpwh_fy2026_expenditure_program.pdf --report site/data/factuality_report.json
```

After deploy, confirm the home page, `data/factuality_report.json`, a Davao City search, one PDF source link, and filtered-CSV download on the deployed URL.
