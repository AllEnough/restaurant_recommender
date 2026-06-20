import pandas as pd


DIFFICULTY_SCORE = {
    "簡單": 20,
    "中等": 12,
    "困難": 5,
}


INGREDIENT_ALIASES = {
    "蛋": "雞蛋",
    "雞蛋液": "雞蛋",
    "青蔥": "蔥",
    "蔥花": "蔥",
    "青菜葉": "青菜",
    "葉菜": "青菜",
    "高麗": "高麗菜",
    "洋芋": "馬鈴薯",
    "土豆": "馬鈴薯",
    "紅蘿蔔絲": "紅蘿蔔",
    "胡蘿蔔": "紅蘿蔔",
    "蕃茄": "番茄",
    "豬肉片": "豬肉",
    "豬肉絲": "豬肉",
    "雞胸": "雞胸肉",
    "白米飯": "白飯",
    "米飯": "白飯",
    "意麵": "義大利麵",
}


def normalize_ingredient(value):
    ingredient = str(value).strip().lower()
    return INGREDIENT_ALIASES.get(ingredient, ingredient)


def load_recipes(file_path="recipes.csv"):
    df = pd.read_csv(file_path)
    numeric_columns = ["missing_allowed", "time", "calories"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.dropna(subset=numeric_columns)


def parse_ingredients(text):
    if not text:
        return set()
    separators = [",", "，", "、", " ", "\n"]
    normalized = str(text)
    for separator in separators[1:]:
        normalized = normalized.replace(separator, separators[0])
    return {normalize_ingredient(item) for item in normalized.split(",") if item.strip()}


def get_ingredient_normalization_report(text):
    if not text:
        return []
    separators = [",", "，", "、", " ", "\n"]
    raw_text = str(text)
    for separator in separators[1:]:
        raw_text = raw_text.replace(separator, separators[0])

    report = []
    seen = set()
    for raw_item in raw_text.split(","):
        original = raw_item.strip()
        if not original:
            continue
        normalized = normalize_ingredient(original)
        key = (original, normalized)
        if key not in seen:
            report.append({"original": original, "normalized": normalized, "changed": original.lower() != normalized})
            seen.add(key)
    return report


def collect_ingredient_options(df):
    ingredients = set()
    for value in df["ingredients"]:
        ingredients.update(parse_ingredients(value))
    return sorted(ingredients)


def calculate_recipe_score(row, user_ingredients, max_time, difficulty_preference, max_calories=None):
    recipe_ingredients = parse_ingredients(row["ingredients"])
    matched = sorted(recipe_ingredients & user_ingredients)
    missing = sorted(recipe_ingredients - user_ingredients)

    if not recipe_ingredients:
        match_ratio = 0
    else:
        match_ratio = len(matched) / len(recipe_ingredients)

    ingredient_score = match_ratio * 50

    if row["time"] <= max_time:
        time_score = 20
    else:
        over_time = row["time"] - max_time
        time_score = max(0, 20 - over_time * 1.5)

    if difficulty_preference == "不限":
        difficulty_score = DIFFICULTY_SCORE.get(row["difficulty"], 10)
    elif row["difficulty"] == difficulty_preference:
        difficulty_score = 20
    else:
        difficulty_score = 8

    calorie_score = 10
    if max_calories is not None and row["calories"] > max_calories:
        calorie_score = max(0, 10 - ((row["calories"] - max_calories) / 50))

    missing_penalty = max(0, len(missing) - int(row["missing_allowed"])) * 5
    score = ingredient_score + time_score + difficulty_score + calorie_score - missing_penalty

    reasons = []
    if matched:
        reasons.append(f"符合食材：{'、'.join(matched)}")
    if missing:
        reasons.append(f"缺少食材：{'、'.join(missing)}")
    else:
        reasons.append("現有食材已足夠")
    if row["time"] <= max_time:
        reasons.append("烹飪時間符合需求")
    if difficulty_preference == "不限" or row["difficulty"] == difficulty_preference:
        reasons.append("難度符合偏好")
    if max_calories is not None and row["calories"] <= max_calories:
        reasons.append("熱量符合需求")

    return {
        "score": round(max(score, 0), 2),
        "reason": "、".join(reasons),
        "matched_ingredients": "、".join(matched),
        "missing_ingredients": "、".join(missing),
        "matched_count": len(matched),
        "missing_count": len(missing),
        "recall_score": round(match_ratio * 100, 1),
        "ingredient_score": round(ingredient_score, 1),
        "time_score": round(time_score, 1),
        "difficulty_score": round(difficulty_score, 1),
        "calorie_score": round(calorie_score, 1),
        "missing_penalty": round(missing_penalty, 1),
    }


def recall_recipe_candidates(df, user_ingredients):
    candidates = df.copy()
    candidates["recall_matches"] = candidates["ingredients"].apply(
        lambda value: len(parse_ingredients(value) & user_ingredients)
    )
    if user_ingredients and (candidates["recall_matches"] > 0).any():
        candidates = candidates[candidates["recall_matches"] > 0]
        candidates["recall_strategy"] = "標準化食材交集召回"
    else:
        candidates["recall_strategy"] = "條件式全庫備援召回"
    return candidates


def load_recipe_knowledge(file_path="recipe_knowledge.csv"):
    knowledge = pd.read_csv(file_path, dtype=str).fillna("")
    required_columns = {
        "ingredient",
        "recipe_name",
        "knowledge_id",
        "steps",
        "tips",
        "source_name",
        "verified_date",
        "產地",
        "有效期限",
    }
    missing = required_columns - set(knowledge.columns)
    if missing:
        raise ValueError(f"食譜知識庫缺少欄位：{', '.join(sorted(missing))}")
    return knowledge


def attach_recipe_knowledge(results, knowledge):
    if results.empty:
        return results.copy()
    enriched = results.merge(knowledge, how="left", left_on="name", right_on="recipe_name")
    enriched["knowledge_status"] = enriched["knowledge_id"].apply(
        lambda value: "已檢索可信內容" if str(value).strip() else "缺少可信內容"
    )
    return enriched.drop(columns=["recipe_name"], errors="ignore")


def recommend_recipes(
    df,
    ingredient_text,
    max_time,
    difficulty_preference,
    top_n=5,
    max_calories=None,
    max_missing=None,
    only_cookable=False,
):
    user_ingredients = parse_ingredients(ingredient_text)
    results = recall_recipe_candidates(df, user_ingredients)

    scores = results.apply(
        lambda row: calculate_recipe_score(row, user_ingredients, max_time, difficulty_preference, max_calories),
        axis=1,
    )

    score_columns = [
        "score",
        "reason",
        "matched_ingredients",
        "missing_ingredients",
        "matched_count",
        "missing_count",
        "recall_score",
        "ingredient_score",
        "time_score",
        "difficulty_score",
        "calorie_score",
        "missing_penalty",
    ]
    for column in score_columns:
        results[column] = scores.apply(lambda value, key=column: value[key])

    if max_calories is not None:
        results = results[results["calories"] <= max_calories]
    if max_missing is not None:
        results = results[results["missing_count"] <= max_missing]
    if only_cookable:
        results = results[results["missing_count"] == 0]

    results = results.sort_values(
        by=["score", "recall_score", "matched_count", "time"],
        ascending=[False, False, False, True],
    )
    return results.head(top_n)


if __name__ == "__main__":
    recipes = load_recipes()
    result = recommend_recipes(recipes, "雞蛋,白飯,蔥", 20, "簡單", max_calories=650, max_missing=2)
    print(result[["name", "category", "time", "difficulty", "score", "reason"]])
