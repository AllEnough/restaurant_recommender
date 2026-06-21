from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from ingredient import calculate_priority as core_calculate_priority
from recommender import load_data, recommend_restaurants
from recipe_rank import normalize_ingredient as normalize_core_ingredient
from recipe_recommender import (
    attach_recipe_knowledge,
    collect_ingredient_options,
    get_ingredient_normalization_report,
    load_recipe_knowledge,
    load_recipes,
    parse_ingredients,
    recommend_recipes,
)
from review_analyzer import analyze_reviews, load_reviews, merge_review_analysis


ROOT = Path(__file__).resolve().parent.parent

RESTAURANT_SCENARIOS = {
    "手動自訂": {"smart_mode": "自訂"},
    "大學生省錢午餐": {
        "smart_mode": "省錢外食",
        "required_categories": ["便當", "飯類", "麵食", "水餃", "鍋貼", "小吃", "素食"],
    },
    "上班族快速外帶": {
        "smart_mode": "快速午餐",
        "required_categories": ["便當", "飯類", "麵食", "水餃", "鍋貼", "輕食"],
    },
    "老師聚餐不踩雷": {
        "smart_mode": "不想踩雷",
        "required_categories": ["日式", "義式", "火鍋", "鐵板燒", "美式", "韓式", "泰式", "港式"],
    },
}

RECIPE_SCENARIOS = {
    "手動自訂": "自訂",
    "宅家不出門": "我不想出門",
    "清冰箱減浪費": "清冰箱模式",
    "健身低熱量": "低熱量",
}


def serializable_records(frame: pd.DataFrame) -> list[dict]:
    clean = frame.copy().where(pd.notna(frame), None)
    return clean.to_dict(orient="records")


def top_overlap(first: pd.DataFrame, second: pd.DataFrame, top_n: int) -> float:
    first_names = set(first.head(top_n)["name"].tolist())
    second_names = set(second.head(top_n)["name"].tolist())
    if not first_names:
        return 0.0
    return round(len(first_names & second_names) / len(first_names) * 100, 1)


def restaurant_analysis(
    baseline: pd.DataFrame,
    enhanced: pd.DataFrame,
    displayed: pd.DataFrame,
    top_n: int,
    review_weight: int,
) -> dict:
    baseline_top = baseline.head(top_n)
    enhanced_top = enhanced.head(top_n)
    baseline_ranks = {name: index + 1 for index, name in enumerate(baseline["name"].tolist())}
    enhanced_ranks = {name: index + 1 for index, name in enumerate(enhanced["name"].tolist())}
    comparison = []
    for name in dict.fromkeys(baseline_top["name"].tolist() + enhanced_top["name"].tolist()):
        row = enhanced[enhanced["name"] == name]
        if row.empty:
            row = baseline[baseline["name"] == name]
        item = row.iloc[0]
        comparison.append(
            {
                "name": name,
                "baseline_rank": baseline_ranks.get(name),
                "enhanced_rank": enhanced_ranks.get(name),
                "rank_change": baseline_ranks.get(name, len(baseline) + 1) - enhanced_ranks.get(name, len(enhanced) + 1),
                "base_score": round(float(item.get("score", 0)), 1),
                "final_score": round(float(item.get("final_score", item.get("score", 0))), 1),
                "negative_ratio": round(float(item.get("negative_ratio", 0)), 1),
            }
        )

    risk_counts = enhanced["review_risk"].value_counts().to_dict() if "review_risk" in enhanced else {}
    sensitivity = []
    strategies = [
        ("目前綜合排序", "final_score", False),
        ("省錢優先", "cp_score", False),
        ("距離優先", "distance", True),
        ("評分優先", "rating", False),
        ("口碑優先", "sentiment_score", False),
        ("低負評優先", "negative_ratio", True),
    ]
    for label, column, ascending in strategies:
        if column in enhanced and not enhanced.empty:
            winner = enhanced.sort_values(column, ascending=ascending).iloc[0]
            sensitivity.append({"strategy": label, "winner": winner["name"], "value": round(float(winner[column]), 1)})

    score_breakdown = []
    for _, row in displayed.iterrows():
        score_breakdown.append(
            {
                "name": row["name"],
                "base_score": round(float(row.get("score", 0)), 1),
                "review_adjustment": round(float(row.get("review_adjustment", 0)) * review_weight / 100, 1),
                "intent_adjustment": round(float(row.get("intent_adjustment", 0)), 1),
                "final_score": round(float(row.get("final_score", row.get("score", 0))), 1),
            }
        )

    return {
        "dashboard": {
            "candidate_count": len(enhanced),
            "average_negative_ratio": round(float(enhanced_top["negative_ratio"].mean()), 1) if not enhanced_top.empty else 0,
            "low_risk_count": int((enhanced["review_risk"] == "低").sum()) if "review_risk" in enhanced else 0,
            "average_final_score": round(float(enhanced_top["final_score"].mean()), 1) if not enhanced_top.empty else 0,
        },
        "evaluation": {
            "top_overlap": top_overlap(baseline, enhanced, top_n),
            "baseline_average_negative": round(float(baseline_top["negative_ratio"].mean()), 1) if not baseline_top.empty else 0,
            "enhanced_average_negative": round(float(enhanced_top["negative_ratio"].mean()), 1) if not enhanced_top.empty else 0,
            "first_changed": bool(not baseline_top.empty and not enhanced_top.empty and baseline_top.iloc[0]["name"] != enhanced_top.iloc[0]["name"]),
            "comparison": comparison,
        },
        "risk_distribution": {str(key): int(value) for key, value in risk_counts.items()},
        "score_breakdown": score_breakdown,
        "sensitivity": sensitivity,
    }


