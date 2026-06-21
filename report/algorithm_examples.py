"""直接呼叫正式系統三個核心演算法模組的報告展示程式。"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingredient import calculate_priority
from recipe_rank import recommend_recipes
from review_score import analyze_restaurant_reviews


def print_rows(title: str, rows: list[dict], score_key: str) -> None:
    print(f"\n{title}")
    for rank, row in enumerate(
        sorted(rows, key=lambda item: item[score_key], reverse=True), start=1
    ):
        print(f"{rank}. {row}")


def main() -> None:
    reviews = [
        "這家很好吃，價格便宜，服務好",
        "餐點新鮮，速度快，會再來",
        "今天等很久，而且有點太鹹",
        "份量多，但是服務差一點",
    ]
    print("評論風險分析")
    print(analyze_restaurant_reviews("午餐小店", reviews))

    ingredient_rows = [
        {"name": "雞胸肉", "days_stored": 2, "shelf_life": 3, "price": 90, "perishability": "high"},
        {"name": "高麗菜", "days_stored": 4, "shelf_life": 7, "price": 45, "perishability": "middle"},
        {"name": "罐頭玉米", "days_stored": 10, "shelf_life": 180, "price": 35, "perishability": "low"},
    ]
    priorities = [calculate_priority(item) for item in ingredient_rows]
    print_rows("食材使用優先順序", priorities, "priority_score")

    recipes = recommend_recipes("雞肉, 青菜, 蛋")
    print_rows("食譜候選與基礎排序", recipes, "score")


if __name__ == "__main__":
    main()
