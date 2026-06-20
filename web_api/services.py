from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from recommender import load_data, recommend_restaurants
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
    result = apply_review_adjustment(result, payload.use_review_analysis, payload.review_weight)
    intent = payload.scenario if payload.scenario != "手動自訂" else payload.smart_mode
    result = apply_intent_adjustment(result, intent).head(payload.top_n)
    return {
        "results": serializable_records(result),
        "meta": {
            "candidate_count": len(candidates),
            "result_count": len(result),
            "scenario": payload.scenario,
            "smart_mode": payload.smart_mode,
        },
    }


def calculate_priority(item) -> dict:
    shelf_life = max(int(item.shelf_life), 1)
    days_stored = max(int(item.days_stored), 0)
    remaining = max(shelf_life - days_stored, 0)
    expiry = min(days_stored / shelf_life, 1) * 45
    expiry += {0: 30, 1: 22, 2: 14}.get(remaining, 0)
    price_score = min(float(item.price) / 150, 1) * 20
    perishability_score = {"低": 5, "中": 10, "高": 15}.get(item.perishability, 10)
    score = round(min(expiry + price_score + perishability_score, 100), 1)
    penalty = float(item.price) * {"低": 0.8, "中": 1.0, "高": 1.25}.get(item.perishability, 1)
    ratio = round(penalty / (remaining + 1), 2)
    level = "高" if score >= 75 else "中" if score >= 45 else "低"
    return {
        "ingredient": item.name,
        "priority_score": score,
        "scheduling_ratio": ratio,
        "remaining_days": remaining,
        "level": level,
        "price": item.price,
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
    result = recommend_recipes(
        recipes,
        ingredient_text,
        payload.max_time,
        payload.difficulty,
        len(recipes),
        payload.max_calories,
        payload.max_missing,
        payload.only_cookable,
    )
    result = attach_recipe_knowledge(result, load_recipe_knowledge(ROOT / "recipe_knowledge.csv"))
    priority_rows = [calculate_priority(item) for item in payload.ingredients]
    profiles = {row["ingredient"]: row for row in priority_rows}
    result = apply_recipe_priority(result, profiles).head(payload.top_n)
    records = serializable_records(result)
    for row in records:
        row["steps"] = [step.strip() for step in str(row.get("steps", "")).split("|") if step.strip()]
    return {
        "results": records,
        "priorities": sorted(priority_rows, key=lambda row: (-row["priority_score"], -row["scheduling_ratio"])),
        "normalization": get_ingredient_normalization_report(ingredient_text),
        "meta": {
            "result_count": len(result),
            "scenario": payload.scenario,
            "smart_mode": payload.smart_mode,
        },
    }
