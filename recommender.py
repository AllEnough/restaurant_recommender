import pandas as pd


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


def load_data(file_path="restaurants.csv"):
    df = pd.read_csv(file_path)
    numeric_columns = ["price", "rating", "distance", "spicy_level"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.dropna(subset=numeric_columns)


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

    if not reasons:
        reasons.append("綜合條件接近需求")

    return round(max(score, 0), 2), "、".join(reasons)


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
):
    results = df.copy()

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
        ),
        axis=1,
    )

    results["score"] = scores.apply(lambda x: x[0])
    results["reason"] = scores.apply(lambda x: x[1])
    results = results.sort_values(by="score", ascending=False)

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
    )
    print(result[["name", "category", "price", "rating", "distance", "score", "reason"]])
