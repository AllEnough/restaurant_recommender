"""智慧飲食決策系統核心演算法的簡化展示版。

執行方式：
    python3 report/algorithm_examples.py

此檔案只保留報告時需要說明的分數計算；正式網站另包含篩選、
資料清理、API 驗證、情境規則與錯誤處理。
"""

from __future__ import annotations


RESTAURANT_WEIGHTS = {
    "rating": 25,
    "price": 20,
    "distance": 15,
    "category": 10,
    "context": 10,
    "takeout": 5,
    "spicy": 5,
    "speed": 10,
}


def restaurant_score(restaurant: dict, user: dict) -> dict:
    """計算外食基礎分數，再加入評論與情境意圖調整。"""
    parts = {}
    parts["rating"] = restaurant["rating"] / 5 * RESTAURANT_WEIGHTS["rating"]
    parts["price"] = (
        RESTAURANT_WEIGHTS["price"]
        if restaurant["price"] <= user["budget"]
        else max(0, RESTAURANT_WEIGHTS["price"] - (restaurant["price"] - user["budget"]) * 0.2)
    )
    parts["distance"] = (
        RESTAURANT_WEIGHTS["distance"]
        if restaurant["distance"] <= user["max_distance"]
        else max(0, RESTAURANT_WEIGHTS["distance"] - (restaurant["distance"] - user["max_distance"]) * 2)
    )
    parts["category"] = (
        RESTAURANT_WEIGHTS["category"]
        if user["category"] == "不限" or restaurant["category"] == user["category"]
        else 0
    )
    parts["context"] = 5 * int(restaurant["weather"] == user["weather"])
    parts["context"] += 5 * int(restaurant["mood"] == user["mood"])
    parts["takeout"] = RESTAURANT_WEIGHTS["takeout"] * int(restaurant["takeout"])
    parts["spicy"] = (
        RESTAURANT_WEIGHTS["spicy"]
        if restaurant["spicy_level"] <= user["max_spicy_level"]
        else -(restaurant["spicy_level"] - user["max_spicy_level"]) * 3
    )
    parts["speed"] = RESTAURANT_WEIGHTS["speed"] if restaurant["serve_speed"] == "快" else 5

    base_score = min(max(sum(parts.values()), 0), 100)
    review_adjustment = max(
        min((restaurant["sentiment_score"] - 50) * 0.16 - restaurant["negative_ratio"] * 0.08, 10),
        -12,
    )

    intent_adjustment = 0.0
    if user["intent"] == "省錢":
        cp_score = min(restaurant["rating"] / restaurant["price"] * 1600, 100)
        intent_adjustment += min(cp_score / 10, 10)
        intent_adjustment += max(0, (140 - restaurant["price"]) / 20)
    elif user["intent"] == "不踩雷":
        intent_adjustment += max(0, (restaurant["rating"] - 4.0) * 10)
        intent_adjustment += max(0, (40 - restaurant["negative_ratio"]) / 4)
    intent_adjustment = max(min(intent_adjustment, 18), -12)

    final_score = min(
        max(base_score + review_adjustment * user["review_weight"] + intent_adjustment, 0),
        135,
    )
    return {
        "name": restaurant["name"],
        "base_score": round(base_score, 1),
        "review_adjustment": round(review_adjustment * user["review_weight"], 1),
        "intent_adjustment": round(intent_adjustment, 1),
        "final_score": round(final_score, 1),
    }


def ingredient_priority(ingredient: dict) -> dict:
    """依保存進度、價格與易腐程度計算食材使用優先級。"""
    shelf_life = max(ingredient["shelf_life"], 1)
    days_stored = max(ingredient["days_stored"], 0)
    remaining_days = max(shelf_life - days_stored, 0)

    expiry_score = min(days_stored / shelf_life, 1) * 45
    expiry_score += {0: 30, 1: 22, 2: 14}.get(remaining_days, 0)
    price_score = min(ingredient["price"] / 150, 1) * 20
    perishability_score = {"低": 5, "中": 10, "高": 15}[ingredient["perishability"]]
    priority_score = min(expiry_score + price_score + perishability_score, 100)

    waste_cost = ingredient["price"] * {"低": 0.8, "中": 1.0, "高": 1.25}[ingredient["perishability"]]
    scheduling_ratio = waste_cost / (remaining_days + 1)
    return {
        **ingredient,
        "remaining_days": remaining_days,
        "priority_score": round(priority_score, 1),
        "scheduling_ratio": round(scheduling_ratio, 2),
    }


