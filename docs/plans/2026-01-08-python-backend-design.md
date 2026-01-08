# Python 后端重构设计

## 概述

将 model-price 从纯前端 + TypeScript 后端重构为 Python (FastAPI) 后端 + React 前端的混合项目。

**目标：**
- 后端语言：TypeScript → Python (FastAPI)
- 为将来数据库持久化做准备（当前仍用 JSON 文件）
- 删除 CLI，所有功能通过 Web 界面操作
- 采用分层架构，代码清晰可维护

## 项目结构

```
model-price/
├── backend/                     # Python 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── models/              # Pydantic 数据模型
│   │   │   ├── __init__.py
│   │   │   └── pricing.py
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── pricing.py
│   │   │   └── sync.py
│   │   ├── providers/           # 数据源适配器
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── openrouter.py
│   │   │   ├── azure.py
│   │   │   ├── aws_bedrock.py
│   │   │   └── manual.py
│   │   └── routes/              # API 路由
│   │       ├── __init__.py
│   │       └── pricing.py
│   ├── requirements.txt
│   └── pyproject.toml
├── web/                         # 前端（React + Vite）
├── data/                        # 数据文件
│   ├── pricing.json
│   └── manual/
└── README.md
```

删除原 `src/` 目录（TypeScript 后端代码）。

## API 设计

```
GET  /api/models                 # 获取所有模型
     ?provider=openai            # 按供应商过滤
     ?capability=vision          # 按能力过滤
     ?q=gpt-4                    # 搜索

GET  /api/models/by-provider     # 按供应商分组返回

GET  /api/models/by-family       # 按模型家族分组

GET  /api/models/{id}            # 获取单个模型详情

GET  /api/providers              # 供应商列表及统计

GET  /api/stats                  # 整体统计信息

POST /api/sync                   # 触发同步
     ?provider=openai            # 可选：只同步指定供应商

GET  /api/health                 # 健康检查
```

**与原 API 的变化：**
- `/api/pricing` → `/api/models`
- `/api/pricing/by-model` → `/api/models/by-family`
- `/api/search?q=` → `/api/models?q=`（合并到 models 端点）
- 新增 `/api/health`

## 数据模型 (Pydantic)

```python
class Pricing(BaseModel):
    input: float
    output: float
    cached_input: float | None = None
    reasoning_output: float | None = None

class Capabilities(BaseModel):
    text: bool = True
    vision: bool = False
    audio: bool = False
    embedding: bool = False

class Model(BaseModel):
    id: str                         # "openai:gpt-4o"
    provider: str                   # "openai"
    model_id: str                   # "gpt-4o"
    name: str
    pricing: Pricing
    capabilities: Capabilities
    context_length: int | None = None
    max_output_tokens: int | None = None
    source: Literal["api", "manual"]
    updated_at: datetime

class Provider(BaseModel):
    id: str
    name: str
    model_count: int
    source: Literal["api", "manual"]

class SyncResult(BaseModel):
    provider: str
    success: bool
    models_count: int
    error: str | None = None
```

## Services 层

```python
# app/services/pricing.py
class PricingService:
    def __init__(self, data_path: Path):
        self.data_path = data_path

    def get_all(self, filters: dict | None = None) -> list[Model]: ...
    def get_by_id(self, model_id: str) -> Model | None: ...
    def get_by_provider(self) -> dict[str, list[Model]]: ...
    def get_by_family(self) -> dict[str, list[Model]]: ...
    def get_providers(self) -> list[Provider]: ...
    def get_stats(self) -> dict: ...
    def save(self, models: list[Model]) -> None: ...

# app/services/sync.py
class SyncService:
    def __init__(self, providers: list[BaseProvider], pricing_service: PricingService):
        self.providers = providers
        self.pricing_service = pricing_service

    async def sync_all(self) -> list[SyncResult]: ...
    async def sync_provider(self, provider_id: str) -> SyncResult: ...
```

**关键点：** 将来接数据库时，只需修改 `PricingService` 的实现。

## Providers 层

```python
# app/providers/base.py
class BaseProvider(ABC):
    id: str
    name: str
    source: str  # "api" | "manual"

    @abstractmethod
    async def fetch_models(self) -> list[Model]: ...

# 具体实现
class OpenRouterProvider(BaseProvider): ...   # OpenRouter API
class AzureProvider(BaseProvider): ...        # Azure 定价 API
class AWSBedrockProvider(BaseProvider): ...   # AWS Price List API
class ManualProvider(BaseProvider): ...       # data/manual/*.json
```

HTTP 客户端使用 `httpx`（支持异步）。

## 前端改动

新建 `web/src/api.ts` 封装 API 调用：

```typescript
const API_BASE = '/api';

export const api = {
  getModels: (params?: { provider?: string; q?: string }) =>
    fetch(`${API_BASE}/models?${new URLSearchParams(params)}`),

  getModelsByProvider: () =>
    fetch(`${API_BASE}/models/by-provider`),

  getModelsByFamily: () =>
    fetch(`${API_BASE}/models/by-family`),

  getProviders: () =>
    fetch(`${API_BASE}/providers`),

  getStats: () =>
    fetch(`${API_BASE}/stats`),

  sync: (provider?: string) =>
    fetch(`${API_BASE}/sync${provider ? `?provider=${provider}` : ''}`, { method: 'POST' }),
};
```

组件中替换硬编码的 API 路径为 `api.*` 调用。

## 配置与运行

**backend/app/config.py:**
```python
class Settings(BaseSettings):
    data_dir: Path = Path("../data")
    host: str = "0.0.0.0"
    port: int = 3001
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_prefix="APP_")
```

**依赖 (requirements.txt):**
```
fastapi>=0.115
uvicorn[standard]>=0.32
httpx>=0.27
pydantic>=2.0
pydantic-settings>=2.0
```

**package.json 脚本:**
```json
{
  "scripts": {
    "dev": "concurrently \"npm run server\" \"npm run web\"",
    "server": "cd backend && uvicorn app.main:app --reload --port 3001",
    "web": "cd web && vite",
    "build:web": "cd web && vite build"
  }
}
```

## 实施步骤

1. 创建 `backend/` 目录结构
2. 实现 Pydantic 数据模型
3. 实现 Providers 层（移植现有 TypeScript 逻辑）
4. 实现 Services 层
5. 实现 Routes 层
6. 创建 FastAPI 入口 (`main.py`)
7. 更新前端 API 调用
8. 更新 package.json 脚本
9. 删除 `src/` 目录
10. 测试所有功能
