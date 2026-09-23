# PH Infra Budget Finder

A simple public search page for FY 2026 DPWH budget records. Search a place, office, or project name, then open the original DBM PDF for each result.

The public site is static: no backend, database connection, live AI call, or public API key.

## Live site

- https://ph-infra-budget-finder.pages.dev/
- https://github.com/thesupportperson/ph-infra-budget-finder

## Data release

The current release has 2,107 source-checked FY 2026 records. The page 714 financial summary is included and converted from the PDF's thousand-peso column. Page 715 continues historical release details and has no FY 2026 amount column. Later performance pages are not budget records.

Before publishing a changed release, run:

```powershell
python -m unittest discover -s tests -v
python -m src.audit_dataset --input site/data/projects.json --out data/processed/extraction_audit.json
python -m src.verify_factuality --dataset site/data/projects.json --pdf data/raw/dpwh_fy2026_expenditure_program.pdf --report site/data/factuality_report.json
```

## Rebuild the static data

```powershell
python -m src.parse_pdf --input data/raw/dpwh_fy2026_expenditure_program.pdf --db data/processed/dpwh_fy2026_release.sqlite --include-hierarchy
python -m src.export_static --db data/processed/dpwh_fy2026_release.sqlite --out site/data
```

## Deploy

Cloudflare Pages serves the `site/` folder. The current deployment is direct; deploy a verified release with:

```powershell
npx wrangler pages deploy site --project-name ph-infra-budget-finder --branch main
```
## Jev offline check

Jev runs only during local processing. It adds structured project-type, location-clarity, title-specificity, and neutral review signals after the parser has already recorded the source facts. It cannot change an amount, source page, office, or PDF link.

```powershell
python -m src.classify_jev --db data/processed/dpwh_fy2026_release.sqlite --limit 25 --leaf-only
```

The Typesafe key belongs only in the git-ignored `.env` file. The public site contains no key and makes no Jev API calls.
