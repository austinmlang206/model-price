# Model Price Backend

AI 模型定价 API 服务，基于 FastAPI 构建。

## 技术栈

- **Python** >= 3.12
- **FastAPI** - Web 框架
- **uvicorn** - ASGI 服务器
- **httpx** - 异步 HTTP 客户端
- **Playwright** - 浏览器自动化（用于爬虫）
- **Pydantic** - 数据验证
- **uv** - 包管理器

## 快速开始

### 安装依赖

```bash
uv sync
```

### 安装 Playwright 浏览器（首次运行）

```bash
uv run playwright install chromium
```

### 配置环境变量（可选）

```bash
cp .env.example .env
# 编辑 .env 进行配置
```

### 启动服务

```bash
uv run main.py
```

服务将在 http://localhost:8000 启动

- API 文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/models` | 获取所有模型价格（支持筛选和排序） |
| GET | `/api/models/{id}` | 获取单个模型详情 |
| PATCH | `/api/models/{id}` | 更新模型元数据 |
| GET | `/api/providers` | 获取所有提供商列表 |
| GET | `/api/families` | 获取模型系列列表 |
| GET | `/api/stats` | 获取统计信息 |
| POST | `/api/refresh` | 刷新定价数据（支持 `?provider=xxx` 筛选） |
| POST | `/api/refresh/metadata` | 刷新模型元数据 |
| GET | `/api/health` | 健康检查 |

## 项目结构

```
backend/
├── main.py              # FastAPI 应用入口
├── config.py            # 配置管理（Pydantic Settings）
├── models/              # Pydantic 数据模型
│   └── pricing.py
├── providers/           # 数据源提供者
│   ├── base.py          # 基类
│   ├── registry.py      # 提供者注册表
│   ├── aws_bedrock.py
│   ├── azure_openai.py
│   ├── openai.py
│   ├── google_gemini.py
│   ├── openrouter.py
│   └── xai.py
├── services/            # 业务逻辑
│   ├── pricing.py       # 定价服务
│   ├── fetcher.py       # 刷新调度
│   ├── metadata_fetcher.py      # 元数据获取
│   ├── openai_scraper.py        # OpenAI 爬虫
│   └── google_gemini_scraper.py # Gemini 爬虫
├── data/                # 数据存储
│   ├── index.json       # 模型索引
│   ├── model_metadata.json      # 模型元数据
│   ├── user_overrides.json      # 用户覆盖
│   ├── providers/       # 各提供商数据
│   └── fallback/        # 静态备份数据
└── pyproject.toml
```

## 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `HOST` | `0.0.0.0` | 服务监听地址 |
| `PORT` | `8000` | 服务端口 |
| `RELOAD` | `true` | 开发模式热重载 |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | 允许的跨域来源 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `HTTP_TIMEOUT` | `60.0` | HTTP 请求超时（秒） |

完整配置见 `.env.example`

## 数据获取方式

| 提供商 | 获取方式 | 技术方案 |
|--------|----------|----------|
| AWS Bedrock | 公开 API | httpx 异步请求 |
| Azure OpenAI | 公开 API | httpx + 分页 |
| OpenAI | 网页爬虫 | Playwright |
| Google Gemini | 网页爬虫 | Playwright |
| OpenRouter | 公开 API | httpx 异步请求 |
| xAI | 静态数据 | 硬编码 |

## 开发

### 添加依赖

```bash
uv add <package-name>
```

### 类型检查

```bash
uv run pyright
```

### 添加新的数据提供商

1. 在 `providers/` 下创建新文件，继承 `BaseProvider`
2. 实现 `fetch()` 方法
3. 在 `providers/__init__.py` 中导入并注册
