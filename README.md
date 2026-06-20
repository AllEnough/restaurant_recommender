# 智慧飲食決策系統

本專題以「外食避雷、內食減浪費」為核心，整合餐廳評論風險、情境推薦、冰箱保存優先級、可信食譜檢索、登入收藏及 OpenCV 表情辨識。新版正式介面採用 React、Tailwind CSS 與 FastAPI；原本的 Streamlit 介面保留為功能完整的備援展示版本。

## 已完成功能

### 外食決策

- 預算、距離、類型、天氣、時段、外帶、辣度與評分篩選。
- 省錢午餐、快速外帶、聚餐不踩雷等快速情境。
- 餐廳多條件加權、評論情緒、負評比例與情境意圖排序。
- 推薦清單優先顯示，模型分數與進階分析收合於結果後方。
- 瀏覽器定位與 Haversine 距離重算。
- OpenCV 臉部偵測與表情分類，可將結果帶入推薦心情，亦可手動覆寫。

### 內食決策

- 食材名稱標準化、候選召回與混合式排序。
- 依已存放天數、保存期限、價格與易腐程度計算使用優先級。
- 參考排程概念，提高快過期及高浪費成本食材的推薦權重。
- 從 `recipe_knowledge.csv` 檢索審核過的步驟、來源與內容編號。
- 推薦清單先呈現，保存排程與模型資訊置於進階區塊。

### 帳號系統

登入不是展示用假畫面，FastAPI 會實際操作 SQLite：

- `users`：帳號、顯示名稱、`scrypt` 密碼雜湊。
- `sessions`：雜湊後的 Session Token 與到期時間。
- `favorites`：每位使用者收藏的餐廳與食譜。
- Session Token 透過 `HttpOnly`、`SameSite=Lax` Cookie 傳送。
- 線上 HTTPS 環境設定 `APP_SECURE_COOKIE=1`。

## 系統架構

```text
Browser
  └─ React 19 + Tailwind CSS 4
       ├─ 外食與內食操作介面
       ├─ 登入、註冊、收藏
       └─ Camera / Geolocation API
             ↓ HTTPS / JSON
FastAPI
  ├─ Auth / Session / Favorites
  ├─ OpenCV YuNet + MobileFaceNet
  ├─ 餐廳推薦與評論分析
  ├─ 食材召回、混合排序與可信內容檢索
  └─ React production 靜態檔
             ↓
CSV datasets + SQLite app.db + ONNX models
```

## 專案結構

```text
restaurant_recommender/
├── frontend/                 # React、Tailwind CSS、Vite
├── web_api/                  # FastAPI、登入、推薦 API、OpenCV
├── models/                   # YuNet 與表情辨識 ONNX 模型
├── tests/                    # 推薦、帳號、收藏、表情 API 測試
├── data/app.db               # 執行時建立，已忽略於 Git
├── app.py                    # Streamlit 備援介面
├── recommender.py            # 外食推薦
├── recipe_recommender.py     # 內食推薦
├── review_analyzer.py        # 評論分析
├── weather_service.py        # 即時天氣
├── Dockerfile                # React build + FastAPI runtime
├── railway.json              # Railway 健康檢查與重啟策略
└── requirements.txt
```

## 本機執行

Python 建議使用專案 `.venv`，不要安裝到 macOS 系統 Python。

```bash
cd /Users/allenough/Developer/school/python/restaurant_recommender
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

開發模式需開兩個 VSCode Terminal：

```bash
# Terminal 1：FastAPI
.venv/bin/python -m uvicorn web_api.main:app --reload --port 8000
```

```bash
# Terminal 2：React
cd frontend
npm install
npm run dev
```

開啟 `http://127.0.0.1:5173`。API 文件位於 `http://127.0.0.1:8000/docs`。

正式模式：

```bash
cd frontend && npm ci && npm run build && cd ..
.venv/bin/python -m uvicorn web_api.main:app --host 127.0.0.1 --port 8000
```

此時 React 與 API 皆由 `http://127.0.0.1:8000` 提供。

## 自動測試

```bash
.venv/bin/python -m unittest discover -s tests -v
cd frontend && npm run build
```

測試涵蓋推薦 API、註冊登入、Session、收藏、登出與無臉影像錯誤處理。

## Railway 部署

1. 將目前分支推送至 GitHub。
2. Railway 建立 New Project，選擇 Deploy from GitHub Repo。
3. Railway 會由根目錄 `Dockerfile` 建置 React 與 FastAPI。
4. 在 Variables 設定：
   - `APP_DB_PATH=/app/data/app.db`
   - `APP_SECURE_COOKIE=1`
5. 為服務新增 Volume，掛載路徑必須是 `/app/data`，否則 SQLite 帳號會在重新部署後消失。
6. 在 Networking 產生公開網域。
7. 確認 `/api/health` 回傳 `status: ok`，再測試註冊、登出與重新登入。

Railway 會注入 `PORT`，Docker 啟動命令已自動監聽該埠。若未掛 Volume，網站仍能運作，但帳號與收藏資料不是永久保存。

## 隱私與限制

- 表情辨識影像只在單次請求中處理，不寫入磁碟。
- 表情分類只作為餐點推薦訊號，不是心理或醫療判斷。
- 目前餐廳、評論與食譜主要來自專題資料集，不等同即時 Google Maps 全量資料。
- SQLite 適合課堂展示與小型服務；多人正式營運應改用 PostgreSQL。
- Streamlit Community Cloud 只能部署 `app.py` 備援版；React/FastAPI 完整版應部署到 Railway、Render 或其他容器平台。
