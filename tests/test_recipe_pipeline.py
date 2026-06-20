import unittest

from recipe_recommender import (
    attach_recipe_knowledge,
    get_ingredient_normalization_report,
    load_recipe_knowledge,
    load_recipes,
    recommend_recipes,
)


class RecipePipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = load_recipes("recipes.csv")
        cls.knowledge = load_recipe_knowledge("recipe_knowledge.csv")

    def test_ingredient_aliases_are_normalized(self):
        report = get_ingredient_normalization_report("蛋, 青蔥, 蕃茄")
        normalized = {item["normalized"] for item in report}
        self.assertEqual(normalized, {"雞蛋", "蔥", "番茄"})
        self.assertTrue(all(item["changed"] for item in report))

    def test_candidate_recall_requires_an_ingredient_overlap(self):
        result = recommend_recipes(
            self.recipes,
            "蛋, 青蔥, 白米飯",
            max_time=30,
            difficulty_preference="不限",
            top_n=len(self.recipes),
            max_calories=900,
            max_missing=5,
        )
        self.assertFalse(result.empty)
        self.assertTrue((result["recall_matches"] > 0).all())
        self.assertTrue((result["recall_strategy"] == "標準化食材交集召回").all())

    def test_recalled_recipes_have_verified_knowledge(self):
        result = recommend_recipes(
            self.recipes,
            "雞蛋, 白飯, 蔥",
            max_time=60,
            difficulty_preference="不限",
            top_n=len(self.recipes),
            max_calories=900,
            max_missing=5,
        )
        enriched = attach_recipe_knowledge(result, self.knowledge)
        self.assertTrue((enriched["knowledge_status"] == "已檢索可信內容").all())
        self.assertTrue(enriched["knowledge_id"].str.startswith("KB-R").all())


if __name__ == "__main__":
    unittest.main()
