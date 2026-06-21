from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


WEIGHTS = {
    "rating": 25,
    "price": 20,
    "distance": 15,
    "category": 10,
    "context": 10,
    "takeout": 5,
    "spicy": 5,
    "speed": 10,
}

MOOD_STRATEGIES = {
    "省錢": "提高低價與 CP 值餐廳的分數，適合想控制花費的情境。",
    "疲累": "提高近距離與快速出餐餐廳的分數，降低決策與等待成本。",
    "開心": "提高高評分與適合聚餐類型的分數，偏向用餐體驗。",
    "心情不好": "提高甜點、飲料、炸物等療癒型餐點的分數。",
    "選擇困難": "維持綜合排序，並從高分餐廳中提供一筆驚喜推薦。",
}

COMFORT_CATEGORIES = {"甜點", "飲料", "炸物", "小吃"}
SOCIAL_CATEGORIES = {"火鍋", "燒肉", "鐵板燒", "日式", "義式", "韓式", "美式"}
MEAL_TIME_CATEGORIES = {
    "早餐": {"早餐", "早午餐", "飯類", "飲料"},
    "午餐": {"便當", "飯類", "麵食", "小吃", "水餃", "鍋貼", "素食"},
    "下午茶": {"飲料", "甜點", "輕食", "早午餐"},
    "晚餐": {"火鍋", "麵食", "飯類", "日式", "韓式", "義式", "泰式", "鐵板燒", "美式", "港式"},
    "宵夜": {"小吃", "炸物", "飲料", "麵食", "鍋貼", "水餃"},
}
SORT_COLUMNS = {
    "綜合推薦": ["score", "rating"],
    "CP值優先": ["cp_score", "score"],
    "距離最近": ["distance", "score"],
    "評分最高": ["rating", "score"],
}


def load_data(file_path=None):
    file_path = Path(file_path) if file_path else DATA_DIR / "restaurants.csv"
    df = pd.read_csv(file_path)
    numeric_columns = ["price", "rating", "distance", "spicy_level"]
    for optional_column in ["latitude", "longitude"]:
        if optional_column in df.columns:
            numeric_columns.append(optional_column)
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=numeric_columns)
    return df


def get_mood_strategy(mood):
    return MOOD_STRATEGIES.get(mood, "依照一般綜合條件進行推薦。")


def calculate_cp_score(row):
    if row["price"] <= 0:
        return 0
    # 轉成容易閱讀的 0-100 分區間，價格越低且評分越高 CP 值越高。
    return round(min((row["rating"] / row["price"]) * 1600, 100), 2)


def calculate_mood_bonus(row, budget, max_distance, mood):
    bonus = 0
    reasons = []

    if mood == "省錢":
        if row["price"] <= budget * 0.75:
            bonus += 8
            reasons.append("省錢模式：價格更低")
        if calculate_cp_score(row) >= 70:
            bonus += 4
            reasons.append("省錢模式：CP值較高")
    elif mood == "疲累":
        if row["distance"] <= max_distance * 0.7:
            bonus += 6
            reasons.append("疲累模式：距離更近")
        if row["serve_speed"] == "快":
            bonus += 6
            reasons.append("疲累模式：快速出餐")
    elif mood == "開心":
        if row["rating"] >= 4.3:
            bonus += 6
            reasons.append("開心模式：用餐評價佳")
        if row["category"] in SOCIAL_CATEGORIES:
            bonus += 5
            reasons.append("開心模式：適合聚餐")
    elif mood == "心情不好":
        if row["category"] in COMFORT_CATEGORIES:
            bonus += 8
            reasons.append("療癒模式：餐點類型較放鬆")
        if row["rating"] >= 4.2:
            bonus += 3
            reasons.append("療癒模式：評價穩定")

    return bonus, reasons


def get_meal_time_strategy(meal_time):
    categories = sorted(MEAL_TIME_CATEGORIES.get(meal_time, set()))
    if not categories:
        return "不套用時段加權。"
    return f"{meal_time}時段會提高 {', '.join(categories)} 類型的餐點分數。"


