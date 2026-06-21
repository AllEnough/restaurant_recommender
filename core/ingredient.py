
#哪些食材要先用掉：快過期、比較貴、比較容易壞的排前面
ingredients = [
    {
        "name": "雞胸肉",
        "days_stored": 2,
        "shelf_life": 3,
        "price": 90,
        "perishability": "high",
    },
    {
        "name": "高麗菜",
        "days_stored": 4,
        "shelf_life": 7,
        "price": 45,
        "perishability": "middle",
    },
    {
        "name": "罐頭玉米",
        "days_stored": 10,
        "shelf_life": 180,
        "price": 35,
        "perishability": "low",
    },
]


def calculate_priority(item):
    shelf_life = max(item["shelf_life"], 1)
    days_stored = max(item["days_stored"], 0)
    remaining_days = max(shelf_life - days_stored, 0)

    # 保存期限用掉越多，分數越高
    used_ratio = days_stored/shelf_life
    expiry_score = used_ratio*50
    # 價格越高，浪費掉越可惜，提高分數
    price_score = min(item["price"]/150,1)*20

    perishability_score_map = {
        "low": 5,
        "middle": 12,
        "high": 20,
    }
    perishability_score = perishability_score_map.get(item["perishability"], 10)

    priority_score = expiry_score + price_score + perishability_score
    priority_score = round(min(priority_score, 100), 1)

    # scheduling_ratio 是拿來排順序的輔助值，越快過期又越貴先處理
    scheduling_ratio = round(item["price"] / (remaining_days + 1), 2)

    if priority_score >= 75:
        level = "high"
    elif priority_score >= 45:
        level = "middle"
    else:
        level = "low"

    return {
        "name": item["name"],
        "remaining_days": remaining_days,
        "priority_score": priority_score,
        "scheduling_ratio": scheduling_ratio,
        "level": level,
        "price": item["price"],
    }


def main():
    result = [calculate_priority(item) for item in ingredients]
    result = sorted(result, key=lambda item: (-item["priority_score"], -item["scheduling_ratio"]))

    print("食材使用優先順序")
    print()
    for index, item in enumerate(result, start=1):
        print(index, item["name"])
        print("  剩餘天數：", item["remaining_days"])
        print("  優先分數：", item["priority_score"])
        print("  排程參考值：", item["scheduling_ratio"])
        print("  等級：", item["level"])
        print()


if __name__ == "__main__":
    main()
