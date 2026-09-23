import unittest
from src.build_search_index import PUBLIC_FIELDS, build


class TestSearchIndex(unittest.TestCase):
    def test_only_leaf_rows_and_public_fields(self):
        records = [
            {"id": "summary", "is_leaf": 0, "amount": 99},
            {"id": "leaf", "is_leaf": 1, "amount": 42, "project_title": "Road"},
        ]
        index = build(records)
        self.assertEqual(len(index), 1)
        self.assertEqual(index[0]["id"], "leaf")
        self.assertEqual(tuple(index[0]), PUBLIC_FIELDS)
        self.assertNotIn("raw_text", index[0])
