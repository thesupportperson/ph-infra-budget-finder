import unittest
from src.utils import review_label
class TestReview(unittest.TestCase):
 def test_thresholds(self):
  self.assertEqual(review_label(.7),'Needs Manual Review'); self.assertEqual(review_label(.4),'Maybe Review'); self.assertEqual(review_label(.1),'Low Priority'); self.assertEqual(review_label(None),'Unreviewed')
