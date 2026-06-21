# my_recipe_rank.py
# 這份是在整理：食材標準化、候選召回、食譜排序
# 報告講法可以是「先找可能可以煮的，再用多個條件排順序」。


ingredient_alias = {
    "雞肉": "雞胸肉",
    "雞胸": "雞胸肉",
    "雞蛋液": "雞蛋",
    "青菜": "高麗菜",
    "青菜葉": "高麗菜",
    "葉菜": "高麗菜",
    "高麗": "高麗菜",
    "蛋": "雞蛋",
    "青蔥": "蔥",
    "蔥花": "蔥",
    "番茄": "蕃茄",
    "洋芋": "馬鈴薯",
    "土豆": "馬鈴薯",
    "紅蘿蔔絲": "紅蘿蔔",
    "胡蘿蔔": "紅蘿蔔",
    "豬肉片": "豬肉",
    "豬肉絲": "豬肉",
    "白米飯": "白飯",
    "米飯": "白飯",
    "意麵": "義大利麵",
}


recipes = [
    {
        "name": "雞胸肉炒高麗菜",
        "ingredients": ["雞胸肉", "高麗菜", "蒜頭"],
        "time": 20,
        "difficulty": "easy",
        "calories": 420,
    },
    {
        "name": "番茄炒蛋",
        "ingredients": ["蕃茄", "雞蛋", "蔥"],
        "time": 12,
        "difficulty": "easy",
        "calories": 300,
    },
    {
        "name": "奶油燉飯",
        "ingredients": ["白飯", "牛奶", "菇類", "起司"],
        "time": 35,
        "difficulty": "middle",
        "calories": 680,
    },
]


def normalize_ingredient(name):
    name = name.strip()
    return ingredient_alias.get(name, name)


def parse_user_ingredients(text):
    parts = text.replace("，", ",").replace("、", ",").split(",")
    return {normalize_ingredient(part) for part in parts if part.strip()}


def _ingredient_set(value):
    if isinstance(value, str):
        return parse_user_ingredients(value)
    return {normalize_ingredient(item) for item in value}


def recall_candidates(user_ingredients, recipe_rows=None):
    candidates = []
    for recipe in recipe_rows or recipes:
        recipe_ingredients = _ingredient_set(recipe["ingredients"])
        matched = recipe_ingredients & user_ingredients
        if matched:
            item = recipe.copy()
            item["matched"] = sorted(matched)
            item["missing"] = sorted(recipe_ingredients - user_ingredients)
            candidates.append(item)
    return candidates


def score_recipe(recipe, max_time=30, max_calories=600):
    total_ingredients = len(_ingredient_set(recipe["ingredients"]))
    matched_count = len(recipe["matched"])
    missing_count = len(recipe["missing"])

    ingredient_score = matched_count/total_ingredients*50
    time_score = 20 if recipe["time"] <= max_time else max(0,20 - (recipe["time"] - max_time))
    difficulty_score = 15 if recipe["difficulty"] == "easy" else 10
    calorie_score = 10 if recipe["calories"] <= max_calories else 4
    missing_penalty = missing_count*4

    final_score = ingredient_score + time_score + difficulty_score + calorie_score - missing_penalty

    recipe["score"] = round(final_score,1)
    recipe["ingredient_score"] = round(ingredient_score,1)
    recipe["time_score"] = round(time_score, 1)
    recipe["difficulty_score"] = round(difficulty_score, 1)
    recipe["calorie_score"] = round(calorie_score, 1)
    recipe["missing_penalty"] = round(missing_penalty, 1)
    recipe["missing_count"] = missing_count
    return recipe


def recommend_recipes(user_text, recipe_rows=None, max_time=30, max_calories=600):
    user_ingredients = parse_user_ingredients(user_text)
    candidates = recall_candidates(user_ingredients, recipe_rows)
    scored = [score_recipe(recipe, max_time=max_time, max_calories=max_calories) for recipe in candidates]

    #食材符合度、時間、難度、熱量、缺少食材一起看
    return sorted(
        scored,
        key=lambda item: (item["score"], -item["time"],-item["missing_count"]),
        reverse=True,
    )


def main():
    user_text = "雞肉, 青菜, 蛋"
    result = recommend_recipes(user_text)

    print("使用者食材：",user_text)
    print()
    for index, recipe in enumerate(result, start=1):
        print(index, recipe["name"])
        print("  分數：",recipe["score"])
        print("  符合食材：",", ".join(recipe["matched"]))
        print("  缺少食材：",", ".join(recipe["missing"]))
        print()


if __name__ == "__main__":
    main()
