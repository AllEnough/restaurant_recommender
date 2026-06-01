import pandas as pd


POSITIVE_WORDS = {
    "好吃",
    "推薦",
    "親切",
    "快速",
    "便宜",
    "划算",
    "乾淨",
    "新鮮",
    "份量足",
    "香",
    "穩定",
    "舒服",
    "濃郁",
    "爽口",
    "方便",
    "回訪",
    "入味",
    "酥脆",
}

NEGATIVE_WORDS = {
    "太鹹",
    "偏貴",
    "排隊",
    "等很久",
    "油膩",
    "普通",
    "吵",
    "不穩",
    "份量少",
    "太辣",
    "座位少",
    "冷掉",
    "服務慢",
    "味道淡",
    "擁擠",
}

TOPIC_KEYWORDS = {
    "價格": ["便宜", "划算", "偏貴", "價格", "CP"],
    "速度": ["快速", "出餐", "等很久", "服務慢", "排隊"],
    "口味": ["好吃", "太鹹", "香", "濃郁", "味道淡", "入味", "酥脆"],
    "環境": ["乾淨", "舒服", "吵", "擁擠", "座位少"],
    "份量": ["份量足", "份量少"],
}


def load_reviews(file_path="reviews.csv"):
    try:
        reviews = pd.read_csv(file_path)
    except FileNotFoundError:
        return pd.DataFrame(columns=["restaurant_name", "review_text"])

    required_columns = {"restaurant_name", "review_text"}
    if not required_columns.issubset(reviews.columns):
        return pd.DataFrame(columns=["restaurant_name", "review_text"])

    reviews["restaurant_name"] = reviews["restaurant_name"].astype(str).str.strip()
    reviews["review_text"] = reviews["review_text"].astype(str).str.strip()
    return reviews.dropna(subset=["restaurant_name", "review_text"])


def count_hits(text, words):
    return sum(1 for word in words if word in text)


def analyze_review_text(text):
    positive_hits = count_hits(text, POSITIVE_WORDS)
    negative_hits = count_hits(text, NEGATIVE_WORDS)
    score = positive_hits - negative_hits

    if score > 0:
        sentiment = "正向"
    elif score < 0:
        sentiment = "負向"
    else:
        sentiment = "中性"

    positive_words = [word for word in POSITIVE_WORDS if word in text]
    negative_words = [word for word in NEGATIVE_WORDS if word in text]
    return sentiment, score, positive_words, negative_words


def extract_topics(texts):
    topic_scores = {}
    combined_text = " ".join(texts)
    for topic, keywords in TOPIC_KEYWORDS.items():
        topic_scores[topic] = sum(combined_text.count(keyword) for keyword in keywords)
    return [topic for topic, score in sorted(topic_scores.items(), key=lambda item: (-item[1], item[0])) if score > 0]


def summarize_reviews(name, review_count, sentiment_score, negative_ratio, top_positive, top_negative, topics):
    if review_count == 0:
        return "目前沒有評論資料，推薦仍以基本條件為主。"

    topic_text = "、".join(topics[:2]) if topics else "整體體驗"
    if sentiment_score >= 70 and negative_ratio <= 20:
        tone = "評論整體偏正向"
    elif sentiment_score < 45 or negative_ratio >= 45:
        tone = "評論風險較高"
    else:
        tone = "評論呈現中等穩定"

    positive_text = "、".join(top_positive[:3]) if top_positive else "無明顯優點關鍵字"
    negative_text = "、".join(top_negative[:3]) if top_negative else "無明顯負評關鍵字"
    return f"{name} 的{topic_text}被較常提到，{tone}；常見優點：{positive_text}；常見疑慮：{negative_text}。"


def analyze_reviews(reviews):
    if reviews.empty:
        return pd.DataFrame(
            columns=[
                "name",
                "review_count",
                "sentiment_score",
                "negative_ratio",
                "review_adjustment",
                "review_risk",
                "positive_keywords",
                "negative_keywords",
                "review_topics",
                "review_summary",
            ]
        )

    rows = []
    for name, group in reviews.groupby("restaurant_name"):
        sentiments = []
        raw_scores = []
        positive_words = []
        negative_words = []
        texts = group["review_text"].tolist()

        for text in texts:
            sentiment, score, positives, negatives = analyze_review_text(text)
            sentiments.append(sentiment)
            raw_scores.append(score)
            positive_words.extend(positives)
            negative_words.extend(negatives)

        review_count = len(texts)
        negative_count = sentiments.count("負向")
        positive_count = sentiments.count("正向")
        negative_ratio = round((negative_count / review_count) * 100, 1) if review_count else 0
        sentiment_score = round(min(max(50 + sum(raw_scores) * 8 + positive_count * 4 - negative_count * 6, 0), 100), 1)
        review_adjustment = round(max(min((sentiment_score - 50) * 0.16 - negative_ratio * 0.08, 10), -12), 1)

        if negative_ratio >= 45 or sentiment_score < 45:
            review_risk = "高"
        elif negative_ratio >= 25 or sentiment_score < 60:
            review_risk = "中"
        else:
            review_risk = "低"

        top_positive = sorted(set(positive_words), key=lambda word: (-positive_words.count(word), word))
        top_negative = sorted(set(negative_words), key=lambda word: (-negative_words.count(word), word))
        topics = extract_topics(texts)

        rows.append(
            {
                "name": name,
                "review_count": review_count,
                "sentiment_score": sentiment_score,
                "negative_ratio": negative_ratio,
                "review_adjustment": review_adjustment,
                "review_risk": review_risk,
                "positive_keywords": "、".join(top_positive[:5]),
                "negative_keywords": "、".join(top_negative[:5]),
                "review_topics": "、".join(topics[:4]),
                "review_summary": summarize_reviews(
                    name,
                    review_count,
                    sentiment_score,
                    negative_ratio,
                    top_positive,
                    top_negative,
                    topics,
                ),
            }
        )

    return pd.DataFrame(rows)


def merge_review_analysis(restaurants, review_analysis):
    merged = restaurants.merge(review_analysis, on="name", how="left")
    defaults = {
        "review_count": 0,
        "sentiment_score": 50.0,
        "negative_ratio": 0.0,
        "review_adjustment": 0.0,
        "review_risk": "未知",
        "positive_keywords": "",
        "negative_keywords": "",
        "review_topics": "",
        "review_summary": "目前沒有評論資料，推薦仍以基本條件為主。",
    }
    for column, value in defaults.items():
        merged[column] = merged[column].fillna(value)
    return merged
