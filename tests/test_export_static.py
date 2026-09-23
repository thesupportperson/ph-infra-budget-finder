import unittest
from src.utils import peso
class TestExport(unittest.TestCase):
 def test_peso(self): self.assertEqual(peso(250000000),'₱250,000,000')
