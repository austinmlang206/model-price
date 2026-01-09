# Model Price

一个前后端分离的 AI 模型定价展示应用。

## 技术栈

- **后端**: Python + FastAPI + uv (包管理)
- **前端**: React + TypeScript + Vite

## 项目结构

```
model-price/
├── backend/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── models/              # Pydantic 数据模型
│   │   └── pricing.py
│   ├── providers/           # 数据源提供者
│   │   ├── base.py          # 基类
│   │   ├── registry.py      # 提供者注册表
│   │   ├── aws_bedrock.py
│   │   ├── azure_openai.py
│   │   ├── openai.py
│   │   ├── google_gemini.py
│   │   ├── openrouter.py
│   │   └── xai.py
│   ├── services/            # 业务逻辑
│   │   ├── pricing.py       # 定价服务
│   │   ├── fetcher.py       # 刷新调度
│   │   ├── metadata_fetcher.py      # 元数据获取
│   │   ├── openai_scraper.py        # OpenAI 爬虫
│   │   └── google_gemini_scraper.py # Gemini 爬虫
│   ├── data/                # 数据存储
│   │   ├── index.json       # 模型索引
│   │   ├── model_metadata.json      # 模型元数据
│   │   ├── user_overrides.json      # 用户覆盖
│   │   ├── providers/       # 各提供商数据
│   │   │   └── *.json
│   │   └── fallback/        # 静态备份数据
│   │       └── *.json
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── components/      # React 组件
│   │   │   ├── FilterBar.tsx
│   │   │   ├── ModelCard.tsx
│   │   │   ├── ModelTable.tsx
│   │   │   ├── RefreshButton.tsx
│   │   │   ├── CapabilityBadge.tsx
│   │   │   ├── ModalityIcons.tsx
│   │   │   └── ViewToggle.tsx
│   │   ├── config/          # 前端配置
│   │   │   ├── api.ts
│   │   │   ├── capabilities.ts
│   │   │   ├── providers.ts
│   │   │   ├── version.ts
│   │   │   └── visualization.ts
│   │   ├── hooks/
│   │   │   └── useModels.ts
│   │   └── types/
│   │       └── pricing.ts
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 快速开始

### 1. 启动后端

```bash
cd backend
uv run main.py
```

后端将在 http://localhost:8000 启动

API 文档: http://localhost:8000/docs

### 2. 启动前端

```bash
cd frontend
npm run dev
```

前端将在 http://localhost:5173 启动

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/models` | 获取所有模型价格（支持筛选和排序） |
| GET | `/api/models/{id}` | 获取单个模型详情 |
| PATCH | `/api/models/{id}` | 更新模型元数据 |
| GET | `/api/providers` | 获取所有提供商列表 |
| GET | `/api/families` | 获取模型系列列表 |
| GET | `/api/stats` | 获取统计信息 |
| POST | `/api/refresh` | 刷新定价数据（支持按提供商刷新） |
| POST | `/api/refresh/metadata` | 刷新模型元数据 |
| GET | `/api/health` | 健康检查 |

## 数据获取方式

本项目从多个渠道获取 AI 模型定价数据，以下是各渠道的数据获取技术方案：

### 汇总对比

| 渠道 | 数据获取方式 | 技术方案 | 是否需要认证 | 维护难度 |
|------|------------|---------|------------|---------:|
| **AWS Bedrock** | 公开 API | httpx 异步请求 | 无需 | 低 |
| **Azure OpenAI** | 公开 API | httpx + 分页 | 无需 | 低 |
| **OpenAI** | 网页爬虫 | Playwright | 无需 | 高 |
| **Google Gemini** | 网页爬虫 | Playwright | 无需 | 高 |
| **OpenRouter** | 公开 API | httpx 异步请求 | 无需 | 低 |
| **xAI** | 静态数据 | 硬编码 | N/A | 中 |

### 各渠道详细说明

#### 1. AWS Bedrock
- **数据来源**: AWS 公开定价 API（无需认证）
- **API 端点**:
  - `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/us-east-1/index.json`
  - `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/...`
- **技术方案**: 使用 `httpx` 异步请求，`asyncio.gather()` 并发获取两个数据源
- **数据解析**: 解析 products 和 terms 字段，正则匹配模型名称

#### 2. Azure OpenAI
- **数据来源**: Azure 零售价格 API（无需认证）
- **API 端点**: `https://prices.azure.com/api/retail/prices`
- **技术方案**: `httpx` 异步请求 + 自动分页处理
- **数据过滤**: 通过 `serviceName eq 'Foundry Models'` 筛选 AI 模型
- **价格标准化**: 将 1K 单位价格转换为每百万 token 价格

#### 3. OpenAI
- **数据来源**: 官方定价页面爬虫 + 静态数据备份
- **目标页面**: `https://platform.openai.com/docs/pricing`
- **技术方案**: **Playwright** 无头浏览器自动化爬取
- **爬虫特点**:
  - 自动安装 Chromium 浏览器
  - 模拟真实 User-Agent
  - 解析 HTML 表格和卡片布局
  - 处理多标签页（Standard、Batch 定价）
- **容错机制**: 爬虫失败时回退到代码中的静态数据

#### 4. Google Gemini
- **数据来源**: 官方定价页面爬虫 + 静态数据备份
- **目标页面**: `https://ai.google.dev/pricing`
- **技术方案**: **Playwright** 无头浏览器自动化爬取
- **容错机制**: 爬虫失败时回退到代码中的静态数据

#### 5. OpenRouter
- **数据来源**: 公开 RESTful API（无需认证）
- **API 端点**: `https://openrouter.ai/api/v1/models`
- **技术方案**: `httpx` 异步请求，API 结构清晰，实现最简洁
- **价格转换**: API 返回 per-token 价格，需乘以 1,000,000 转换

#### 6. xAI (Grok)
- **数据来源**: 静态数据（硬编码）
- **参考文档**: `https://docs.x.ai/docs/models`
- **原因**: xAI 没有提供公开的定价 API
- **维护方式**: 需要定期手动更新代码中的静态数据

### 技术栈

- **HTTP 客户端**: `httpx`（异步）
- **浏览器自动化**: `Playwright`（OpenAI、Google Gemini）
- **并发处理**: `asyncio`

## 开发

### 后端开发

```bash
cd backend

# 添加依赖
uv add <package-name>

# 运行开发服务器 (带热重载)
uv run main.py
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build
```
