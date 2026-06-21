from collections import Counter


positive_words = [
    "好吃",
    "推薦",
    "便宜",
    "新鮮",
    "服務好",
    "速度快",
    "乾淨",
    "份量多",
]

negative_words = [
    "難吃",
    "太貴",
    "等很久",
    "服務差",
    "不新鮮",
    "髒",
    "太鹹",
    "失望",
]


def analyze_one_review(text):

    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    raw_score = pos_count - neg_count

    if raw_score > 0:
        label = "positive"
    elif raw_score < 0:
        label = "negative"
    else:
        label = "neutral"

    return {
        "text": text,
        "label": label,
        "raw_score": raw_score,
        "positive_hits": pos_count,
        "negative_hits": neg_count,
    }


def analyze_restaurant_reviews(restaurant_name, reviews):
    results = [analyze_one_review(review) for review in reviews]
    labels = Counter(item["label"] for item in results)

    review_count = len(results)
    negative_count = labels["negative"]
    negative_ratio = round(negative_count / review_count * 100, 1) if review_count else 0

    #50當作中間值，正面字多就往上，負面字多就往下
    total_raw_score = sum(item["raw_score"] for item in results)
    sentiment_score = 50 + total_raw_score * 10
    sentiment_score = max(0, min(100, sentiment_score))

    #這個調整值是給推薦排序用的
    #分數高一點就加分，負評比例高就扣分
    risk_adjustment = round((sentiment_score - 50)*0.12-negative_ratio*0.08, 1)

    if negative_ratio >= 45 or sentiment_score < 45:
        risk_level = "high"
    elif negative_ratio >= 25 or sentiment_score < 60:
        risk_level = "middle"
    else:
        risk_level = "low"

    return {
        "restaurant": restaurant_name,
        "review_count": review_count,
        "sentiment_score": round(sentiment_score, 1),
        "negative_ratio": negative_ratio,
        "risk_adjustment": risk_adjustment,
        "risk_level": risk_level,
        "detail": results,
    }


def main():
    demo_reviews = [
        "這家很好吃，價格便宜，服務好",
        "餐點新鮮，速度快，會再來",
        "今天等很久，而且有點太鹹",
        "份量多，但是服務差一點",
    ]

    result = analyze_restaurant_reviews("午餐小店", demo_reviews)

    print("餐廳：", result["restaurant"])
    print("評論數：", result["review_count"])
    print("情緒分數：", result["sentiment_score"])
    print("負評比例：", str(result["negative_ratio"]) + "%")
    print("風險調整：", result["risk_adjustment"])
    print("風險等級：", result["risk_level"])


if __name__ == "__main__":
    main()
