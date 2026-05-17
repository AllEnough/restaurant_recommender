# 今天吃什麼：餐廳與食譜智慧推薦系統

本專題是一套使用 Python 與 Streamlit 製作的智慧飲食推薦系統，目標是解決大學生常見的「不知道吃什麼」問題。

系統分成兩種使用情境：

- **外食推薦**：根據預算、距離、餐點類型、天氣、心情、外帶需求、辣度與出餐速度推薦餐廳。
- **內食推薦**：根據冰箱現有食材、可接受烹飪時間與料理難度推薦食譜。

## 專題特色

- 支援外食族與內食族兩種情境。
- 使用多條件加權評分模型推薦餐廳。
- 使用食材比對模型推薦食譜。
- 根據使用者心情調整餐廳推薦策略。
- 提供推薦分數與推薦理由，提升可解釋性。
- 使用互動式地圖標示推薦餐廳位置。
- 使用圖表呈現餐廳與食譜資料分析。
- 可部署到 Streamlit Community Cloud 供組員或老師線上查看。

## 使用技術

| 類別 | 技術 |
|---|---|
| 程式語言 | Python |
| 網頁介面 | Streamlit |
| 資料處理 | pandas |
| 互動式地圖 | folium、streamlit-folium |
| 資料格式 | CSV |
| 版本管理 | Git、GitHub |
| 雲端部署 | Streamlit Community Cloud |

## 專案結構

```text
restaurant_recommender/
├── app.py                    # Streamlit 主程式
├── recommender.py            # 外食餐廳推薦模型
├── recipe_recommender.py     # 內食食譜推薦模型
├── restaurants.csv           # 餐廳資料集
├── recipes.csv               # 食譜資料集
├── requirements.txt          # Python 套件需求
├── report/
│   ├── project_outline.md       # 專題報告大綱
│   └── presentation_outline.md  # 簡報大綱
└── README.md
```

## 功能介紹

### 1. 外食推薦

使用者可以輸入：

- 預算上限
- 可接受距離
- 餐點類型
- 目前天氣
- 目前心情
- 是否需要外帶
- 可接受辣度
- 是否希望快速出餐

系統會輸出：

- 推薦餐廳排名
- 推薦分數
- 推薦理由
- 推薦分數比較圖
- 推薦餐廳互動地圖

### 2. 情緒策略推薦

不同心情會影響推薦分數：

| 心情 | 推薦策略 |
|---|---|
| 省錢 | 低價與 CP 值高的餐廳加分 |
| 疲累 | 距離近與快速出餐的餐廳加分 |
| 開心 | 高評分與適合聚餐的餐廳加分 |
| 心情不好 | 甜點、飲料、炸物、小吃加分 |
| 選擇困難 | 從高分餐廳中產生今日驚喜推薦 |

### 3. 虛擬美食地圖

外食推薦結果會以圖針標示在互動式地圖上。

圖針資訊包含：

- 餐廳名稱
- 餐點類型
- 平均價格
- 評分
- 距離
- 推薦分數
- CP 值
- 推薦理由

### 4. 內食食譜推薦

使用者可以輸入冰箱現有食材，例如：

```text
雞蛋, 白飯, 蔥
```

系統會根據食材符合度、烹飪時間、料理難度與缺少食材數量推薦食譜。

輸出結果包含：

- 食譜名稱
- 食譜類型
- 料理時間
- 難度
- 熱量
- 符合食材
- 缺少食材
- 推薦分數
- 推薦理由

## 推薦模型概念

### 外食餐廳推薦分數

```text
餐廳推薦分數 =
評分分數
+ 價格符合度
+ 距離符合度
+ 類型符合度
+ 天氣與心情符合度
+ 外帶符合度
+ 辣度符合度
+ 出餐速度分數
+ 情緒策略加權
```

分數限制在 0 到 100 分之間，分數越高代表越符合使用者需求。

### 內食食譜推薦分數

```text
食譜推薦分數 =
食材符合度
+ 烹飪時間符合度
+ 難度符合度
+ 基礎分數
- 缺少食材懲罰
```

當使用者輸入的食材越接近食譜所需食材，推薦分數越高。

## 本機執行方式

### 1. 建立虛擬環境

```bash
python3 -m venv .venv
```

### 2. 啟用虛擬環境

macOS / Linux：

```bash
source .venv/bin/activate
```

Windows：

```bash
.venv\Scripts\activate
```

### 3. 安裝套件

```bash
pip install -r requirements.txt
```

### 4. 執行網站

```bash
streamlit run app.py
```

開啟瀏覽器後，通常會看到：

```text
http://localhost:8501
```

## 雲端部署

本專案可部署至 Streamlit Community Cloud。

部署步驟：

1. 將專案推送到 GitHub。
2. 登入 Streamlit Community Cloud。
3. 選擇 GitHub repository。
4. Main file path 設定為：

```text
app.py
```

5. 按下 Deploy。

## 資料集說明

### restaurants.csv

餐廳資料欄位包含：

- `name`：餐廳名稱
- `category`：餐點類型
- `price`：平均價格
- `rating`：評分
- `distance`：距離，單位為步行分鐘
- `serve_speed`：出餐速度
- `takeout`：是否可外帶
- `weather`：適合天氣
- `mood`：適合心情
- `spicy_level`：辣度等級
- `latitude`：緯度
- `longitude`：經度

### recipes.csv

食譜資料欄位包含：

- `name`：食譜名稱
- `category`：食譜類型
- `ingredients`：所需食材
- `missing_allowed`：可接受缺少食材數
- `time`：烹飪時間
- `difficulty`：料理難度
- `calories`：預估熱量

## 報告與簡報資料

報告與簡報大綱放在 `report/` 資料夾：

- `report/project_outline.md`
- `report/presentation_outline.md`

## 未來改進方向

- 串接 Google Maps API 或真實餐廳評論資料。
- 將模擬座標改成真實餐廳座標。
- 串接食譜 API，擴充食譜資料來源。
- 加入使用者歷史紀錄與個人化偏好。
- 加入營養素分析。
- 導入機器學習模型，根據使用者回饋調整推薦權重。
