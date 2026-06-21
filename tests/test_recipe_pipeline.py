import unittest

from core.recipe_recommender import (
    attach_recipe_knowledge,
    get_ingredient_normalization_report,
    load_recipe_knowledge,
    load_recipes,
    recommend_recipes,
)


class RecipePipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = load_recipes()
        cls.knowledge = load_recipe_knowledge()

    def test_ingredient_aliases_are_normalized(self):
        report = get_ingredient_normalization_report("蛋, 青蔥, 蕃茄")
        normalized = {item["normalized"] for item in report}
        self.assertEqual(normalized, {"雞蛋", "蔥", "蕃茄"})
        changes = {item["original"]: item["changed"] for item in report}
        self.assertTrue(changes["蛋"])
        self.assertTrue(changes["青蔥"])
        self.assertFalse(changes["蕃茄"])

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

    def test_recipe_without_complete_trusted_content_is_excluded(self):
        result = recommend_recipes(
            self.recipes,
            "雞蛋, 白飯, 蔥",
            max_time=60,
            difficulty_preference="不限",
            top_n=len(self.recipes),
            max_calories=900,
            max_missing=5,
        )
        target = result.iloc[0]["name"]
        incomplete = self.knowledge.copy()
        incomplete.loc[incomplete["recipe_name"] == target, "steps"] = ""
        enriched = attach_recipe_knowledge(result, incomplete)
        self.assertNotIn(target, set(enriched["name"]))
        self.assertTrue((enriched["knowledge_status"] == "已檢索可信內容").all())

    def test_knowledge_schema_and_ingredients_match_recipe_data(self):
        self.assertEqual(
            list(self.knowledge.columns),
            [
                "ingredient",
                "recipe_name",
                "knowledge_id",
                "steps",
                "tips",
                "source_name",
                "verified_date",
                "產地",
                "有效期限",
            ],
        )
        expected = self.recipes.set_index("name")["ingredients"]
        actual = self.knowledge.set_index("recipe_name")["ingredient"]
        self.assertEqual(actual.to_dict(), expected.to_dict())
        self.assertTrue(self.knowledge["產地"].str.strip().ne("").all())
        self.assertTrue(self.knowledge["有效期限"].str.strip().ne("").all())


if __name__ == "__main__":
    unittest.main()
