# project — 實戰專案 task-api

貫穿全書的實戰專案：一個以 **FastAPI** 打造的分層後端服務 `task-api`（任務管理 API），
用來把書中各 Part 的觀念（型別、錯誤處理、測試、Web、資料庫、架構、部署）串成一個真實可跑的服務。

```text
project/
└── app/
    ├── main.py            # FastAPI 進入點
    ├── api/               # 路由層
    ├── service/           # 業務邏輯層
    ├── repository/        # 資料存取層
    └── models/            # 資料模型（pydantic / ORM）
```

啟動：

```bash
pip install -e ".[web]"
uvicorn project.app.main:app --reload
```

> 🚧 於 Part 14（Web）前後開始實作，隨後續 Part 逐步擴充（資料庫、架構、部署）。
