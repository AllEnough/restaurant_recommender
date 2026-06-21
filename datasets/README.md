# Dataset files

| 檔案 | 用途 |
|---|---|
| `restaurants.csv` | 餐廳條件、座標與基本評分 |
| `reviews.csv` | 餐廳評論文字 |
| `recipes.csv` | 食譜條件與所需食材 |
| `recipe_knowledge.csv` | 經審核的料理步驟與來源資訊 |
核心載入器會從此唯讀目錄解析 CSV，不依賴執行指令所在路徑。此目錄不可作為 Railway Volume 掛載點。