def calculate_meal_time_bonus(row, meal_time):
    categories = MEAL_TIME_CATEGORIES.get(meal_time, set())
    if not categories:
        return 0, []
    if row["category"] in categories:
        return 7, [f"{meal_time}時段：餐點類型適合"]
    return 0, []


def calculate_score(
    row,
    budget,
    max_distance,
    category,
    weather,
    mood,
    need_takeout,
    max_spicy_level=5,
    prefer_fast=False,
    meal_time="不套用",
):
    score = 0
    reasons = []

    rating_score = (row["rating"] / 5) * WEIGHTS["rating"]
    score += rating_score
    if row["rating"] >= 4.3:
        reasons.append("評分高")

    if row["price"] <= budget:
        price_score = WEIGHTS["price"]
        reasons.append("價格符合預算")
    else:
        over_price = row["price"] - budget
        price_score = max(0, WEIGHTS["price"] - over_price * 0.2)
    score += price_score

    if row["distance"] <= max_distance:
        distance_score = WEIGHTS["distance"]
        reasons.append("距離符合需求")
    else:
        over_distance = row["distance"] - max_distance
        distance_score = max(0, WEIGHTS["distance"] - over_distance * 2)
    score += distance_score

    if category == "不限" or row["category"] == category:
        score += WEIGHTS["category"]
        reasons.append("餐點類型符合偏好")

    context_score = 0
    if row["weather"] == weather:
        context_score += 5
        reasons.append("適合目前天氣")
    if row["mood"] == mood:
        context_score += 5
        reasons.append("符合目前心情")
    score += context_score

    if need_takeout == "不限":
        score += WEIGHTS["takeout"]
    elif need_takeout == row["takeout"]:
        score += WEIGHTS["takeout"]
        if need_takeout == "yes":
            reasons.append("可外帶")
        else:
            reasons.append("適合內用")

    if row["spicy_level"] <= max_spicy_level:
        score += WEIGHTS["spicy"]
        reasons.append("辣度可接受")
    else:
        score -= (row["spicy_level"] - max_spicy_level) * 3
        reasons.append("辣度較高")

    if prefer_fast:
        if row["serve_speed"] == "快":
            score += WEIGHTS["speed"]
            reasons.append("出餐速度快")
        elif row["serve_speed"] == "中":
            score += WEIGHTS["speed"] * 0.5
    else:
        score += WEIGHTS["speed"] * 0.5

    mood_bonus, mood_reasons = calculate_mood_bonus(row, budget, max_distance, mood)
    score += mood_bonus
    reasons.extend(mood_reasons)

    meal_time_bonus, meal_time_reasons = calculate_meal_time_bonus(row, meal_time)
    score += meal_time_bonus
    reasons.extend(meal_time_reasons)

    if not reasons:
        reasons.append("綜合條件接近需求")

    return round(min(max(score, 0), 100), 2), "、".join(reasons)


