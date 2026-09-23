import unittest
from src.classify_jev import public_label


class TestJevLabels(unittest.TestCase):
    def test_unclear_location_label_needs_high_confidence(self):
        answers = {
            'location_clarity': {'choice': 'unclear', 'confidence': 0.9},
            'title_specificity': {'choice': 'specific', 'confidence': 0.9},
            'manual_review': {'noul': 0.1},
        }
        self.assertEqual(public_label(answers), 'Unclear Location')

    def test_low_confidence_does_not_create_public_label(self):
        answers = {
            'location_clarity': {'choice': 'clear', 'confidence': 0.9},
            'title_specificity': {'choice': 'broad', 'confidence': 0.5},
            'manual_review': {'noul': 0.2},
        }
        self.assertEqual(public_label(answers), '')


if __name__ == '__main__':
    unittest.main()
