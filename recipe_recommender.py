import pandas as pd

from recipe_rank import (
    normalize_ingredient as core_normalize_ingredient,
    parse_user_ingredients,
    recall_candidates as core_recall_candidates,
    score_recipe as core_score_recipe,
)


def normalize_ingredient(value):
    return core_normalize_ingredient(str(value).lower())


def load_recipes(file_path="recipes.csv"):
    df = pd.read_csv(file_path)
    numeric_columns = ["missing_allowed", "time", "calories"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.dropna(subset=numeric_columns)


def parse_ingredients(text):
    if not text:
        return set()
    return parse_user_ingredients(str(text).replace(" ", ",").replace("\n", ","))


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
    core_row = row.to_dict()
    core_row["ingredients"] = sorted(recipe_ingredients)
    core_row["matched"] = matched
    core_row["missing"] = missing
    core_row["difficulty"] = {"簡單": "easy", "中等": "middle", "困難": "hard"}.get(
        row["difficulty"], str(row["difficulty"]).lower()
    )
    scored = core_score_recipe(
        core_row,
        max_time=max_time,
        max_calories=max_calories if max_calories is not None else 10**9,
    )
    match_ratio = len(matched) / len(recipe_ingredients) if recipe_ingredients else 0

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
        "score": round(max(scored["score"], 0), 2),
        "reason": "、".join(reasons),
        "matched_ingredients": "、".join(matched),
        "missing_ingredients": "、".join(missing),
        "matched_count": len(matched),
        "missing_count": len(missing),
        "recall_score": round(match_ratio * 100, 1),
        "ingredient_score": scored["ingredient_score"],
        "time_score": scored["time_score"],
        "difficulty_score": scored["difficulty_score"],
        "calorie_score": scored["calorie_score"],
        "missing_penalty": scored["missing_penalty"],
    }


def recall_recipe_candidates(df, user_ingredients):
    recalled = core_recall_candidates(user_ingredients, df.to_dict("records"))
    candidates = pd.DataFrame(recalled, columns=[*df.columns, "matched", "missing"])
    if candidates.empty:
        candidates["recall_matches"] = pd.Series(dtype=int)
        candidates["recall_strategy"] = pd.Series(dtype=str)
        return candidates
    candidates["recall_matches"] = candidates["matched"].apply(len)
    candidates["recall_strategy"] = "標準化食材交集召回"
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
    if knowledge["recipe_name"].duplicated().any():
        duplicates = sorted(knowledge.loc[knowledge["recipe_name"].duplicated(), "recipe_name"].unique())
        raise ValueError(f"食譜知識庫包含重複食譜：{', '.join(duplicates)}")
    if knowledge["knowledge_id"].duplicated().any():
        duplicates = sorted(knowledge.loc[knowledge["knowledge_id"].duplicated(), "knowledge_id"].unique())
        raise ValueError(f"食譜知識庫包含重複內容編號：{', '.join(duplicates)}")
    trusted_columns = ["recipe_name", "knowledge_id", "steps", "source_name", "verified_date"]
    blank_rows = knowledge[trusted_columns].apply(lambda column: column.str.strip().eq("")).any(axis=1)
    if blank_rows.any():
        rows = ", ".join(str(index + 2) for index in knowledge.index[blank_rows])
        raise ValueError(f"食譜知識庫可信來源欄位不可空白，CSV 列：{rows}")
    return knowledge


def attach_recipe_knowledge(results, knowledge):
    if results.empty:
        return results.copy()
    enriched = results.merge(
        knowledge,
        how="left",
        left_on="name",
        right_on="recipe_name",
        validate="many_to_one",
    )
    trusted_columns = ["knowledge_id", "steps", "source_name", "verified_date"]
    trusted = enriched[trusted_columns].apply(lambda column: column.astype(str).str.strip().ne("")).all(axis=1)
    enriched["knowledge_status"] = trusted.map(
        {True: "已檢索可信內容", False: "缺少可信內容"}
    )
    enriched = enriched[trusted].copy()
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
    if difficulty_preference != "不限":
        results = results[results["difficulty"] == difficulty_preference]

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
    if results.empty:
        for column in score_columns:
            results[column] = pd.Series(dtype=float if column.endswith("score") or column.endswith("count") else str)
        return results

    scores = results.apply(
        lambda row: calculate_recipe_score(row, user_ingredients, max_time, difficulty_preference, max_calories),
        axis=1,
    )

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
