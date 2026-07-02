# 多階段建置：實戰專案 task-api（見 project/）
# Part 14 前後會補上 project/ 內容，此 Dockerfile 先定義部署骨架。

# ---- builder：安裝依賴 ----
FROM python:3.12-slim AS builder

WORKDIR /app

# 只複製依賴宣告，善用 layer 快取
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[web]"

# ---- runtime：精簡執行環境 ----
FROM python:3.12-slim AS runtime

# 12-factor：以非 root 使用者執行
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

# 複製已安裝的套件與原始碼
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY project ./project

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# graceful shutdown 由 uvicorn 處理
CMD ["uvicorn", "project.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