def recipe_analysis(
    baseline: pd.DataFrame,
    enhanced: pd.DataFrame,
    displayed: pd.DataFrame,
    priorities: list[dict],
    normalization: list[dict],
    top_n: int,
) -> dict:
    baseline_top = baseline.head(top_n)
    enhanced_top = enhanced.head(top_n)
    baseline_ranks = {name: index + 1 for index, name in enumerate(baseline["name"].tolist())}
    enhanced_ranks = {name: index + 1 for index, name in enumerate(enhanced["name"].tolist())}
    comparison = []
    for name in dict.fromkeys(baseline_top["name"].tolist() + enhanced_top["name"].tolist()):
        row = enhanced[enhanced["name"] == name]
        if row.empty:
            row = baseline[baseline["name"] == name]
        item = row.iloc[0]
        comparison.append(
            {
                "name": name,
                "baseline_rank": baseline_ranks.get(name),
                "enhanced_rank": enhanced_ranks.get(name),
                "rank_change": baseline_ranks.get(name, len(baseline) + 1) - enhanced_ranks.get(name, len(enhanced) + 1),
                "base_score": round(float(item.get("score", 0)), 1),
                "final_score": round(float(item.get("final_score", item.get("score", 0))), 1),
                "missing_count": int(item.get("missing_count", 0)),
            }
        )

    score_breakdown = []
    for _, row in displayed.iterrows():
        score_breakdown.append(
            {
                "name": row["name"],
                "ingredient_score": round(float(row.get("ingredient_score", 0)), 1),
                "time_score": round(float(row.get("time_score", 0)), 1),
                "difficulty_score": round(float(row.get("difficulty_score", 0)), 1),
                "calorie_score": round(float(row.get("calorie_score", 0)), 1),
                "missing_penalty": round(float(row.get("missing_penalty", 0)), 1),
                "priority_bonus": round(float(row.get("priority_bonus", 0)), 1),
                "final_score": round(float(row.get("final_score", 0)), 1),
            }
        )

    coverage = int((displayed["knowledge_status"] == "已檢索可信內容").sum()) if "knowledge_status" in displayed else 0
    high_priority_names = {row["ingredient"] for row in priorities if row["level"] == "高"}
    high_priority_usage = sum(
        any(name in high_priority_names for name in parse_ingredients(value))
        for value in enhanced_top.get("priority_ingredients", pd.Series(dtype=str))
    )
    return {
        "dashboard": {
            "candidate_count": len(enhanced),
            "cookable_count": int((enhanced["missing_count"] == 0).sum()) if "missing_count" in enhanced else 0,
            "average_missing_count": round(float(enhanced_top["missing_count"].mean()), 1) if not enhanced_top.empty else 0,
            "average_priority_bonus": round(float(enhanced_top["priority_bonus"].mean()), 1) if not enhanced_top.empty else 0,
        },
        "evaluation": {
            "top_overlap": top_overlap(baseline, enhanced, top_n),
            "baseline_average_missing": round(float(baseline_top["missing_count"].mean()), 1) if not baseline_top.empty else 0,
            "enhanced_average_missing": round(float(enhanced_top["missing_count"].mean()), 1) if not enhanced_top.empty else 0,
            "high_priority_usage": int(high_priority_usage),
            "comparison": comparison,
        },
        "score_breakdown": score_breakdown,
        "priorities": priorities,
        "normalization": normalization,
        "knowledge_coverage": {"covered": coverage, "total": len(displayed)},
    }


