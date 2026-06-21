# Runtime data

此目錄只放執行時產生的持久化資料：

- `app.db`：帳號、Session 與收藏的 SQLite 資料庫。

Railway Volume 掛載在 `/app/data`；唯讀 CSV 必須放在 `datasets/`，避免被 Volume 遮蔽。`*.db` 不納入 Git。