def calculate_score_breakdown(
    row,
    budget,
    max_distance,
    category,
    weather,
    mood,
    need_takeout,
    max_spicy_level=5,
    prefer_fast=False,
    meal_time="不套用",
):
    def clean_score(value):
        return float(round(value, 2))

    components = []

    rating_score = (row["rating"] / 5) * WEIGHTS["rating"]
    components.append(("評分", clean_score(rating_score), f"餐廳評分 {row['rating']} / 5"))

    if row["price"] <= budget:
        price_score = WEIGHTS["price"]
        price_note = f"{row['price']} 元符合 {budget} 元預算"
    else:
        over_price = row["price"] - budget
        price_score = max(0, WEIGHTS["price"] - over_price * 0.2)
        price_note = f"超出預算 {over_price} 元，價格分數降低"
    components.append(("價格", clean_score(price_score), price_note))

    if row["distance"] <= max_distance:
        distance_score = WEIGHTS["distance"]
        distance_note = f"{row['distance']} 分鐘符合可接受距離"
    else:
        over_distance = row["distance"] - max_distance
        distance_score = max(0, WEIGHTS["distance"] - over_distance * 2)
        distance_note = f"超出距離 {over_distance} 分鐘，距離分數降低"
    components.append(("距離", clean_score(distance_score), distance_note))

    category_score = WEIGHTS["category"] if category == "不限" or row["category"] == category else 0
    category_note = "餐點類型符合偏好" if category_score else "餐點類型未完全符合"
    components.append(("餐點類型", clean_score(category_score), category_note))

    context_score = 0
    context_notes = []
    if row["weather"] == weather:
        context_score += 5
        context_notes.append("符合天氣")
    if row["mood"] == mood:
        context_score += 5
        context_notes.append("符合心情")
    components.append(("情境", clean_score(context_score), "、".join(context_notes) or "情境符合度普通"))

    if need_takeout == "不限":
        takeout_score = WEIGHTS["takeout"]
        takeout_note = "不限制外帶"
    elif need_takeout == row["takeout"]:
        takeout_score = WEIGHTS["takeout"]
        takeout_note = "外帶需求符合"
    else:
        takeout_score = 0
        takeout_note = "外帶需求不符合"
    components.append(("外帶", clean_score(takeout_score), takeout_note))

    if row["spicy_level"] <= max_spicy_level:
        spicy_score = WEIGHTS["spicy"]
        spicy_note = "辣度可接受"
    else:
        spicy_score = -((row["spicy_level"] - max_spicy_level) * 3)
        spicy_note = "辣度高於可接受範圍"
    components.append(("辣度", clean_score(spicy_score), spicy_note))

    if prefer_fast:
        if row["serve_speed"] == "快":
            speed_score = WEIGHTS["speed"]
            speed_note = "出餐速度快"
        elif row["serve_speed"] == "中":
            speed_score = WEIGHTS["speed"] * 0.5
            speed_note = "出餐速度中等"
        else:
            speed_score = 0
            speed_note = "出餐速度較慢"
    else:
        speed_score = WEIGHTS["speed"] * 0.5
        speed_note = "未特別要求快速出餐"
    components.append(("出餐速度", clean_score(speed_score), speed_note))

    mood_bonus, mood_reasons = calculate_mood_bonus(row, budget, max_distance, mood)
    components.append(("心情策略", clean_score(mood_bonus), "、".join(mood_reasons) or "無額外心情加權"))

    meal_time_bonus, meal_time_reasons = calculate_meal_time_bonus(row, meal_time)
    components.append(("用餐時段", clean_score(meal_time_bonus), "、".join(meal_time_reasons) or "無時段加權"))

    total = round(min(max(sum(component[1] for component in components), 0), 100), 2)
    return components, total


def sort_restaurants(results, sort_by):
    if sort_by == "距離最近":
        return results.sort_values(by=["distance", "score"], ascending=[True, False])
    columns = SORT_COLUMNS.get(sort_by, SORT_COLUMNS["綜合推薦"])
    return results.sort_values(by=columns, ascending=[False] * len(columns))


def recommend_restaurants(
    df,
    budget,
    max_distance,
    category,
    weather,
    mood,
    need_takeout,
    max_spicy_level=5,
    prefer_fast=False,
    top_n=5,
    sort_by="綜合推薦",
    min_rating=0.0,
    meal_time="不套用",
):
    results = df.copy()
    results = results[results["rating"] >= min_rating]

    scores = results.apply(
        lambda row: calculate_score(
            row,
            budget,
            max_distance,
            category,
            weather,
            mood,
            need_takeout,
            max_spicy_level,
            prefer_fast,
            meal_time,
        ),
        axis=1,
    )

    results["score"] = scores.apply(lambda x: x[0])
    results["reason"] = scores.apply(lambda x: x[1])
    results["cp_score"] = results.apply(calculate_cp_score, axis=1)
    results = sort_restaurants(results, sort_by)

    return results.head(top_n)


if __name__ == "__main__":
    df = load_data()
    result = recommend_restaurants(
        df,
        budget=150,
        max_distance=8,
        category="不限",
        weather="冷",
        mood="疲累",
        need_takeout="不限",
        max_spicy_level=2,
        prefer_fast=True,
        sort_by="綜合推薦",
        min_rating=0,
        meal_time="晚餐",
    )
    print(result[["name", "category", "price", "rating", "distance", "cp_score", "score", "reason"]])
