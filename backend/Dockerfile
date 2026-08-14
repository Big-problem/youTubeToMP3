# 1. 使用官方 Python 基礎映像檔
FROM python:3.11-slim

# 2. 從官方 image 複製 uv 工具（官方推薦的最佳實踐）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. 安裝系統層級套件：FFmpeg 與 Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    && ln -sf /usr/bin/nodejs /usr/bin/node \
    && rm -rf /var/lib/apt/lists/*

# 4. 設定容器內的工作目錄
WORKDIR /app

# 5. 先複製專案與依賴設定檔（利用 Docker 快取加速構建）
COPY pyproject.toml uv.lock README.md ./

# 6. 使用 uv 嚴格對照 uv.lock 安裝環境
RUN uv sync --frozen --no-dev

# 7. 將 uv 建立的 .venv 環境加入 PATH，讓後續指令可以直接呼叫 uvicorn
ENV PATH="/app/.venv/bin:$PATH"

# 8. 複製後端主要程式碼
COPY . .

# 9. 啟動 FastAPI 伺服器
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]