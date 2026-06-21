import unittest
from types import SimpleNamespace

from ingredient import calculate_priority as core_calculate_priority
from recipe_rank import parse_user_ingredients, recommend_recipes as core_recommend_recipes
from review_analyzer import analyze_reviews
from review_score import analyze_restaurant_reviews
from web_api.services import calculate_priority

import pandas as pd


class TeamModuleIntegrationTest(unittest.TestCase):
    def test_review_analyzer_uses_review_score_result(self):
        texts = ["好吃又便宜", "等很久而且太鹹"]
        core = analyze_restaurant_reviews("測試餐廳", texts)
        frame = pd.DataFrame(
            {"restaurant_name": ["測試餐廳"] * len(texts), "review_text": texts}
        )
        integrated = analyze_reviews(frame).iloc[0]
        self.assertEqual(integrated["sentiment_score"], core["sentiment_score"])
        self.assertEqual(integrated["negative_ratio"], core["negative_ratio"])
        self.assertEqual(integrated["review_adjustment"], core["risk_adjustment"])

    def test_recipe_pipeline_uses_recipe_rank_aliases_and_formula(self):
        self.assertEqual(parse_user_ingredients("雞肉, 青菜, 蛋"), {"雞胸肉", "高麗菜", "雞蛋"})
        result = core_recommend_recipes("雞肉, 青菜, 蛋")
        self.assertEqual(result[0]["name"], "雞胸肉炒高麗菜")
        self.assertIn("ingredient_score", result[0])

    def test_priority_wrapper_matches_ingredient_core(self):
        source = {
            "name": "豆腐",
            "days_stored": 2,
            "shelf_life": 3,
            "price": 35,
            "perishability": "high",
        }
        core = core_calculate_priority(source)
        integrated = calculate_priority(
            SimpleNamespace(
                name="豆腐",
                days_stored=2,
                shelf_life=3,
                price=35,
                perishability="高",
            )
        )
        self.assertEqual(integrated["priority_score"], core["priority_score"])
        self.assertEqual(integrated["scheduling_ratio"], core["scheduling_ratio"])
        self.assertEqual(integrated["level"], "中")


if __name__ == "__main__":
    unittest.main()
