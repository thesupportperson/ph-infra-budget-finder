import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_local_env():
    """Load developer-only settings without exposing them to the static website."""
    path = ROOT / '.env'
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        if '=' not in line or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip())


load_local_env()
DB_PATH = ROOT / 'data' / 'processed' / 'budget.sqlite'
JEV_DRY_RUN = os.getenv('JEV_DRY_RUN', 'true').lower() == 'true'
JEV_BUDGET_USD = float(os.getenv('JEV_BUDGET_USD', '1.00'))
JEV_PRICE_PER_1M_INPUT_TOKENS = float(os.getenv('JEV_PRICE_PER_1M_INPUT_TOKENS', '0.042'))
JEV_MODEL = os.getenv('JEV_MODEL', 'jev-latest')
TYPESAFE_API_KEY = os.getenv('TYPESAFE_API_KEY', '')