def haversine_minutes(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    meters = radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))
    return round(max(meters / 80, 1), 1)


def apply_location(frame: pd.DataFrame, latitude: float | None, longitude: float | None) -> pd.DataFrame:
    if latitude is None or longitude is None:
        return frame
    result = frame.copy()
    result["distance"] = result.apply(
        lambda row: haversine_minutes(latitude, longitude, row["latitude"], row["longitude"]),
        axis=1,
    )
    return result


def apply_review_adjustment(result: pd.DataFrame, enabled: bool, weight: int) -> pd.DataFrame:
    result = result.copy()
    if not enabled or result.empty:
        result["final_score"] = result["score"]
        return result
    result["final_score"] = (
        result["score"] + result["review_adjustment"] * (weight / 100)
    ).clip(0, 110).round(1)
    return result.sort_values(
        by=["final_score", "sentiment_score", "score", "rating"],
        ascending=[False, False, False, False],
    )


def apply_intent_adjustment(result: pd.DataFrame, intent: str) -> pd.DataFrame:
    result = result.copy()
    adjustments = []
    for _, row in result.iterrows():
        adjustment = 0.0
        if intent in ("省錢外食", "大學生省錢午餐"):
            adjustment += min(float(row.get("cp_score", 0)) / 10, 10)
            adjustment += max(0, (140 - float(row["price"])) / 20)
            if row["category"] in ["便當", "飯類", "麵食", "水餃", "鍋貼", "素食"]:
                adjustment += 3
        elif intent in ("快速午餐", "疲累近距離", "上班族快速外帶"):
            adjustment += max(0, (10 - float(row["distance"])) * 1.6)
            adjustment += {"快": 7, "中": 3}.get(row["serve_speed"], 0)
            adjustment += 5 if row["takeout"] == "yes" else 0
        elif intent in ("不想踩雷", "老師聚餐不踩雷"):
            adjustment += max(0, (float(row["rating"]) - 4.0) * 10)
            adjustment += max(0, (40 - float(row.get("negative_ratio", 40))) / 4)
            adjustment += 5 if row.get("review_risk") == "低" else 0
            adjustment -= 8 if row.get("review_risk") == "高" else 0
        adjustments.append(round(max(min(adjustment, 18), -12), 1))
    result["intent_adjustment"] = adjustments
    result["final_score"] = (result["final_score"] + result["intent_adjustment"]).clip(0, 135).round(1)
    return result.sort_values(
        by=["final_score", "intent_adjustment", "score", "rating"],
        ascending=[False, False, False, False],
    )


def restaurant_options() -> dict:
    restaurants = load_data(ROOT / "restaurants.csv")
    return {
        "categories": sorted(restaurants["category"].unique().tolist()),
        "scenarios": list(RESTAURANT_SCENARIOS),
        "smart_modes": ["自訂", "快速午餐", "省錢外食", "不想踩雷", "疲累近距離"],
    }


def recommend_restaurant_payload(payload) -> dict:
    restaurants = apply_location(
        load_data(ROOT / "restaurants.csv"), payload.latitude, payload.longitude
    )
    scenario = RESTAURANT_SCENARIOS.get(payload.scenario, RESTAURANT_SCENARIOS["手動自訂"])
    candidate_data = restaurants
    required = scenario.get("required_categories", [])
    if required:
        candidate_data = candidate_data[candidate_data["category"].isin(required)]

    candidates = recommend_restaurants(
        candidate_data,
        payload.budget,
        payload.max_distance,
        payload.category,
        payload.weather,
        payload.mood,
        payload.need_takeout,
        payload.max_spicy_level,
        payload.prefer_fast,
        len(candidate_data),
        payload.sort_by,
        payload.min_rating,
        payload.meal_time,
    )
    reviews = analyze_reviews(load_reviews(ROOT / "reviews.csv"))
    result = merge_review_analysis(candidates, reviews)
    if payload.use_review_analysis:
        result = result[result["negative_ratio"] <= payload.max_negative_ratio]
        if payload.hide_high_risk:
            result = result[result["review_risk"] != "高"]
    baseline = result.sort_values(by=["score", "rating"], ascending=[False, False]).reset_index(drop=True)
    result = apply_review_adjustment(result, payload.use_review_analysis, payload.review_weight)
    intent = payload.scenario if payload.scenario != "手動自訂" else payload.smart_mode
    enhanced = apply_intent_adjustment(result, intent).reset_index(drop=True)
    result = enhanced.head(payload.top_n)
    return {
        "results": serializable_records(result),
        "analysis": restaurant_analysis(baseline, enhanced, result, payload.top_n, payload.review_weight),
        "meta": {
            "candidate_count": len(candidates),
            "result_count": len(result),
            "scenario": payload.scenario,
            "smart_mode": payload.smart_mode,
        },
    }


