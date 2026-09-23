import sqlite3
from pathlib import Path

PROJECT_COLUMNS = """id TEXT PRIMARY KEY, fiscal_year INTEGER, budget_stage TEXT, agency TEXT, region TEXT,
province TEXT, city_municipality TEXT, possible_congressional_district TEXT, implementing_office TEXT,
project_title TEXT, project_type TEXT, amount REAL, amount_display TEXT, location_clarity TEXT,
title_specificity TEXT, needs_manual_review_score REAL, review_label TEXT, review_reason TEXT,
is_large_allocation_score REAL, citizen_readability TEXT, source_name TEXT, source_url TEXT,
source_page TEXT, source_pdf_page INTEGER, row_level TEXT, parent_row_id TEXT, is_leaf INTEGER, extraction_confidence TEXT, extraction_note TEXT, raw_text TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP"""

def connect(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute(f"CREATE TABLE IF NOT EXISTS projects ({PROJECT_COLUMNS})")
    con.execute("""CREATE TABLE IF NOT EXISTS jev_usage (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT,
                 model TEXT, input_tokens INTEGER, output_tokens INTEGER, estimated_cost_usd REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    con.execute("""CREATE TABLE IF NOT EXISTS jev_decisions (
                 project_id TEXT PRIMARY KEY, model TEXT NOT NULL, project_type_choice TEXT,
                 project_type_confidence REAL, location_choice TEXT, location_confidence REAL,
                 title_choice TEXT, title_confidence REAL, manual_review_probability REAL,
                 public_label TEXT, response_json TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    return con


