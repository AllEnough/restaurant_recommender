import pandas as pd


DIFFICULTY_SCORE = {
    "簡單": 20,
    "中等": 12,
    "困難": 5,
}


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
    return {item.strip() for item in normalized.split(",") if item.strip()}


def calculate_recipe_score(row, user_ingredients, max_time, difficulty_preference):
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

    missing_penalty = max(0, len(missing) - int(row["missing_allowed"])) * 5
    score = ingredient_score + time_score + difficulty_score + 10 - missing_penalty

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

    return round(max(score, 0), 2), "、".join(reasons), "、".join(matched), "、".join(missing)


def recommend_recipes(df, ingredient_text, max_time, difficulty_preference, top_n=5):
    user_ingredients = parse_ingredients(ingredient_text)
    results = df.copy()

    scores = results.apply(
        lambda row: calculate_recipe_score(row, user_ingredients, max_time, difficulty_preference),
        axis=1,
    )

    results["score"] = scores.apply(lambda value: value[0])
    results["reason"] = scores.apply(lambda value: value[1])
    results["matched_ingredients"] = scores.apply(lambda value: value[2])
    results["missing_ingredients"] = scores.apply(lambda value: value[3])
    results = results.sort_values(by=["score", "time"], ascending=[False, True])

    return results.head(top_n)


if __name__ == "__main__":
    recipes = load_recipes()
    result = recommend_recipes(recipes, "雞蛋,白飯,蔥", 20, "簡單")
    print(result[["name", "category", "time", "difficulty", "score", "reason"]])
