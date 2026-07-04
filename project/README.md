# project — 實戰專案 task-api

貫穿全書的實戰專案:一個以 **FastAPI** 打造的分層後端服務 `task-api`(任務管理 API),
把書中各 Part 的觀念(型別、pydantic 驗證、錯誤處理、測試、Web、分層架構、Repository/DI、部署)
串成一個真實可跑、可測的服務。

## 分層架構(依賴由外往內)

```text
project/app/
├── main.py                 # app factory:組裝各層 + /health + 例外處理(啟動進入點)
├── api/
│   ├── routes.py           # 路由層:HTTP ←→ service(Annotated 依賴注入)
│   └── deps.py             # FastAPI 依賴:取出 TaskService
├── service/
│   └── task_service.py     # 業務邏輯層:規則 + 領域例外(依賴 Repository 介面)
├── repository/
│   ├── base.py             # 資料存取介面:TaskRepository(Protocol)
│   └── memory.py           # 記憶體實作(可替換成 SQL 等)
├── models/
│   └── task.py             # 資料模型:pydantic schema + 領域實體
├── exceptions.py           # 領域例外(與 HTTP 解耦)
└── test_task_api.py        # 測試:HTTP 端到端(TestClient)+ service 單元
```

**設計重點**:業務層只依賴 `TaskRepository` **介面**(不知道背後是記憶體還是 DB),
透過**依賴注入**取得實作——可替換、可脫離 HTTP 測試(見 [Part 16 架構](../chapters/16-architecture/README.md))。

## API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/health` | 健康檢查 |
| GET | `/tasks` | 列出所有任務 |
| POST | `/tasks` | 建立任務(body: `{title, description?}`)→ 201 |
| GET | `/tasks/{id}` | 取得任務(不存在 → 404) |
| PATCH | `/tasks/{id}` | 部分更新 |
| POST | `/tasks/{id}/complete` | 標記完成 |
| DELETE | `/tasks/{id}` | 刪除 → 204 |

## 啟動與測試

```bash
pip install -e ".[web]"
uvicorn project.app.main:app --reload     # http://127.0.0.1:8000/docs

pytest project                            # 執行 task-api 測試
```

> 目前資料層為記憶體實作(重啟即清空)。後續可依 [Part 15 資料庫](../chapters/15-database/README.md)
> 新增 SQL Repository、依 [Part 31 部署](../chapters/31-cloud-platform-deployment/README.md) 上雲。