def recipe_score(recipe: dict, owned: set[str], priorities: dict[str, dict]) -> dict:
    """整合食材符合度、限制條件與保存優先級。"""
    required = set(recipe["ingredients"])
    matched = required & owned
    missing = required - owned

    ingredient_score = len(matched) / len(required) * 50
    time_score = 20 if recipe["time"] <= 30 else max(0, 20 - (recipe["time"] - 30) * 1.5)
    difficulty_score = {"簡單": 20, "普通": 14, "困難": 8}[recipe["difficulty"]]
    calorie_score = 10 if recipe["calories"] <= 600 else max(0, 10 - (recipe["calories"] - 600) / 50)
    missing_penalty = max(0, len(missing) - recipe["missing_allowed"]) * 5
    base_score = ingredient_score + time_score + difficulty_score + calorie_score - missing_penalty

    used_priority = sum(priorities[name]["priority_score"] for name in matched)
    high_priority_count = sum(priorities[name]["priority_score"] >= 75 for name in matched)
    priority_bonus = min(used_priority / 8 + high_priority_count * 5, 25)
    return {
        "name": recipe["name"],
        "matched": "、".join(sorted(matched)),
        "missing": "、".join(sorted(missing)) or "無",
        "base_score": round(base_score, 1),
        "priority_bonus": round(priority_bonus, 1),
        "final_score": round(min(max(base_score + priority_bonus, 0), 125), 1),
    }


def print_ranking(title: str, rows: list[dict], score_key: str) -> None:
    print(f"\n{title}")
    for rank, row in enumerate(sorted(rows, key=lambda item: item[score_key], reverse=True), start=1):
        print(f"{rank}. {row}")


def main() -> None:
    user = {
        "budget": 150,
        "max_distance": 10,
        "category": "不限",
        "weather": "熱",
        "mood": "省錢",
        "max_spicy_level": 2,
        "intent": "省錢",
        "review_weight": 0.6,
    }
    restaurants = [
        {"name": "校門口便當", "rating": 4.0, "price": 95, "distance": 3, "category": "便當", "weather": "熱", "mood": "省錢", "takeout": True, "spicy_level": 1, "serve_speed": "快", "sentiment_score": 76, "negative_ratio": 10},
        {"name": "學生火鍋", "rating": 4.4, "price": 190, "distance": 8, "category": "火鍋", "weather": "冷", "mood": "開心", "takeout": False, "spicy_level": 3, "serve_speed": "中", "sentiment_score": 62, "negative_ratio": 28},
    ]
    print_ranking("外食推薦排名", [restaurant_score(row, user) for row in restaurants], "final_score")

    ingredients = [
        {"name": "雞蛋", "days_stored": 12, "shelf_life": 14, "price": 60, "perishability": "中"},
        {"name": "豆腐", "days_stored": 2, "shelf_life": 3, "price": 35, "perishability": "高"},
        {"name": "蔥", "days_stored": 3, "shelf_life": 7, "price": 25, "perishability": "高"},
    ]
    priority_rows = [ingredient_priority(item) for item in ingredients]
    print_ranking("食材使用優先順序", priority_rows, "scheduling_ratio")
    priorities = {row["name"]: row for row in priority_rows}

    recipes = [
        {"name": "雞蛋豆腐煎", "ingredients": ["雞蛋", "豆腐", "醬油"], "time": 12, "difficulty": "簡單", "calories": 360, "missing_allowed": 1},
        {"name": "蔥花蛋餅", "ingredients": ["雞蛋", "蔥", "麵粉", "牛奶"], "time": 18, "difficulty": "普通", "calories": 420, "missing_allowed": 2},
    ]
    owned = set(priorities)
    print_ranking("食譜混合推薦排名", [recipe_score(row, owned, priorities) for row in recipes], "final_score")


if __name__ == "__main__":
    main()
