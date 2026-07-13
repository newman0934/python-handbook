# Python Handbook — 常用指令入口
# 註：Windows 需自備 make，或直接執行對應的 python/pytest 指令。

.PHONY: help install test test-all lint fmt type chapters run docker-build clean

help: ## 顯示可用指令
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## 安裝專案與開發依賴
	pip install -e ".[dev,web]"

test: ## 跑「已完成」測試（不含 exercises 的紅燈）
	pytest project examples solutions

test-all: ## 跑全部測試（含 exercises，預期部分紅燈）
	pytest

lint: ## ruff 檢查 + mypy 型別檢查 + 章節合規
	ruff check .
	mypy .
	python scripts/check_chapters.py

chapters: ## 章節合規檢查（模板區塊、連結、```python 語法）
	python scripts/check_chapters.py

fmt: ## ruff 自動格式化
	ruff format .
	ruff check --fix .

type: ## 只跑 mypy
	mypy .

run: ## 啟動實戰專案 task-api
	uvicorn project.app.main:app --reload

docker-build: ## 建置 task-api 映像
	docker build -t python-handbook-task-api .

clean: ## 清理快取
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
