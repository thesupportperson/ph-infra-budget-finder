from .config import JEV_BUDGET_USD, JEV_PRICE_PER_1M_INPUT_TOKENS

def estimated_cost(input_tokens):
    return input_tokens / 1_000_000 * JEV_PRICE_PER_1M_INPUT_TOKENS

def allowed(spent, next_input_tokens):
    return spent + estimated_cost(next_input_tokens) <= JEV_BUDGET_USD
