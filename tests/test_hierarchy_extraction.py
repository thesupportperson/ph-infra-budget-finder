import unittest
from src.parse_pdf import clean_label, row_level, total_amount_for


class TestHierarchyExtraction(unittest.TestCase):
    def test_rightmost_column_is_the_total(self):
        items = [(351, 100, "66,850,000 37,883,000"), (534, 100, "104,733,000")]
        self.assertEqual(total_amount_for(100, items), 104_733_000)

    def test_clean_label_removes_joined_columns(self):
        self.assertEqual(clean_label("14,324,565,000 General Administration 2,040,000"), "General Administration")

    def test_row_levels_are_explicit(self):
        self.assertEqual(row_level("Region XI - Davao", False), "regional_summary")
        self.assertEqual(row_level("Davao City District Engineering Office", False), "office_allocation")
        self.assertEqual(row_level("100000000000001 Road Works", True), "program_summary")


    def test_interleaved_code_is_a_program_row(self):
        import re
        label = "FLOOD MANAGEMENT PROGRAM 320100000000000"
        code = re.search(r"\d{15}", label)
        title = clean_label(label[:code.start()] + " " + label[code.end():])
        self.assertEqual(title, "FLOOD MANAGEMENT PROGRAM")
        self.assertEqual(row_level(title, True), "program_summary")
if __name__ == "__main__":
    unittest.main()

