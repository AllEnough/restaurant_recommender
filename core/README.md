# Core modules

此目錄只放可重用的決策與資料處理邏輯，不包含 FastAPI 路由或 React 介面。

| 檔案 | 責任 |
|---|---|
| `recommender.py` | 外食多條件基礎推薦 |
| `review_score.py` | 評論情緒、負評比例與風險公式 |
| `review_analyzer.py` | 評論資料集彙整、主題與摘要 |
| `recipe_rank.py` | 食材標準化、候選召回與食譜基礎排序 |
| `ingredient.py` | 食材保存優先級與排程比值 |
| `recipe_recommender.py` | CSV、DataFrame 與可信知識庫轉接 |
| `weather_service.py` | 天氣取得與情境分類 |

正式 API 由 `web_api/services.py` 組合這些模組。
