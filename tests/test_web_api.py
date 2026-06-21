import os
import tempfile
import unittest

import cv2
import numpy as np

TEST_DATABASE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DATABASE.close()
os.environ["APP_DB_PATH"] = TEST_DATABASE.name

from fastapi.testclient import TestClient

from web_api.emotion import EXPRESSIONS, load_models, predict_expression
from web_api.main import app


class WebApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        os.unlink(TEST_DATABASE.name)

    def test_recommendation_endpoints(self):
        restaurant = self.client.post("/api/recommend/restaurants", json={"scenario": "大學生省錢午餐"})
        self.assertEqual(restaurant.status_code, 200)
        restaurant_data = restaurant.json()
        self.assertGreater(len(restaurant_data["results"]), 0)
        self.assertIn("dashboard", restaurant_data["analysis"])
        self.assertIn("evaluation", restaurant_data["analysis"])
        self.assertGreater(len(restaurant_data["analysis"]["score_breakdown"]), 0)
        self.assertGreater(len(restaurant_data["analysis"]["sensitivity"]), 0)

        recipe = self.client.post(
            "/api/recommend/recipes",
            json={
                "ingredients": [
                    {"name": "蛋", "days_stored": 4, "shelf_life": 14, "price": 60, "perishability": "中"},
                    {"name": "豆腐", "days_stored": 2, "shelf_life": 3, "price": 35, "perishability": "高"},
                ]
            },
        )
        self.assertEqual(recipe.status_code, 200)
        recipe_data = recipe.json()
        self.assertGreater(len(recipe_data["results"]), 0)
        self.assertIn("dashboard", recipe_data["analysis"])
        self.assertIn("evaluation", recipe_data["analysis"])
        self.assertGreater(len(recipe_data["analysis"]["priorities"]), 0)
        self.assertGreater(len(recipe_data["analysis"]["score_breakdown"]), 0)

    def test_recipe_scenarios_apply_real_constraints(self):
        ingredients = [
            {"name": "雞蛋", "days_stored": 4, "shelf_life": 14, "price": 60, "perishability": "中"},
            {"name": "白飯", "days_stored": 1, "shelf_life": 3, "price": 20, "perishability": "中"},
            {"name": "蔥", "days_stored": 3, "shelf_life": 7, "price": 25, "perishability": "高"},
            {"name": "醬油", "days_stored": 30, "shelf_life": 180, "price": 70, "perishability": "低"},
        ]
        home = self.client.post(
            "/api/recommend/recipes", json={"scenario": "宅家不出門", "ingredients": ingredients}
        ).json()
        fitness = self.client.post(
            "/api/recommend/recipes", json={"scenario": "健身低熱量", "ingredients": ingredients}
        ).json()
        self.assertTrue(home["meta"]["effective_only_cookable"])
        self.assertEqual(home["meta"]["effective_max_missing"], 0)
        self.assertEqual(fitness["meta"]["effective_max_calories"], 500)

    def test_register_login_and_favorites(self):
        register = self.client.post(
            "/api/auth/register",
            json={"display_name": "測試使用者", "email": "student@example.com", "password": "secure-pass-123"},
        )
        self.assertEqual(register.status_code, 201)
        self.assertEqual(register.json()["user"]["display_name"], "測試使用者")

        favorite = self.client.post(
            "/api/favorites", json={"kind": "recipe", "item_name": "番茄炒蛋"}
        )
        self.assertEqual(favorite.status_code, 201)
        favorites = self.client.get("/api/favorites")
        self.assertEqual(favorites.status_code, 200)
        self.assertEqual(favorites.json()["favorites"][0]["item_name"], "番茄炒蛋")

        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/api/favorites").status_code, 401)

        login = self.client.post(
            "/api/auth/login",
            json={"email": "student@example.com", "password": "secure-pass-123"},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)

    def test_emotion_endpoint_rejects_image_without_face(self):
        blank = np.zeros((320, 320, 3), dtype=np.uint8)
        _, encoded = cv2.imencode(".jpg", blank)
        response = self.client.post(
            "/api/emotion/analyze",
            files={"image": ("blank.jpg", encoded.tobytes(), "image/jpeg")},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("沒有偵測到", response.json()["detail"])

    def test_ferplus_model_has_eight_probability_outputs(self):
        _, network = load_models()
        expression, confidence, scores = predict_expression(
            network, np.zeros((112, 112, 3), dtype=np.uint8)
        )
        self.assertEqual(len(EXPRESSIONS), 8)
        self.assertEqual(set(scores), set(EXPRESSIONS))
        self.assertIn(expression, EXPRESSIONS)
        self.assertAlmostEqual(sum(scores.values()), 1.0, places=3)
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)


if __name__ == "__main__":
    unittest.main()
