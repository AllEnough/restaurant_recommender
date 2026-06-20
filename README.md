# 智慧飲食決策系統

智慧飲食決策系統是一套面向外食族與內食族的 Web 應用。外食模式整合預算、距離、情境與評論風險；內食模式根據冰箱食材、保存期限與料理限制推薦食譜。系統另提供 OpenCV 表情辨識、登入、Session 與收藏功能。

## 線上網站

- 正式網站：[restaurantrecommender-production.up.railway.app](https://restaurantrecommender-production.up.railway.app)
- 健康檢查：[API Health](https://restaurantrecommender-production.up.railway.app/api/health)
- API 文件：網站網址後加上 `/docs`

## 核心功能

| 模組 | 已完成功能 |
|---|---|
| 外食推薦 | 預算、距離、類型、天氣、時段、外帶、辣度、速度與最低評分 |
| 評論分析 | 情緒分數、負評比例、風險分級、常見優缺點與排名調整 |
| 情境感知 | 快速情境、心情策略、瀏覽器定位與 Haversine 距離 |
| 美食地圖 | React Leaflet、OpenStreetMap、排名／CP 值圖針與使用者位置 |
| OpenCV | YuNet 臉部偵測、MobileFaceNet 表情分類、心情映射 |
| 內食推薦 | 食材標準化、候選召回、料理限制與混合式排序 |
| 保存決策 | 已放天數、剩餘期限、價格、易腐程度與使用優先級 |
| 可信內容 | 從審核知識庫取得料理步驟、內容編號、來源與日期 |
| 進階分析 | 決策 Dashboard、模型前後比較、排名變化、分數拆解與敏感度分析 |
| 帳號系統 | SQLite 註冊、登入、七天 Session、登出與收藏 |
| 部署 | React production build、FastAPI、Docker、Railway Volume |

推薦頁面會先呈現答案，再將評論細節、分數拆解與保存排程放入預設展開、可收合的進階區塊。舊版推薦資料缺少分析欄位時，畫面會提示重新計算。

## 技術架構

```text
Browser
  └─ React 19 + Tailwind CSS 4 + Vite
       ├─ 外食／內食介面
       ├─ Login / Favorites
       └─ Camera / Geolocation
                    ↓ JSON / HTTPS
FastAPI + Uvicorn
  ├─ Recommendation API
  ├─ Authentication API
  ├─ OpenCV DNN
  └─ React static files
                    ↓
CSV datasets + SQLite + ONNX models
```

正式版採單一服務部署：Docker 第一階段建置 React，第二階段執行 FastAPI；FastAPI 同時提供 `/api/*` 與 React 靜態網站。`app.py` 的 Streamlit 版本僅保留為備援介面。

外食推薦完成後，React Leaflet 會在推薦清單與進階分析之間顯示互動地圖。底圖使用 OpenStreetMap；圖針依第一名與 CP 值分色，點擊可查看推薦資訊並前往 Google Maps。

## 專案結構

```text
restaurant_recommender/
├── frontend/                 # React、Tailwind CSS、Vite
├── web_api/
│   ├── main.py               # FastAPI 與靜態網站
│   ├── services.py           # API 推薦流程
│   ├── auth.py               # SQLite 帳號、Session、收藏
│   └── emotion.py            # OpenCV 表情辨識
├── models/                   # YuNet、MobileFaceNet ONNX
├── tests/                    # Python 自動測試
├── report/                   # 專題報告與簡報大綱
│   └── algorithm_examples.py # 可獨立執行的演算法展示
├── recommender.py            # 外食基礎推薦模型
├── recipe_recommender.py     # 內食召回與排序
├── review_analyzer.py        # 評論文字分析
├── weather_service.py        # 天氣資料與分類
├── restaurants.csv
├── reviews.csv
├── recipes.csv
├── recipe_knowledge.csv
├── app.py                    # Streamlit 備援版
├── Dockerfile
├── railway.json
└── requirements.txt
```

`data/app.db` 會在後端啟動時自動建立，且已排除於 Git。

## 本機開發

### 需求

- Python 3.11 以上
- Node.js 20 以上
- npm
- VSCode

### 安裝 Python 套件

```bash
cd /Users/allenough/Developer/school/python/restaurant_recommender
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 啟動 FastAPI

```bash
.venv/bin/python -m uvicorn web_api.main:app --reload --port 8000
```

API 文件：`http://127.0.0.1:8000/docs`

### 啟動 React

另開一個 Terminal：

```bash
cd frontend
npm install
npm run dev
```

網站：`http://127.0.0.1:5173`

### 模擬正式模式

```bash
cd frontend
npm ci
npm run build
cd ..
.venv/bin/python -m uvicorn web_api.main:app --host 127.0.0.1 --port 8000
```

此時 React 與 API 都由 `http://127.0.0.1:8000` 提供。

## API 摘要

| Method | Path | 說明 |
|---|---|---|
| GET | `/api/health` | 健康檢查 |
| GET | `/api/options` | 餐廳與食譜選項 |
| GET | `/api/weather` | 即時天氣分類 |
| POST | `/api/recommend/restaurants` | 外食推薦 |
| POST | `/api/recommend/recipes` | 內食推薦 |
| POST | `/api/emotion/analyze` | 單張圖片表情辨識 |
| POST | `/api/auth/register` | 註冊並建立 Session |
| POST | `/api/auth/login` | 登入 |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/me` | 目前登入者 |
| GET/POST/DELETE | `/api/favorites` | 收藏管理 |

## 帳號與資料庫

登入功能會實際寫入 SQLite，不是前端模擬。

| Table | 用途 |
|---|---|
| `users` | Email、顯示名稱、`scrypt` 密碼雜湊 |
| `sessions` | SHA-256 Token 雜湊、使用者與到期時間 |
| `favorites` | 使用者收藏的餐廳與食譜 |

Session Cookie 設定為 `HttpOnly` 與 `SameSite=Lax`；線上環境透過 `APP_SECURE_COOKIE=1` 啟用 Secure Cookie。

## 測試

```bash
.venv/bin/python -m unittest discover -s tests -v
npm run build --prefix frontend
```

目前測試涵蓋：

- 食材別名標準化。
- 食譜候選必須命中食材。
- 召回食譜必須具有可信知識內容。
- 外食與內食 API。
- 註冊、登入、Session、收藏與登出。
- 無人臉影像的錯誤處理。
- 外食與內食 API 必須回傳 Dashboard、模型評估及分數拆解資料。

報告時可獨立執行核心演算法範例：

```bash
python3 report/algorithm_examples.py
```

## Railway 部署

GitHub `main` 更新後，Railway 會依照 `Dockerfile` 自動重新部署。

### Variables

```text
PORT=8000
APP_DB_PATH=/app/data/app.db
APP_SECURE_COOKIE=1
```

### Volume

將 Railway Volume 掛載到：

```text
/app/data
```

沒有 Volume 時，重新部署後 SQLite 帳號與收藏可能消失。

### Public Networking

- Target Port：`8000`
- Healthcheck：`/api/health`

部署完成後應先確認 `/api/health` 回傳 HTTP 200，再測試註冊、收藏、登出、重新登入與重新部署後的資料保存。

## 隱私、限制與未來方向

- 相機影像只在單次請求的記憶體中處理，不寫入資料庫或檔案。
- 表情分類只作為飲食推薦訊號，不是心理或醫療判斷。
- 目前餐廳、評論與食譜為專題資料集，不是即時 Google Maps 全量資料。
- 目前可信食譜層是本地檢索，尚未串接 LLM，因此不宣稱已完成完整 RAG。
- SQLite 適合單一課堂展示服務；多副本與大量使用者應改用 PostgreSQL。
- 後續可擴充合法授權的地點 API、向量檢索、來源約束 LLM 與推薦成效實驗。