def calculate_priority(item) -> dict:
    core_result = core_calculate_priority(
        {
            "name": normalize_core_ingredient(item.name),
            "days_stored": item.days_stored,
            "shelf_life": item.shelf_life,
            "price": item.price,
            "perishability": {"低": "low", "中": "middle", "高": "high"}[item.perishability],
        }
    )
    return {
        "ingredient": core_result["name"],
        "priority_score": core_result["priority_score"],
        "scheduling_ratio": core_result["scheduling_ratio"],
        "remaining_days": core_result["remaining_days"],
        "level": {"low": "低", "middle": "中", "high": "高"}[core_result["level"]],
        "price": core_result["price"],
    }


def apply_recipe_priority(result: pd.DataFrame, profiles: dict[str, dict]) -> pd.DataFrame:
    result = result.copy()
    bonuses, priority_names = [], []
    for _, row in result.iterrows():
        matched = parse_ingredients(row["matched_ingredients"])
        used = [name for name in matched if name in profiles]
        total = sum(profiles[name]["priority_score"] for name in used)
        high_count = sum(profiles[name]["level"] == "高" for name in used)
        bonuses.append(round(min(total / 8 + high_count * 5, 25), 1))
        priority_names.append("、".join(used))
    result["priority_bonus"] = bonuses
    result["priority_ingredients"] = priority_names
    result["final_score"] = (result["score"] + result["priority_bonus"]).clip(0, 125).round(1)
    return result.sort_values(
        by=["final_score", "priority_bonus", "score"], ascending=[False, False, False]
    )


def recipe_options() -> dict:
    recipes = load_recipes(ROOT / "recipes.csv")
    return {
        "ingredients": collect_ingredient_options(recipes),
        "scenarios": list(RECIPE_SCENARIOS),
        "smart_modes": ["自訂", "我不想出門", "清冰箱模式", "快速料理", "低熱量"],
    }


def recommend_recipe_payload(payload) -> dict:
    recipes = load_recipes(ROOT / "recipes.csv")
    ingredient_text = ",".join(item.name for item in payload.ingredients)
    max_time = payload.max_time
    max_calories = payload.max_calories
    max_missing = payload.max_missing
    only_cookable = payload.only_cookable
    if payload.scenario == "宅家不出門":
        max_missing = 0
        only_cookable = True
    elif payload.scenario == "健身低熱量":
        max_time = min(max_time, 40)
        max_calories = min(max_calories, 500)
    result = recommend_recipes(
        recipes,
        ingredient_text,
        max_time,
        payload.difficulty,
        len(recipes),
        max_calories,
        max_missing,
        only_cookable,
    )
    recalled_count = len(result)
    result = attach_recipe_knowledge(result, load_recipe_knowledge(ROOT / "recipe_knowledge.csv"))
    knowledge_excluded_count = recalled_count - len(result)
    baseline = result.sort_values(by=["score", "recall_score", "matched_count", "time"], ascending=[False, False, False, True]).reset_index(drop=True)
    priority_rows = [calculate_priority(item) for item in payload.ingredients]
    profiles = {row["ingredient"]: row for row in priority_rows}
    enhanced = apply_recipe_priority(result, profiles).reset_index(drop=True)
    result = enhanced.head(payload.top_n)
    records = serializable_records(result)
    for row in records:
        row["steps"] = [step.strip() for step in str(row.get("steps", "")).split("|") if step.strip()]
    normalization = get_ingredient_normalization_report(ingredient_text)
    sorted_priorities = sorted(priority_rows, key=lambda row: (-row["priority_score"], -row["scheduling_ratio"]))
    return {
        "results": records,
        "priorities": sorted_priorities,
        "normalization": normalization,
        "analysis": recipe_analysis(baseline, enhanced, result, sorted_priorities, normalization, payload.top_n),
        "meta": {
            "result_count": len(result),
            "scenario": payload.scenario,
            "smart_mode": payload.smart_mode,
            "effective_max_time": max_time,
            "effective_max_calories": max_calories,
            "effective_max_missing": max_missing,
            "effective_only_cookable": only_cookable,
            "knowledge_constraint": "strict_verified_only",
            "knowledge_excluded_count": knowledge_excluded_count,
        },
    }
