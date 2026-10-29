import unittest
from pathlib import Path
import app


class AppTest(unittest.TestCase):
    def setUp(self):
        self.old_db = app.DB
        app.DB = Path(__file__).with_name("test_home_buyer.db")
        app.DB.unlink(missing_ok=True)

    def tearDown(self):
        app.DB = self.old_db
        Path(__file__).with_name("test_home_buyer.db").unlink(missing_ok=True)

    def test_save_history_and_score(self):
        item = {"source_url": "https://example.invalid/1", "title": "A", "total_price": 300,
                "unit_price": 40000, "area": 75, "year": 2015, "commute_minutes": 30,
                "school_score": 70, "risk_score": 20}
        first = app.save_listing(item)
        item["total_price"] = 295
        self.assertEqual(first, app.save_listing(item))
        with app.db() as conn:
            self.assertEqual(1, conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0])
            self.assertEqual(295, conn.execute("SELECT total_price FROM listings").fetchone()[0])
        result = app.score(item, {"budget": 320, "max_commute": 45})
        self.assertGreaterEqual(result["score"], 80)
        self.assertEqual("优先看房", result["decision"])

    def test_rejects_bad_listing_and_host(self):
        with self.assertRaises(ValueError):
            app.save_listing({"title": "bad", "total_price": 0, "unit_price": 1, "area": 1})
        with self.assertRaises(ValueError):
            app.collect("https://example.com/house/1")


if __name__ == "__main__":
    unittest.main()
