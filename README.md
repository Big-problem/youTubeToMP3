# YouTube to MP3 Converter

基於 **FastAPI** + **`yt-dlp`** 的高效 YouTube 轉 MP3 工具，搭配 **Chrome 擴充功能前端**，可將音訊直接下載至本機資料夾。

---

## 💡 特點與機制

- **直接寫入本機下載資料夾**：轉檔完成後，MP3 檔案直接寫入 Windows 的預設「下載」資料夾，無需經過瀏覽器二次傳輸。
- **低限流風險**：採用 WSL 家用網路 IP 進行抓取，避免雲端機房 IP 常見的 HTTP 429 封鎖問題。
- **非同步處理**：後端採用背景任務處理轉檔，前端輪詢狀態並呈現象徵性的進度條。

---

## 🛠️ 環境需求

- **WSL2** (Ubuntu / Linux 環境)
- **Python 3.11+**
- **[uv](https://github.com/astral-sh/uv)** (Python 套件管理工具)
- **FFmpeg** & **Node.js**（提供 `yt-dlp` 音訊處理與 JS 解密支援）

---

## 🚀 後端啟動方式 (WSL)

### 1. 安裝系統套件 (若尚未安裝)
```bash
sudo apt update && sudo apt install -y ffmpeg nodejs
```

### 2. 安裝專案依賴
進入 `backend` 資料夾後執行：
```bash
uv sync
```

### 3. 啟動 FastAPI 服務
執行以下指令開啟後端伺服器：

```bash
uv run uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

> 📌 **注意**：服務預設於 `http://localhost:5000` 運作。`--reload` 模式會在程式碼變更時自動重載。

---

## 🧩 前端安裝 (Chrome 擴充功能)

1. 開啟 Chrome 瀏覽器，前往 `chrome://extensions/`
2. 開啟右上角的**「開發者模式」**
3. 點選**「載入未打包項目」**，並選擇本專案的 `frontend` 資料夾
4. 點擊擴充功能圖示即可開始貼上 YouTube 網址進行轉檔

---

## 📁 專案架構概覽

```text
.
├── backend/
│   ├── app.py           # FastAPI 主要服務邏輯
│   ├── pyproject.toml   # uv 專案設定檔
│   ├── uv.lock          # 鎖定依賴套件版本
│   └── downloads/       # (選用) 本地快取或暫存目錄
├── frontend/
│   ├── manifest.json    # Chrome 擴充功能設定
│   ├── popup.html       # 擴充功能介面
│   ├── popup.js         # 前端輪詢與觸發邏輯
│   └── icons/           # 圖示檔案
└── README.md            # 本說明文件
```