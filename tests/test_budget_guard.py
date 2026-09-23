import unittest
from src.budget_guard import estimated_cost
class TestBudget(unittest.TestCase):
 def test_cost(self): self.assertAlmostEqual(estimated_cost(1_000_000),.042)
