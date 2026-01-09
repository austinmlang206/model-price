# Model Price

一个前后端分离的 AI 模型定价展示应用。

## 技术栈

- **后端**: Python + FastAPI + uv (包管理)
- **前端**: React + TypeScript + Vite

## 项目结构

```
model-price/
├── backend/           # Python 后端
│   ├── main.py        # FastAPI 应用入口
│   ├── pyproject.toml # uv 项目配置
│   └── uv.lock        # 依赖锁定文件
├── frontend/          # React 前端
│   ├── src/           # 源代码
│   ├── package.json   # npm 配置
│   └── vite.config.ts # Vite 配置
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
| GET | `/api/models` | 获取所有模型价格 |
| GET | `/api/models/{id}` | 获取单个模型详情 |
| POST | `/api/models` | 创建新模型记录 |
| DELETE | `/api/models/{id}` | 删除模型记录 |
| GET | `/api/health` | 健康检查 |

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

