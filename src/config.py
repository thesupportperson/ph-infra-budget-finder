import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "budget.sqlite"
JEV_DRY_RUN = os.getenv("JEV_DRY_RUN", "true").lower() == "true"
JEV_BUDGET_USD = float(os.getenv("JEV_BUDGET_USD", "1.00"))
JEV_PRICE_PER_1M_INPUT_TOKENS = float(os.getenv("JEV_PRICE_PER_1M_INPUT_TOKENS", "0.042"))
